# PA2 Concurrent Hash Table — Rust implementation plan (extra credit)

This document is the agreed implementation plan for building the assignment in **Rust** (extra credit path). It consolidates the official **PA2 Concurrent Hash Table Description**, the **`PA#2 Expected Output`** workload, **`commands_comprehensive_test.txt`**, **`hash.log`**, **`Jenkins hash function.md`**, **`rwlock.c`**, and the design notes in **`PA2_GPT_Analysis.md`**.

---

## 1. Goals and success criteria

| Goal | How we verify |
|------|----------------|
| Correct concurrent behavior | Shared list never corrupted; RW lock used as specified (read: search/print; write: insert/delete/update). |
| Ordered thread starts | Condition-variable (or equivalent) turn gate so thread **N** begins only after **N−1** has passed the gate; overlap allowed after wake. |
| Correct hashing | **Jenkins one-at-a-time** over the name bytes; results match expectations for the same names. |
| Deterministic print order | List kept **sorted by hash** ascending so `PRINT` and final print need no extra sort. |
| I/O contract | Read **`commands.txt`** (hardcoded path); write **`hash.log`**; command results to **stdout**. |
| Final print | After all worker threads complete, emit **one additional** full database print (even if last command was already `print`). |
| Extra credit docs | **`README`** (build/run + AI citation) plus **separate Markdown** teaching Rust thread/memory safety (not the README). |
| Build contract | **`make`** produces executable **`chash`** (Cargo release binary copied to `./chash` is acceptable). |

**Grading nuance (official spec):** only the **final** printed database state may be what the autograder checks for table contents; intermediate prints still matter for lock/rubric behavior and self-testing. Treat **`PA#2 Expected Output.md`** as the **stdout string baseline** for the comprehensive workload.

---

## 2. Scope: what we are building

- **Not** a classic bucket array hash table. The assignment is a **global singly linked list** of `hashRecord`-style nodes; hash identifies the record for grading data (collisions ignored).
- **Two synchronization layers** (do not merge them mentally):
  1. **Turn / priority scheduler** — answers “when may this thread *start* its work sequence?”
  2. **`RwLock` on the table** — answers “who may read or mutate the shared list right now?”

Per course rationale (and `PA2_GPT_Analysis.md`): **wake/signal the next thread early** (right after claiming your turn), **before** list lock and full operation complete, so later threads can overlap (e.g. hash computation) with earlier ones—otherwise the program becomes purely sequential.

---

## 3. Data model

### 3.1 Logical record

Align with the spec’s `hashRecord`:

- `hash: u32` — Jenkins hash of `name`
- `name: String` — up to 50 characters (validate or truncate per your reading of the spec; test data stays within limits)
- `salary: u32`
- List linkage via `next: Option<Box<Node>>`

### 3.2 Table type

- `HashTable { head: Option<Box<Node>> }` — all records in **one** list, **sorted by `hash` ascending**.
- **Duplicate insert:** if `hash` already exists → error path (no second node with same hash for provided grading sets).

### 3.3 Operations (pure logic in `table` module)

| Operation | Lock | Behavior |
|-----------|------|----------|
| `insert` | Write | Compute hash **outside** lock; inside lock, insert in sorted order or reject duplicate. |
| `delete` | Write | Remove by hash; report success or miss. Prefer **one** write-lock critical section (inline traverse), not delete→search with nested read locks. |
| `update` | Write | Find by hash; update `salary` or report not found. |
| `search` | Read | Find by hash; return `Option<Record>` for printing. |
| `print` | Read | Format `Current Database:` + lines `hash,name,salary` in list order (= sorted by hash). |

---

## 4. Hash function

Implement **exactly** the Jenkins one-at-a-time loop from **`Jenkins hash function.md`**:

- Iterate bytes of the name (UTF-8 bytes are fine for ASCII test names).
- Use **wrapping** `u32` arithmetic for `+=`, `<<`, `>>`, `^`.

Unit-test against known vectors if you add any from the Jenkins note (e.g. short strings).

---

## 5. Input: `commands.txt`

### 5.1 Hard requirements

- Filename **`commands.txt`** hardcoded (no argv for command file).
- First line: thread header as in comprehensive file: **`threads,<count>,<ignored>`** (e.g. `threads,60,0`). Parse **`<count>`** as number of worker threads; validate it matches the number of command lines following (or document mismatch handling).

### 5.2 Command line formats

The **short** assignment table and the **comprehensive** sample differ. The parser must accept the **comprehensive** shapes used for grading-style tests:

