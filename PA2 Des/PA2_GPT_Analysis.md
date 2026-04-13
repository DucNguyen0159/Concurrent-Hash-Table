All description file and supportive files are in PA2 Des folder, some are pdf files (but I turn into md files already, also in PA2 Des folder) so this is GPT version md file for Cursor to know about the project.

Here is the full picture of what this assignment is asking you to build, how it works, and what you need to understand before coding. The assignment is a concurrent hash table implemented in Rust for extra credit, based on a linked-list-backed table of records keyed by a 32-bit Jenkins hash of the name string. It supports insert, delete, update, search, and print, uses condition variables for ordered thread start, and uses a reader-writer lock to protect the shared linked list from corruption during concurrent access.

1. What the project is

A concurrent hash table lets multiple threads operate on one shared collection of key-value records without corrupting the data. In this assignment, each record stores:

a 32-bit hash
a name string up to 50 chars
a salary
a pointer to the next node

The project description explicitly says the table is implemented as a linked list of nodes, and the hash is computed from the key using Jenkins one-at-a-time hash. It also says you should ignore collisions for this assignment, because the provided grading data is guaranteed collision-free.

So even though it is called a “hash table,” this assignment is really closer to:

compute hash(name)
store/search/update/delete nodes in a linked list by that hash
protect the shared list with synchronization

That means you do not need to build a bucket array or collision chains for this assignment.

2. Core data model

The description shows this C-style structure:

hash: uint32_t
name: char[50]
salary: uint32_t
next: pointer to next record

In Rust, the equivalent concept is a linked list node with fields like:

hash: u32
name: String
salary: u32
next: Option<Box<Node>>

But because this is concurrent shared state, you usually will not expose raw mutation directly. You will likely wrap the whole list in synchronization primitives and let worker threads operate through safe methods.

3. Supported operations and what each must do

The assignment defines four data operations plus print:

Insert

insert(key, value) computes the hash of the name, acquires a write lock, searches the list for that hash, and if not found inserts a new node. If the hash already exists, it reports a duplicate error. Then it releases the write lock.

Delete

delete(key) computes the hash, acquires a write lock, searches the list, removes the node if found, otherwise does nothing except report the miss. Then releases the write lock.

Update

updateSalary(key, value) finds the matching node and updates its salary. Since this changes shared data, it should be treated as a write operation, even though the page describing functions is shorter here. Conceptually it must hold exclusive access while modifying the node.

Search

search(key) computes the hash, acquires a read lock, searches for the node, returns the value if found, otherwise returns null / not found, then releases the read lock. The caller prints either the record or “No Record Found” style output.

Print

print outputs the current database contents, sorted by hash, to stdout. The expected output page says the print command should show Current Database: followed by all records sorted by hash. Also, you must do one final print at the end of the run, even if the last command in the file is not print.

4. Important simplification: collisions are ignored

This matters a lot.

Normally, a hash table must handle two different names producing the same hash. This assignment says the grading data is guaranteed collision-free, so you can safely use the hash as the unique identity for searching/inserting/deleting for this project.

That means:

you do not need collision chains
you do not need open addressing
you do not need to compare original names after hash match for grading correctness

Still, keeping the original name is required because it is part of the record and output.

5. The hash function you must use

The project requires Jenkins one-at-a-time hash. The support PDF shows the function and gives sample values, and the project page directly links to it.

Conceptually it does this for each byte of the string:

add the byte to hash
mix with shifts and adds
after the loop, do final mixing

Why this matters:

every name becomes a deterministic 32-bit integer
that integer is what your operations use as the key
your print output is sorted by this hash

In Rust, you will implement the same logic over name.as_bytes() using u32 with wrapping arithmetic.

6. Input format

Your program must read a text file called commands.txt. The description says you should not read from console input and should hardcode that filename into the program.

The command formats shown in the assignment are:

insert,<name>,<salary>,<priority>
delete,<name>,<priority>
update,<name>,<new salary value>
search,<name>,<priority>
print,<priority>

However, the support command file you uploaded shows update commands with four fields, like:

update,Shigeru Miyamoto,90000,12
update,Hideo Kojima,97000,13

So in practice, your parser should be based on the actual supplied file format, not just the shortened description table. The support file strongly suggests that every command is associated with a thread priority/order number, including update.

That means your parser should probably accept:

insert,name,salary,priority
delete,name,priority
update,name,new_salary,priority
search,name,priority
print,priority

That is the safer interpretation for this project.

7. What “priority” means here

The priority field is not OS thread priority. It is the logical turn number used to enforce deterministic starting order across threads.

The expected-output support pages explain why this is needed:

condition variables ensure threads start in order
but they do not prevent the actual execution bodies from overlapping in time
the expensive hash computation can happen before lock acquisition, so multiple threads can be active concurrently
reader-writer locks are still needed to protect the shared linked list

This is one of the most important concepts in the whole assignment:

Condition variable solves:

“Whose turn is it to begin?”

Reader-writer lock solves:

“Who is allowed to touch shared memory right now?”

Those are different problems. The support PDF says this explicitly and even gives the deli-counter analogy: condition variables manage ordering, RW locks manage physical access to the shared data.

8. Thread behavior you are expected to implement

Each command should run as its own worker thread. The thread has a priority/turn number from the command file. The behavior is roughly:

thread starts and waits until current_turn == my_priority
when it is its turn, it logs “awakened”
it signals the next thread immediately
it computes the hash
it acquires the needed RW lock
it performs the operation on the linked list
it releases the lock
it prints the command result to stdout
it logs lock activity to hash.log

The support “Rationale for Priority Ordering AND Mutual Exclusion” pages make clear that signaling the next thread happens early, before the entire operation is finished, so threads can overlap and the assignment remains concurrent instead of becoming fully sequential.

9. Why signal-next-thread early?

