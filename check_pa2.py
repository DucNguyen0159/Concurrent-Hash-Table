#!/usr/bin/env python3
"""Simple validator for the PA2 Concurrent Hash Table program.

What this script does:
1) Writes each test input to commands.txt
2) Runs the program binary
3) Captures stdout exactly
4) Reads hash.log
5) Normalizes only line endings and trailing spaces at line ends
6) Compares stdout to expected output
7) Prints PASS/FAIL and unified diffs on failures
8) For the concurrency test, checks whether two read operations overlap
9) Exits nonzero if any stdout test fails
"""

from __future__ import annotations

import difflib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


OVERLAP_CASES = {
    "03_concurrent_prints": {
        "first_thread": 10,
        "second_thread": 11,
        "repeat_runs": 30,
    }
}


@dataclass
class TestCase:
    name: str
    basename: str
    commands_input: str
    expected_stdout: str


def normalize_text(text: str) -> str:
    """Normalize only line endings and trailing spaces at line ends."""
    # Normalize CRLF/CR to LF.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove trailing spaces and tabs from each line, preserving internal spaces.
    lines = text.split("\n")
    lines = [line.rstrip(" \t") for line in lines]
    return "\n".join(lines)


def make_unified_diff(expected: str, actual: str, test_name: str) -> str:
    expected_lines = expected.splitlines(keepends=True)
    actual_lines = actual.splitlines(keepends=True)
    diff_lines = difflib.unified_diff(
        expected_lines,
        actual_lines,
        fromfile=f"{test_name} expected",
        tofile=f"{test_name} actual",
    )
    return "".join(diff_lines)


