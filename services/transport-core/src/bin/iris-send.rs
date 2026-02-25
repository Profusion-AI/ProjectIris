use std::{path::PathBuf, time::Duration};

use anyhow::{bail, Result};
use clap::Parser;
use iris_transport_core::{
    framing::{now_ns, write_frame, Frame},
    input::{collect_payloads, InputKind},
    profile::LatencyProfile,
    transport::{connect_publisher, ClientConnect},
};

#[derive(Parser, Debug)]
#[command(name = "iris-send", about = "Iris QUIC publisher")]
struct Args {
    #[arg(long, default_value = "127.0.0.1:7443")]
    relay: std::net::SocketAddr,

    #[arg(long, default_value = "localhost")]
    server_name: String,

    #[arg(long, default_value = "certs/relay-cert.pem")]
    ca_cert: PathBuf,

    #[arg(long)]
    control_token: Option<String>,

    #[arg(long)]
    stream_id: u32,

    #[arg(long, default_value = "real-time")]
    profile: LatencyProfile,

    #[arg(long, default_value_t = 30)]
    fps: u64,

    #[arg(long, default_value_t = 120)]
    frames: u64,

    #[arg(long, default_value_t = 1024)]
    payload_size: usize,

    #[arg(long)]
    input_file: Option<PathBuf>,

    #[arg(long, default_value_t = 8192)]
    chunk_size: usize,

    #[arg(long, default_value_t = 0)]
    stale_prefix_frames: u64,

    #[arg(long, default_value_t = 0)]
    stale_offset_ms: u64,
}

#[tokio::main]
async fn main() -> Result<()> {
    init_tracing();
    let args = Args::parse();

    if args.input_file.is_some() && args.frames > 0 && args.payload_size > 0 {
        // input_file wins by design. these args are harmless but likely accidental.
    }

    let input = match args.input_file {
        Some(path) => InputKind::File {
            path,
            chunk_size: args.chunk_size,
        },
        None => InputKind::Synthetic {
            frames: args.frames,
            payload_size: args.payload_size,
        },
    };

    let payloads = collect_payloads(&input).await?;
    if payloads.is_empty() {
        bail!("no frames to send")
    }

    let (_endpoint, _conn, mut send) = connect_publisher(
        &ClientConnect {
            relay_addr: args.relay,
            server_name: args.server_name,
            ca_cert_path: args.ca_cert,
            control_token: args.control_token,
        },
        args.stream_id,
        args.profile,
    )
    .await?;

    let frame_gap = Duration::from_millis(1_000 / args.fps.max(1));
    let stale_offset_ns = args.stale_offset_ms.saturating_mul(1_000_000);

    for (idx, payload) in payloads.into_iter().enumerate() {
        let mut ts = now_ns();
        if (idx as u64) < args.stale_prefix_frames {
            ts = ts.saturating_sub(stale_offset_ns);
        }
        let frame = Frame::data(args.stream_id, idx as u64, ts, payload);
        write_frame(&mut send, &frame).await?;
        tokio::time::sleep(frame_gap).await;
    }

    let _ = send.finish();
    Ok(())
}

fn init_tracing() {
    let filter = std::env::var("RUST_LOG").unwrap_or_else(|_| "info".to_string());
    let _ = tracing_subscriber::fmt()
        .with_env_filter(filter)
        .with_target(false)
        .try_init();
}
