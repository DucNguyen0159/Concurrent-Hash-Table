================================================================================
  COP 4600 PA2 — Concurrent Hash Table (Rust extra credit)
  Repository: https://github.com/DucNguyen0159/Concurrent-Hash-Table
================================================================================

PREREQUISITES
-------------
  - Rust (stable) and Cargo — required.
  - GNU Make — optional. Only needed for the course-style "make" step that
    copies the built binary to the project root as chash or chash.exe.
    Many Windows machines do not have make; use Cargo only (below).


BUILD
-----
  Option A — recommended on Windows (always works):

    cargo build --release

  The executable is:
    - Windows:  target\release\chash.exe
    - Unix:     target/release/chash

  Nothing is copied to the repo root unless you copy it yourself or use
  Option B.

  Option B — matches hand-in instructions ("make" then run chash in root):

    make

  Requires "make" on your PATH. The Makefile runs cargo build --release,
  then copies the binary to the project root:
    - Windows:  chash.exe
    - Unix:     ./chash


RUN
---
  1. Run from the project root (where commands.txt is). A sample
     commands.txt is included.

  2. After "cargo build --release":
       Windows (PowerShell):  .\target\release\chash.exe
       Unix:                  ./target/release/chash

     After "make" (only if that succeeded):
       Windows:  .\chash.exe
       Unix:     ./chash

  Stdout for the bundled workload matches PA2 Des/PA#2 Expected Output.md
  (lines 6-160).


OUTPUT
------
  - stdout: command results (insert/update/delete/search/print messages).
  - hash.log: synchronization diagnostics (timestamps, thread turns, locks,
    then lock counts and "Final Table:" snapshot at end of run).

  See RUST_EXPLANATION.md for the Rust extra-credit design summary.


PROJECT FILES
-------------
  Course specs, sample commands, expected output, and implementation notes
  are under the folder: PA2 Des/


SUBMISSION NOTE
---------------
  This README.txt is the plain-text README for instructor/grader use.
  README.md in the same directory is for GitHub and may contain the same
  information in Markdown form.


AI USE CITATION (required by course policy — fill in before submitting)
-----------------------------------------------------------------------
  Tools used (e.g., ChatGPT, Cursor, Copilot):

  What you used the tool for (design, debugging, code generation, etc.):

  Example prompts or workflow (enough detail to show real use):

  How you verified correctness (tests, diff against expected output, etc.):

  I am responsible for the final submitted work.

================================================================================
