use std::str::FromStr;

use anyhow::{bail, Result};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum LatencyProfile {
    Realtime,
    Buffered,
}

impl LatencyProfile {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Realtime => "real-time",
            Self::Buffered => "buffered",
        }
    }

    pub fn max_staleness_ms(self) -> u64 {
        match self {
            Self::Realtime => 250,
            Self::Buffered => 10_000,
        }
    }

    pub fn playout_buffer_ms(self) -> u64 {
        match self {
            Self::Realtime => 0,
            Self::Buffered => 2_000,
        }
    }
}

impl FromStr for LatencyProfile {
    type Err = anyhow::Error;

    fn from_str(s: &str) -> Result<Self> {
        match s {
            "real-time" | "realtime" | "rt" => Ok(Self::Realtime),
            "buffered" | "buf" => Ok(Self::Buffered),
            _ => bail!("invalid profile {s}. use real-time or buffered"),
        }
    }
}
