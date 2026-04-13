# Concurrent Hash Table (COP 4600 PA2)

Course project: a **concurrent hash table** backed by a sorted linked list, with thread-safe access (reader–writer style locking) and ordered thread startup. This repository targets the **Rust extra-credit** implementation described in course materials; assignment specs and reference files live under **`PA2 Des/`**.

**GitHub:** [https://github.com/DucNguyen0159/Concurrent-Hash-Table](https://github.com/DucNguyen0159/Concurrent-Hash-Table)

## Prerequisites

- [Rust](https://rustup.rs/) (stable toolchain) and **Cargo** (required)
- **GNU Make** (optional): only needed if you want the course-style `make` step that copies the binary to the repo root as `chash` / `chash.exe`. Many Windows setups do not have `make`; that is fine.

## Build

**Option A — always works (recommended on Windows)**

```bash
cargo build --release
```

The executable is **`target/release/chash`** (macOS/Linux) or **`target\release\chash.exe`** (Windows). Nothing is copied to the project root unless you do that yourself or use Option B.

**Option B — matches “run `make` to get `chash`” hand-in instructions**

```bash
make
```

Requires `make` on your `PATH`. On Windows the `Makefile` copies `target\release\chash.exe` → **`chash.exe`** in the repo root; on Unix it copies → **`./chash`**.

## Run

From the project root (where **`commands.txt`** lives — a sample is already committed):

- **After `cargo build --release`:**  
  - Windows PowerShell: **`.\target\release\chash.exe`**  
  - Unix: **`./target/release/chash`**
- **After `make`:**  
  - Windows: **`.\chash.exe`**  
  - Unix: **`./chash`**

The program reads `commands.txt`, writes **`hash.log`** (timestamps, turn + lock events, footer with lock counts and final table), and prints command results to **stdout**. Stdout for the bundled workload matches **`PA2 Des/PA#2 Expected Output.md`** (lines 6–160).

## Source layout

| Path | Purpose |
|------|--------|
| `src/main.rs` | Threads, `RwLock` table, turn gate, stdout ordering, final `hash.log` footer |
| `src/command.rs` | Parse `threads,...` header and command lines |
| `src/hash.rs` | Jenkins one-at-a-time hash |
| `src/table.rs` | Sorted linked list + operations |
| `src/sync.rs` | `Mutex` + `Condvar` turn manager |
| `src/logger.rs` | Serialized `hash.log` lines + lock counters |

## Repository layout

| Path | Purpose |
|------|--------|
| `PA2 Des/` | Assignment description, expected output, sample logs, `implement_plan.md` |
| `README.txt` | Plain-text README for course submission (build/run + AI citation) |
| `README.md` | This file — for GitHub |
| `RUST_EXPLANATION.md` | Extra-credit Rust / thread-safety write-up |

## Course submission

Use **`README.txt`** in the zip you upload, per instructor instructions. Keep **`README.md`** in sync for GitHub when you change build steps or run instructions.

## Git remotes

This clone is configured with:

```text
origin → https://github.com/DucNguyen0159/Concurrent-Hash-Table.git
```

Typical workflow:

```bash
git fetch origin
git pull origin main
git push origin main
```

Use **HTTPS** with a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) or switch the remote to **SSH** if you prefer (`git@github.com:DucNguyen0159/Concurrent-Hash-Table.git`).

## AI use (course policy)

Summarize tools, prompts, and how you validated outputs in **`README.txt`** before submission. A short pointer here is not a substitute for the full citation in `README.txt`.
