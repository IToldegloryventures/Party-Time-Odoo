"""
Script to remove the deprecated event timing columns from the database.

Usage:
    odoo-bin shell -c odoo.conf -d <db> --load=script scripts/remove_deprecated_event_fields.py

This mirrors migration 19.0.4.4.4: it drops the `ptt_event_time` and
`ptt_event_duration` columns from `project.project` and purges the related
`ir.model.fields` / `ir.model.data` entries so staging/live installs stay
consistent.
"""

from odoo import api, SUPERUSER_ID

DEPRECATED_FIELDS = [
    ("project.project", "ptt_event_time"),
    ("project.project", "ptt_event_duration"),
]


def remove_deprecated_event_fields(env):
    """Drop deprecated columns and clear their metadata."""
    cr = env.cr

    for _model_name, field_name in DEPRECATED_FIELDS:
        cr.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'project_project'
              AND column_name = %s
            """,
            (field_name,),
        )
        if not cr.fetchone():
            print(f"Column {field_name} already absent, skipping")
            continue

        cr.execute(f"SELECT COUNT(*) FROM project_project WHERE {field_name} IS NOT NULL")
        row = cr.fetchone()
        populated = row[0] if row else 0
        if populated:
            print(f"Column {field_name} still had {populated} populated rows; values will be dropped")

        cr.execute(f"ALTER TABLE project_project DROP COLUMN IF EXISTS {field_name}")
        print(f"Dropped column {field_name}")

    field_names = [field for _, field in DEPRECATED_FIELDS]

    field_recs = env["ir.model.fields"].search(
        [("model", "=", "project.project"), ("name", "in", field_names)]
    )
    if field_recs:
        print(f"Removing {len(field_recs)} ir.model.fields records for deprecated fields")
        field_recs.unlink()

    data_recs = env["ir.model.data"].search(
        [
            ("module", "=", "ptt_business_core"),
            ("model", "=", "ir.model.fields"),
            ("name", "in", field_names),
        ]
    )
    if data_recs:
        print(f"Removing {len(data_recs)} ir.model.data records for deprecated fields")
        data_recs.unlink()


if __name__ == "__main__":
    env = api.Environment(cr, SUPERUSER_ID, {})
    remove_deprecated_event_fields(env)
    print("Deprecated event fields cleanup complete.")
