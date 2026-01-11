#!/usr/bin/env python3
"""
Script to check for errors in Odoo modules using the shell
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

# Initialize Odoo
odoo.tools.config.parse_config(['-c', r'C:\Users\ashpt\Party-Time-Odoo\odoo.conf'])

try:
    # Try to initialize the registry
    db_name = config['db_name']
    if isinstance(db_name, list):
        db_name = db_name[0] if db_name else None
    print(f"Checking database: {db_name}")
    
    from odoo.orm.registry import Registry
    registry = Registry(db_name)
    
    print("[OK] Registry initialized successfully")
    
    # Check for module errors
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        
        # Check for modules with errors
        Module = env['ir.module.module']
        error_modules = Module.search([
            ('state', 'in', ['to install', 'to upgrade', 'to remove']),
        ])
        
        if error_modules:
            print(f"\n[WARNING] Found {len(error_modules)} modules in pending state:")
            for mod in error_modules:
                print(f"  - {mod.name}: {mod.state}")
        else:
            print("[OK] No modules in error state")
        
        # Check for installed modules
        installed = Module.search([('state', '=', 'installed')])
        print(f"[OK] Found {len(installed)} installed modules")
        
        # Try to access some key models
        try:
            partners = env['res.partner'].search([], limit=1)
            print(f"[OK] Can access res.partner model ({len(partners)} records found)")
        except Exception as e:
            print(f"[ERROR] Error accessing res.partner: {e}")
        
        # Check custom modules
        custom_modules = ['ptt_business_core', 'ptt_operational_dashboard', 'ptt_vendor_management', 'ptt_contact_forms']
        print("\nChecking custom modules:")
        for mod_name in custom_modules:
            mod = Module.search([('name', '=', mod_name)], limit=1)
            if mod:
                print(f"  - {mod_name}: {mod.state}")
                if mod.state == 'installed':
                    try:
                        # Try to load the module through Odoo's module system
                        from odoo.modules.module import load_openerp_module
                        load_openerp_module(mod_name)
                        print(f"    [OK] Module loads successfully")
                    except Exception as e:
                        print(f"    [ERROR] Load error: {e}")
                        import traceback
                        traceback.print_exc()
            else:
                print(f"  - {mod_name}: not found")
    
    print("\n[OK] All checks completed successfully!")
    
except Exception as e:
    print(f"\n[ERROR] Error during check: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
