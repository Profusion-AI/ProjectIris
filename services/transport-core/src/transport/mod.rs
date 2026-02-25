use std::{collections::HashMap, net::SocketAddr, path::Path, sync::Arc, time::Duration};

use anyhow::{anyhow, Context, Result};
use quinn::{ClientConfig, Connection, Endpoint, RecvStream, SendStream, ServerConfig};
use tokio::sync::{broadcast, RwLock};
use tracing::{info, warn};

use crate::{
    framing::{now_ns, parse_control, read_frame, write_frame, Frame},
    metrics::StreamMetrics,
    profile::LatencyProfile,
};

#[derive(Clone)]
pub struct RelayConfig {
    pub bind_addr: SocketAddr,
    pub cert_path: std::path::PathBuf,
    pub key_path: std::path::PathBuf,
}

#[derive(Clone)]
pub struct ClientConnect {
    pub relay_addr: SocketAddr,
    pub server_name: String,
    pub ca_cert_path: std::path::PathBuf,
}

#[derive(Default)]
struct RelayState {
    channels: RwLock<HashMap<u32, broadcast::Sender<Frame>>>,
    metrics: StreamMetrics,
}

pub async fn run_relay(config: RelayConfig) -> Result<()> {
    let server_config = load_server_config(&config.cert_path, &config.key_path)?;
    let endpoint = Endpoint::server(server_config, config.bind_addr)?;
    let state = Arc::new(RelayState::default());

    info!("relay listening on {}", config.bind_addr);
    while let Some(incoming) = endpoint.accept().await {
        let state = state.clone();
        tokio::spawn(async move {
            match incoming.await {
                Ok(conn) => {
                    if let Err(e) = handle_connection(conn, state).await {
                        warn!(error = %e, "connection handling failed");
                    }
                }
                Err(e) => warn!(error = %e, "incoming connection failed"),
            }
        });
    }

    Ok(())
}

async fn handle_connection(conn: Connection, state: Arc<RelayState>) -> Result<()> {
    info!(remote = %conn.remote_address(), "new connection");
    loop {
        let (mut send, mut recv) = match conn.accept_bi().await {
            Ok(pair) => pair,
            Err(_) => return Ok(()),
        };

        let control = read_frame(&mut recv)
            .await
            .context("missing or invalid control frame")?;
        let (role, stream_id, profile) = parse_control(&control)?;

        match role {
            crate::ClientRole::Publisher => {
                let tx = channel_for_stream(&state, stream_id).await;
                let state_clone = state.clone();
                tokio::spawn(async move {
                    if let Err(e) = handle_publisher(stream_id, recv, tx, &state_clone).await {
                        warn!(error = %e, stream_id, "publisher closed with error");
                    }
                });
                let _ = send.finish();
            }
            crate::ClientRole::Subscriber => {
                let rx = channel_for_stream(&state, stream_id).await.subscribe();
                let state_clone = state.clone();
                tokio::spawn(async move {
                    if let Err(e) =
                        handle_subscriber(stream_id, profile, send, rx, &state_clone).await
                    {
                        warn!(error = %e, stream_id, "subscriber closed with error");
                    }
                });
            }
        }
    }
}

async fn channel_for_stream(state: &Arc<RelayState>, stream_id: u32) -> broadcast::Sender<Frame> {
    {
        let read = state.channels.read().await;
        if let Some(sender) = read.get(&stream_id) {
            return sender.clone();
        }
    }

    let mut write = state.channels.write().await;
    write
        .entry(stream_id)
        .or_insert_with(|| {
            let (tx, _rx) = broadcast::channel(2048);
            tx
        })
        .clone()
}

async fn handle_publisher(
    stream_id: u32,
    mut recv: RecvStream,
    tx: broadcast::Sender<Frame>,
    state: &Arc<RelayState>,
) -> Result<()> {
    loop {
        let frame = match read_frame(&mut recv).await {
            Ok(frame) => frame,
            Err(_) => break,
        };

        if frame.stream_id != stream_id {
            warn!(
                stream_id,
                got = frame.stream_id,
                "stream id mismatch from publisher"
            );
            continue;
        }

        state.metrics.record_in(frame.payload.len());
        let _ = tx.send(frame);
    }
    Ok(())
}

