use std::sync::atomic::{AtomicU64, Ordering};

#[derive(Debug, Default)]
pub struct StreamMetrics {
    pub frames_in: AtomicU64,
    pub frames_out: AtomicU64,
    pub frames_dropped: AtomicU64,
    pub bytes_in: AtomicU64,
    pub bytes_out: AtomicU64,
    pub latency_acc_ns: AtomicU64,
    pub latency_samples: AtomicU64,
}

impl StreamMetrics {
    pub fn record_in(&self, payload_len: usize) {
        self.frames_in.fetch_add(1, Ordering::Relaxed);
        self.bytes_in
            .fetch_add(payload_len as u64, Ordering::Relaxed);
    }

    pub fn record_out(&self, payload_len: usize) {
        self.frames_out.fetch_add(1, Ordering::Relaxed);
        self.bytes_out
            .fetch_add(payload_len as u64, Ordering::Relaxed);
    }

    pub fn record_drop(&self) {
        self.frames_dropped.fetch_add(1, Ordering::Relaxed);
    }

    pub fn record_latency_ns(&self, ns: u64) {
        self.latency_acc_ns.fetch_add(ns, Ordering::Relaxed);
        self.latency_samples.fetch_add(1, Ordering::Relaxed);
    }

    pub fn snapshot(&self) -> MetricsSnapshot {
        let samples = self.latency_samples.load(Ordering::Relaxed);
        let total_ns = self.latency_acc_ns.load(Ordering::Relaxed);
        MetricsSnapshot {
            frames_in: self.frames_in.load(Ordering::Relaxed),
            frames_out: self.frames_out.load(Ordering::Relaxed),
            frames_dropped: self.frames_dropped.load(Ordering::Relaxed),
            bytes_in: self.bytes_in.load(Ordering::Relaxed),
            bytes_out: self.bytes_out.load(Ordering::Relaxed),
            avg_latency_ms: if samples == 0 {
                0.0
            } else {
                total_ns as f64 / samples as f64 / 1_000_000.0
            },
        }
    }
}

#[derive(Debug)]
pub struct MetricsSnapshot {
    pub frames_in: u64,
    pub frames_out: u64,
    pub frames_dropped: u64,
    pub bytes_in: u64,
    pub bytes_out: u64,
    pub avg_latency_ms: f64,
}
