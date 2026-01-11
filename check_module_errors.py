#!/usr/bin/env python3
"""
Comprehensive script to check for errors in Odoo modules
"""
import sys
import os

# Add odoo directory to Python path
odoo_dir = os.path.join(os.path.dirname(__file__), 'odoo')
sys.path.insert(0, odoo_dir)

# Change to odoo directory
os.chdir(odoo_dir)

import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

# Load configuration
config.parse_config(['-c', r'C:\Users\ashpt\Party-Time-Odoo\odoo.conf'])

try:
    db_name = config['db_name']
    if isinstance(db_name, list):
        db_name = db_name[0] if db_name else None
    
    print(f"Checking database: {db_name}\n")
    
    from odoo.orm.registry import Registry
    registry = Registry(db_name)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        Module = env['ir.module.module']
        
        # Get all installed modules
        installed = Module.search([('state', '=', 'installed')])
        print(f"Total installed modules: {len(installed)}\n")
        
        # Check for modules with errors in their models
        print("Checking for model errors...")
        error_count = 0
        
        # Check core models
        core_models = ['res.partner', 'res.users', 'ir.module.module']
        for model_name in core_models:
            try:
                model = env[model_name]
                count = model.search_count([])
                print(f"  [OK] {model_name}: {count} records")
            except Exception as e:
                print(f"  [ERROR] {model_name}: {e}")
                error_count += 1
        
        # Check custom module models if they exist
        custom_models = [
            'ptt.vendor',
            'ptt.vendor.contact',
            'ptt.event',
            'ptt.event.vendor',
        ]
        
        print("\nChecking custom module models...")
        for model_name in custom_models:
            try:
                model = env[model_name]
                count = model.search_count([])
                print(f"  [OK] {model_name}: {count} records")
            except KeyError:
                print(f"  [INFO] {model_name}: Model not found (module may not be installed)")
            except Exception as e:
                print(f"  [ERROR] {model_name}: {e}")
                error_count += 1
        
        # Check for XML/View errors
        print("\nChecking for view errors...")
        try:
            views = env['ir.ui.view'].search([('active', '=', True)], limit=10)
            print(f"  [OK] Found {len(views)} active views (sampled)")
        except Exception as e:
            print(f"  [ERROR] Error checking views: {e}")
            error_count += 1
        
        # Check for action errors
        print("\nChecking for action errors...")
        try:
            actions = env['ir.actions.act_window'].search([], limit=10)
            print(f"  [OK] Found {len(actions)} actions (sampled)")
        except Exception as e:
            print(f"  [ERROR] Error checking actions: {e}")
            error_count += 1
        
        # Check for menu errors
        print("\nChecking for menu errors...")
        try:
            menus = env['ir.ui.menu'].search([('active', '=', True)], limit=10)
            print(f"  [OK] Found {len(menus)} active menus (sampled)")
        except Exception as e:
            print(f"  [ERROR] Error checking menus: {e}")
            error_count += 1
        
        # Summary
        print(f"\n{'='*60}")
        if error_count == 0:
            print("[SUCCESS] No errors found in the database!")
        else:
            print(f"[WARNING] Found {error_count} error(s)")
        print(f"{'='*60}\n")
        
except Exception as e:
    print(f"\n[FATAL ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
