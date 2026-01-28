"""
Full field audit for an Odoo DB.

Run inside Odoo shell:
    odoo-bin shell < tools/full_field_audit.py

Outputs:
- /tmp/field_audit_all.csv : all fields on all models with non-null counts
- /tmp/field_audit_ptt.csv : only fields whose name starts with ptt_ or x_

Columns: model, field, ttype, store, related, modules, records_with_value, total_records

Note: Counting every field can take a few minutes on large DBs. It uses
search_count with a simple domain (field != False) per field; related/non-stored
fields will return -1 for records_with_value.
"""
import csv
import os

OUT_ALL = "/tmp/field_audit_all.csv"
OUT_CUSTOM = "/tmp/field_audit_ptt.csv"
PREFIXES = ("ptt_", "x_")

fields_model = env["ir.model.fields"].sudo()

all_fields = fields_model.search([])

def audit(fields, out_path):
    rows = []
    for f in fields:
        model_name = f.model
        field_name = f.name
        ttype = f.ttype
        store = f.store
        related = f.related or ""
        modules = ",".join(f.modules or [])
        try:
            model = env[model_name].sudo()
        except KeyError:
            non_null = -1
            total = 0
        else:
            try:
                non_null = model.search_count([(field_name, "!=", False)])
            except Exception:
                non_null = -1  # non-stored/related or domain issue
            try:
                total = model.search_count([])
            except Exception:
                total = -1
        rows.append((model_name, field_name, ttype, store, related, modules, non_null, total))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(["model", "field", "ttype", "store", "related", "modules", "records_with_value", "total_records"])
        for r in sorted(rows):
            writer.writerow(r)
    return rows

# All fields
audit(all_fields, OUT_ALL)

# Custom prefixes
custom_fields = all_fields.filtered(lambda f: f.name.startswith(PREFIXES))
audit(custom_fields, OUT_CUSTOM)

print(f"Wrote: {OUT_ALL} (all fields)")
print(f"Wrote: {OUT_CUSTOM} (ptt_/x_ fields)")