| Command | Comprehensive pattern | Notes |
|---------|------------------------|--------|
| `insert` | `insert,<name>,<salary>,<priority>` | 4 fields after split; name has no commas in provided tests. |
| `delete` | `delete,<name>,<priority>` | If extended to 3 trailing fields, last is priority (simple case: 3 fields total). |
| `update` | `update,<name>,<new_salary>,<priority>` | Spec table omits priority; **tests include it** — always parse 4 fields. |
| `search` | `search,<name>,<placeholder>,<priority>` | e.g. `search,Shigeru Miyamoto,0,6` — **priority is last field**; middle `0` ignored. |
| `print` | `print,<a>,<b>,<priority>` | e.g. `print,0,0,5` — **priority is last field**. |

**Parsing strategy:** for each line, split on commas, dispatch on first token, then interpret **priority as the last integer field** where the format has extra placeholders. This stays compatible with minimal `print,<p>` if ever used.

Skip empty lines; trim whitespace.

---

## 6. Concurrency architecture

### 6.1 Shared state (typical layout)

- `Arc<RwLock<HashTable>>` — list protection.
- `Arc<TurnState>` — `Mutex<usize>` current turn (or next allowed priority) + `Condvar`.
- `Arc<Logger>` — mutex-wrapped writer to **`hash.log`** so lines never interleave.
- Optional `Arc<Mutex<()>>` or a dedicated print mutex — **serialize stdout** so multi-line `Current Database:` blocks are not torn between threads.

### 6.2 Worker thread lifecycle (per command)

1. Log: **`WAITING FOR MY TURN`** (see §7 for exact line shape).
2. Wait on condvar until `current_turn == my_priority` (while-loop pattern; handle spurious wakeups).
3. On turn: log **`AWAKENED FOR WORK`**; **advance** shared turn counter and **`notify_all`** (or broadcast) so waiting threads can re-check—**before** taking the table RW lock and before the heavy part if you want maximum overlap.
4. Log command line (with hash if applicable—see §7).
5. **Compute hash** outside the `RwLock` when possible.
6. Acquire **read** or **write** lock; log **ACQUIRED**; perform operation; log **RELEASED**; drop guard.
7. Print human-facing result to stdout (under stdout mutex if used).

### 6.3 Main thread

- Parse file → `Vec<Command>` with priorities.
- Spawn **one `std::thread` per command`** (or scoped threads) with `JoinHandle` collection.
- **Join all** in spawn order or any order (completion order does not replace turn order for *starting* the critical sequence).
- After all joins: acquire **read** lock, print **final** `Current Database:` block (same format as command-time print). This satisfies the “final PRINT even if file ended with PRINT” rule.

### 6.4 Rust primitives mapping

| Concept | Rust |
|---------|------|
| Shared ownership | `Arc<...>` |
| Turn + CV | `Mutex<usize>` + `Condvar` |
| Reader–writer lock | `std::sync::RwLock` (platform policy; acceptable for coursework unless spec demands custom fairness) |
| Threads | `std::thread::spawn` |
| Poisoned locks | Prefer `unwrap_or_else(|e| e.into_inner())` or explicit error messages for robustness |

**Note:** `PA2_GPT_Analysis.md` suggests safe Rust only; avoid `unsafe` unless there is a strong reason.

---

## 7. `hash.log` format

Follow the **sample `hash.log`** in this folder and the assignment text.

- Timestamp: **microseconds** since Unix epoch (assignment uses `gettimeofday`; in Rust use `SystemTime` → duration since `UNIX_EPOCH` → `as_micros()` or equivalent, cast/widen to match **64-bit** style in sample if needed for consistency).
- Each line: `<timestamp>: THREAD <id> <rest>`  
  Sample uses a **space** after the thread id for lock messages, e.g. `THREAD 0 WAITING FOR MY TURN`, `THREAD 0 READ LOCK ACQUIRED`.
- Command execution line: include command and parameters; with hash when known, e.g. `THREAD 0 INSERT,<hash>,<name>,<salary>` matching course examples.

**Ordering:** log WAITING before blocking; AWAKENED after wake; lock ACQUIRED/RELEASED bracketing the critical section; ensure logger mutex covers the whole line write + flush.

**End of log (optional but in sample):** summary lines such as lock acquisition/release counts and “Final Table:” — include only if you want to match sample; **confirm against current semester rubric** (assignment text focuses on per-event lines).

---

## 8. Stdout strings (match comprehensive expected output)

The short spec table and **`PA#2 Expected Output.md`** can disagree. For the comprehensive test, **match the expected output file**, for example:

