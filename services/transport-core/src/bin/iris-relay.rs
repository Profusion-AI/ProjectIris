use std::path::PathBuf;

use anyhow::Result;
use clap::Parser;
use iris_transport_core::transport::{generate_self_signed_cert, run_relay, RelayConfig};

#[derive(Parser, Debug)]
#[command(name = "iris-relay", about = "Iris QUIC relay")]
struct Args {
    #[arg(long, default_value = "127.0.0.1:7443")]
    bind: std::net::SocketAddr,

    #[arg(long, default_value = "certs/relay-cert.pem")]
    cert: PathBuf,

    #[arg(long, default_value = "certs/relay-key.pem")]
    key: PathBuf,

    #[arg(long, default_value_t = false)]
    auto_cert: bool,

    #[arg(long)]
    required_control_token: Option<String>,
}

#[tokio::main]
async fn main() -> Result<()> {
    init_tracing();
    let args = Args::parse();

    if args.auto_cert {
        if let Some(parent) = args.cert.parent() {
            std::fs::create_dir_all(parent)?;
        }
        if !args.cert.exists() || !args.key.exists() {
            generate_self_signed_cert(&args.cert, &args.key)?;
        }
    }

    run_relay(RelayConfig {
        bind_addr: args.bind,
        cert_path: args.cert,
        key_path: args.key,
        required_control_token: args.required_control_token,
    })
    .await
}

fn init_tracing() {
    let filter = std::env::var("RUST_LOG").unwrap_or_else(|_| "info".to_string());
    let _ = tracing_subscriber::fmt()
        .with_env_filter(filter)
        .with_target(false)
        .try_init();
}
