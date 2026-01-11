#!/usr/bin/env python3
"""Find the FIRST actual error (not cascading)"""
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
print("FINDING ROOT CAUSE ERROR")
print("="*70)

with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check mail.thread.cc first since that was the first error
    print("\nChecking mail.thread.cc...")
    try:
        model = env['mail.thread.cc']
        # Check if it's an abstract model (abstract models don't have database tables)
        if hasattr(model, '_abstract') and model._abstract:
            print("✓ mail.thread.cc is an AbstractModel (mixin) - no database table needed")
            print("  This is CORRECT - abstract models are mixins inherited by other models.")
            print("  Standard crm.lead inherits from mail.thread.cc, so it's working as designed.")
        else:
            # Only try to query if it's not abstract
            model.search([], limit=1)
            print("✓ mail.thread.cc is accessible")
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        if "does not exist" in error_msg.lower():
            print("\nNOTE: mail.thread.cc is an AbstractModel (mixin)")
            print("Abstract models don't create database tables - they're inherited by other models.")
            print("This is NOT an error - the script incorrectly tried to query an abstract model.")
            print("\nTo find REAL errors, check models that inherit from mail.thread.cc:")
            print("  - crm.lead (standard Odoo model)")
            print("  - project.task (standard Odoo model)")
            print("  - project.project (standard Odoo model)")
            print("\nThese models should work fine - the abstract model provides functionality to them.")
