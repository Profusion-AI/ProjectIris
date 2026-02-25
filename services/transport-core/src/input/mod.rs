use std::path::PathBuf;

use anyhow::{bail, Result};
use tokio::{fs::File, io::AsyncReadExt};

pub enum InputKind {
    Synthetic { frames: u64, payload_size: usize },
    File { path: PathBuf, chunk_size: usize },
}

pub async fn collect_payloads(kind: &InputKind) -> Result<Vec<Vec<u8>>> {
    match kind {
        InputKind::Synthetic {
            frames,
            payload_size,
        } => {
            let mut out = Vec::with_capacity(*frames as usize);
            for i in 0..*frames {
                let mut payload = vec![0u8; *payload_size];
                payload[0..8].copy_from_slice(&i.to_be_bytes());
                out.push(payload);
            }
            Ok(out)
        }
        InputKind::File { path, chunk_size } => {
            let mut file = File::open(path).await?;
            let mut out = Vec::new();
            loop {
                let mut buf = vec![0u8; *chunk_size];
                let n = file.read(&mut buf).await?;
                if n == 0 {
                    break;
                }
                buf.truncate(n);
                out.push(buf);
            }
            if out.is_empty() {
                bail!("file input produced zero frames")
            }
            Ok(out)
        }
    }
}
