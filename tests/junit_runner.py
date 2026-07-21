"""Run the unittest suite and emit JUnit-style XML to test-results.xml.

Uses only the standard library. This produces the machine-readable test report
required by the submission without any third-party test runner.
"""

import sys
import time
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run():
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"))

    result = unittest.TestResult()
    start = time.time()
    suite.run(result)
    elapsed = time.time() - start

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)

    testsuite = ET.Element("testsuite", {
        "name": "recon-engine",
        "tests": str(total),
        "failures": str(failures),
        "errors": str(errors),
        "skipped": str(skipped),
        "time": f"{elapsed:.3f}",
    })

    # record each failure/error explicitly; passes are counted in the totals
    def add_case(name, kind, message):
        case = ET.SubElement(testsuite, "testcase", {"name": name})
        if kind:
            el = ET.SubElement(case, kind)
            el.text = message

    for test, tb in result.failures:
        add_case(str(test), "failure", tb)
    for test, tb in result.errors:
        add_case(str(test), "error", tb)

    tree = ET.ElementTree(testsuite)
    out = ROOT / "test-results.xml"
    tree.write(out, encoding="utf-8", xml_declaration=True)

    print(f"tests={total} failures={failures} errors={errors} skipped={skipped}")
    print(f"wrote {out}")
    return 0 if (failures == 0 and errors == 0) else 1


if __name__ == "__main__":
    sys.exit(run())
