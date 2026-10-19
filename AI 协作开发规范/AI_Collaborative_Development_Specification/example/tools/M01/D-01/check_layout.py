"""Check DEMO layout data only. No firmware, hardware, or device writes."""
import argparse
import json
from pathlib import Path


def check_layout(data):
    if data.get("kind") != "DEMO_ONLY":
        raise ValueError("this example accepts DEMO_ONLY data")
    stores = data["stores"]
    for name, store in stores.items():
        capacity = store["capacity"]
        if type(capacity) is not int or capacity <= 0:
            raise ValueError(f"{name}: invalid capacity")
        intervals = []
        for region in store["regions"]:
            start, length = region["offset"], region["length"]
            if type(start) is not int or type(length) is not int:
                raise ValueError(f"{name}: offsets and lengths must be integers")
            if start < 0 or length <= 0 or start + length > capacity:
                raise ValueError(f"{name}/{region['name']}: out of bounds")
            intervals.append((start, start + length, region["name"]))
        intervals.sort()
        for previous, current in zip(intervals, intervals[1:]):
            if previous[1] > current[0]:
                raise ValueError(f"{name}: overlapping regions")
    if not stores:
        raise ValueError("no stores were supplied")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--layout", type=Path,
                        default=Path(__file__).parent / "fixtures" / "layout.json")
    args = parser.parse_args()
    try:
        data = json.loads(args.layout.read_text(encoding="utf-8"))
        check_layout(data)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"DEMO layout check failed: {error}\n")
    print(json.dumps({"scope": "DEMO_ONLY", "layout_data_valid": True,
                      "firmware_or_board_verified": False}))


if __name__ == "__main__":
    main()
