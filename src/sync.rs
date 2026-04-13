//! Turn gate: threads start in strict priority order; advance + notify is separate so work can overlap.

use std::sync::{Condvar, Mutex};

pub struct TurnManager {
    turn: Mutex<usize>,
    cv: Condvar,
}

impl TurnManager {
    pub fn new() -> Self {
        Self {
            turn: Mutex::new(0),
            cv: Condvar::new(),
        }
    }

    /// Block until shared `turn == my_priority` (spurious wakeups handled).
    pub fn wait_until_turn(&self, my_priority: usize) {
        let mut t = self
            .turn
            .lock()
            .unwrap_or_else(|e| e.into_inner());
        while *t != my_priority {
            t = self
                .cv
                .wait(t)
                .unwrap_or_else(|e| e.into_inner());
        }
    }

    /// Increment turn and wake waiters so the next priority can start (call after logging AWAKENED).
    pub fn advance_and_notify_all(&self) {
        let mut t = self
            .turn
            .lock()
            .unwrap_or_else(|e| e.into_inner());
        *t += 1;
        self.cv.notify_all();
    }
}
