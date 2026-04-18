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
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


OVERLAP_CASES = {
    "03_concurrent_prints": {
        "first_thread": 10,
        "second_thread": 11,
        "repeat_runs": 30,
    }
}

BASIC_HASHLOG_CASES = {
    "01_duplicate_insert": True,
    "02_missing_delete_update_search": True,
    "03_concurrent_prints": True,
    "04_teacher_comprehensive": True,
    "05_large_mixed_stress": True,
}

SAMPLE_HASHLOG_CASES = {
    "04_teacher_comprehensive": {
        "mode": "structure_only"
    }
}

COMMAND_TYPES = {"INSERT", "DELETE", "UPDATE", "SEARCH", "PRINT"}
COMMAND_LINE_RE = re.compile(r"^THREAD\s+\d+\s+([A-Z]+)")


@dataclass
class TestCase:
    name: str
    basename: str
    commands_input: str
    expected_stdout: str
    sample_hashlog: Optional[str] = None


@dataclass
class LogSummary:
    waiting: int = 0
    awakened: int = 0
    command_lines: int = 0
    command_types: list[str] = field(default_factory=list)
    read_acq: int = 0
    read_rel: int = 0
    write_acq: int = 0
    write_rel: int = 0
    footer_acq: Optional[int] = None
    footer_rel: Optional[int] = None


def normalize_text(text: str) -> str:
    """Normalize only line endings and trailing spaces at line ends."""
    # Normalize CRLF/CR to LF.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove trailing spaces and tabs from each line, preserving internal spaces.
    lines = text.split("\n")
    lines = [line.rstrip(" \t") for line in lines]
    return "\n".join(lines)


def normalize_for_stdout_compare(text: str) -> str:
    """Normalize stdout text, then ignore one optional final newline."""
    normalized = normalize_text(text)
    if normalized.endswith("\n"):
        return normalized[:-1]
    return normalized


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


def parse_command_types(commands_input: str) -> list[str]:
    """Return command names from commands input, excluding the header line."""
    lines = [line for line in normalize_text(commands_input).split("\n") if line.strip()]
    if not lines:
        return []

    command_types: list[str] = []
    for line in lines[1:]:
        command_name = line.split(",", 1)[0].strip().upper()
        command_types.append(command_name)
    return command_types


def strip_timestamp_prefix(line: str) -> str:
    """Remove leading numeric timestamp prefix like '12345: ' if present."""
    if ": " not in line:
        return line
    maybe_ts, rest = line.split(": ", 1)
    if maybe_ts.isdigit():
        return rest
    return line


def parse_footer_count(line: str, prefix: str) -> Optional[int]:
    if not line.startswith(prefix):
        return None
    remainder = line[len(prefix):].strip()
    if not remainder:
        return None
    try:
        return int(remainder)
    except ValueError:
        return None


def parse_hash_log(hash_log_text: str) -> LogSummary:
    summary = LogSummary()

    for raw_line in normalize_text(hash_log_text).split("\n"):
        if not raw_line.strip():
            continue

        line = strip_timestamp_prefix(raw_line.strip())

        if "WAITING FOR MY TURN" in line:
            summary.waiting += 1
            continue
        if "AWAKENED FOR WORK" in line:
            summary.awakened += 1
            continue
        if "READ LOCK ACQUIRED" in line:
            summary.read_acq += 1
            continue
        if "READ LOCK RELEASED" in line:
            summary.read_rel += 1
            continue
        if "WRITE LOCK ACQUIRED" in line:
            summary.write_acq += 1
            continue
        if "WRITE LOCK RELEASED" in line:
            summary.write_rel += 1
            continue

        acq = parse_footer_count(line, "Number of lock acquisitions:")
        if acq is not None:
            summary.footer_acq = acq
            continue

        rel = parse_footer_count(line, "Number of lock releases:")
        if rel is not None:
            summary.footer_rel = rel
            continue

        command_match = COMMAND_LINE_RE.match(line)
        if command_match:
            maybe_command = command_match.group(1)
            if maybe_command in COMMAND_TYPES:
                summary.command_lines += 1
                summary.command_types.append(maybe_command)

    return summary


