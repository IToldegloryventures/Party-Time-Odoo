#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test ptt_vendor_management models against local Odoo database
Uses Odoo's proper initialization
"""
import sys
import os

# Add Odoo to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'odoo'))

import odoo
from odoo import api
from odoo.modules.registry import Registry
from odoo.tools import config

print("=" * 70)
print("PTT Vendor Management - Database Model Validation")
print("=" * 70)

# Load config
config_file = os.path.join(os.path.dirname(__file__), 'odoo.conf')
if os.path.exists(config_file):
    odoo.tools.config.parse_config(['-c', config_file])
else:
    print(f"ERROR: Config file not found: {config_file}")
    sys.exit(1)

# Get database name
db_name = config.get('db_name')
if not db_name:
    # Try to find a database
    import psycopg2
    try:
        conn = psycopg2.connect(
            host=config.get('db_host', 'localhost'),
            port=config.get('db_port', 5432),
            user=config.get('db_user', 'odoo'),
            password=config.get('db_password', ''),
            database='postgres'
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT datname FROM pg_database 
            WHERE datistemplate = false 
            AND datname NOT IN ('postgres', 'template0', 'template1')
            ORDER BY datname LIMIT 5;
        """)
        dbs = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        
        if dbs:
            print(f"\nAvailable databases: {', '.join(dbs)}")
            db_name = dbs[0]
            print(f"Using first database: {db_name}")
        else:
            print("\nERROR: No databases found. Please create a database first.")
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR: Could not connect to PostgreSQL: {e}")
        print("Please ensure PostgreSQL is running and credentials are correct")
        sys.exit(1)

print(f"\nDatabase: {db_name}")

# Initialize registry
print("\n1. Initializing Odoo registry...")
try:
    registry = Registry(db_name)
    print(f"   [OK] Registry initialized")
except Exception as e:
    print(f"   [ERROR] Failed to initialize registry: {e}")
    print(f"   NOTE: Database may need to be initialized with Odoo first")
    print(f"   Run: python odoo/odoo-bin -c odoo.conf -d {db_name} --init base --stop-after-init")
    sys.exit(1)

# Test models
print("\n2. Testing model availability...")
module_name = 'ptt_vendor_management'
models_to_test = [
    'ptt.vendor.rfq',
    'ptt.vendor.quote.history',
    'ptt.vendor.document',
    'ptt.document.type',
    'ptt.vendor.task',
    'ptt.project.vendor.assignment',
    'ptt.vendor.invite.wizard',
    'ptt.rfq.send.wizard',
    'ptt.rfq.done.wizard',
]

model_results = {}
with registry.cursor() as cr:
    env = api.Environment(cr, 1, {})  # Use admin user (ID 1)
    
    # Check if module is installed
    module_obj = env['ir.module.module']
    module = module_obj.search([('name', '=', module_name)], limit=1)
    
    if module:
        print(f"\n   Module '{module_name}' status: {module.state}")
        if module.state != 'installed':
            print(f"   [WARNING] Module is not installed. Models may not be available.")
    else:
        print(f"\n   [INFO] Module '{module_name}' not found in database")
        print(f"   [INFO] Install module to test models: python odoo/odoo-bin -c odoo.conf -d {db_name} -i {module_name} --stop-after-init")
    
    # Test each model
    for model_name in models_to_test:
        try:
            model = env.get(model_name)
            if model is None:
                model_results[model_name] = "NOT_FOUND"
                print(f"   [ERROR] {model_name}: Model not found in registry")
            else:
                # Verify it's the right model
                if hasattr(model, '_name') and model._name == model_name:
                    # Try a simple search to verify it works
                    try:
                        count = model.search_count([])
                        model_results[model_name] = "OK"
                        print(f"   [OK] {model_name} (records: {count})")
                    except Exception as e:
                        model_results[model_name] = f"SEARCH_ERROR: {e}"
                        print(f"   [WARNING] {model_name}: Model found but search failed - {e}")
                else:
                    model_results[model_name] = "NAME_MISMATCH"
                    print(f"   [WARNING] {model_name}: Name mismatch (got {model._name if hasattr(model, '_name') else 'unknown'})")
        except Exception as e:
            model_results[model_name] = f"ERROR: {e}"
            print(f"   [ERROR] {model_name}: {e}")

# Check dependencies
print("\n3. Checking dependencies...")
manifest_path = os.path.join('addons', module_name, '__manifest__.py')
if os.path.exists(manifest_path):
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = eval(f.read())
    
    dependencies = manifest.get('depends', [])
    missing_deps = []
    
    with registry.cursor() as cr:
        env = api.Environment(cr, 1, {})
        module_obj = env['ir.module.module']
        
        for dep in dependencies:
            dep_module = module_obj.search([
                ('name', '=', dep),
                ('state', '=', 'installed')
            ], limit=1)
            
            if not dep_module:
                missing_deps.append(dep)
                print(f"   [MISSING] {dep}")
            else:
                print(f"   [OK] {dep}")

# Summary
print("\n" + "=" * 70)
print("VALIDATION SUMMARY")
print("=" * 70)

ok_models = [m for m, r in model_results.items() if r == "OK"]
error_models = [m for m, r in model_results.items() if r != "OK"]

if ok_models:
    print(f"\n[SUCCESS] {len(ok_models)} model(s) validated:")
    for m in ok_models:
        print(f"  + {m}")

if error_models:
    print(f"\n[ISSUES] {len(error_models)} model(s) with issues:")
    for m in error_models:
        print(f"  - {m}: {model_results[m]}")

if missing_deps:
    print(f"\n[MISSING DEPENDENCIES] {len(missing_deps)}:")
    for dep in missing_deps:
        print(f"  - {dep}")
    print("\n  Install missing dependencies first, then install ptt_vendor_management")

if not module or module.state != 'installed':
    print(f"\n[ACTION REQUIRED]")
    print(f"  To test models, install the module:")
    print(f"  python odoo/odoo-bin -c odoo.conf -d {db_name} -i {module_name} --stop-after-init")
    print(f"\n  Or upgrade if already installed:")
    print(f"  python odoo/odoo-bin -c odoo.conf -d {db_name} -u {module_name} --stop-after-init")

if len(ok_models) == len(models_to_test) and not missing_deps:
    print(f"\n[READY] All models are validated and ready!")
    sys.exit(0)
elif len(ok_models) > 0:
    print(f"\n[PARTIAL] Some models validated. Fix issues above for full validation.")
    sys.exit(0)
else:
    print(f"\n[NOT READY] Models need to be installed/upgraded first.")
    sys.exit(1)
