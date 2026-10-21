"""Audit DEMO material links independently; no actual board verdict is produced."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def audit(summary):
    if summary["kind"] != "DEMO_ONLY":
        raise ValueError("summary is not DEMO_ONLY")
    if summary["accepted_candidate"] != "DEMO-M01-R2":
        raise ValueError("unapproved final candidate")
    if summary["case_set"] != "DEMO-CASES-M01-02":
        raise ValueError("unapproved case set")
    if summary.get("board_tests_executed_by_this_tool") is not False:
        raise ValueError("offline tool must not claim board execution")
    expected = {f"M01-T{number:02d}" for number in range(1, 8)}
    rows = summary["results"]
    if len(rows) != len(expected) or {row["case_id"] for row in rows} != expected:
        raise ValueError("missing or duplicate case results")
    raw = {}
    failures = set()
    for round_name in ("R01", "R02", "R03"):
        relative = f"evidence/M01/{round_name}/results.csv"
        with (ROOT / relative).open(encoding="utf-8", newline="") as stream:
            for record in csv.DictReader(stream):
                key = (record["candidate"], record["case_id"], relative)
                if key in raw or record["kind"] != "DEMO_ONLY":
                    raise ValueError("invalid or duplicate raw record")
                raw[key] = record
                if record["result"] == "FAIL":
                    failures.add(key)
    reuse_cases = {"M01-T01", "M01-T03", "M01-T06"}
    for row in rows:
        case_id = row["case_id"]
        candidate = "DEMO-M01-R1" if case_id in reuse_cases else "DEMO-M01-R2"
        source = ("evidence/M01/R01/results.csv" if case_id in reuse_cases
                  else "evidence/M01/R03/results.csv" if case_id == "M01-T07"
                  else "evidence/M01/R02/results.csv")
        reuse_basis = "" if case_id == "M01-T07" else "C-REUSE-02"
        if row["candidate"] != candidate or row["source_csv"] != source:
            raise ValueError(f"{case_id}: unapproved source or candidate")
        if row["reuse_basis"] != reuse_basis:
            raise ValueError(f"{case_id}: invalid reuse authority")
        actual = raw[(candidate, case_id, source)]
        for field in ("kind", "result", "evidence_file"):
            if row[field] != actual[field]:
                raise ValueError(f"{case_id}: does not match raw record")
        if row["result"] not in {"PASS", "FAIL", "UNTESTED"}:
            raise ValueError(f"{case_id}: invalid result")
        evidence = (ROOT / row["evidence_file"]).resolve()
        if not evidence.is_relative_to(ROOT / "evidence" / "M01"):
            raise ValueError(f"{case_id}: evidence path escapes the example")
        if not evidence.is_file() or not evidence.read_text(encoding="utf-8").startswith("DEMO_ONLY"):
            raise ValueError(f"{case_id}: missing DEMO evidence")
    reported_failures = {(row["candidate"], row["case_id"], row["source_csv"])
                         for row in summary["prior_failures"]}
    if reported_failures != failures:
        raise ValueError("prior failures were dropped or invented")
    all_pass = all(row["result"] == "PASS" for row in rows)
    if summary["all_cases_pass"] is not all_pass:
        raise ValueError("summary verdict disagrees with its rows")
    return {"scope": "DEMO_ONLY", "records_consistent": True,
            "all_cases_pass": all_pass, "real_board_acceptance": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path,
                        default=ROOT / "evidence/M01/R03/summary.json")
    args = parser.parse_args()
    try:
        report = audit(json.loads(args.summary.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"DEMO evidence audit failed: {error}\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
