================================================================================
  Concurrent Hash Table — Rust implementation
  https://github.com/DucNguyen0159/Concurrent-Hash-Table
================================================================================

AUTHORS
--------
  Contributor          Contact
  -------------------  --------------------------------------------------
  Henry Nguyen         https://github.com/DucNguyen0159
                       @DucNguyen0159

  Minh Thien Pham      —


OVERVIEW
--------
  Multi-threaded program: reads commands.txt (hard-coded path), maintains
  a sorted singly linked list keyed by Jenkins one-at-a-time hashes, uses
  std::sync::RwLock for readers vs writers, and std::sync::Mutex + Condvar
  for strict command-index turn order. Writes hash.log; prints results to
  stdout.


PREREQUISITES
-------------
  - Rust (stable) and Cargo — required.
  - GNU Make — optional; only for Makefile copy of the release binary to
    the repository root (chash / chash.exe). Windows systems often lack
    Make; Cargo alone is sufficient.


BUILD
-----
  Option A (portable, recommended on Windows):

    cargo build --release

  Output binaries:
    Windows:  target\release\chash.exe
    Unix:     target/release/chash

  The repository root is not modified unless the binary is copied manually
  or Option B is used.

  Option B (Makefile + copy to root):

    make

  Requires make on PATH. Runs cargo build --release, then copies:
    Windows -> chash.exe in repo root
    Unix    -> ./chash in repo root


RUN
-----
  Working directory: repository root (must contain commands.txt).
  A sample commands.txt is committed.

  After cargo build --release:
    Windows PowerShell:  .\target\release\chash.exe
    Unix:                ./target/release/chash

  After a successful make:
    Windows:  .\chash.exe
    Unix:     ./chash


OUTPUT
------
  stdout  — command outcomes (insert / update / delete / search / print).
  hash.log — timestamped WAITING / AWAKENED / lock lines, then lock counts
             and a Final Table: section.

  For the bundled commands.txt, stdout was validated against a frozen
  golden capture of the same workload (lines 6 through 160 of that file).

  RUST_EXPLANATION.md — design notes for Rust concurrency / safety.


SUBMISSION
----------
  When a rubric asks for plain text, include this README.txt in the
  archive. README.md mirrors build/run information for GitHub.


GENERATIVE-AI ATTRIBUTION (academic integrity)
----------------------------------------------
  Tools used throughout the project lifecycle:

    - OpenAI ChatGPT (GPT family, browser and API-style use as available
      during the work period)
    - Cursor (editor with integrated AI assistant / agent)

  Roles — ChatGPT (GPT):
    - Consolidated requirements from local markdown and text notes
      (command grammar, stdout formats, hash.log layout, grading themes).
    - Produced and refined an implementation-plan breakdown: module split
      (command, hash, table, sync, logger, main), turn ordering vs RwLock
      separation, edge cases (e.g. print/search lines with extra comma
      fields), and ordering of implementation steps.
    - Answered Rust std::sync questions (RwLock vs Mutex, Condvar wait
      loops, channel vs sorted stdout), and suggested message strings
      aligned with the golden expected-stdout document.
    - Drafted starter patterns for Jenkins hash (wrapping u32 arithmetic)
      and sorted linked-list insert/delete.

  Roles — Cursor:
    - Implemented the Rust crate in the workspace: Cargo.toml, Makefile,
      src/*.rs, commands.txt copy, RUST_EXPLANATION.md.
    - Ran cargo build / cargo test / cargo check, compared program stdout
      to the golden expected-stdout capture and adjusted logic (e.g. turn
      advance after critical sections, final-print behavior for that file).
    - Synchronized README.md and README.txt with accurate Windows vs Unix
      run paths; updated .gitignore for build artifacts.
    - Earlier session: initial git remote, README scaffolding, sample
      commits / push workflow documentation.

  Example prompts (representative, paraphrased):
    - "Read the implementation plan and specification notes; implement
      Rust chash with the described modules; stdout must match the golden
      expected-output lines 6-160 for commands.txt."
    - "Why does the first Current Database block miss rows? Fix turn vs
      RwLock ordering."

  Verification performed:
    - cargo test (hash unit tests).
    - cargo build --release.
    - Diff of program stdout against the frozen golden expected-output file
      for the committed workload.
    - Manual inspection of hash.log (lock counts, Final Table section).

  All generated material was reviewed, edited, and executed locally before
  submission. Responsibility for correctness, originality where required,
  and compliance with course policy rests with the human submitters.


================================================================================
