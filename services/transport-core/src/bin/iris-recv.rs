use std::{io::Write, path::PathBuf};

use anyhow::Result;
use clap::Parser;
use iris_transport_core::{
    framing::{now_ns, read_frame},
    profile::LatencyProfile,
    transport::{connect_subscriber, ClientConnect},
};

#[derive(Parser, Debug)]
#[command(name = "iris-recv", about = "Iris QUIC subscriber")]
struct Args {
    #[arg(long, default_value = "127.0.0.1:7443")]
    relay: std::net::SocketAddr,

    #[arg(long, default_value = "localhost")]
    server_name: String,

    #[arg(long, default_value = "certs/relay-cert.pem")]
    ca_cert: PathBuf,

    #[arg(long)]
    stream_id: u32,

    #[arg(long, default_value = "real-time")]
    profile: LatencyProfile,

    #[arg(long, default_value_t = 120)]
    max_frames: u64,

    #[arg(long)]
    output_file: Option<PathBuf>,
}

#[tokio::main]
async fn main() -> Result<()> {
    init_tracing();
    let args = Args::parse();

    let (_endpoint, _conn, mut recv) = connect_subscriber(
        &ClientConnect {
            relay_addr: args.relay,
            server_name: args.server_name,
            ca_cert_path: args.ca_cert,
        },
        args.stream_id,
        args.profile,
    )
    .await?;

    let mut out: Box<dyn Write> = match args.output_file {
        Some(path) => Box::new(std::fs::File::create(path)?),
        None => Box::new(std::io::stdout()),
    };

    let mut total = 0u64;
    let mut latency_acc_ms = 0f64;

    while total < args.max_frames {
        let frame = match read_frame(&mut recv).await {
            Ok(frame) => frame,
            Err(_) => break,
        };

        let latency_ms = (now_ns().saturating_sub(frame.timestamp_ns)) as f64 / 1_000_000.0;
        latency_acc_ms += latency_ms;

        out.write_all(&frame.payload)?;
        total += 1;
    }

    if total > 0 {
        eprintln!(
            "received_frames={} avg_latency_ms={:.2}",
            total,
            latency_acc_ms / total as f64
        );
    }

    Ok(())
}

fn init_tracing() {
    let filter = std::env::var("RUST_LOG").unwrap_or_else(|_| "info".to_string());
    let _ = tracing_subscriber::fmt()
        .with_env_filter(filter)
        .with_target(false)
        .try_init();
}
