"""
Odoo Studio legacy field cleanup script for Party-Time-Odoo
Removes unused x_studio_* fields from the database.
To be run as an Odoo shell script (odoo-bin shell -c odoo.conf -d <dbname> -i <module> --load=script)
"""

from odoo import api, SUPERUSER_ID

def cleanup_legacy_studio_fields(env):
    # List of legacy fields to remove
    legacy_fields = [
        ('x_services_requested', 'x_studio_sequence'),
        ('x_crm_lead_line_200d0', 'x_studio_sequence'),
    ]
    for model, field in legacy_fields:
        field_recs = env['ir.model.fields'].search([
            ('model', '=', model),
            ('name', '=', field)
        ])
        if field_recs:
            print(f"Removing {field} from {model}...")
            field_recs.unlink()
        else:
            print(f"Field {field} on {model} not found.")

if __name__ == "__main__":
    env = api.Environment(cr, SUPERUSER_ID, {})
    cleanup_legacy_studio_fields(env)
    print("Legacy Studio fields cleanup complete.")
