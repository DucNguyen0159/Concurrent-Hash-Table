Concurrent Hash Table (Rust)
Repository: https://github.com/DucNguyen0159/Concurrent-Hash-Table

Authors
-------
Henry Nguyen
  GitHub: https://github.com/DucNguyen0159
  Username: @DucNguyen0159

Minh Thien Pham
  GitHub: https://github.com/MinhThien-Pham
  Username: @MinhThien-Pham


Overview
--------
This project is a Rust implementation of the PA2 Concurrent Hash Table assignment.

The program:
- reads commands from a hard-coded file named commands.txt
- maintains a sorted singly linked list keyed by Jenkins one-at-a-time hashes
- uses a reader-writer lock for the shared table
- uses a mutex and condition variable to enforce thread turn order
- prints command results to stdout
- writes synchronization and lock events to hash.log


Prerequisites
-------------
Required:
- Rust stable toolchain
- Cargo

Optional:
- GNU Make

Note:
Cargo alone is enough to build and run the project.
The Makefile is only an extra convenience step that copies the release binary
into the repository root.


Build
-----
Option A (recommended, portable):
  cargo build --release

Output binaries:
  Windows: target\release\chash.exe
  macOS / Linux: target/release/chash

Option B (Makefile copy step):
  make

This runs cargo build --release and copies the binary into the repository root:
  Windows: chash.exe
  macOS / Linux: chash


Run
---
Run from the repository root so the hard-coded commands.txt path resolves correctly.

After cargo build --release:
  Windows PowerShell:
    .\target\release\chash.exe

  macOS / Linux:
    ./target/release/chash

After make:
  Windows PowerShell:
    .\chash.exe

  macOS / Linux:
    ./chash


Program Output
--------------
stdout:
- insert / update / delete / search result messages
- print output blocks
- final database print when required by the assignment/test file

hash.log:
- WAITING FOR MY TURN
- AWAKENED FOR WORK
- READ LOCK ACQUIRED / RELEASED
- WRITE LOCK ACQUIRED / RELEASED
- footer counts and final table snapshot


Validation
----------
A checker script is included:

  python check_pa2.py

The checker:
- loads test cases from tests/cases/
- overwrites root commands.txt with each test case input
- runs the compiled program
- compares stdout to expected output
- performs lightweight hash.log checks
- performs the repeated reader-overlap check for the concurrent prints case
- performs a structure-only hash.log check for the teacher comprehensive case

Current test-case files:
- tests/cases/01_duplicate_insert.commands.txt
- tests/cases/01_duplicate_insert.expected.txt
- tests/cases/02_missing_delete_update_search.commands.txt
- tests/cases/02_missing_delete_update_search.expected.txt
- tests/cases/03_concurrent_prints.commands.txt
- tests/cases/03_concurrent_prints.expected.txt
- tests/cases/04_teacher_comprehensive.commands.txt
- tests/cases/04_teacher_comprehensive.expected.txt
- tests/cases/04_teacher_comprehensive.sample_hashlog.txt


Important Files
---------------
- src/main.rs
    Thread workflow, turn ordering, stdout aggregation, final hash.log footer
- src/command.rs
    commands.txt parsing
- src/hash.rs
    Jenkins one-at-a-time hash
- src/table.rs
    Sorted linked-list table and CRUD operations
- src/sync.rs
    Mutex + Condvar turn manager
- src/logger.rs
    hash.log writer and lock counters
- RUST_EXPLANATION.md
    Extra-credit Rust explanation for a beginner reader


Generative-AI Attribution
-------------------------
This project used AI tools for planning, implementation support, debugging,
testing, and documentation.

Tools used:
- ChatGPT
- Cursor

How they were used:
- understanding and organizing the assignment specification and rubric
- discussing Rust synchronization choices such as RwLock, Mutex, and Condvar
- suggesting module structure and implementation steps
- helping review stdout formatting and hash.log behavior
- helping design and refine the checker script (check_pa2.py) and external test cases
- helping improve README.md, README.txt, and the Rust explanation document

Example prompts used (representative, paraphrased):
- "Help break this concurrent hash table assignment into Rust modules and implementation steps."
- "Check whether my stdout matches the assignment's expected output."
- "Review my hash.log behavior against the rubric."
- "Help refactor check_pa2.py to load external test cases and validate stdout and log structure."
- "Help rewrite README and README.txt so they better match the assignment requirements."

Verification performed by the student team:
- built the project locally with cargo build --release
- ran the compiled program from the repository root
- checked stdout against expected outputs
- inspected hash.log for lock behavior and footer counts
- ran python check_pa2.py on the included test cases
- manually reviewed and edited AI-generated suggestions before keeping them

All final code, documentation, and submission decisions were reviewed by the
human authors. We reviewed the final code and documentation ourselves and take responsibility for the submission.
