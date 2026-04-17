# Concurrent Hash Table

Multi-threaded in-memory table: sorted singly linked list keyed by Jenkins hashes, protected with a reader-writer lock; thread start order enforced with a mutex and condition variable. Command files drive insert / delete / update / search / print; output goes to **stdout** and **hash.log**.

**Repository:** [https://github.com/DucNguyen0159/Concurrent-Hash-Table](https://github.com/DucNguyen0159/Concurrent-Hash-Table)

## Authors

| Contributor | GitHub |
|:-------------|:-------|
| **Henry Nguyen** | [@DucNguyen0159](https://github.com/DucNguyen0159) |
| **Minh Thien Pham** | [@MinhThien-Pham](https://github.com/MinhThien-Pham) |

## Prerequisites

- [Rust](https://rustup.rs/) stable toolchain and **Cargo** (required)
- **GNU Make** (optional): copies the release binary into the repository root as `chash` or `chash.exe` to match Makefile-based submission checks. Windows environments often omit Make; the Cargo-only path below is sufficient to build and run.

## Build

**Option A — portable (recommended on Windows)**

```bash
cargo build --release
```

Artifact locations:

- Windows: `target\release\chash.exe`
- macOS / Linux: `target/release/chash`

No file is placed in the repository root unless copied manually or Option B is used.

**Option B — Makefile copy step**

```bash
make
```

Requires `make` on `PATH`. Invokes `cargo build --release`, then copies the binary to the project root (`chash.exe` on Windows, `chash` on Unix).

## Run

Execute from the repository root so the hard-coded path **commands.txt** resolves.

| Build method | Windows (PowerShell) | Unix shell |
|--------------|----------------------|------------|
| After `cargo build --release` | `.\target\release\chash.exe` | `./target/release/chash` |
| After `make` | `.\chash.exe` | `./chash` |

**Outputs**

- **stdout:** per-command messages (insert, update, delete, search, print blocks).
- **`hash.log`:** timestamped thread / lock events, then lock totals and a `Final Table:` snapshot.

## Validation

This repository includes a Python checker that loads test cases from files in **tests/cases** and runs them automatically.

Run:

```bash
python check_pa2.py
```

Current test-case files:

- `tests/cases/01_duplicate_insert.commands.txt`
- `tests/cases/01_duplicate_insert.expected.txt`
- `tests/cases/02_missing_delete_update_search.commands.txt`
- `tests/cases/02_missing_delete_update_search.expected.txt`
- `tests/cases/03_concurrent_prints.commands.txt`
- `tests/cases/03_concurrent_prints.expected.txt`
- `tests/cases/04_teacher_comprehensive.commands.txt`
- `tests/cases/04_teacher_comprehensive.expected.txt`
- `tests/cases/04_teacher_comprehensive.sample_hashlog.txt`

Checker behavior:

- Overwrites root `commands.txt` per test case.
- Runs the program binary and captures stdout.
- Normalizes only line endings and trailing spaces/tabs at line ends.
- Compares stdout to expected output and prints PASS/FAIL with unified diff on mismatch.
- Runs basic hash.log checks for configured cases.
- Runs repeated reader-overlap check for `03_concurrent_prints`.
- Runs structure-only sample-hashlog check for `04_teacher_comprehensive`.
- Exits nonzero if any stdout check fails.

## Source layout

| Path | Role |
|------|------|
| `check_pa2.py` | Case-driven validator (stdout + hash.log checks) |
| `src/main.rs` | Thread pool, `RwLock` table, turn gate, ordered stdout aggregation, `hash.log` footer |
| `src/command.rs` | `commands.txt` parsing (`threads` header, command lines) |
| `src/hash.rs` | Jenkins one-at-a-time hash |
| `src/table.rs` | Sorted list, CRUD + database string formatting |
| `src/sync.rs` | `Mutex` + `Condvar` turn manager |
| `src/logger.rs` | Mutex-backed `hash.log` writer and lock counters |
| `tests/cases/` | External command/expected/sample-hashlog case files |

## Other paths

| Path | Role |
|------|------|
| `README.txt` | Plain-text hand-in copy (build / run / AI attribution) |
| `RUST_EXPLANATION.md` | Rust concurrency and memory-safety notes (extra-credit documentation) |

## Git

Example remote:

```text
https://github.com/DucNguyen0159/Concurrent-Hash-Table.git
```

```bash
git fetch origin
git pull origin main
git push origin main
```

HTTPS pushes require a [GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) or SSH credentials configured for the host.

## Generative-AI disclosure

High-level attribution appears here; the plain-text **`README.txt`** contains the full citation required for academic submission. Tools: **ChatGPT (GPT)** and **Cursor** — see `README.txt` for scope, prompts, and verification steps.
