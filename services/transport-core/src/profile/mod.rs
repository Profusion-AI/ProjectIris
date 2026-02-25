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
            Self::Realtime => 200,
            Self::Buffered => 10_000,
        }
    }

    pub fn playout_buffer_ms(self) -> u64 {
        match self {
            Self::Realtime => 0,
            Self::Buffered => 10_000,
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

#[cfg(test)]
mod tests {
    use super::LatencyProfile;

    #[test]
    fn profile_thresholds_are_tunable_and_explicit() {
        assert_eq!(LatencyProfile::Realtime.max_staleness_ms(), 200);
        assert_eq!(LatencyProfile::Buffered.playout_buffer_ms(), 10_000);
    }
}