Because if you wait until the full operation finishes before waking the next thread, the whole assignment becomes sequential and there is no real concurrency. The support PDF explicitly says that moving the signal to the end would eliminate concurrency entirely and defeat the purpose of the assignment.

So the intended design is:

ordered starts
overlapping execution
protected critical sections

That is exactly what your professor wants you to demonstrate.

10. Reader-writer lock concept

The provided rwlock.c support file shows the classic readers-writer lock design using semaphores:

a counter readers
a mutex protecting that counter
a separate writelock
first reader blocks writers
last reader releases writers
writers take exclusive lock directly

Meaning:

Read lock

Multiple readers may enter together, as long as no writer is active.

Write lock

Only one writer at a time, and no readers at the same time.

For your assignment:

search can use read lock
print should also use read lock if it only reads the list
insert, delete, update must use write lock
11. Starvation note

The support page says reader-writer locks are used partly to prevent writer starvation.

In plain words, starvation means one thread keeps waiting forever because other threads keep getting served first. In practice, the exact starvation behavior depends on the lock implementation you choose. In Rust, if you use the standard library RwLock, you get the implementation the platform provides, and strict fairness is not always guaranteed. For coursework, this is usually acceptable unless the professor specifically requires a custom fair RW lock.

12. What data structure operations must really do

Since the shared structure is a linked list, you need to understand these list operations clearly.

Search list by hash

Traverse from head until:

found matching hash, return node/reference
or hit end, not found
Insert into sorted order

The print requirement says output must be sorted by hash. The cleanest design is to keep the linked list itself always sorted by hash. Then print is easy and deterministic.

During insert:

if list empty, insert at head
if new hash smaller than head, insert before head
otherwise walk until correct position
reject if duplicate hash found
Delete node

Need to handle:

deleting head
deleting middle
deleting tail
deleting missing entry
Update salary

Find matching node and mutate salary only.

Print

Walk from head to tail and print every node in order. If you maintain sorted order during insert, no extra sorting step is needed.

That last choice is very important in Rust, because “clone all nodes into a vector, sort, print” is possible but more work than maintaining sorted order from the start.

13. What stdout must show

The project page gives expected styles for command feedback:

insert success: inserted values
insert duplicate: duplicate entry failed
update success: updated record from old values to new values
update miss: entry not found
delete success: deleted record
delete miss: entry not deleted, not in database
search hit: found values
search miss: <search string> not found
print: Current Database: plus all records sorted by hash

Exact punctuation and wording may matter for grading, so you should compare your output carefully against the expected-output PDF. That support file exists specifically to help match the grader’s format.

14. What goes into hash.log

The description requires diagnostic output in hash.log to prove synchronization is happening correctly. It says to log:

command execution start with parameters
waiting for turn
awakened for work
read lock acquired
read lock released
write lock acquired
write lock released

with timestamps in this style:

<timestamp>: THREAD <priority> <message>

It even provides a C snippet using gettimeofday() to get timestamps in microseconds. In Rust, you would usually use SystemTime::now() and convert to microseconds since UNIX epoch.

Also important: the log is for synchronization events, while command result messages go to stdout. Those are two separate outputs.

15. Commands file you uploaded: what it tells us

Your attached command file is valuable because it shows the actual style of workload your program must support. It includes:

first line: threads,60
then a long mix of insert/search/update/delete/print commands
priorities increasing from 0 up to 59

That first line almost certainly means:

total number of worker threads to create is 60

Then each subsequent command line corresponds to one thread and one priority/turn number.

That also implies your parser should probably:

read the first line
extract total thread count
read all later commands into a command list
spawn one thread per command
16. The meaning of “thread priority” in your file

From the command file, priorities appear to be unique and sequential:

insert,...,0
insert,...,1
insert,...,2
...
print,...,59

So your condition-variable scheduler can use a shared integer like current_turn, initially 0. Each thread waits until current_turn == my_priority, then increments it and wakes others.

That is much simpler than real priority scheduling. It is really just turn-based ordered start.

17. The two synchronization layers you need

This assignment makes the most sense if you think in two layers.

Layer 1: ordering

Shared state:

current_turn: usize
Mutex
Condvar

Purpose:

make sure thread 0 starts before thread 1
thread 1 before thread 2
etc.
Layer 2: list protection

Shared state:

the linked list
wrapped in an RwLock

Purpose:

allow multiple readers
exclude writers
prevent list corruption

This separation is exactly what the rationale document is teaching.

18. Rust concepts you need before coding

Since this is the Rust extra-credit version, these are the big Rust ideas you need.

Ownership

Only one owner of a value at a time. Shared structures across threads must be wrapped in shared smart pointers like Arc.

Borrowing

References let you access data without moving ownership. Rust checks that mutable and immutable access are safe.

Arc<T>

Atomic reference-counted shared ownership. Needed because multiple threads need access to the same shared table and synchronization objects.

Mutex<T>

Provides exclusive access to data. Good for current_turn, log file writing, and maybe command-result serialization if needed.

Condvar

Lets threads sleep until a condition becomes true. Perfect for “wait until it is my priority.”

RwLock<T>

Allows many readers or one writer. Perfect for the shared linked list.

Option<Box<Node>>

Common way to build linked lists in Rust.

thread::spawn

Creates threads.

JoinHandle

Lets the main thread wait for workers to finish.

Result

Rust error handling. You should use it for file reading/parsing and maybe lock poisoning cases.

19. One practical Rust design that fits this assignment well

A very clean design is:

Command enum
Node struct
LinkedList / HashTable struct
SharedState struct for turn ordering
Logger struct or shared log mutex
main()
Command

Enum with variants:

Insert { name, salary, priority }
Delete { name, priority }
Update { name, salary, priority }
Search { name, priority }
Print { priority }
Node

Holds hash, name, salary, next.

HashTable

Actually stores just:

head: Option<Box<Node>>

Methods:

