//! COP 4600 PA2 — concurrent hash table (Rust). Reads `commands.txt`, writes `hash.log`, stdout.

mod command;
mod hash;
mod logger;
mod sync;
mod table;

use command::Command;
use hash::jenkins_one_at_a_time;
use logger::Logger;
use sync::TurnManager;
use table::{HashTable, Record};

use std::io;
use std::sync::mpsc;
use std::sync::{Arc, RwLock};
use std::thread;

const COMMANDS_FILE: &str = "commands.txt";
const LOG_FILE: &str = "hash.log";

/// One thread per command; turn gate + `RwLock` on the shared table.
fn worker(
    cmd: Command,
    table: Arc<RwLock<HashTable>>,
    turns: Arc<TurnManager>,
    logger: Arc<Logger>,
    tx: mpsc::Sender<(usize, String)>,
) -> io::Result<()> {
    let id = cmd.priority();

    logger.log_waiting(id)?;
    turns.wait_until_turn(id);
    logger.log_awakened(id)?;

    let stdout = match cmd {
        Command::Insert {
            name,
            salary,
            priority,
        } => {
            let h = jenkins_one_at_a_time(&name);
            logger.log_command(
                id,
                &format!("INSERT,{},{},{}", h, name, salary),
            )?;
            logger.log_write_lock_acquired(priority)?;
            let res = {
                let mut g = table.write().unwrap_or_else(|e| e.into_inner());
                g.insert(Record {
                    hash: h,
                    name: name.clone(),
                    salary,
                })
            };
            logger.log_write_lock_released(priority)?;
            match res {
                Ok(()) => format!("Inserted {},{},{}\n", h, name, salary),
                Err(_) => format!(
                    "Duplicate entry:  Insert failed.  Entry {h} is a duplicate.\n"
                ),
            }
        }
        Command::Delete { name, priority } => {
            let h = jenkins_one_at_a_time(&name);
            logger.log_command(id, &format!("DELETE,{h},{name}"))?;
            logger.log_write_lock_acquired(priority)?;
            let removed = {
                let mut g = table.write().unwrap_or_else(|e| e.into_inner());
                g.delete(h)
            };
            logger.log_write_lock_released(priority)?;
            match removed {
                Some(rec) => format!("Deleted record for {}\n", rec.line()),
                None => format!("Entry {h} not deleted. Not in database.\n"),
            }
        }
        Command::Update {
            name,
            salary,
            priority,
        } => {
            let h = jenkins_one_at_a_time(&name);
            logger.log_command(
                id,
                &format!("UPDATE,{},{},{}", h, name, salary),
            )?;
            logger.log_write_lock_acquired(priority)?;
            let res = {
                let mut g = table.write().unwrap_or_else(|e| e.into_inner());
                g.update(h, salary)
            };
            logger.log_write_lock_released(priority)?;
            match res {
                Some((old, new)) => format!(
                    "Updated record {h} from {} to {}\n",
                    old.line(),
                    new.line()
                ),
                None => format!("Update failed. Entry {h} not found.\n"),
            }
        }
        Command::Search { name, priority } => {
            let h = jenkins_one_at_a_time(&name);
            logger.log_command(id, &format!("SEARCH,{h},{name}"))?;
            logger.log_read_lock_acquired(priority)?;
            let found = {
                let g = table.read().unwrap_or_else(|e| e.into_inner());
                g.search(h)
            };
            logger.log_read_lock_released(priority)?;
            match found {
                Some(rec) => format!("Found: {}\n", rec.line()),
                None => format!("{name} not found.\n"),
            }
        }
        Command::Print { priority } => {
            logger.log_command(id, "PRINT")?;
            logger.log_read_lock_acquired(priority)?;
            let block = {
                let g = table.read().unwrap_or_else(|e| e.into_inner());
                g.format_database()
            };
            logger.log_read_lock_released(priority)?;
            block
        }
    };

    // Release the next thread only after this command finishes (avoids e.g. PRINT before prior INSERTs).
    turns.advance_and_notify_all();

    tx.send((id, stdout)).map_err(|_| {
        io::Error::new(io::ErrorKind::BrokenPipe, "stdout collector dropped")
    })?;

    Ok(())
}

fn main() -> io::Result<()> {
    let (_, commands) = command::parse_commands_file(COMMANDS_FILE)?;
    let skip_extra_stdout_print = matches!(commands.last(), Some(Command::Print { .. }));

    let table = Arc::new(RwLock::new(HashTable::new()));
    let turns = Arc::new(TurnManager::new());
    let logger = Arc::new(Logger::create(LOG_FILE)?);

    let (tx, rx) = mpsc::channel::<(usize, String)>();

    let mut handles = Vec::new();
    for cmd in commands {
        let table = Arc::clone(&table);
        let turns = Arc::clone(&turns);
        let logger = Arc::clone(&logger);
        let tx = tx.clone();
        handles.push(thread::spawn(move || {
            if let Err(e) = worker(cmd, table, turns, logger, tx) {
                eprintln!("worker error: {e}");
            }
        }));
    }
    drop(tx);

    for h in handles {
        let _ = h.join();
    }

    let mut out: Vec<(usize, String)> = rx.into_iter().collect();
    out.sort_by_key(|(p, _)| *p);
    for (_, s) in out {
        print!("{s}");
    }

    if !skip_extra_stdout_print {
        let final_db = {
            let g = table.read().unwrap_or_else(|e| e.into_inner());
            g.format_database()
        };
        print!("{final_db}");
    }

    let final_lines = {
        let g = table.read().unwrap_or_else(|e| e.into_inner());
        g.record_lines()
    };
    logger.write_footer(&final_lines)?;

    Ok(())
}
