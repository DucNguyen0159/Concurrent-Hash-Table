//! Parse `commands.txt`: `threads,<n>,...` header plus command lines (comprehensive 4-field forms).

use std::fs::File;
use std::io::{self, BufRead, BufReader};
use std::num::ParseIntError;

#[derive(Debug, Clone)]
pub enum Command {
    Insert {
        name: String,
        salary: u32,
        priority: usize,
    },
    Delete {
        name: String,
        priority: usize,
    },
    Update {
        name: String,
        salary: u32,
        priority: usize,
    },
    Search {
        name: String,
        priority: usize,
    },
    Print {
        priority: usize,
    },
}

impl Command {
    pub fn priority(&self) -> usize {
        match self {
            Command::Insert { priority, .. }
            | Command::Delete { priority, .. }
            | Command::Update { priority, .. }
            | Command::Search { priority, .. }
            | Command::Print { priority } => *priority,
        }
    }
}

pub fn parse_commands_file(path: &str) -> io::Result<(usize, Vec<Command>)> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);
    let mut lines = reader.lines();

    let first = lines
        .next()
        .transpose()?
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidData, "empty commands.txt"))?;

    let thread_count = parse_threads_header(first.trim())?;

    let mut commands = Vec::new();
    for (idx, line) in lines.enumerate() {
        let line = line?;
        let trimmed = line.trim();
        if trimmed.is_empty() {
            continue;
        }
        let cmd = parse_command_line(trimmed).map_err(|e| {
            io::Error::new(
                io::ErrorKind::InvalidData,
                format!("line {}: {}", idx + 2, e),
            )
        })?;
        commands.push(cmd);
    }

    if thread_count != commands.len() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            format!(
                "threads header says {}, found {} command lines",
                thread_count,
                commands.len()
            ),
        ));
    }

    Ok((thread_count, commands))
}

fn parse_threads_header(line: &str) -> Result<usize, io::Error> {
    let parts: Vec<&str> = line.split(',').map(|s| s.trim()).collect();
    if parts.is_empty() || parts[0].to_lowercase() != "threads" {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "first line must start with threads,<count>,...",
        ));
    }
    parts[1]
        .parse()
        .map_err(|_| io::Error::new(io::ErrorKind::InvalidData, "invalid thread count"))
}

fn parse_u32(s: &str) -> Result<u32, String> {
    s.parse().map_err(|_: ParseIntError| format!("invalid u32: {s}"))
}

fn parse_usize(s: &str) -> Result<usize, String> {
    s.parse().map_err(|_: ParseIntError| format!("invalid usize: {s}"))
}

fn parse_command_line(line: &str) -> Result<Command, String> {
    let parts: Vec<&str> = line.split(',').map(|s| s.trim()).collect();
    if parts.is_empty() {
        return Err("empty command".into());
    }
    let head = parts[0].to_lowercase();
    match head.as_str() {
        "insert" => {
            if parts.len() < 4 {
                return Err("insert: need insert,<name>,<salary>,<priority>".into());
            }
            let priority = parse_usize(*parts.last().unwrap())?;
            let salary = parse_u32(parts[parts.len() - 2])?;
            let name = parts[1..parts.len() - 2].join(",");
            if name.is_empty() {
                return Err("insert: missing name".into());
            }
            Ok(Command::Insert {
                name,
                salary,
                priority,
            })
        }
        "delete" => {
            if parts.len() < 3 {
                return Err("delete: need at least delete,<name>,<priority>".into());
            }
            let priority = parse_usize(*parts.last().unwrap())?;
            let name = if parts.len() == 3 {
                parts[1].to_string()
            } else {
                parts[1..parts.len() - 2].join(",")
            };
            if name.is_empty() {
                return Err("delete: missing name".into());
            }
            Ok(Command::Delete { name, priority })
        }
        "update" => {
            if parts.len() < 4 {
                return Err("update: need update,<name>,<salary>,<priority>".into());
            }
            let priority = parse_usize(*parts.last().unwrap())?;
            let salary = parse_u32(parts[parts.len() - 2])?;
            let name = parts[1..parts.len() - 2].join(",");
            if name.is_empty() {
                return Err("update: missing name".into());
            }
            Ok(Command::Update {
                name,
                salary,
                priority,
            })
        }
        "search" => {
            if parts.len() < 3 {
                return Err("search: need at least search,<name>,<priority>".into());
            }
            let priority = parse_usize(*parts.last().unwrap())?;
            let name = if parts.len() == 3 {
                parts[1].to_string()
            } else {
                parts[1..parts.len() - 2].join(",")
            };
            if name.is_empty() {
                return Err("search: missing name".into());
            }
            Ok(Command::Search { name, priority })
        }
        "print" => {
            if parts.len() < 2 {
                return Err("print: need print,<priority> or print,...,<priority>".into());
            }
            let priority = parse_usize(*parts.last().unwrap())?;
            Ok(Command::Print { priority })
        }
        other => Err(format!("unknown command: {other}")),
    }
}
