#!/usr/bin/env python3
"""Find specific model/field errors"""
import sys
import os

odoo_dir = os.path.join(os.path.dirname(__file__), 'odoo')
sys.path.insert(0, odoo_dir)
os.chdir(odoo_dir)

import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

config.parse_config(['-c', r'C:\Users\ashpt\Party-Time-Odoo\odoo.conf'])

db_name = config['db_name']
if isinstance(db_name, list):
    db_name = db_name[0]

from odoo.orm.registry import Registry
registry = Registry(db_name)

print("="*70)
print("CHECKING FOR MODEL/FIELD ERRORS")
print("="*70)

errors_found = []

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get all models
    Model = env['ir.model']
    all_models = Model.search([])
    
    print(f"\nChecking {len(all_models)} models for errors...\n")
    
    for ir_model in all_models:
        model_name = ir_model.model
        try:
            model = env[model_name]
            # Try to access fields
            fields = model._fields
            # Try a simple search
            model.search([], limit=1)
        except Exception as e:
            error_msg = str(e)
            errors_found.append({
                'model': model_name,
                'error': error_msg
            })
            print(f"[ERROR] Model: {model_name}")
            print(f"        Error: {error_msg}\n")
    
    # Check for field errors in custom modules
    print("\n" + "="*70)
    print("CHECKING CUSTOM MODULE MODELS")
    print("="*70 + "\n")
    
    custom_models_to_check = [
        'ptt.vendor',
        'ptt.vendor.contact', 
        'ptt.event',
        'ptt.event.vendor',
        'ptt.operational.metric',
    ]
    
    for model_name in custom_models_to_check:
        try:
            model = env[model_name]
            fields = model._fields
            print(f"[OK] {model_name}: {len(fields)} fields")
            # Check for problematic fields
            for field_name, field in fields.items():
                if hasattr(field, 'comodel_name') and field.comodel_name:
                    try:
                        # Check if related model exists
                        related_model = env[field.comodel_name]
                    except KeyError:
                        errors_found.append({
                            'model': model_name,
                            'field': field_name,
                            'error': f"Related model '{field.comodel_name}' does not exist"
                        })
                        print(f"  [ERROR] Field '{field_name}': Related model '{field.comodel_name}' not found")
        except KeyError:
            print(f"[INFO] {model_name}: Not found (may not be installed)")
        except Exception as e:
            errors_found.append({
                'model': model_name,
                'error': str(e)
            })
            print(f"[ERROR] {model_name}: {e}\n")

print("\n" + "="*70)
print("SUMMARY")
print("="*70)

if errors_found:
    print(f"\nFound {len(errors_found)} error(s):\n")
    for i, err in enumerate(errors_found, 1):
        print(f"{i}. Model: {err['model']}")
        if 'field' in err:
            print(f"   Field: {err['field']}")
        print(f"   Error: {err['error']}\n")
else:
    print("\nNo model/field errors found!")