def decode_output(data: bytes) -> str:
    """Decode subprocess output safely."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode(errors="replace")


def find_program_path(workdir: Path) -> Path:
    """Find the most likely program binary path.

    Requirement preference:
    - Windows: chash.exe if present
    - Unix: ./chash

    Extra fallback paths are included for convenience.
    """
    is_windows = os.name == "nt"

    candidates = []
    if is_windows:
        candidates.extend(
            [
                workdir / "chash.exe",
                workdir / "chash",
                workdir / "target" / "release" / "chash.exe",
                workdir / "target" / "release" / "chash",
            ]
        )
    else:
        candidates.extend(
            [
                workdir / "chash",
                workdir / "chash.exe",
                workdir / "target" / "release" / "chash",
                workdir / "target" / "release" / "chash.exe",
            ]
        )

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate

    expected_hint = "chash.exe" if is_windows else "./chash"
    searched = "\n".join(f"- {p}" for p in candidates)
    raise FileNotFoundError(
        f"Could not find program binary. Expected {expected_hint} (or fallback paths).\n"
        f"Searched:\n{searched}"
    )


def run_program(program_path: Path, workdir: Path) -> tuple[str, str, int]:
    """Run the program and return (stdout, hash_log_text, returncode)."""
    hash_log = workdir / "hash.log"

    # Start clean so each test reads only this run's log.
    if hash_log.exists():
        hash_log.unlink()

    completed = subprocess.run(
        [str(program_path)],
        cwd=str(workdir),
        capture_output=True,
        text=False,
        check=False,
    )

    stdout_text = decode_output(completed.stdout)

    if hash_log.exists():
        hash_log_text = hash_log.read_text(encoding="utf-8", errors="replace")
    else:
        hash_log_text = ""

    return stdout_text, hash_log_text, completed.returncode


def find_first_index(lines: list[str], needle: str) -> Optional[int]:
    for i, line in enumerate(lines):
        if needle in line:
            return i
    return None


def check_read_overlap(hash_log_text: str, first_thread: int, second_thread: int) -> tuple[bool, str]:
    """Check overlap rule:

    overlap = THREAD {second_thread} READ LOCK ACQUIRED appears after
              THREAD {first_thread} READ LOCK ACQUIRED and before
              THREAD {first_thread} READ LOCK RELEASED.
    """
    normalized_log = normalize_text(hash_log_text)
    lines = normalized_log.split("\n")

    first_acq = find_first_index(lines, f"THREAD {first_thread} READ LOCK ACQUIRED")
    first_rel = find_first_index(lines, f"THREAD {first_thread} READ LOCK RELEASED")
    second_acq = find_first_index(lines, f"THREAD {second_thread} READ LOCK ACQUIRED")

    if first_acq is None:
        return False, f"THREAD {first_thread} READ LOCK ACQUIRED not found in hash.log"
    if first_rel is None:
        return False, f"THREAD {first_thread} READ LOCK RELEASED not found in hash.log"
    if second_acq is None:
        return False, f"THREAD {second_thread} READ LOCK ACQUIRED not found in hash.log"

    if first_acq >= first_rel:
        return False, f"THREAD {first_thread} release appears before/at its acquire in hash.log"

    overlap = first_acq < second_acq < first_rel
    details = (
        f"indices: T{first_thread}_ACQ={first_acq}, T{second_thread}_ACQ={second_acq}, "
        f"T{first_thread}_REL={first_rel}; "
        f"overlap={'YES' if overlap else 'NO'}"
    )
    return overlap, details


def load_test_case(commands_path: Path) -> TestCase:
    basename = commands_path.name.removesuffix(".commands.txt")
    expected_path = commands_path.with_name(f"{basename}.expected.txt")

    return TestCase(
        name=basename.replace("_", " "),
        basename=basename,
        commands_input=commands_path.read_text(encoding="utf-8"),
        expected_stdout=expected_path.read_text(encoding="utf-8"),
    )


def run_overlap_check(
    program_path: Path,
    workdir: Path,
    commands_input: str,
    first_thread: int,
    second_thread: int,
    repeat_runs: int,
) -> tuple[bool, str]:
    """Run the overlap test repeatedly and report the first observed overlap."""

    for run_number in range(1, repeat_runs + 1):
        commands_file = workdir / "commands.txt"
        commands_file.write_text(commands_input, encoding="utf-8", newline="\n")

        _, hash_log_raw, _ = run_program(program_path, workdir)
        overlap, _ = check_read_overlap(hash_log_raw, first_thread, second_thread)
        if overlap:
            return True, f"PASS (observed overlap on run {run_number} of {repeat_runs})"

    return False, f"FAIL (no overlap observed in {repeat_runs} runs)"


def main() -> int:
    workdir = Path(__file__).resolve().parent
    cases_dir = workdir / "tests" / "cases"
    commands_files = sorted(cases_dir.glob("*.commands.txt"))
    test_cases = [load_test_case(commands_path) for commands_path in commands_files]

    try:
        program_path = find_program_path(workdir)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(f"Using program binary: {program_path}")

    any_stdout_failures = False

    for test in test_cases:
        commands_file = workdir / "commands.txt"
        commands_file.write_text(test.commands_input, encoding="utf-8", newline="\n")

        actual_stdout_raw, hash_log_raw, returncode = run_program(program_path, workdir)

        actual_stdout = normalize_text(actual_stdout_raw)
        expected_stdout = normalize_text(test.expected_stdout)

        stdout_ok = actual_stdout == expected_stdout

        print(f"\n=== {test.name} ===")
        print(f"Program return code: {returncode}")

        if stdout_ok:
            print("STDOUT: PASS")
        else:
            print("STDOUT: FAIL")
            diff = make_unified_diff(expected_stdout, actual_stdout, test.name)
            if diff:
                print("Unified diff:")
                print(diff, end="" if diff.endswith("\n") else "\n")
            else:
                print("Unified diff: (no visible diff generated)")
            any_stdout_failures = True

        overlap_case = OVERLAP_CASES.get(test.basename)
        if overlap_case is not None:
            overlap, summary = run_overlap_check(
                program_path,
                workdir,
                test.commands_input,
                overlap_case["first_thread"],
                overlap_case["second_thread"],
                overlap_case["repeat_runs"],
            )
            print(f"LOG CONCURRENCY CHECK: {summary}")

    if any_stdout_failures:
        print("\nOverall result: FAIL (one or more stdout tests failed)")
        return 1

    print("\nOverall result: PASS (all stdout tests passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
