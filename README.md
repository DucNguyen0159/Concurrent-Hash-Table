# Concurrent Hash Table (COP 4600 PA2)

Course project: a **concurrent hash table** backed by a sorted linked list, with thread-safe access (reader–writer style locking) and ordered thread startup. This repository targets the **Rust extra-credit** implementation described in course materials; assignment specs and reference files live under **`PA2 Des/`**.

**GitHub:** [https://github.com/DucNguyen0159/Concurrent-Hash-Table](https://github.com/DucNguyen0159/Concurrent-Hash-Table)

## Prerequisites

- [Rust](https://rustup.rs/) (stable toolchain) and **Cargo**
- **GNU Make** (or compatible `make`) for the course-required `make` → `chash` build

## Build

```bash
make
```

This should produce the `chash` executable (release build; see `Makefile` once added).

## Run

1. Place **`commands.txt`** in the project root (or run from the directory that contains it).
2. Execute **`./chash`** (on Windows, `.\chash.exe` if applicable).

The program reads `commands.txt`, writes diagnostic output to **`hash.log`**, and prints command results to **stdout**.

## Repository layout

| Path | Purpose |
|------|--------|
| `PA2 Des/` | Assignment description, expected output, sample `commands_comprehensive_test.txt`, `hash.log`, Jenkins reference, `implement_plan.md` |
| `README.txt` | Plain-text README for course submission (build/run + AI citation) |
| `README.md` | This file — for GitHub |

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
