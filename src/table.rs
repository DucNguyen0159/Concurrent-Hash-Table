//! Sorted singly linked list keyed by Jenkins hash (collisions ignored for grading data).

use std::fmt::Write;

#[derive(Debug, Clone)]
pub struct Record {
    pub hash: u32,
    pub name: String,
    pub salary: u32,
}

impl Record {
    pub fn line(&self) -> String {
        format!("{},{},{}", self.hash, self.name, self.salary)
    }
}

#[derive(Debug)]
struct Node {
    record: Record,
    next: Option<Box<Node>>,
}

#[derive(Debug, Default)]
pub struct HashTable {
    head: Option<Box<Node>>,
}

impl HashTable {
    pub fn new() -> Self {
        Self { head: None }
    }

    pub fn insert(&mut self, record: Record) -> Result<(), Record> {
        insert_sorted(&mut self.head, record)
    }

    pub fn delete(&mut self, hash: u32) -> Option<Record> {
        delete_by_hash(&mut self.head, hash)
    }

    pub fn update(&mut self, hash: u32, new_salary: u32) -> Option<(Record, Record)> {
        update_by_hash(&mut self.head, hash, new_salary)
    }

    pub fn search(&self, hash: u32) -> Option<Record> {
        search_by_hash(&self.head, hash)
    }

    /// `Current Database:` plus one line per record, ascending hash, trailing newline.
    pub fn format_database(&self) -> String {
        let mut out = String::new();
        writeln!(out, "Current Database:").unwrap();
        let mut cur = self.head.as_ref();
        while let Some(n) = cur {
            writeln!(out, "{}", n.record.line()).unwrap();
            cur = n.next.as_ref();
        }
        out
    }

    /// One `hash,name,salary` string per node (for `hash.log` final table).
    pub fn record_lines(&self) -> Vec<String> {
        let mut v = Vec::new();
        let mut cur = self.head.as_ref();
        while let Some(n) = cur {
            v.push(n.record.line());
            cur = n.next.as_ref();
        }
        v
    }
}

fn insert_sorted(link: &mut Option<Box<Node>>, record: Record) -> Result<(), Record> {
    match link {
        None => {
            *link = Some(Box::new(Node {
                record,
                next: None,
            }));
            Ok(())
        }
        Some(node) if record.hash == node.record.hash => Err(record),
        Some(node) if record.hash < node.record.hash => {
            let take = link.take();
            *link = Some(Box::new(Node {
                record,
                next: take,
            }));
            Ok(())
        }
        Some(node) => insert_sorted(&mut node.next, record),
    }
}

fn delete_by_hash(link: &mut Option<Box<Node>>, hash: u32) -> Option<Record> {
    match link {
        None => None,
        Some(node) if node.record.hash == hash => {
            let mut boxed = link.take().unwrap();
            *link = boxed.next.take();
            Some(boxed.record)
        }
        Some(node) => delete_by_hash(&mut node.next, hash),
    }
}

fn update_by_hash(
    link: &mut Option<Box<Node>>,
    hash: u32,
    new_salary: u32,
) -> Option<(Record, Record)> {
    match link {
        None => None,
        Some(node) if node.record.hash == hash => {
            let old = node.record.clone();
            node.record.salary = new_salary;
            let new = node.record.clone();
            Some((old, new))
        }
        Some(node) => update_by_hash(&mut node.next, hash, new_salary),
    }
}

fn search_by_hash(link: &Option<Box<Node>>, hash: u32) -> Option<Record> {
    match link {
        None => None,
        Some(node) if node.record.hash == hash => Some(node.record.clone()),
        Some(node) => search_by_hash(&node.next, hash),
    }
}
