"""
Run all PTT cleanup scripts in the correct order.

Usage:
    odoo-bin shell -c odoo.conf -d <dbname> --load=script scripts/run_ptt_cleanup.py

Sequence:
1) Audit orphan fields/models.
2) Drop legacy Studio columns.
3) Remove orphan vendor service fields.
4) Remove deprecated event timing columns.
"""

import os
import sys

from odoo import api, SUPERUSER_ID

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.append(SCRIPT_DIR)

from cleanup_legacy_studio_fields import cleanup_legacy_studio_fields
from cleanup_orphan_service_fields import cleanup_orphan_service_fields
from ptt_orphan_audit import audit_orphan_fields, audit_orphan_models
from remove_deprecated_event_fields import remove_deprecated_event_fields


def run_cleanup(env):
    """Execute each cleanup step in order."""
    print("[1/4] Auditing orphan PTT fields/models...")
    audit_orphan_fields(env)
    audit_orphan_models(env)

    print("[2/4] Dropping legacy Studio columns...")
    cleanup_legacy_studio_fields(env)

    print("[3/4] Removing orphan vendor service fields...")
    cleanup_orphan_service_fields(env.cr, None)

    print("[4/4] Removing deprecated event timing fields...")
    remove_deprecated_event_fields(env)

    print("PTT cleanup sequence complete.")


if __name__ == "__main__":
    env = api.Environment(cr, SUPERUSER_ID, {})
    run_cleanup(env)