insert
delete
update
search
print_all
Shared objects
Arc<(Mutex<usize>, Condvar)> for turn ordering
Arc<RwLock<HashTable>> for the list
Arc<Mutex<File>> for hash.log

That maps very naturally to the assignment requirements.

20. Behavior of each command under locking

Here is the intended operation flow.

Insert thread
wait for turn
log awakened
signal next thread
compute hash
acquire write lock
log write lock acquired
insert if not duplicate
log write lock released
release lock
print result
Delete thread

Same pattern, but remove node if found.

Update thread

Same pattern, but mutate salary if found.

Search thread
wait for turn
log awakened
signal next thread
compute hash
acquire read lock
log read lock acquired
search
log read lock released
release lock
print result
Print thread

Treat like a read-only traversal:

acquire read lock
print all nodes in sorted order
release read lock
21. Why hash computation should happen before lock

The rationale document specifically highlights this: expensive hash computation can happen before taking the RW lock, so multiple threads can overlap in that phase. That is how the program remains concurrent even though start order is controlled.

So do not hold the write lock while doing unrelated prep work longer than necessary. Acquire the lock only around the linked-list access.

22. Important grading detail about delete

The project page says delete may involve one or two sets of lock operations depending on implementation:

if delete calls search internally, you may see nested or repeated lock behavior
otherwise you may have only one set of operations

That tells you the grader likely allows either:

separate search then delete
or one direct traversal under write lock

In Rust, the direct traversal under one write lock is cleaner.

23. Final deliverables

The assignment page lists these final deliverables:

main program
Makefile
additional source files if modularized
README with anything graders need and AI citation
submit as a single zip file

Because you are doing Rust extra credit, page 4 also says you must include separate documentation teaching the project as if the reader were new to Rust, especially highlighting:

thread safety
memory safety
how Rust differs from C
features you used
preferably in Markdown, separate from README
24. Big C-to-Rust translation ideas

The assignment and sample lock file are written from a C viewpoint. In Rust:

C pointer-linked list

becomes

Option<Box<Node>>
manual memory free

becomes

automatic drop when ownership leaves scope
raw pthread lock style

becomes

Mutex, Condvar, RwLock
shared mutable globals

becomes

Arc<Mutex<T>> or Arc<RwLock<T>>
use-after-free / data race risk

becomes

blocked by Rust’s ownership and sync rules at compile time in normal safe Rust

That is a big part of why the extra credit exists.

25. Likely tricky parts in Rust

These are the parts most students struggle with.

A. Linked-list insert/delete with mutable references

Rust is strict about aliasing. Head insertion and middle deletion take care.

B. Sharing one table across threads

Need Arc<RwLock<HashTable>>.

C. Waiting by turn number

Need a Condvar loop, not if. Always do:

lock mutex
while current_turn != my_priority, wait
D. Log file writes from many threads

Need a Mutex<File> so log lines do not interleave.

E. Poisoned locks

If a thread panics while holding a lock, Rust marks it poisoned. For coursework, many students use .unwrap() and assume no panic, but more polished code handles it gracefully.

26. Definitions you should know cold

Here are the terms most likely to matter.

Concurrent

Multiple threads make progress during overlapping time.

Parallel

Multiple threads literally run at the same time on different CPU cores. Concurrent code may or may not be parallel.

Critical section

Code that touches shared mutable data and must be protected.

Mutual exclusion

Guarantee that only one conflicting access happens at a time.

Read lock

Shared lock for read-only access.

Write lock

Exclusive lock for modification.

Condition variable

A waiting/signaling primitive for coordination based on a condition.

Race condition

Result depends on unpredictable timing.

Data race

Two threads access same memory concurrently, at least one write, without proper synchronization.

Deadlock

Threads wait forever due to circular waiting.

Starvation

A thread never gets access because others keep beating it.

Deterministic ordering

Program behavior follows a reproducible logical order, useful for grading.

27. A good mental model for the whole project

Think of each command thread as doing two separate jobs:

Job 1: scheduling job
“Wait until it is my turn to begin.”

Job 2: data-structure job
“Safely perform my operation on the shared linked list.”

That mindset keeps condition-variable logic separate from hash-table logic, which makes the code much easier to reason about.

28. What you do not need for this project

Based on the description, you do not need:

real OS priority scheduling
collision resolution
dynamic resizing
bucket arrays
lock-free programming
custom memory allocators
unsafe Rust, unless you choose it for some reason

A safe-Rust solution with standard synchronization primitives is the right target.

29. Suggested implementation order

This is the order I would use.

Implement Jenkins hash in Rust.
Implement command parsing from commands.txt.
Implement a non-concurrent linked list with:
insert sorted
search
update
delete
print
Test single-thread correctness first.
Add RwLock around the table.
Add log file support.
Add condition variable turn ordering.
Spawn one thread per command.
Compare stdout and hash.log against the expected files.
Add the mandatory final print.

That order keeps debugging manageable.

30. Most likely grading failures

These are the things I would be extra careful about.

parsing the actual command format incorrectly, especially update with priority
forgetting the final print at the end
using mutex-only instead of RW lock
signaling next thread too late and accidentally making the program sequential
not logging wait/acquire/release events correctly to hash.log
not maintaining sorted order by hash for print output
mismatching exact output wording
allowing interleaved log lines without a file mutex
31. The biggest takeaway

The assignment is really testing three skills together:

data structures
linked-list insert/search/update/delete/print
concurrency
condition variables for ordered starts, RW lock for safe access
systems thinking
separate logical ordering from physical memory protection

That separation is the heart of the assignment, and the rationale support file makes that very explicit.

For the Rust version, I would create 7 files. That is not the only valid structure, but it is a clean modular design that matches the assignment well and avoids one giant file. The assignment explicitly says the deliverables include the main program, a Makefile, other source files if needed, and a README, and it encourages a modular design instead of a monolithic file. It also says the Rust extra credit needs a separate documentation file, preferably Markdown.

