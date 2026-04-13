# Rust extra credit — how this project uses memory and thread safety

This document is for readers new to Rust. It explains what the compiler gives you here and how it differs from a typical C + `pthread` solution.

## The problem

Several threads share one linked list of employee records. They must:

1. Start in a fixed **turn order** (thread 0, then 1, …) so grading traces are understandable.
2. Protect the list with **reader–writer** rules: many readers OR one writer.

In C you would use `pthread_mutex_t`, `pthread_cond_t`, and either a hand-rolled RW lock or a library. You must not mis-order lock/unlock or free nodes while another thread still reads them.

## Ownership and `Arc`

In Rust, every value has a single owner. To share the same table, logger, and turn manager across threads, this project wraps them in **`Arc<T>`** (atomic reference counting). Cloning an `Arc` is cheap and gives another handle to the **same** heap data; the data is freed when the last `Arc` goes away.

There is no manual `free()` of the shared table; dropping the last `Arc` cleans up.

## `RwLock` — safe many-readers / one-writer

The list lives inside **`Arc<RwLock<HashTable>>`**.

- **`read()`** returns a guard that allows concurrent reads with other readers, but blocks while a writer holds the lock. `search` and `print` use read guards.
- **`write()`** is exclusive: one writer at a time, no readers. `insert`, `delete`, and `update` use write guards.

The type system prevents you from mutating the list while only holding a read guard, which avoids data races at compile time.

## `Mutex` + `Condvar` — turn order

Turn order is **not** the same problem as protecting the list. A separate **`TurnManager`** holds a **`Mutex<usize>`** (current turn) and a **`Condvar`**. Threads wait in a loop until `current_turn == my_id`, then the winner increments the counter and notifies others.

This matches the course idea: condition variables answer “whose turn to run?”, while the `RwLock` answers “who may touch the shared list?”.

## Poisoned locks

If a thread panics while holding a mutex, Rust marks the lock as **poisoned**. This code uses **`unwrap_or_else(|e| e.into_inner())`** to recover the inner data and keep going; for coursework, panics in workers are avoided.

## Linked list without raw pointers

Nodes use **`Option<Box<Node>>`**. Each `Box` owns its node; `Option` represents end-of-list. There is no `NULL` pointer arithmetic; the compiler checks that `next` is only followed when it is `Some`.

## `unsafe`

This project uses **only safe Rust** for the table and synchronization. No `unsafe` blocks are required for the assignment logic.

## Compared to C

| C style | Rust style here |
|--------|-------------------|
| `malloc` / `free` for nodes | `Box` + automatic drop |
| `pthread_mutex_lock` around everything | `RwLock` for reads vs writes |
| Global pointers | `Arc` + locks |
| Data races if you forget a lock | Compile-time checks on guard lifetimes |

## Further reading

- The Rust Book: [Concurrency](https://doc.rust-lang.org/book/ch16-00-concurrency.html), [`Arc` and `Mutex`](https://doc.rust-lang.org/book/ch16-03-shared-state.html)
- `std::sync` docs: `RwLock`, `Condvar`, `Mutex`
