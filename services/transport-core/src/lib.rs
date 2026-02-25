pub mod framing;
pub mod input;
pub mod metrics;
pub mod profile;
pub mod transport;

pub const PROTOCOL_VERSION: u8 = 1;
pub const FLAG_CONTROL: u8 = 0b0000_0001;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ClientRole {
    Publisher,
    Subscriber,
}

impl ClientRole {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Publisher => "PUB",
            Self::Subscriber => "SUB",
        }
    }
}