Files to create
1. src/main.rs

This is the entry point.

What it does:

reads commands.txt
parses the threads,... header and all commands
creates shared synchronization objects
spawns one thread per command
waits for all threads to finish
does the required final print
2. src/command.rs

This holds your command definitions.

What it should contain:

enum Command
parser logic for lines like:
insert,name,salary,priority
delete,name,priority
update,name,salary,priority
search,name,priority
print,priority

This file keeps parsing separate from concurrency and data structure code.

3. src/hash.rs

This contains the Jenkins one-at-a-time hash function.

What it does:

takes a &str
returns u32
uses wrapping arithmetic exactly like the required algorithm
4. src/table.rs

This is the actual linked-list hash table implementation.

What it should contain:

Node struct
HashTable struct
methods:
insert
delete
update
search
print_all

This file should focus only on list/data behavior, not threads.

5. src/sync.rs

This handles thread coordination.

What it should contain:

turn-order state using Mutex + Condvar
helper functions like:
wait_for_turn(priority)
signal_next()

This is where the “priority ordering” logic belongs.

6. src/logger.rs

This handles hash.log.

What it should contain:

shared file wrapper using Mutex<File>
helper methods like:
log_waiting(thread_id)
log_awakened(thread_id)
log_read_lock_acquired(thread_id)
log_read_lock_released(thread_id)
log_write_lock_acquired(thread_id)
log_write_lock_released(thread_id)
log_command(...)

This keeps log formatting consistent.

7. README.md

This is required for build/run instructions and AI citation. The project page says the README should include anything graders need to know and the AI use citation.

One more file for Rust extra credit

Because you are doing the Rust extra-credit version, I strongly recommend adding:

8. RUST_EXPLANATION.md

This is the separate Rust teaching document your professor asks for.

It should explain:

thread-safe features you used
memory-safe features you used
how Rust differs from C here
how your design works for someone new to Rust

The assignment specifically asks for a separate documentation file, preferably Markdown, and says not to use the README for that explanation.

So, how many files?
Minimum practical answer

7 files

src/main.rs
src/command.rs
src/hash.rs
src/table.rs
src/sync.rs
src/logger.rs
README.md
Best answer for full credit plus Rust extra credit

8 files

the 7 above
RUST_EXPLANATION.md


Recommended design
Here is the clean design I would use.

High-level architecture:

commands.txt
   |
   v
main.rs
   |
   +--> command.rs    -> parse input lines into Command enum
   +--> hash.rs       -> compute Jenkins hash
   +--> sync.rs       -> enforce turn ordering with Mutex + Condvar
   +--> logger.rs     -> write hash.log safely
   +--> table.rs      -> shared linked-list hash table protected by RwLock

Shared objects

Your threads should all share these:

Arc<RwLock<HashTable>>      // protects the linked list
Arc<(Mutex<usize>, Condvar)> // current turn / thread ordering
Arc<Mutex<File>>            // protects hash.log writes

Main flow:

main
 ├─ read commands.txt
 ├─ parse thread count and command list
 ├─ create shared table
 ├─ create shared turn-order controller
 ├─ create shared logger
 ├─ spawn one thread per command
 ├─ join all threads
 └─ do final print

Internal design
Command enum:
enum Command {
    Insert { name: String, salary: u32, priority: usize },
    Delete { name: String, priority: usize },
    Update { name: String, salary: u32, priority: usize },
    Search { name: String, priority: usize },
    Print  { priority: usize },
}

Node and HashTable:
struct Node {
    hash: u32,
    name: String,
    salary: u32,
    next: Option<Box<Node>>,
}

struct HashTable {
    head: Option<Box<Node>>,
}

The list should stay sorted by hash so print is easy and deterministic.

Thread design

Each worker thread should do this:

Worker flow

Thread starts
   |
   v
Log: WAITING FOR MY TURN
   |
   v
Wait on Condvar until current_turn == my_priority
   |
   v
Log: AWAKENED FOR WORK
   |
   v
Advance current_turn and signal next thread
   |
   v
Compute hash (if needed)
   |
   v
Acquire RwLock
   |
   +--> read lock for search/print
   |
   +--> write lock for insert/delete/update
   |
   v
Do operation on linked list
   |
   v
Release lock
   |
   v
Print command result to stdout
   |
   v
Thread exits

That matches the project’s intended separation between:

condition variables for ordered starts
reader-writer locking for shared data protection
State diagram

Here is a simple version of the thread state diagram.

+---------+
| Created |
+---------+
     |
     v
+----------------------+
| Waiting for My Turn  |
| (Condvar wait loop)  |
+----------------------+
     |
     | current_turn == my_priority
     v
+----------------------+
| Awakened / Start     |
| signal next thread   |
+----------------------+
     |
     v
+----------------------+
| Compute Hash         |
| (if command needs it)|
+----------------------+
     |
     v
+----------------------+
| Acquire Lock         |
| read or write        |
+----------------------+
     |
     v
+----------------------+
| Execute Operation    |
| insert/delete/etc.   |
+----------------------+
     |
     v
+----------------------+
| Release Lock         |
+----------------------+
     |
     v
+----------------------+
| Print Result / Log   |
+----------------------+
     |
     v
+---------+
|  Done   |
+---------+

