"""Summarize synthetic M01 records. This does not execute board test cases."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCES = ("evidence/M01/R01/results.csv", "evidence/M01/R02/results.csv")
CANDIDATE = "DEMO-M01-R2"
REUSE = {"M01-T01", "M01-T03", "M01-T06"}
CASES = {f"M01-T{number:02d}" for number in range(1, 7)}


def summarize():
    records = []
    seen = set()
    for source in SOURCES:
        with (ROOT / source).open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if not rows:
            raise ValueError(f"{source}: no data")
        for row in rows:
            if row["kind"] != "DEMO_ONLY" or row["case_id"] not in CASES:
                raise ValueError(f"{source}: invalid demo record")
            if row["result"] not in {"PASS", "FAIL", "UNTESTED"}:
                raise ValueError(f"{source}: invalid result")
            identity = (row["candidate"], row["case_id"])
            if identity in seen:
                raise ValueError(f"{source}: duplicate record")
            seen.add(identity)
            records.append({**row, "source_csv": source})
    selected = []
    for case_id in sorted(CASES):
        candidate = "DEMO-M01-R1" if case_id in REUSE else CANDIDATE
        matches = [row for row in records
                   if row["case_id"] == case_id and row["candidate"] == candidate]
        if len(matches) != 1:
            raise ValueError(f"{case_id}: missing approved result")
        selected.append({**matches[0],
                         "reuse_basis": "C-REUSE-01" if case_id in REUSE else ""})
    prior_failures = [{"candidate": row["candidate"], "case_id": row["case_id"],
                       "source_csv": row["source_csv"]}
                      for row in records if row["result"] == "FAIL"]
    return {"kind": "DEMO_ONLY", "accepted_candidate": CANDIDATE,
            "case_set": "DEMO-CASES-M01-01", "results": selected,
            "prior_failures": prior_failures,
            "all_cases_pass": all(row["result"] == "PASS" for row in selected),
            "board_tests_executed_by_this_tool": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        help="write a new file, refusing to overwrite existing data")
    args = parser.parse_args()
    try:
        result = summarize()
        rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
        if args.output is None:
            print(rendered, end="")
        else:
            output = args.output.resolve()
            if not output.is_relative_to(ROOT / "evidence" / "M01"):
                raise ValueError("output must stay in this example's evidence/M01")
            with output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(rendered)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"DEMO summary failed: {error}\n")


if __name__ == "__main__":
    main()
