use anyhow::{anyhow, bail, Result};
use tokio::io::{AsyncRead, AsyncReadExt, AsyncWrite, AsyncWriteExt};

use crate::{FLAG_CONTROL, PROTOCOL_VERSION};

pub const HEADER_LEN: usize = 26;
pub const MAX_PAYLOAD_LEN: usize = 1024 * 1024;

#[derive(Debug, Clone)]
pub struct Frame {
    pub version: u8,
    pub flags: u8,
    pub stream_id: u32,
    pub seq_no: u64,
    pub timestamp_ns: u64,
    pub payload: Vec<u8>,
}

#[derive(Debug, Clone)]
pub struct ControlMessage {
    pub role: crate::ClientRole,
    pub stream_id: u32,
    pub profile: crate::profile::LatencyProfile,
    pub token: Option<String>,
}

impl Frame {
    pub fn control(stream_id: u32, payload: impl Into<Vec<u8>>) -> Self {
        Self {
            version: PROTOCOL_VERSION,
            flags: FLAG_CONTROL,
            stream_id,
            seq_no: 0,
            timestamp_ns: now_ns(),
            payload: payload.into(),
        }
    }

    pub fn data(stream_id: u32, seq_no: u64, timestamp_ns: u64, payload: Vec<u8>) -> Self {
        Self {
            version: PROTOCOL_VERSION,
            flags: 0,
            stream_id,
            seq_no,
            timestamp_ns,
            payload,
        }
    }

    pub fn is_control(&self) -> bool {
        self.flags & FLAG_CONTROL == FLAG_CONTROL
    }
}

pub async fn write_frame<W: AsyncWrite + Unpin>(writer: &mut W, frame: &Frame) -> Result<()> {
    let mut header = [0u8; HEADER_LEN];
    header[0] = frame.version;
    header[1] = frame.flags;
    header[2..6].copy_from_slice(&frame.stream_id.to_be_bytes());
    header[6..14].copy_from_slice(&frame.seq_no.to_be_bytes());
    header[14..22].copy_from_slice(&frame.timestamp_ns.to_be_bytes());

    let payload_len: u32 = frame
        .payload
        .len()
        .try_into()
        .map_err(|_| anyhow!("payload too large"))?;
    header[22..26].copy_from_slice(&payload_len.to_be_bytes());

    writer.write_all(&header).await?;
    writer.write_all(&frame.payload).await?;
    writer.flush().await?;
    Ok(())
}

pub async fn read_frame<R: AsyncRead + Unpin>(reader: &mut R) -> Result<Frame> {
    let mut header = [0u8; HEADER_LEN];
    reader.read_exact(&mut header).await?;

    let version = header[0];
    if version != PROTOCOL_VERSION {
        bail!("unsupported protocol version {version}");
    }

    let flags = header[1];
    let stream_id = u32::from_be_bytes(header[2..6].try_into()?);
    let seq_no = u64::from_be_bytes(header[6..14].try_into()?);
    let timestamp_ns = u64::from_be_bytes(header[14..22].try_into()?);
    let payload_len = u32::from_be_bytes(header[22..26].try_into()?) as usize;
    if payload_len > MAX_PAYLOAD_LEN {
        bail!("payload too large: {payload_len} > {MAX_PAYLOAD_LEN}");
    }

    let mut payload = vec![0u8; payload_len];
    reader.read_exact(&mut payload).await?;

    Ok(Frame {
        version,
        flags,
        stream_id,
        seq_no,
        timestamp_ns,
        payload,
    })
}

pub fn parse_control(
    frame: &Frame,
) -> Result<(crate::ClientRole, u32, crate::profile::LatencyProfile)> {
    let control = parse_control_message(frame)?;
    Ok((control.role, control.stream_id, control.profile))
}

pub fn parse_control_message(frame: &Frame) -> Result<ControlMessage> {
    if !frame.is_control() {
        bail!("expected control frame")
    }

    let cmd = String::from_utf8(frame.payload.clone())?;
    let mut parts = cmd.split_whitespace();
    let role = match parts.next() {
        Some("PUB") => crate::ClientRole::Publisher,
        Some("SUB") => crate::ClientRole::Subscriber,
        other => bail!("invalid control role: {:?}", other),
    };

    let stream_id: u32 = parts
        .next()
        .ok_or_else(|| anyhow!("missing stream id"))?
        .parse()?;

    let profile = parts
        .next()
        .ok_or_else(|| anyhow!("missing profile"))?
        .parse()?;

    let mut token = None;
    if let Some(part) = parts.next() {
        let value = part
            .strip_prefix("token=")
            .ok_or_else(|| anyhow!("invalid control token segment"))?;
        if value.is_empty() {
            bail!("empty control token");
        }
        token = Some(value.to_string());
    }

    if parts.next().is_some() {
        bail!("unexpected extra control frame segments");
    }

    Ok(ControlMessage {
        role,
        stream_id,
        profile,
        token,
    })
}

pub fn now_ns() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos() as u64)
        .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn roundtrip_frame() {
        let mut buf = Vec::new();
        let frame = Frame::data(10, 2, 12345, vec![1, 2, 3]);
        write_frame(&mut buf, &frame).await.expect("write frame");

        let mut cursor = std::io::Cursor::new(buf);
        let parsed = read_frame(&mut cursor).await.expect("read frame");

        assert_eq!(parsed.stream_id, 10);
        assert_eq!(parsed.seq_no, 2);
        assert_eq!(parsed.timestamp_ns, 12345);
        assert_eq!(parsed.payload, vec![1, 2, 3]);
    }

    #[test]
    fn parse_control_with_token() {
        let frame = Frame::control(10, "PUB 10 real-time token=signed-value");
        let parsed = parse_control_message(&frame).expect("control parse");
        assert_eq!(parsed.role, crate::ClientRole::Publisher);
        assert_eq!(parsed.stream_id, 10);
        assert_eq!(parsed.profile, crate::profile::LatencyProfile::Realtime);
        assert_eq!(parsed.token.as_deref(), Some("signed-value"));
    }

    #[tokio::test]
    async fn reject_oversized_payload() {
        let mut buf = Vec::new();
        let mut header = [0u8; HEADER_LEN];
        header[0] = PROTOCOL_VERSION;
        header[22..26].copy_from_slice(&((MAX_PAYLOAD_LEN + 1) as u32).to_be_bytes());
        buf.extend_from_slice(&header);

        let mut cursor = std::io::Cursor::new(buf);
        let err = read_frame(&mut cursor)
            .await
            .expect_err("expected oversized payload");
        assert!(err.to_string().contains("payload too large"));
    }
}
