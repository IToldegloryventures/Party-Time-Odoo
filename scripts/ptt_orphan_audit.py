"""
PTT Custom Field/Model Orphan Audit Script
- Lists all ptt_* fields in the DB not defined in any Python model file
- Lists all ptt_* models not referenced in any view, action, or menu
- Optionally removes or archives orphans (manual review recommended before deletion)

Usage: odoo-bin shell -c odoo.conf -d <dbname> -i <module> --load=script
"""

import os
from odoo import api, SUPERUSER_ID

def get_code_fields():
    code_fields = set()
    for root, _, files in os.walk('addons'):
        for file in files:
            if file.endswith('.py'):
                with open(os.path.join(root, file), encoding='utf-8') as f:
                    for line in f:
                        if 'ptt_' in line and 'fields.' in line:
                            parts = line.strip().split('=')
                            if parts:
                                name = parts[0].strip()
                                if name.startswith('ptt_'):
                                    code_fields.add(name)
    return code_fields

def audit_orphan_fields(env):
    db_fields = env['ir.model.fields'].search([('name', 'like', 'ptt_%')])
    code_fields = get_code_fields()
    orphans = []
    for f in db_fields:
        if f.name not in code_fields:
            orphans.append((f.model, f.name))
    print('Orphan DB fields (not in code):')
    for o in orphans:
        print(o)
    return orphans

def audit_orphan_models(env):
    db_models = env['ir.model'].search([('model', 'like', 'ptt_%')])
    used_models = set()
    # Check for model usage in views, actions, menus
    for root, _, files in os.walk('addons'):
        for file in files:
            if file.endswith('.xml'):
                with open(os.path.join(root, file), encoding='utf-8') as f:
                    content = f.read()
                    for m in db_models:
                        if m.model in content:
                            used_models.add(m.model)
    orphans = [m.model for m in db_models if m.model not in used_models]
    print('Orphan models (not in any view/action/menu):')
    for o in orphans:
        print(o)
    return orphans

def remove_orphan_fields(env, orphans):
    for model, field in orphans:
        recs = env['ir.model.fields'].search([('model', '=', model), ('name', '=', field)])
        if recs:
            print(f"Removing orphan field {field} from {model}")
            recs.unlink()

def remove_orphan_models(env, orphans):
    for model in orphans:
        recs = env['ir.model'].search([('model', '=', model)])
        if recs:
            print(f"Removing orphan model {model}")
            recs.unlink()

if __name__ == "__main__":
    env = api.Environment(cr, SUPERUSER_ID, {})
    orphan_fields = audit_orphan_fields(env)
    orphan_models = audit_orphan_models(env)
    # Uncomment to remove orphans automatically (manual review recommended first)
    # remove_orphan_fields(env, orphan_fields)
    # remove_orphan_models(env, orphan_models)
    print("PTT orphan audit complete.")