More detailed state diagram by command type

                        +------------------+
                        |  Thread Created  |
                        +------------------+
                                  |
                                  v
                    +------------------------------+
                    | WAITING FOR MY TURN          |
                    | Mutex + Condvar              |
                    +------------------------------+
                                  |
                                  v
                    +------------------------------+
                    | AWAKENED                      |
                    | increment current_turn       |
                    | notify next thread          |
                    +------------------------------+
                                  |
                                  v
                    +------------------------------+
                    | PREPARE COMMAND              |
                    | parse fields / compute hash  |
                    +------------------------------+
                                  |
                +-----------------+------------------+
                |                                    |
                v                                    v
   +---------------------------+       +---------------------------+
   | READ PATH                 |       | WRITE PATH                |
   | search, print             |       | insert, delete, update    |
   +---------------------------+       +---------------------------+
                |                                    |
                v                                    v
   +---------------------------+       +---------------------------+
   | ACQUIRE READ LOCK         |       | ACQUIRE WRITE LOCK        |
   +---------------------------+       +---------------------------+
                |                                    |
                v                                    v
   +---------------------------+       +---------------------------+
   | READ LIST                 |       | MODIFY LIST               |
   +---------------------------+       +---------------------------+
                |                                    |
                v                                    v
   +---------------------------+       +---------------------------+
   | RELEASE READ LOCK         |       | RELEASE WRITE LOCK        |
   +---------------------------+       +---------------------------+
                \                                    /
                 \                                  /
                  v                                v
                    +------------------------------+
                    | PRINT RESULT TO STDOUT       |
                    | WRITE LOG ENTRIES            |
                    +------------------------------+
                                  |
                                  v
                        +------------------+
                        |       DONE       |
                        +------------------+

File-by-file responsibility diagram

main.rs
 ├─ calls parse_commands() from command.rs
 ├─ creates shared HashTable from table.rs
 ├─ creates turn controller from sync.rs
 ├─ creates logger from logger.rs
 ├─ spawns worker threads
 └─ performs final print

command.rs
 └─ converts each line into Command enum

hash.rs
 └─ computes Jenkins hash(name) -> u32

table.rs
 ├─ Node
 ├─ HashTable
 ├─ insert
 ├─ delete
 ├─ update
 ├─ search
 └─ print_all

sync.rs
 ├─ current_turn
 ├─ wait_for_turn()
 └─ signal_next()

logger.rs
 ├─ open hash.log
 └─ write synchronized log entries

My recommendation

Use the 8-file structure. It is neat, easy to debug, and matches the assignment better than stuffing everything into one file.

Best structure:

src/main.rs
src/command.rs
src/hash.rs
src/table.rs
src/sync.rs
src/logger.rs
README.md
RUST_EXPLANATION.md

Next, I can give you the exact folder structure plus starter code skeleton for every file.

One correction from my earlier message: for a real Rust project, you should also include Cargo.toml. So the clean full project is 10 files:

Cargo.toml
Makefile
src/main.rs
src/command.rs
src/hash.rs
src/table.rs
src/sync.rs
src/logger.rs
README.md
RUST_EXPLANATION.md

This code is designed to match the assignment structure: commands.txt is hardcoded, hash.log is produced, start order is controlled with Mutex + Condvar, and the shared linked list is protected with RwLock. That aligns with the project description and the support files.

One honest note before you use it: the logic is complete, but you should still do one final pass on the exact stdout wording against your professor’s expected-output PDF, because formatting differences are often what break grading scripts. The structure, behavior, synchronization, and file layout are all here.

1. Cargo.toml
[package]
name = "chash"
version = "0.1.0"
edition = "2021"

[dependencies]

2. Makefile
BINARY = chash

all:
	cargo build --release
	cp target/release/$(BINARY) ./$(BINARY)

run: all
	./$(BINARY)

clean:
	cargo clean
	rm -f $(BINARY) hash.log

.PHONY: all run clean

3. src/command.rs
use std::fs::File;
use std::io::{self, BufRead, BufReader};

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

    pub fn name(&self) -> Option<&str> {
        match self {
            Command::Insert { name, .. }
            | Command::Delete { name, .. }
            | Command::Update { name, .. }
            | Command::Search { name, .. } => Some(name.as_str()),
            Command::Print { .. } => None,
        }
    }

    pub fn log_message(&self, hash: Option<u32>) -> String {
        match self {
            Command::Insert { name, salary, .. } => {
                if let Some(h) = hash {
                    format!("INSERT,{},{},{}", h, name, salary)
                } else {
                    format!("INSERT,{},{}", name, salary)
                }
            }
            Command::Delete { name, .. } => {
                if let Some(h) = hash {
                    format!("DELETE,{},{}", h, name)
                } else {
                    format!("DELETE,{}", name)
                }
            }
            Command::Update { name, salary, .. } => {
                if let Some(h) = hash {
                    format!("UPDATE,{},{},{}", h, name, salary)
                } else {
                    format!("UPDATE,{},{}", name, salary)
                }
            }
            Command::Search { name, .. } => {
                if let Some(h) = hash {
                    format!("SEARCH,{},{}", h, name)
                } else {
                    format!("SEARCH,{}", name)
                }
            }
            Command::Print { .. } => "PRINT".to_string(),
        }
    }
}

pub fn parse_commands_file(path: &str) -> io::Result<(usize, Vec<Command>)> {
    let file = File::open(path)?;
    let reader = BufReader::new(file);

    let mut lines = reader.lines();
    let first_line = match lines.next() {
        Some(line) => line?,
        None => {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "commands.txt is empty",
            ))
        }
    };

    let total_threads = parse_threads_header(&first_line)?;

    let mut commands = Vec::new();

    for (idx, line) in lines.enumerate() {
        let line = line?;
        let trimmed = line.trim();

        if trimmed.is_empty() {
            continue;
        }

        let command = parse_command_line(trimmed).map_err(|msg| {
            io::Error::new(
                io::ErrorKind::InvalidData,
                format!("line {}: {}", idx + 2, msg),
            )
        })?;

        commands.push(command);
    }

    Ok((total_threads, commands))
}

fn parse_threads_header(line: &str) -> io::Result<usize> {
    let parts: Vec<&str> = line.split(',').map(|s| s.trim()).collect();
    if parts.len() != 2 || parts[0].to_lowercase() != "threads" {
        return Err(io::Error::new(
            io::ErrorKind::InvalidData,
            "first line must be: threads,<count>",
        ));
    }

    parts[1].parse::<usize>().map_err(|_| {
        io::Error::new(
            io::ErrorKind::InvalidData,
            "invalid thread count in threads header",
        )
    })
}