def validate_log_invariants(
    expected_command_types: list[str],
    summary: LogSummary,
    require_exact_command_type_multiset: bool,
) -> tuple[bool, str]:
    expected_command_count = len(expected_command_types)

    if summary.command_lines != expected_command_count:
        return False, f"expected {expected_command_count} command lines, got {summary.command_lines}"
    if summary.waiting != expected_command_count:
        return False, f"expected {expected_command_count} WAITING lines, got {summary.waiting}"
    if summary.awakened != expected_command_count:
        return False, f"expected {expected_command_count} AWAKENED lines, got {summary.awakened}"

    expected_write_commands = sum(
        cmd in {"INSERT", "UPDATE", "DELETE"} for cmd in expected_command_types
    )
    expected_read_commands = sum(
        cmd in {"SEARCH", "PRINT"} for cmd in expected_command_types
    )

    if summary.write_acq != expected_write_commands:
        return False, f"expected {expected_write_commands} WRITE LOCK ACQUIRED, got {summary.write_acq}"
    if summary.write_rel != expected_write_commands:
        return False, f"expected {expected_write_commands} WRITE LOCK RELEASED, got {summary.write_rel}"
    if summary.read_acq != expected_read_commands:
        return False, f"expected {expected_read_commands} READ LOCK ACQUIRED, got {summary.read_acq}"
    if summary.read_rel != expected_read_commands:
        return False, f"expected {expected_read_commands} READ LOCK RELEASED, got {summary.read_rel}"

    total_acq = summary.read_acq + summary.write_acq
    total_rel = summary.read_rel + summary.write_rel
    if total_acq != total_rel:
        return False, f"total lock acquisitions {total_acq} != releases {total_rel}"

    if summary.footer_acq is not None and summary.footer_acq != total_acq:
        return False, f"footer acquisitions {summary.footer_acq} != parsed acquisitions {total_acq}"
    if summary.footer_rel is not None and summary.footer_rel != total_rel:
        return False, f"footer releases {summary.footer_rel} != parsed releases {total_rel}"

    if require_exact_command_type_multiset:
        expected_counter = Counter(expected_command_types)
        actual_counter = Counter(summary.command_types)
        if actual_counter != expected_counter:
            return False, "command types in log do not match command types in input"

    return True, "ok"


def run_basic_hashlog_check(commands_input: str, hash_log_text: str) -> tuple[bool, str]:
    expected_command_types = parse_command_types(commands_input)
    parsed_log = parse_hash_log(hash_log_text)
    return validate_log_invariants(
        expected_command_types,
        parsed_log,
        require_exact_command_type_multiset=False,
    )


def run_structure_only_hashlog_check(
    commands_input: str,
    hash_log_text: str,
    sample_hashlog_text: str,
) -> tuple[bool, str]:
    if not sample_hashlog_text.strip():
        return False, "sample hash.log is empty"

    sample = parse_hash_log(sample_hashlog_text)
    actual = parse_hash_log(hash_log_text)

    category_requirements = [
        ("WAITING", sample.waiting, actual.waiting),
        ("AWAKENED", sample.awakened, actual.awakened),
        ("COMMAND", sample.command_lines, actual.command_lines),
        ("READ_ACQ", sample.read_acq, actual.read_acq),
        ("READ_REL", sample.read_rel, actual.read_rel),
        ("WRITE_ACQ", sample.write_acq, actual.write_acq),
        ("WRITE_REL", sample.write_rel, actual.write_rel),
    ]
    for label, sample_count, actual_count in category_requirements:
        if sample_count > 0 and actual_count == 0:
            return False, f"category {label} missing from actual hash.log"

    expected_command_types = parse_command_types(commands_input)
    return validate_log_invariants(
        expected_command_types,
        actual,
        require_exact_command_type_multiset=True,
    )


def load_test_case(commands_path: Path) -> TestCase:
    basename = commands_path.name.removesuffix(".commands.txt")
    expected_path = commands_path.with_name(f"{basename}.expected.txt")
    sample_hashlog_path = commands_path.with_name(f"{basename}.sample_hashlog.txt")

    if not expected_path.exists():
        raise FileNotFoundError(f"Missing expected output file: {expected_path}")

    return TestCase(
        name=basename.replace("_", " "),
        basename=basename,
        commands_input=commands_path.read_text(encoding="utf-8"),
        expected_stdout=expected_path.read_text(encoding="utf-8"),
        sample_hashlog=(
            sample_hashlog_path.read_text(encoding="utf-8", errors="replace")
            if sample_hashlog_path.exists()
            else None
        ),
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
    if not commands_files:
        print(f"ERROR: no .commands.txt files found in {cases_dir}")
        return 2

    try:
        test_cases = [load_test_case(commands_path) for commands_path in commands_files]
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2

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

        actual_stdout = normalize_for_stdout_compare(actual_stdout_raw)
        expected_stdout = normalize_for_stdout_compare(test.expected_stdout)

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

        if BASIC_HASHLOG_CASES.get(test.basename):
            basic_ok, basic_message = run_basic_hashlog_check(
                test.commands_input,
                hash_log_raw,
            )
            if basic_ok:
                print("BASIC HASH.LOG CHECK: PASS")
            else:
                print(f"BASIC HASH.LOG CHECK: FAIL ({basic_message})")

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

        sample_case = SAMPLE_HASHLOG_CASES.get(test.basename)
        if sample_case is not None:
            if test.sample_hashlog is None:
                print("HASH.LOG STRUCTURE CHECK: FAIL (sample hash.log file missing)")
            elif sample_case.get("mode") == "structure_only":
                structure_ok, structure_message = run_structure_only_hashlog_check(
                    test.commands_input,
                    hash_log_raw,
                    test.sample_hashlog,
                )
                if structure_ok:
                    print("HASH.LOG STRUCTURE CHECK: PASS")
                else:
                    print(f"HASH.LOG STRUCTURE CHECK: FAIL ({structure_message})")
            else:
                print("HASH.LOG STRUCTURE CHECK: FAIL (unsupported sample hash.log mode)")

    if any_stdout_failures:
        print("\nOverall result: FAIL (one or more stdout tests failed)")
        return 1

    print("\nOverall result: PASS (all stdout tests passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
