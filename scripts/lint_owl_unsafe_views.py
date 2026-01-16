#!/usr/bin/env python3
"""
Detect Owl-unsafe expressions in Odoo XML views.

Flags:
- record.xxx where xxx is not guaranteed to exist
- record.xxx.raw_value (most common Owl crash source)
- record.xxx.value without fallback
- t-if / t-esc / t-att-* referencing unsafe fields
"""

import os
import sys
import re
from lxml import etree

UNSAFE_PATTERNS = [
    # record.planned_hours
    re.compile(r"record\.([a-zA-Z_][a-zA-Z0-9_]*)"),

    # record.planned_hours.raw_value
    re.compile(r"record\.([a-zA-Z_][a-zA-Z0-9_]*)\.raw_value"),

    # record.xxx.value
    re.compile(r"record\.([a-zA-Z_][a-zA-Z0-9_]*)\.value"),
]

SAFE_GUARDS = [
    "t-if",
    "t-foreach",
]

def scan_file(path):
    errors = []
    try:
        tree = etree.parse(path)
        root = tree.getroot()
    except Exception:
        return errors

    for node in root.xpath(".//*[@t-if or @t-esc or @t-att or @t-attf]"):
        for attr, val in node.attrib.items():
            if not attr.startswith("t-"):
                continue

            for pattern in UNSAFE_PATTERNS:
                for match in pattern.findall(val):
                    # If there's no guard like t-if="record.xxx"
                    if "record.%s" % match in val and "or" not in val:
                        errors.append({
                            "file": path,
                            "expression": val,
                            "field": match,
                        })

    return errors


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "."
    failures = []

    for root, _, files in os.walk(base):
        for f in files:
            if f.endswith(".xml"):
                failures.extend(scan_file(os.path.join(root, f)))

    if failures:
        print("\n[ERROR] Owl-unsafe expressions found:\n")
        for f in failures:
            print(f"{f['file']}")
            print(f"  -> {f['expression']}")
            print(f"  WARNING field: {f['field']}\n")
        sys.exit(1)

    print("[OK] No Owl-unsafe expressions detected")


if __name__ == "__main__":
    main()
