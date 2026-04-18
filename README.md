# Concurrent Hash Table

<p align="center">
  Multi-threaded in-memory hash table in Rust using a sorted singly linked list, Jenkins hashing,
  <code>RwLock</code>, and <code>Mutex + Condvar</code> turn control.
</p>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/QUICK%20START-1f2937?style=for-the-badge" alt="Quick Start"></a>
  <a href="#features"><img src="https://img.shields.io/badge/FEATURES-374151?style=for-the-badge" alt="Features"></a>
  <a href="#concurrency"><img src="https://img.shields.io/badge/CONCURRENCY-8b5cf6?style=for-the-badge" alt="Concurrency"></a>
  <a href="#validation"><img src="https://img.shields.io/badge/VALIDATION-10b981?style=for-the-badge" alt="Validation"></a>
  <a href="#source-layout"><img src="https://img.shields.io/badge/SOURCE%20LAYOUT-f59e0b?style=for-the-badge" alt="Source Layout"></a>
  <a href="#authors"><img src="https://img.shields.io/badge/AUTHORS-ec4899?style=for-the-badge" alt="Authors"></a>
</p>

<p align="center">
  <a href="https://github.com/DucNguyen0159/Concurrent-Hash-Table">Repository</a>
</p>

---

## Overview

This project is a multi-threaded concurrent hash table implemented in Rust.

It reads a hard-coded `commands.txt` file from the repository root, maintains a sorted singly linked list keyed by Jenkins one-at-a-time hashes, uses `RwLock` to separate readers from writers, and uses `Mutex + Condvar` to enforce strict turn order between threads.

Program results are printed to **stdout**, and synchronization activity is written to **`hash.log`**.

## Features

- **Concurrent table access** with `RwLock` for many-readers / one-writer behavior
- **Deterministic thread ordering** using `Mutex` + `Condvar`
- **Jenkins one-at-a-time hash** for key generation
- **Command-driven execution** through `commands.txt`
- **Structured logging** to `hash.log`
- **Automated validation** with `check_pa2.py`
- **Portable Cargo build** plus an optional **Makefile copy step**

## Quick Start

### Prerequisites

- [Rust](https://rustup.rs/) stable toolchain and **Cargo**
- **GNU Make** is optional
  - Use it only if you want the release binary copied to the repository root as `chash` or `chash.exe`
  - On many Windows setups, `make` is not installed, so the Cargo-only path is usually the easiest option

### Build

#### Option A: Cargo only (recommended)

```bash
cargo build --release
```

**Output binary**

- **Windows:** `target\release\chash.exe`
- **macOS / Linux:** `target/release/chash`

This option does **not** copy the binary into the repository root.

#### Option B: Makefile build + copy to root

```bash
make
```

This runs `cargo build --release` and then copies the binary into the project root:

- **Windows:** `chash.exe`
- **macOS / Linux:** `./chash`

### Run

> Run the program from the **repository root** so the hard-coded `commands.txt` path resolves correctly.

| Build method | Windows (PowerShell) | Unix shell |
|---|---|---|
| After `cargo build --release` | `.\target\release\chash.exe` | `./target/release/chash` |
| After `make` | `.\chash.exe` | `./chash` |

### Outputs

- **stdout**: command results for insert, update, delete, search, and print
- **`hash.log`**: waiting / awakened / lock events, followed by lock totals and a `Final Table:` snapshot

### Makefile Commands

```bash
make        # build release binary and copy it to the repo root
make run    # build, copy, then run
make test   # run cargo tests
make clean  # remove build artifacts and generated binaries/logs
```

## Concurrency

This project separates two different synchronization problems:

- **Who may access the shared table?** → `RwLock`
- **Whose turn is it to run next?** → `Mutex + Condvar`

In practice:

- `search` and `print` use **read locks**
- `insert`, `delete`, and `update` use **write locks**
- turn order is controlled independently so grading traces stay understandable

## Validation

This repository includes a Python checker that loads cases from `tests/cases/` and validates behavior automatically.

```bash
python check_pa2.py
```

### What the checker does

- Writes each test input into the root `commands.txt`
- Runs the program binary
- Captures stdout
- Reads `hash.log`
- Normalizes only line endings and trailing spaces at line ends
- Compares stdout against expected output
- Prints **PASS / FAIL** and a unified diff on mismatches
- Runs extra hash-log checks for configured cases
- Repeats the reader-overlap check for `03_concurrent_prints`
- Exits with a nonzero status if any stdout check fails

<details>
<summary><strong>Bundled test-case files</strong></summary>

- `tests/cases/01_duplicate_insert.commands.txt`
- `tests/cases/01_duplicate_insert.expected.txt`
- `tests/cases/02_missing_delete_update_search.commands.txt`
- `tests/cases/02_missing_delete_update_search.expected.txt`
- `tests/cases/03_concurrent_prints.commands.txt`
- `tests/cases/03_concurrent_prints.expected.txt`
- `tests/cases/04_teacher_comprehensive.commands.txt`
- `tests/cases/04_teacher_comprehensive.expected.txt`
- `tests/cases/04_teacher_comprehensive.sample_hashlog.txt`

</details>

## Source Layout

| Path | Role |
|---|---|
| `src/main.rs` | Thread pool, turn gate, ordered stdout aggregation, `hash.log` footer |
| `src/command.rs` | Parses `commands.txt` (`threads` header and command lines) |
| `src/hash.rs` | Jenkins one-at-a-time hash |
| `src/table.rs` | Sorted linked-list table and CRUD operations |
| `src/sync.rs` | `Mutex` + `Condvar` turn manager |
| `src/logger.rs` | Mutex-backed `hash.log` writer and lock counters |
| `check_pa2.py` | Case-driven validator for stdout and `hash.log` |
| `tests/cases/` | External command, expected-output, and sample-hashlog files |

## Other Files

| Path | Role |
|---|---|
| `README.txt` | Plain-text hand-in copy for academic submission |
| `RUST_EXPLANATION.md` | Rust concurrency and memory-safety notes |
| `Makefile` | Build / test / run / clean shortcuts |
| `commands.txt` | Sample command input used by the program |

## Authors

| Contributor | GitHub |
|---|---|
| **Henry Nguyen** | [@DucNguyen0159](https://github.com/DucNguyen0159) |
| **Minh Thien Pham** | [@MinhThien-Pham](https://github.com/MinhThien-Pham) |

## Git

Example remote:

```text
https://github.com/DucNguyen0159/Concurrent-Hash-Table.git
```

Basic workflow:

```bash
git fetch origin
git pull origin main
git push origin main
```

If you use HTTPS, GitHub may require a personal access token or SSH credentials depending on your setup.

## Generative-AI Disclosure

High-level attribution appears here. The plain-text **`README.txt`** contains the fuller academic-integrity write-up used for submission.

Tools mentioned in the project documentation:

- **ChatGPT (GPT)**
- **Cursor**

## Notes

- The program expects `commands.txt` to exist in the repository root.
- A sample `commands.txt` is already included.
- If a rubric asks for a plain-text README, use **`README.txt`**.

---

<p align="center">
  Built for a Rust-based concurrent systems programming assignment.
</p>
