# Rust Explanation for a New Reader

This file is written for someone who is new to Rust and new to concurrency.

The goal of this project is to implement a **concurrent hash table** for the PA2 assignment. In this repository, the program:

- reads commands from `commands.txt`
- spawns one thread per command
- stores employee records in a shared table
- prints command results to `stdout`
- writes thread and lock activity to `hash.log`

The current code uses:

- `Arc` to share the same data across threads
- `RwLock` to protect the shared table
- `Mutex + Condvar` to control turn order
- `Box` and `Option` to build a linked list safely

---

## 1. What problem is this code solving?

Several threads need to work with the **same linked list** of records.

Each record has:

- a hash
- a name
- a salary

The threads run commands like:

- `insert`
- `delete`
- `update`
- `search`
- `print`

Two different synchronization problems must be solved:

### A. Who is allowed to touch the shared table?
That is the **reader-writer lock** problem.

- Multiple readers should be allowed at the same time.
- A writer must be alone.
- Readers and writers must not corrupt the list.

### B. Which thread is allowed to start next?
That is the **turn-order** problem.

The assignment wants commands to start in priority order, so the project uses a separate turn manager for that.

These are two different jobs, so the code uses **two different synchronization mechanisms**.

---

## 2. Big idea: Rust separates ownership and access

Rust tries to prevent common memory and concurrency bugs *before the program runs*.

In a C version of this assignment, you would probably use:

- `malloc()` / `free()` for linked-list nodes
- `pthread_mutex_t`
- `pthread_cond_t`
- maybe a custom reader-writer lock

That can work, but it is easy to make mistakes such as:

- forgetting to free memory
- freeing a node too early
- reading a node that has already been deleted
- mutating shared data without the correct lock
- unlocking the wrong lock, or unlocking too late

Rust does not magically remove all mistakes, but it helps by making many unsafe patterns hard or impossible to express in safe code.

---

## 3. `Arc`: shared ownership across threads

In Rust, every value has an owner.

Normally, one value has one owner. But in this project, the same shared objects must be used by many threads:

- the hash table
- the turn manager
- the logger

To do that, the project wraps them in `Arc`.

`Arc` means **Atomic Reference Counted pointer**.

You can think of it like this:

- one shared object lives on the heap
- many threads can hold handles to it
- cloning an `Arc` does **not** copy the whole object
- it only creates another shared handle
- when the last handle goes away, the object is automatically cleaned up

In this project, `main.rs` creates shared values like:

- `Arc<RwLock<HashTable>>`
- `Arc<TurnManager>`
- `Arc<Logger>`

Then each worker thread gets clones of those `Arc`s.

That is how many threads can safely refer to the same table, same turn manager, and same logger.

---

## 4. `RwLock`: many readers or one writer

The shared hash table is wrapped in:

```rust
Arc<RwLock<HashTable>>
```

This means:

- `Arc` = shared ownership across threads
- `RwLock` = access control for readers and writers

### Read lock
When code calls `read()`, it gets a **read guard**.

That guard allows reading the table, but not modifying it.

Many threads can hold read guards at the same time.

This is used for:

- `search`
- `print`

### Write lock
When code calls `write()`, it gets a **write guard**.

That guard allows modifying the table.

Only one thread may hold a write guard at a time, and no readers may hold read guards at the same time.

This is used for:

- `insert`
- `delete`
- `update`

### Why is this nice in Rust?
The guard itself controls the lifetime of the lock.

That means:

- when the guard exists, the lock is held
- when the guard goes out of scope, the lock is released automatically

So instead of manually remembering every unlock in every path, Rust lets scope and ownership help manage lock lifetime.

That makes the code easier to reason about and reduces some common mistakes.

---

## 5. `Mutex + Condvar`: turn order is a separate problem

The hash table lock is not used to decide **whose turn it is**.

That would mix two different concerns together.

Instead, the project uses a separate type called `TurnManager`, which internally uses:

- `Mutex<usize>`
- `Condvar`

The `usize` stores the current allowed turn.

The logic is:

1. each thread knows its priority / turn number
2. it calls `wait_until_turn(my_id)`
3. if it is not that thread's turn yet, it waits on the condition variable
4. when the correct thread starts, it continues
5. later, the turn manager increments the turn and notifies waiting threads

So:

- `TurnManager` answers: **Who is allowed to start now?**
- `RwLock<HashTable>` answers: **Who is allowed to read or write the table now?**

That separation is very important for understanding the design.

---

## 6. One worker thread, step by step

A worker thread in `src/main.rs` follows this general flow:

### Step 1: wait for its turn
The thread logs:

- `WAITING FOR MY TURN`

Then it blocks until the turn manager says its priority is allowed to start.

### Step 2: wake up
The thread logs:

- `AWAKENED FOR WORK`

Now it can begin processing its command.

### Step 3: log the command
The thread logs the command it is about to perform, such as:

- `INSERT,...`
- `DELETE,...`
- `UPDATE,...`
- `SEARCH,...`
- `PRINT`

### Step 4: acquire the correct table lock
Depending on the command:

- `insert`, `delete`, `update` use a **write lock**
- `search`, `print` use a **read lock**

The lock acquisition is also logged.

### Step 5: advance the turn
Once the thread has the lock it needs, it advances the turn so the next priority thread may begin trying to run.

This means:

- start order is still controlled
- but useful overlap is still possible when the lock type allows it

For example, another reader may start while a reader is still active.

### Step 6: do the actual work
Examples:

- insert a new record
- delete a record
- update salary
- search by hash
- format the database into a printable string

### Step 7: release the lock
When the guard goes out of scope, the lock is released.

Then the thread logs:

- `READ LOCK RELEASED`
- or `WRITE LOCK RELEASED`

### Step 8: send stdout text back to `main`
The worker does not print directly in random thread order.

Instead, it sends `(priority, stdout_text)` through a channel.

### Step 9: `main` prints output in order
The main thread gathers all worker outputs, sorts them by priority, and prints them in order.

This keeps the final `stdout` stable and easier to grade.

---

## 7. How the linked list works without raw pointers

The table is implemented as a **sorted singly linked list** in `src/table.rs`.

The main data structure is conceptually like this:

- `HashTable` has `head`
- `head` is an `Option<Box<Node>>`
- each `Node` contains:
	- a `Record`
	- another `Option<Box<Node>>` called `next`

### Why `Box`?
`Box<T>` means a value stored on the heap with one owner.

A linked-list node points to the next node, so heap allocation makes sense here.

### Why `Option`?
In C, you might use `NULL` for "no next node".

In Rust, `Option<Box<Node>>` means:

- `Some(node)` = there is a next node
- `None` = end of list

This is safer and clearer than manually checking null pointers.

### Why this helps beginners
It is still a linked list, but the language helps express:

- whether a next node exists
- who owns each node
- when nodes are dropped automatically

There is no manual `free()` call in the linked list code.

When a node is removed and no owner remains, Rust drops it automatically.

---

## 8. CRUD operations in this project

The table supports the expected assignment operations:

### Insert
- compute the Jenkins hash
- take a write lock
- insert into the sorted list
- reject duplicates by hash

### Delete
- compute the hash
- take a write lock
- remove the matching node if it exists

### Update
- compute the hash
- take a write lock
- change the salary if found

### Search
- compute the hash
- take a read lock
- return a cloned record if found

### Print
- take a read lock
- build a string that starts with `Current Database:`
- list records in ascending hash order

The list stays sorted by hash, so print output comes out in sorted order.

---

## 9. Why `search()` returns a clone

In this code, search returns an owned `Record` value instead of a reference into the shared list.

That is useful because:

- the read guard can be released after the search
- the caller gets its own safe copy of the data
- no borrowed reference escapes the lock guard lifetime