fn parse_command_line(line: &str) -> Result<Command, String> {
    let parts: Vec<&str> = line.split(',').map(|s| s.trim()).collect();
    if parts.is_empty() {
        return Err("empty command".to_string());
    }

    match parts[0].to_lowercase().as_str() {
        "insert" => {
            if parts.len() != 4 {
                return Err("insert must be: insert,<name>,<salary>,<priority>".to_string());
            }

            let salary = parts[2]
                .parse::<u32>()
                .map_err(|_| "invalid salary for insert".to_string())?;
            let priority = parts[3]
                .parse::<usize>()
                .map_err(|_| "invalid priority for insert".to_string())?;

            Ok(Command::Insert {
                name: parts[1].to_string(),
                salary,
                priority,
            })
        }
        "delete" => {
            if parts.len() != 3 {
                return Err("delete must be: delete,<name>,<priority>".to_string());
            }

            let priority = parts[2]
                .parse::<usize>()
                .map_err(|_| "invalid priority for delete".to_string())?;

            Ok(Command::Delete {
                name: parts[1].to_string(),
                priority,
            })
        }
        "update" => {
            if parts.len() != 4 {
                return Err("update must be: update,<name>,<salary>,<priority>".to_string());
            }

            let salary = parts[2]
                .parse::<u32>()
                .map_err(|_| "invalid salary for update".to_string())?;
            let priority = parts[3]
                .parse::<usize>()
                .map_err(|_| "invalid priority for update".to_string())?;

            Ok(Command::Update {
                name: parts[1].to_string(),
                salary,
                priority,
            })
        }
        "search" => {
            if parts.len() != 3 {
                return Err("search must be: search,<name>,<priority>".to_string());
            }

            let priority = parts[2]
                .parse::<usize>()
                .map_err(|_| "invalid priority for search".to_string())?;

            Ok(Command::Search {
                name: parts[1].to_string(),
                priority,
            })
        }
        "print" => {
            if parts.len() != 2 {
                return Err("print must be: print,<priority>".to_string());
            }

            let priority = parts[1]
                .parse::<usize>()
                .map_err(|_| "invalid priority for print".to_string())?;

            Ok(Command::Print { priority })
        }
        other => Err(format!("unknown command: {}", other)),
    }
}

4. src/hash.rs
pub fn jenkins_one_at_a_time(key: &str) -> u32 {
    let mut hash: u32 = 0;

    for byte in key.as_bytes() {
        hash = hash.wrapping_add(*byte as u32);
        hash = hash.wrapping_add(hash << 10);
        hash ^= hash >> 6;
    }

    hash = hash.wrapping_add(hash << 3);
    hash ^= hash >> 11;
    hash = hash.wrapping_add(hash << 15);

    hash
}

5. src/table.rs
use std::fmt::Write;

#[derive(Debug, Clone)]
pub struct Record {
    pub hash: u32,
    pub name: String,
    pub salary: u32,
}

impl Record {
    pub fn display_line(&self) -> String {
        format!("{},{},{}", self.hash, self.name, self.salary)
    }
}

#[derive(Debug)]
pub struct Node {
    pub record: Record,
    pub next: Option<Box<Node>>,
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

    pub fn format_database(&self) -> String {
        let mut out = String::new();
        let _ = writeln!(out, "Current Database:");

        let mut current = self.head.as_ref();
        while let Some(node) = current {
            let _ = writeln!(out, "{}", node.record.display_line());
            current = node.next.as_ref();
        }

        out
    }
}

