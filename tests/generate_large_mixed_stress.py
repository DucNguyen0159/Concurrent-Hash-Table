#!/usr/bin/env python3
"""Generate a deterministic large mixed PA2 stress case using an independent Python oracle.

Outputs:
- tests/cases/05_large_mixed_stress.commands.txt
- tests/cases/05_large_mixed_stress.expected.txt
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

SEED = 4600
TOTAL_COMMANDS = 220

CASE_BASENAME = "05_large_mixed_stress"


def jenkins_one_at_a_time(key: str) -> int:
    h = 0
    for b in key.encode("utf-8"):
        h = (h + b) & 0xFFFFFFFF
        h = (h + ((h << 10) & 0xFFFFFFFF)) & 0xFFFFFFFF
        h ^= h >> 6
    h = (h + ((h << 3) & 0xFFFFFFFF)) & 0xFFFFFFFF
    h ^= h >> 11
    h = (h + ((h << 15) & 0xFFFFFFFF)) & 0xFFFFFFFF
    return h & 0xFFFFFFFF


@dataclass
class Record:
    hash_value: int
    name: str
    salary: int

    def line(self) -> str:
        return f"{self.hash_value},{self.name},{self.salary}"


class OracleTable:
    def __init__(self) -> None:
        self.by_hash: dict[int, Record] = {}

    def insert(self, name: str, salary: int) -> str:
        h = jenkins_one_at_a_time(name)
        if h in self.by_hash:
            return f"Insert failed. Entry {h} is a duplicate.\n"
        self.by_hash[h] = Record(h, name, salary)
        return f"Inserted {h},{name},{salary}\n"

    def delete(self, name: str) -> str:
        h = jenkins_one_at_a_time(name)
        rec = self.by_hash.pop(h, None)
        if rec is None:
            return f"Entry {h} not deleted. Not in database.\n"
        return f"Deleted record for {rec.line()}\n"

    def update(self, name: str, salary: int) -> str:
        h = jenkins_one_at_a_time(name)
        rec = self.by_hash.get(h)
        if rec is None:
            return f"Update failed. Entry {h} not found.\n"
        old_line = rec.line()
        rec.salary = salary
        new_line = rec.line()
        return f"Updated record {h} from {old_line} to {new_line}\n"

    def search(self, name: str) -> str:
        h = jenkins_one_at_a_time(name)
        rec = self.by_hash.get(h)
        if rec is None:
            return f"{name} not found.\n"
        return f"Found: {rec.line()}\n"

    def print_db(self) -> str:
        out = ["Current Database:\n"]
        for h in sorted(self.by_hash.keys()):
            out.append(f"{self.by_hash[h].line()}\n")
        return "".join(out)


def make_name_pool() -> list[str]:
    first_names = [
        "Shigeru",
        "Hideo",
        "Gabe",
        "Todd",
        "Hidetaka",
        "Hideki",
        "Hironobu",
        "Sid",
        "Satoru",
        "Koji",
        "Yoko",
        "Nobuo",
        "Tetsuya",
        "Masahiro",
        "Yoshi",
        "Suda",
        "Sakurai",
        "Amy",
        "Cory",
        "Jade",
        "Rin",
        "Kai",
        "Avery",
        "Morgan",
        "Reese",
        "Jordan",
        "Taylor",
        "Casey",
        "Dakota",
        "Rowan",
    ]
    last_names = [
        "Miyamoto",
        "Kojima",
        "Newell",
        "Howard",
        "Miyazaki",
        "Kamiya",
        "Sakaguchi",
        "Meier",
        "Iwata",
        "Kondo",
        "Shimomura",
        "Uematsu",
        "Nomura",
        "Sakurai",
        "Suzuki",
        "Tanaka",
        "Nakamura",
        "Carver",
        "Mercer",
        "Rivers",
    ]

    names = [f"{first} {last}" for first in first_names for last in last_names]
    return names


def pick_fresh_name(
    name_pool: list[str],
    idx_ref: list[int],
    existing_hashes: set[int],
    used_names: set[str],
) -> str:
    while idx_ref[0] < len(name_pool):
        candidate = name_pool[idx_ref[0]]
        idx_ref[0] += 1
        h = jenkins_one_at_a_time(candidate)
        if candidate not in used_names and h not in existing_hashes:
            used_names.add(candidate)
            return candidate
    raise RuntimeError("Ran out of unique names for stress-case generation")


def pick_existing_name(rng: random.Random, current_names: list[str]) -> str:
    return rng.choice(current_names)


def pick_missing_name(rng: random.Random, name_pool: list[str], existing_hashes: set[int]) -> str:
    # Choose a name whose hash is currently not present in the table.
    for _ in range(1000):
        candidate = rng.choice(name_pool)
        if jenkins_one_at_a_time(candidate) not in existing_hashes:
            return candidate

    # Guaranteed fallback in the unlikely event random sampling keeps colliding.
    suffix = 0
    while True:
        candidate = f"Missing Person {suffix}"
        if jenkins_one_at_a_time(candidate) not in existing_hashes:
            return candidate
        suffix += 1


def main() -> None:
    rng = random.Random(SEED)
    root = Path(__file__).resolve().parent.parent
    cases_dir = root / "tests" / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)

    commands_path = cases_dir / f"{CASE_BASENAME}.commands.txt"
    expected_path = cases_dir / f"{CASE_BASENAME}.expected.txt"

    table = OracleTable()

    name_pool = make_name_pool()
    rng.shuffle(name_pool)

    # 220 total commands = 40 warm-up inserts + 179 mixed + final print.
    warmup_unique_inserts = 40
    mixed_counts = Counter(
        {
            "insert_unique": 45,
            "insert_duplicate": 25,
            "update_existing": 20,
            "update_missing": 15,
            "delete_existing": 18,
            "delete_missing": 12,
            "search_existing": 25,
            "search_missing": 12,
            "print": 7,
        }
    )

    mixed_categories = []
    for category, count in mixed_counts.items():
        mixed_categories.extend([category] * count)
    rng.shuffle(mixed_categories)

    # Avoid starting with print and avoid adjacent prints for readability.
    if mixed_categories and mixed_categories[0] == "print":
        for i in range(1, len(mixed_categories)):
            if mixed_categories[i] != "print":
                mixed_categories[0], mixed_categories[i] = mixed_categories[i], mixed_categories[0]
                break
    for i in range(1, len(mixed_categories)):
        if mixed_categories[i] == "print" and mixed_categories[i - 1] == "print":
            for j in range(i + 1, len(mixed_categories)):
                if mixed_categories[j] != "print":
                    mixed_categories[i], mixed_categories[j] = mixed_categories[j], mixed_categories[i]
                    break

    commands: list[str] = []
    stdout_lines: list[str] = []

    name_index = [0]
    used_unique_names: set[str] = set()

    operation_counts = Counter()

    def current_names() -> list[str]:
        return [rec.name for rec in table.by_hash.values()]

    # Warm-up phase: guaranteed many unique inserts.
    for _ in range(warmup_unique_inserts):
        name = pick_fresh_name(name_pool, name_index, set(table.by_hash.keys()), used_unique_names)
        salary = rng.randint(58000, 132000)
        priority = len(commands)
        commands.append(f"insert,{name},{salary},{priority}")
        stdout_lines.append(table.insert(name, salary))
        operation_counts["insert"] += 1
        operation_counts["insert_unique"] += 1

    # Mixed phase.
    for category in mixed_categories:
        priority = len(commands)
        existing_hashes = set(table.by_hash.keys())

        if category == "insert_unique":
            name = pick_fresh_name(name_pool, name_index, existing_hashes, used_unique_names)
            salary = rng.randint(58000, 132000)
            commands.append(f"insert,{name},{salary},{priority}")
            stdout_lines.append(table.insert(name, salary))
            operation_counts["insert"] += 1
            operation_counts["insert_unique"] += 1

        elif category == "insert_duplicate":
            name = pick_existing_name(rng, current_names())
            salary = rng.randint(58000, 132000)
            commands.append(f"insert,{name},{salary},{priority}")
            stdout_lines.append(table.insert(name, salary))
            operation_counts["insert"] += 1
            operation_counts["insert_duplicate"] += 1

        elif category == "update_existing":
            name = pick_existing_name(rng, current_names())
            salary = rng.randint(60000, 145000)
            commands.append(f"update,{name},{salary},{priority}")
            stdout_lines.append(table.update(name, salary))
            operation_counts["update"] += 1
            operation_counts["update_existing"] += 1

        elif category == "update_missing":
            name = pick_missing_name(rng, name_pool, existing_hashes)
            salary = rng.randint(60000, 145000)
            commands.append(f"update,{name},{salary},{priority}")
            stdout_lines.append(table.update(name, salary))
            operation_counts["update"] += 1
            operation_counts["update_missing"] += 1

        elif category == "delete_existing":
            name = pick_existing_name(rng, current_names())
            commands.append(f"delete,{name},{priority}")
            stdout_lines.append(table.delete(name))
            operation_counts["delete"] += 1
            operation_counts["delete_existing"] += 1

        elif category == "delete_missing":
            name = pick_missing_name(rng, name_pool, existing_hashes)
            commands.append(f"delete,{name},{priority}")
            stdout_lines.append(table.delete(name))
            operation_counts["delete"] += 1
            operation_counts["delete_missing"] += 1

        elif category == "search_existing":
            name = pick_existing_name(rng, current_names())
            commands.append(f"search,{name},{priority}")
            stdout_lines.append(table.search(name))
            operation_counts["search"] += 1
            operation_counts["search_existing"] += 1

        elif category == "search_missing":
            name = pick_missing_name(rng, name_pool, existing_hashes)
            commands.append(f"search,{name},{priority}")
            stdout_lines.append(table.search(name))
            operation_counts["search"] += 1
            operation_counts["search_missing"] += 1

        elif category == "print":
            commands.append(f"print,{priority}")
            stdout_lines.append(table.print_db())
            operation_counts["print"] += 1

        else:
            raise RuntimeError(f"Unexpected category: {category}")

    # Final required print.
    final_priority = len(commands)
    commands.append(f"print,{final_priority}")
    stdout_lines.append(table.print_db())
    operation_counts["print"] += 1

    if len(commands) != TOTAL_COMMANDS:
        raise RuntimeError(f"Expected {TOTAL_COMMANDS} commands, generated {len(commands)}")

    commands_text = "\n".join([f"threads,{len(commands)}", *commands]) + "\n"
    expected_text = "".join(stdout_lines)

    commands_path.write_text(commands_text, encoding="utf-8", newline="\n")
    expected_path.write_text(expected_text, encoding="utf-8", newline="\n")

    print(f"Generated: {commands_path}")
    print(f"Generated: {expected_path}")
    print(f"Seed: {SEED}")
    print(f"Total commands: {len(commands)}")
    print(
        "Counts: "
        f"insert={operation_counts['insert']} "
        f"(unique={operation_counts['insert_unique']}, duplicate={operation_counts['insert_duplicate']}), "
        f"update={operation_counts['update']} "
        f"(existing={operation_counts['update_existing']}, missing={operation_counts['update_missing']}), "
        f"delete={operation_counts['delete']} "
        f"(existing={operation_counts['delete_existing']}, missing={operation_counts['delete_missing']}), "
        f"search={operation_counts['search']} "
        f"(existing={operation_counts['search_existing']}, missing={operation_counts['search_missing']}), "
        f"print={operation_counts['print']}"
    )


if __name__ == "__main__":
    main()
