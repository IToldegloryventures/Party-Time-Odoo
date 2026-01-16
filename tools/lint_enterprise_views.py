#!/usr/bin/env python3
"""
Static lint for Enterprise view contamination.

Blocks:
- Inheriting from Enterprise views (project_enterprise, sale_timesheet_enterprise)
- Referencing Enterprise-only fields (planned_hours, remaining_hours, etc.)

Usage:
    python tools/lint_enterprise_views.py addons/ptt_business_core/views
    python tools/lint_enterprise_views.py addons/
"""

import sys
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    print("ERROR: lxml not installed. Run: pip install lxml")
    sys.exit(2)

ENTERPRISE_XML_MARKERS = (
    "enterprise",
    "sale_timesheet_enterprise",
    "project_enterprise",
    "hr_timesheet",
    "sale_subscription",
    "planning",
)

ENTERPRISE_FIELDS = {
    "planned_hours",
    "timesheet_ids",
    "analytic_line_ids",
    "remaining_hours",
    "effective_hours",
    "total_hours_spent",
    "subtask_effective_hours",
    "progress",
    "overtime",
    "planning_slot_ids",
}

def lint(path: Path):
    failures = []

    for xml_file in path.rglob("*.xml"):
        try:
            root = etree.parse(str(xml_file))
        except Exception:
            continue

        for record in root.xpath("//record[@model='ir.ui.view']"):
            # Check inherit_id references
            inherit = record.xpath(".//field[@name='inherit_id']/@ref")
            for ref in inherit:
                if any(m in ref for m in ENTERPRISE_XML_MARKERS):
                    failures.append(
                        f"{xml_file}: inherits enterprise view '{ref}'"
                    )

            # Check field references in arch
            arch_fields = record.xpath(".//field[@name='arch']//field/@name")
            for fname in arch_fields:
                if fname in ENTERPRISE_FIELDS:
                    failures.append(
                        f"{xml_file}: references enterprise field '{fname}'"
                    )

    return failures


def main():
    if len(sys.argv) != 2:
        print("Usage: lint_enterprise_views.py <views_dir>")
        print("Example: python tools/lint_enterprise_views.py addons/")
        sys.exit(2)

    target = Path(sys.argv[1])
    if not target.exists():
        print(f"ERROR: Path not found: {target}")
        sys.exit(2)

    failures = lint(target)

    if failures:
        print("\n[ERROR] ENTERPRISE VIEW LINT FAILED\n")
        for f in failures:
            print(" -", f)
        sys.exit(1)

    print("[OK] Enterprise view lint passed - no enterprise contamination detected")


if __name__ == "__main__":
    main()