For a beginner, this is a good example of Rust choosing a simple safe design even if it may copy a small amount of data.

---

## 10. Logging and why `Logger` uses a `Mutex`

Many worker threads write to the same `hash.log`.

If they all wrote to the file at the same time without coordination, the log lines could interleave and become messy.

So `Logger` uses a `Mutex` around the writer.

That means only one thread writes one log line at a time.

The logger also keeps counts of:

- lock acquisitions
- lock releases

At the end, it writes a footer with:

- `Number of lock acquisitions`
- `Number of lock releases`
- `Final Table:`

This is helpful for debugging and checking lock balance.

---

## 11. What is a poisoned lock?

Rust mutexes can become **poisoned** if a thread panics while holding the lock.

That is Rust's way of saying:

> "Something may have gone wrong while protected data was being used."

This project uses:

```rust
unwrap_or_else(|e| e.into_inner())
```

to recover the inner value even if the lock is poisoned.

For coursework, this is a practical way to keep the program going instead of immediately stopping.

For a beginner, the key idea is:
- poisoning is Rust's warning mechanism
- this code chooses to recover and continue

---

## 12. Why this Rust version is safer than a typical C version

Here is a simple comparison.

| In a typical C solution | In this Rust solution |
|---|---|
| Manual `malloc()` / `free()` for nodes | `Box` and automatic drop |
| `NULL` checks for next pointers | `Option<Box<Node>>` |
| Shared pointers can be aliased freely | Shared ownership must be explicit with `Arc` |
| Easy to mix up who owns what | Ownership is part of the type system |
| Lock/unlock mistakes are easier to make | Lock guards release automatically when scope ends |
| Data races possible if locks are used incorrectly | Safe Rust prevents unsynchronized mutation through shared references |

This does **not** mean Rust makes concurrency easy.

It means Rust forces you to express ownership and synchronization more clearly.

That is very useful in a project like this one.

---

## 13. Where each concept appears in this repository

### `src/main.rs`
This is the main orchestration file.

It:
- reads `commands.txt`
- creates the shared `Arc` values
- spawns one thread per command
- gathers worker outputs through a channel
- prints stdout in sorted priority order
- writes the `hash.log` footer

### `src/sync.rs`
This contains `TurnManager`.

It:
- stores the current turn in a `Mutex`
- uses a `Condvar` to put threads to sleep until it is their turn
- wakes up waiting threads when the turn advances

### `src/table.rs`
This contains the linked-list hash table.

It:
- stores records in sorted order
- implements insert, delete, update, search, and print formatting

### `src/logger.rs`
This contains the log writer.

It:
- writes timestamped lines to `hash.log`
- serializes file writes with a mutex
- counts lock acquire/release events
- writes the final footer

---

## 14. A short mental model for a beginner

If you only remember one thing, remember this:

- `Arc` = many threads can own the same shared object
- `RwLock` = many readers or one writer
- `Mutex + Condvar` = whose turn is it?
- `Box` = heap-owned node
- `Option` = maybe there is a next node, maybe not

That is the whole project in one small picture:

- **shared ownership**
- **safe access**
- **clear turn order**
- **safe linked-list memory management**

---

## 15. Final takeaway

This project is a good Rust example because it combines:

- shared state
- multiple threads
- logging
- a linked list
- reader-writer synchronization
- condition-variable turn ordering

In a language like C, all of that is possible, but you must manage memory and synchronization very carefully by hand.

In this Rust version, the language helps enforce safer patterns:

- ownership is explicit
- lock lifetimes follow scope
- node memory is automatically freed
- safe code avoids raw-pointer bugs

That does not remove the need to think carefully, but it does make the code safer and easier to reason about.

---

## Further Reading

- The Rust Book, Chapter 16: Concurrency
- The Rust Book, Chapter 15: Smart Pointers
- Rust standard library docs for:
	- `Arc`
	- `RwLock`
	- `Mutex`
	- `Condvar`
	- `Option`
	- `Box`
