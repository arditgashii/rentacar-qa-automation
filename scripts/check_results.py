"""Compares the failed tests in a JUnit report with expected-failures.txt.

    python scripts/check_results.py reports/junit.xml               # bugs on: exactly the listed tests fail
    python scripts/check_results.py reports/junit.xml --expect-none # bugs off: nothing fails

Exit code 0 when the result is exactly as expected, 1 otherwise, so CI stays meaningful while the
platform keeps its intentional bugs.
"""

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TC_ID = re.compile(r"test_tc_(\d{3,})")
ROOT = Path(__file__).resolve().parent.parent


def failed_tests(junit: Path) -> set[str]:
    failed = set()
    for case in ET.parse(junit).getroot().iter("testcase"):
        if case.find("failure") is not None or case.find("error") is not None:
            match = TC_ID.search(case.get("name", ""))
            failed.add(f"TC-{match.group(1)}" if match else case.get("name", "?"))
    return failed


def expected_failures() -> dict[str, str]:
    lines = (ROOT / "expected-failures.txt").read_text().splitlines()
    return {line.split()[0]: line for line in lines if line.strip() and not line.startswith("#")}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("junit", type=Path)
    parser.add_argument("--expect-none", action="store_true", help="the platform runs without the bugs")
    args = parser.parse_args()

    if not args.junit.is_file():
        print(f"NO REPORT: {args.junit} does not exist, so the suite did not run (see the pytest step)")
        return 1
    expected = {} if args.expect_none else expected_failures()
    failed = failed_tests(args.junit)
    unexpected = sorted(failed - expected.keys())
    fixed = sorted(expected.keys() - failed)

    for test_id in sorted(failed & expected.keys()):
        print(f"expected failure: {expected[test_id]}")
    for test_id in unexpected:
        print(f"UNEXPECTED FAILURE: {test_id}")
    for test_id in fixed:
        print(f"EXPECTED TO FAIL BUT PASSED: {expected[test_id]}")
    if unexpected or fixed:
        return 1
    print(f"result as expected: {len(failed)} known failure(s), nothing else failed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