fn insert_sorted(link: &mut Option<Box<Node>>, record: Record) -> Result<(), Record> {
    match link {
        None => {
            *link = Some(Box::new(Node { record, next: None }));
            Ok(())
        }
        Some(node) if record.hash == node.record.hash => Err(record),
        Some(node) if record.hash < node.record.hash => {
            let next = link.take();
            *link = Some(Box::new(Node { record, next }));
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
            let old_record = node.record.clone();
            node.record.salary = new_salary;
            let new_record = node.record.clone();
            Some((old_record, new_record))
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

6. src/sync.rs
use std::sync::{Condvar, Mutex};

pub struct TurnManager {
    current_turn: Mutex<usize>,
    cv: Condvar,
}

impl TurnManager {
    pub fn new(start_turn: usize) -> Self {
        Self {
            current_turn: Mutex::new(start_turn),
            cv: Condvar::new(),
        }
    }

    pub fn wait_for_turn_and_advance(&self, my_turn: usize) {
        let mut turn = self.current_turn.lock().unwrap_or_else(|e| e.into_inner());

        while *turn != my_turn {
            turn = self.cv.wait(turn).unwrap_or_else(|e| e.into_inner());
        }

        *turn += 1;
        self.cv.notify_all();
    }
}

7. src/logger.rs
use std::fs::File;
use std::io::{self, BufWriter, Write};
use std::sync::Mutex;
use std::time::{SystemTime, UNIX_EPOCH};

pub struct Logger {
    writer: Mutex<BufWriter<File>>,
}

impl Logger {
    pub fn new(path: &str) -> io::Result<Self> {
        let file = File::create(path)?;
        Ok(Self {
            writer: Mutex::new(BufWriter::new(file)),
        })
    }

    pub fn log_command(&self, priority: usize, msg: &str) -> io::Result<()> {
        self.log_line(format!("THREAD {} {}", priority, msg))
    }

    pub fn log_waiting(&self, priority: usize) -> io::Result<()> {
        self.log_line(format!("THREAD {} WAITING FOR MY TURN", priority))
    }

    pub fn log_awakened(&self, priority: usize) -> io::Result<()> {
        self.log_line(format!("THREAD {} AWAKENED FOR WORK", priority))
    }

    pub fn log_read_lock_acquired(&self, priority: usize) -> io::Result<()> {
        self.log_line(format!("THREAD {} READ LOCK ACQUIRED", priority))
    }

    pub fn log_read_lock_released(&self, priority: usize) -> io::Result<()> {
        self.log_line(format!("THREAD {} READ LOCK RELEASED", priority))
    }

    pub fn log_write_lock_acquired(&self, priority: usize) -> io::Result<()> {
        self.log_line(format!("THREAD {} WRITE LOCK ACQUIRED", priority))
    }

    pub fn log_write_lock_released(&self, priority: usize) -> io::Result<()> {
        self.log_line(format!("THREAD {} WRITE LOCK RELEASED", priority))
    }

    fn log_line(&self, msg: String) -> io::Result<()> {
        let timestamp = current_timestamp_micros();
        let mut writer = self.writer.lock().unwrap_or_else(|e| e.into_inner());
        writeln!(writer, "{}: {}", timestamp, msg)?;
        writer.flush()
    }
}

fn current_timestamp_micros() -> u128 {
    match SystemTime::now().duration_since(UNIX_EPOCH) {
        Ok(dur) => dur.as_micros(),
        Err(_) => 0,
    }
}

8. src/main.rs
mod command;
mod hash;
mod logger;
mod sync;
mod table;

use command::{parse_commands_file, Command};
use hash::jenkins_one_at_a_time;
use logger::Logger;
use sync::TurnManager;
use table::{HashTable, Record};

use std::io;
use std::sync::{Arc, Mutex, RwLock};
use std::thread;

const COMMANDS_FILE: &str = "commands.txt";
const LOG_FILE: &str = "hash.log";

fn main() -> io::Result<()> {
    let (declared_threads, commands) = parse_commands_file(COMMANDS_FILE)?;

    if declared_threads != commands.len() {
        eprintln!(
            "Warning: threads header says {}, but {} commands were found.",
            declared_threads,
            commands.len()
        );
    }

    let table = Arc::new(RwLock::new(HashTable::new()));
    let turn_manager = Arc::new(TurnManager::new(0));
    let logger = Arc::new(Logger::new(LOG_FILE)?);

    // Prevent mixed/interleaved stdout lines from multiple threads.
    let stdout_lock = Arc::new(Mutex::new(()));

    let mut handles = Vec::with_capacity(commands.len());

    for command in commands {
        let table = Arc::clone(&table);
        let turn_manager = Arc::clone(&turn_manager);
        let logger = Arc::clone(&logger);
        let stdout_lock = Arc::clone(&stdout_lock);

        let handle = thread::spawn(move || {
            if let Err(err) = worker(command, table, turn_manager, logger, stdout_lock) {
                eprintln!("Worker error: {}", err);
            }
        });

        handles.push(handle);
    }

    for handle in handles {
        if let Err(err) = handle.join() {
            eprintln!("A worker thread panicked: {:?}", err);
        }
    }

    // Required final print at end of run.
    let final_output = {
        let table_guard = table.read().unwrap_or_else(|e| e.into_inner());
        table_guard.format_database()
    };

    {
        let _stdout_guard = stdout_lock.lock().unwrap_or_else(|e| e.into_inner());
        print!("{}", final_output);
    }

    Ok(())
}

fn worker(
    command: Command,
    table: Arc<RwLock<HashTable>>,
    turn_manager: Arc<TurnManager>,
    logger: Arc<Logger>,
    stdout_lock: Arc<Mutex<()>>,
) -> io::Result<()> {
    let priority = command.priority();

    logger.log_waiting(priority)?;
    turn_manager.wait_for_turn_and_advance(priority);
    logger.log_awakened(priority)?;

    let hash = command.name().map(jenkins_one_at_a_time);
    logger.log_command(priority, &command.log_message(hash))?;

    let output = match command {
        Command::Insert {
            name,
            salary,
            priority,
        } => {
            let hash = jenkins_one_at_a_time(&name);
            logger.log_write_lock_acquired(priority)?;

            let result = {
                let mut table_guard = table.write().unwrap_or_else(|e| e.into_inner());
                table_guard.insert(Record {
                    hash,
                    name: name.clone(),
                    salary,
                })
            };

            logger.log_write_lock_released(priority)?;

            match result {
                Ok(()) => format!("Inserted {}\n", format_record(hash, &name, salary)),
                Err(_) => format!("Insert failed. Entry {} is a duplicate.\n", hash),
            }
        }

        Command::Delete { name, priority } => {
            let hash = jenkins_one_at_a_time(&name);
            logger.log_write_lock_acquired(priority)?;

            let result = {
                let mut table_guard = table.write().unwrap_or_else(|e| e.into_inner());
                table_guard.delete(hash)
            };

            logger.log_write_lock_released(priority)?;

            match result {
                Some(record) => format!("Deleted {}\n", record.display_line()),
                None => format!("Delete failed. Entry {} not deleted. Not in database.\n", hash),
            }
        }

        Command::Update {
            name,
            salary,
            priority,
        } => {
            let hash = jenkins_one_at_a_time(&name);
            logger.log_write_lock_acquired(priority)?;

            let result = {
                let mut table_guard = table.write().unwrap_or_else(|e| e.into_inner());
                table_guard.update(hash, salary)
            };

            logger.log_write_lock_released(priority)?;

            match result {
                Some((old_record, new_record)) => format!(
                    "Updated record {} from {} to {}\n",
                    hash,
                    old_record.display_line(),
                    new_record.display_line()
                ),
                None => format!("Update failed. Entry {} not found.\n", hash),
            }
        }

        Command::Search { name, priority } => {
            let hash = jenkins_one_at_a_time(&name);
            logger.log_read_lock_acquired(priority)?;

            let result = {
                let table_guard = table.read().unwrap_or_else(|e| e.into_inner());
                table_guard.search(hash)
            };

            logger.log_read_lock_released(priority)?;

            match result {
                Some(record) => format!("Found: {}\n", record.display_line()),
                None => format!("Not Found: {} not found.\n", name),
            }
        }

        Command::Print { priority } => {
            logger.log_read_lock_acquired(priority)?;

            let result = {
                let table_guard = table.read().unwrap_or_else(|e| e.into_inner());
                table_guard.format_database()
            };

            logger.log_read_lock_released(priority)?;
            result
        }
    };

    {
        let _stdout_guard = stdout_lock.lock().unwrap_or_else(|e| e.into_inner());
        print!("{}", output);
    }

    Ok(())
}

fn format_record(hash: u32, name: &str, salary: u32) -> String {
    format!("{},{},{}", hash, name, salary)
}

9. README.md
# Concurrent Hash Table in Rust

## Build

```bash
make

This builds the Rust project in release mode and copies the executable to:
./chash

Run

Place commands.txt in the project root directory, then run:
./chash

The program:

reads commands.txt
writes synchronization logs to hash.log
writes command output to stdout
Files
src/main.rs - main program and thread orchestration
src/command.rs - command parsing
src/hash.rs - Jenkins one-at-a-time hash
src/table.rs - linked-list-backed table logic
src/sync.rs - turn ordering using mutex + condition variable
src/logger.rs - synchronized hash.log writing
Notes
commands.txt is hardcoded as required by the assignment.
hash.log is recreated on each run.
The linked list is kept sorted by hash so print output is deterministic.
AI Use Citation

I used ChatGPT to help:

understand the assignment requirements
design the Rust module structure
explain synchronization choices
generate and refine portions of the Rust implementation

I reviewed and am responsible for the final submitted code.


---

## 10. `RUST_EXPLANATION.md`

```md
# Rust Explanation for Concurrent Hash Table

This document explains the Rust-specific parts of the project as if the reader is new to Rust.

## Why Rust is useful here

Rust is a strong fit for concurrent programming because it helps prevent:
- data races
- use-after-free bugs
- double free bugs
- many forms of invalid pointer usage

In C, the programmer must manually ensure memory safety and thread safety. In Rust, the compiler helps enforce them.

## Thread-safe features used

### `Arc<T>`
`Arc` means atomic reference-counted shared ownership.

Multiple worker threads need to share:
- the hash table
- the turn-order manager
- the logger
- the stdout mutex

Because several threads need access to the same values, `Arc` is used.

### `Mutex<T>`
A `Mutex` provides exclusive access to data.

This project uses `Mutex` for:
- the turn counter inside the condition-variable scheduler
- the log writer, so log lines do not interleave
- stdout printing, so output lines do not mix together

### `Condvar`
A condition variable lets threads wait until some condition becomes true.

This project uses `Condvar` to enforce priority ordering:
- thread 0 starts first
- then thread 1
- then thread 2
- and so on

The condition variable solves the logical ordering problem.

### `RwLock<T>`
A reader-writer lock allows:
- many readers at the same time
- only one writer at a time

This project uses `RwLock<HashTable>` because:
- `search` and `print` only read
- `insert`, `delete`, and `update` modify the list

The reader-writer lock protects the shared linked list.

## Memory-safe features used

### Ownership
Each value in Rust has a clear owner.

For example:
- the hash table is owned by an `Arc<RwLock<_>>`
- each linked-list node owns its `next` pointer through `Box<Node>`

This helps prevent dangling pointers.

### `Option<Box<Node>>`
The linked list is implemented with:
- `Option<Box<Node>>`

This means:
- either there is no next node: `None`
- or there is a heap-allocated next node: `Some(Box<Node>)`

Rust automatically frees memory when values go out of scope, so there is no manual `free()` like in C.

### No raw pointer manipulation
This implementation uses safe Rust only.
There is no `unsafe` block and no raw pointer arithmetic.

## How the linked list works in Rust

Each node stores:
- `hash`
- `name`
- `salary`
- `next`

The table stores a `head` pointer.

The list is kept sorted by hash.
That makes print output simple and deterministic.

## How thread ordering works

The program uses a shared turn counter:
- starts at 0
- each thread waits until `current_turn == my_priority`
- once awakened, that thread increments the counter and wakes the next one

Important idea:
- ordering is controlled by `Mutex + Condvar`
- data access is controlled by `RwLock`

These are separate concerns.

## How Rust differs from C here

### In C
You might use:
- raw pointers
- `malloc` / `free`
- pthread mutexes
- pthread condition variables
- custom semaphore-based RW locks

### In Rust
You use:
- `Box` for heap allocation
- automatic cleanup with ownership
- `Arc` for shared ownership
- `Mutex`, `Condvar`, and `RwLock` from the standard library

This reduces the chance of memory and synchronization bugs.

## Final takeaway

This project demonstrates that Rust can express the same core systems ideas as C:
- linked data structures
- multi-threading
- synchronization
- shared mutable state

But Rust adds compile-time safety rules that help prevent many common errors.

Folder structure

Your project should look like this:
project/
├── Cargo.toml
├── Makefile
├── README.md
├── RUST_EXPLANATION.md
├── commands.txt
└── src/
    ├── main.rs
    ├── command.rs
    ├── hash.rs
    ├── logger.rs
    ├── sync.rs
    └── table.rs

How to build and run
make
./chash

This matches the assignment’s required file flow:

read commands.txt
produce hash.log
print results to stdout

Important note about exact output strings

Your professor’s grader may care about exact text formatting. The project page shows the required behavior and sample wording, but the support PDFs are image-based, so there may still be tiny punctuation or spacing differences to adjust. The concurrency design, linked-list behavior, hashing, logging, and file structure in the code above are complete and aligned with the assignment docs.