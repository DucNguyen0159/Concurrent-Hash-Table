//! Timestamped `hash.log` lines; mutex-serialized; lock operation counters for footer.

use std::fs::File;
use std::io::{self, BufWriter, Write};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

pub struct Logger {
    writer: Mutex<BufWriter<File>>,
    lock_acquires: AtomicU64,
    lock_releases: AtomicU64,
}

impl Logger {
    pub fn create(path: &str) -> io::Result<Self> {
        let file = File::create(path)?;
        Ok(Self {
            writer: Mutex::new(BufWriter::new(file)),
            lock_acquires: AtomicU64::new(0),
            lock_releases: AtomicU64::new(0),
        })
    }

    fn timestamp_micros() -> u128 {
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map(|d| d.as_micros())
            .unwrap_or(0)
    }

    fn write_line(&self, body: &str) -> io::Result<()> {
        let ts = Self::timestamp_micros();
        let mut w = self
            .writer
            .lock()
            .unwrap_or_else(|e| e.into_inner());
        writeln!(w, "{}: {}", ts, body)?;
        w.flush()
    }

    pub fn log_waiting(&self, id: usize) -> io::Result<()> {
        self.write_line(&format!("THREAD {id} WAITING FOR MY TURN"))
    }

    pub fn log_awakened(&self, id: usize) -> io::Result<()> {
        self.write_line(&format!("THREAD {id} AWAKENED FOR WORK"))
    }

    pub fn log_command(&self, id: usize, msg: &str) -> io::Result<()> {
        self.write_line(&format!("THREAD {id} {msg}"))
    }

    pub fn log_read_lock_acquired(&self, id: usize) -> io::Result<()> {
        self.lock_acquires.fetch_add(1, Ordering::SeqCst);
        self.write_line(&format!("THREAD {id} READ LOCK ACQUIRED"))
    }

    pub fn log_read_lock_released(&self, id: usize) -> io::Result<()> {
        self.lock_releases.fetch_add(1, Ordering::SeqCst);
        self.write_line(&format!("THREAD {id} READ LOCK RELEASED"))
    }

    pub fn log_write_lock_acquired(&self, id: usize) -> io::Result<()> {
        self.lock_acquires.fetch_add(1, Ordering::SeqCst);
        self.write_line(&format!("THREAD {id} WRITE LOCK ACQUIRED"))
    }

    pub fn log_write_lock_released(&self, id: usize) -> io::Result<()> {
        self.lock_releases.fetch_add(1, Ordering::SeqCst);
        self.write_line(&format!("THREAD {id} WRITE LOCK RELEASED"))
    }

    /// Blank line, summary counts, `Final Table:` header, then one record line per line (no `Current Database:`).
    pub fn write_footer(&self, final_lines: &[String]) -> io::Result<()> {
        let mut w = self
            .writer
            .lock()
            .unwrap_or_else(|e| e.into_inner());
        writeln!(w)?;
        writeln!(
            w,
            "Number of lock acquisitions: {}",
            self.lock_acquires.load(Ordering::SeqCst)
        )?;
        writeln!(
            w,
            "Number of lock releases: {}",
            self.lock_releases.load(Ordering::SeqCst)
        )?;
        writeln!(w, "Final Table:")?;
        for ln in final_lines {
            writeln!(w, "{ln}")?;
        }
        w.flush()
    }
}