async fn handle_subscriber(
    stream_id: u32,
    profile: LatencyProfile,
    mut send: SendStream,
    mut rx: broadcast::Receiver<Frame>,
    state: &Arc<RelayState>,
) -> Result<()> {
    let mut buffered_started = false;

    loop {
        let frame = match rx.recv().await {
            Ok(frame) => frame,
            Err(tokio::sync::broadcast::error::RecvError::Lagged(skipped)) => {
                warn!(stream_id, skipped, "subscriber lagged");
                state.metrics.record_drop();
                continue;
            }
            Err(tokio::sync::broadcast::error::RecvError::Closed) => break,
        };

        let age_ms = (now_ns().saturating_sub(frame.timestamp_ns)) / 1_000_000;
        if profile == LatencyProfile::Realtime && age_ms > profile.max_staleness_ms() {
            state.metrics.record_drop();
            continue;
        }

        if profile == LatencyProfile::Buffered && !buffered_started {
            buffered_started = true;
            tokio::time::sleep(Duration::from_millis(profile.playout_buffer_ms())).await;
        }

        write_frame(&mut send, &frame).await?;
        state.metrics.record_out(frame.payload.len());
        let latency_ns = now_ns().saturating_sub(frame.timestamp_ns);
        state.metrics.record_latency_ns(latency_ns);
    }

    let _ = send.finish();
    let snap = state.metrics.snapshot();
    info!(
        stream_id,
        profile = profile.as_str(),
        frames_in = snap.frames_in,
        frames_out = snap.frames_out,
        frames_dropped = snap.frames_dropped,
        avg_latency_ms = snap.avg_latency_ms,
        "subscriber complete"
    );
    Ok(())
}

pub async fn connect_publisher(
    cfg: &ClientConnect,
    stream_id: u32,
    profile: LatencyProfile,
) -> Result<(Endpoint, Connection, SendStream)> {
    let (endpoint, conn) = connect(cfg).await?;
    let (mut send, _recv) = conn.open_bi().await?;
    let control = Frame::control(stream_id, format!("PUB {stream_id} {}", profile.as_str()));
    write_frame(&mut send, &control).await?;
    Ok((endpoint, conn, send))
}

pub async fn connect_subscriber(
    cfg: &ClientConnect,
    stream_id: u32,
    profile: LatencyProfile,
) -> Result<(Endpoint, Connection, RecvStream)> {
    let (endpoint, conn) = connect(cfg).await?;
    let (mut send, recv) = conn.open_bi().await?;
    let control = Frame::control(stream_id, format!("SUB {stream_id} {}", profile.as_str()));
    write_frame(&mut send, &control).await?;
    let _ = send.finish();
    Ok((endpoint, conn, recv))
}

async fn connect(cfg: &ClientConnect) -> Result<(Endpoint, Connection)> {
    let bind_addr: SocketAddr = "0.0.0.0:0".parse()?;
    let mut endpoint = Endpoint::client(bind_addr)?;
    endpoint.set_default_client_config(load_client_config(&cfg.ca_cert_path)?);

    let conn = endpoint
        .connect(cfg.relay_addr, &cfg.server_name)
        .map_err(|e| anyhow!("connect setup failed: {e}"))?
        .await
        .map_err(|e| anyhow!("connect failed: {e}"))?;

    Ok((endpoint, conn))
}

fn load_server_config(cert_path: &Path, key_path: &Path) -> Result<ServerConfig> {
    let cert_chain = load_certs(cert_path)?;
    let key = load_key(key_path)?;
    let mut server_config = ServerConfig::with_single_cert(cert_chain, key)?;
    let transport =
        Arc::get_mut(&mut server_config.transport).context("transport config not unique")?;
    transport.max_concurrent_bidi_streams(1024_u32.into());
    Ok(server_config)
}

fn load_client_config(ca_cert_path: &Path) -> Result<ClientConfig> {
    let mut roots = rustls::RootCertStore::empty();
    for cert in load_certs(ca_cert_path)? {
        roots.add(cert)?;
    }

    let tls = rustls::ClientConfig::builder()
        .with_root_certificates(roots)
        .with_no_client_auth();

    Ok(ClientConfig::new(Arc::new(
        quinn::crypto::rustls::QuicClientConfig::try_from(tls)?,
    )))
}

fn load_certs(path: &Path) -> Result<Vec<rustls::pki_types::CertificateDer<'static>>> {
    let cert_data =
        std::fs::read(path).with_context(|| format!("read cert file: {}", path.display()))?;
    let mut reader = std::io::BufReader::new(cert_data.as_slice());
    let certs: Vec<_> =
        rustls_pemfile::certs(&mut reader).collect::<std::result::Result<_, _>>()?;
    if certs.is_empty() {
        return Err(anyhow!("no certificates found in {}", path.display()));
    }
    Ok(certs)
}

fn load_key(path: &Path) -> Result<rustls::pki_types::PrivateKeyDer<'static>> {
    let key_data =
        std::fs::read(path).with_context(|| format!("read key file: {}", path.display()))?;
    let mut reader = std::io::BufReader::new(key_data.as_slice());

    if let Some(key) = rustls_pemfile::private_key(&mut reader)? {
        return Ok(key);
    }

    Err(anyhow!("no private key found in {}", path.display()))
}

pub fn generate_self_signed_cert(cert_path: &Path, key_path: &Path) -> Result<()> {
    let cert = rcgen::generate_simple_self_signed(vec!["localhost".into()])?;
    std::fs::write(cert_path, cert.serialize_pem()?)?;
    std::fs::write(key_path, cert.serialize_private_key_pem())?;
    Ok(())
}
