"""
Audit custom (ptt_* / x_*) fields for data usage.

Run inside Odoo shell:
    odoo-bin shell < tools/ptt_field_audit.py

Outputs a CSV to /tmp/ptt_field_audit.csv with:
model,field,records_with_value,total_records
and prints a sorted table to stdout.
"""
import csv
import os

FIELD_PREFIXES = ("ptt_", "x_")

out_path = "/tmp/ptt_field_audit.csv"

fields_model = env["ir.model.fields"].sudo()

custom_fields = fields_model.search([
    ("name", "ilike", f"{FIELD_PREFIXES[0]}%"),
])
# include x_
custom_fields |= fields_model.search([
    ("name", "ilike", f"{FIELD_PREFIXES[1]}%"),
])

rows = []

for f in custom_fields:
    model_name = f.model
    field_name = f.name
    try:
        model = env[model_name].sudo()
    except KeyError:
        continue  # model missing
    # Count non-null values; use search_count to avoid loading records
    try:
        non_null = model.search_count([(field_name, "!=", False)])
        total = model.search_count([])
    except Exception:
        # field might be related/compute without storage
        non_null = -1
        total = model.search_count([])
    rows.append((model_name, field_name, non_null, total))

# Write CSV
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", newline="", encoding="utf-8") as fcsv:
    writer = csv.writer(fcsv)
    writer.writerow(["model", "field", "records_with_value", "total_records"])
    for r in sorted(rows):
        writer.writerow(r)

# Print a quick table (sorted by records_with_value asc)
rows_sorted = sorted(rows, key=lambda r: (r[2], r[0], r[1]))
print("model.field | records_with_value / total")
print("----------------------------------------")
for model_name, field_name, non_null, total in rows_sorted:
    print(f"{model_name}.{field_name}: {non_null} / {total}")

print(f"\nCSV written to {out_path}")