- Insert success: `Inserted <hash>,<name>,<salary>` (no extra words—see expected file).
- Search hit: `Found: <hash>,<name>,<salary>`
- Search miss: **`<name> not found.`** (not necessarily `Not Found: ...` from the short table).
- Update success / failure: mirror **exact** lines in expected output (`Update failed. Entry ...`).
- Delete success: `Deleted record for <hash>,<name>,<salary>`
- Print: `Current Database:` then one record per line `hash,name,salary`.

**Typo in spec PDF:** table says “Updated failed”; expected file uses **“Update failed”** — follow **expected output**.

Run a **diff** against `PA#2 Expected Output.md` (minus timestamps) after implementation.

---

## 9. Module / crate layout (recommended)

Aligned with `PA2_GPT_Analysis.md` modular advice + course “not monolithic” rule:

| Unit | Responsibility |
|------|----------------|
| `src/main.rs` | Parse argv (if any), open `commands.txt`, build shared state, spawn/join, final print. |
| `src/command.rs` | `Command` enum, parsing, priority accessor. |
| `src/hash.rs` | `jenkins_one_at_a_time(&str) -> u32` |
| `src/table.rs` | `Node`, `HashTable`, insert/delete/update/search, `format_database`. |
| `src/sync.rs` | `TurnManager` / `wait_for_turn` / advance + notify. |
| `src/logger.rs` | Timestamped `hash.log` writes, all message helpers. |

**Root files:**

- `Cargo.toml` — package name `chash`, edition 2021.
- `Makefile` — `make` / `make clean` / optional `make run`; copies `target/release/chash` to `./chash`.
- `README.txt` or `README.md` — **build**, **run**, how to place `commands.txt`, **AI citation paragraph(s)** (required by course AI policy).
- **`RUST_EXPLANATION.md`** (or similar) — extra credit: teach Rust memory/thread safety, `Arc`/`RwLock`/`Condvar`, why no data races, differences from C, as requested in the extra credit section of the assignment.

---

## 10. Implementation order (minimize debug pain)

1. **`hash.rs`** + small tests.
2. **`table.rs`** single-threaded: sorted insert, search, update, delete, format print.
3. **`command.rs`** parser against **`commands_comprehensive_test.txt`** (copy to `commands.txt` for runs).
4. **`logger.rs`** — correct line format, mutex.
5. **`sync.rs`** — turn manager only; unit test with dummy threads.
6. **`main.rs`** — wire `RwLock` + workers + logger + stdout mutex.
7. **Final print** + lock logging completeness.
8. Polish stdout to **byte-match** expected output file.
9. **`RUST_EXPLANATION.md`** + README AI paragraph.

---

## 11. Testing checklist

- [ ] Comprehensive `commands.txt`: stdout matches **`PA#2 Expected Output.md`**.
- [ ] `hash.log`: WAITING / AWAKENED / READ/WRITE ACQUIRE+RELEASE for each operation; no interleaved broken lines.
- [ ] Turn order: thread 0’s AWAKENED before thread 1 begins work (log inspection); still observe overlapping hash or lock phases when possible.
- [ ] Final database line count and hashes match expected final block.
- [ ] Duplicate insert / missing update/delete/search paths (use small hand-crafted file).
- [ ] `make` produces `./chash`; `./chash` runs from directory containing `commands.txt`.

---

## 12. Submission packaging (zip)

Per assignment: single zip, **`make` → `chash`**, include all sources, **Makefile**, **README** with AI attribution, plus **Rust-only** teaching doc for extra credit. Double-check course submission portal for **README name** (`README.txt` vs `.md`).

---

## 13. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| stdout torn across threads | Mutex around `println!` / `print!` blocks. |
| Parser wrong for `print,0,0,N` / `search,name,0,N` | Treat **last field as priority**; add tests. |
| String mismatch vs autograder | Diff against **`PA#2 Expected Output.md`**, not only the short table. |
| `RwLock` writer starvation | Document platform behavior; acceptable unless rubric requires fair lock. |
| Poisoned mutex after panic | Avoid panics in workers; or handle poison consistently. |

---

## 14. References inside `PA2 Des`

- **`PA2 Concurrent Hash Table Description.md`** — authoritative requirements and rubric themes.
- **`PA#2 Expected Output.md`** — stdout golden file for comprehensive run.
- **`commands_comprehensive_test.txt`** — parser and workload reference.
- **`hash.log`** — log line structure and rhythm.
- **`Jenkins hash function.md`** — hash algorithm.
- **`rwlock.c`** — conceptual RW lock behavior (readers counter + writer exclusion).
- **`PA2_GPT_Analysis.md`** — extended rationale, Rust mapping, module split, worker flow diagram; treat embedded code as **advisory** until validated against this plan and expected output.

---

*Document version: 1.0 — created for Rust extra-credit implementation track.*
