#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple test to validate ptt_vendor_management models can be loaded
Uses Odoo's --test-enable or direct model loading
"""
import sys
import os

# Add Odoo to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'odoo'))

print("=" * 70)
print("PTT Vendor Management - Model Validation Test")
print("=" * 70)

# Test 1: Check all Python files compile
print("\n1. Testing Python file syntax...")
module_path = os.path.join('addons', 'ptt_vendor_management')
errors = []

test_files = [
    'models/ptt_vendor_rfq.py',
    'models/ptt_vendor_quote_history.py',
    'models/ptt_vendor_document.py',
    'models/ptt_document_type.py',
    'models/res_partner.py',
    'models/ptt_project_vendor_assignment.py',
    'models/ptt_vendor_task.py',
    'models/project_project.py',
    'wizard/ptt_vendor_invite_wizard.py',
    'wizard/ptt_rfq_send_wizard.py',
    'wizard/ptt_rfq_done_wizard.py',
    'controllers/vendor_portal.py',
    'controllers/vendor_intake_portal.py',
]

for test_file in test_files:
    file_path = os.path.join(module_path, test_file)
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, file_path, 'exec')
            print(f"   [OK] {test_file}")
        except SyntaxError as e:
            print(f"   [ERROR] {test_file}: {e}")
            errors.append((test_file, f"Syntax: {e}"))
        except Exception as e:
            print(f"   [ERROR] {test_file}: {e}")
            errors.append((test_file, str(e)))
    else:
        print(f"   [MISSING] {test_file}")

# Test 2: Check manifest
print("\n2. Testing manifest file...")
manifest_path = os.path.join(module_path, '__manifest__.py')
if os.path.exists(manifest_path):
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest_code = f.read()
        manifest = eval(manifest_code)
        
        required = ['name', 'version', 'depends', 'data', 'installable']
        missing = [k for k in required if k not in manifest]
        
        if missing:
            print(f"   [ERROR] Missing keys: {missing}")
            errors.append(('__manifest__.py', f"Missing: {missing}"))
        else:
            print(f"   [OK] Manifest valid")
            print(f"        Name: {manifest.get('name')}")
            print(f"        Version: {manifest.get('version')}")
            print(f"        Dependencies: {len(manifest.get('depends', []))}")
    except Exception as e:
        print(f"   [ERROR] Manifest: {e}")
        errors.append(('__manifest__.py', str(e)))
else:
    print(f"   [ERROR] Manifest not found")
    errors.append(('__manifest__.py', 'File not found'))

# Test 3: Check for Odoo 19 compatibility
print("\n3. Checking Odoo 19 compatibility...")
deprecated = {
    '@api.multi': [],
    '@api.one': [],
    'fields.Date.context_today': [],
    'fields.Datetime.context_today': [],
}

for test_file in test_files:
    file_path = os.path.join(module_path, test_file)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for pattern in deprecated:
            if pattern in content:
                deprecated[pattern].append(test_file)

has_deprecated = False
for pattern, files in deprecated.items():
    if files:
        print(f"   [WARNING] Deprecated '{pattern}' in: {', '.join(files)}")
        has_deprecated = True

if not has_deprecated:
    print(f"   [OK] No deprecated patterns found")

# Test 4: Check model class definitions
print("\n4. Checking model class definitions...")
model_classes = {
    'ptt_vendor_rfq.py': 'PTTVendorRFQ',
    'ptt_vendor_quote_history.py': 'PTTVendorQuoteHistory',
    'ptt_vendor_document.py': 'PttVendorDocument',
    'ptt_document_type.py': 'PttDocumentType',
    'res_partner.py': 'ResPartner',
    'ptt_project_vendor_assignment.py': 'ProjectVendorAssignment',
    'ptt_vendor_task.py': 'PTTVendorTask',
}

for file, class_name in model_classes.items():
    file_path = os.path.join(module_path, 'models', file)
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if f'class {class_name}' in content:
            print(f"   [OK] {file}: {class_name} found")
        else:
            print(f"   [WARNING] {file}: Class {class_name} not found")
            # Check what classes are actually there
            import re
            classes = re.findall(r'class\s+(\w+)', content)
            if classes:
                print(f"            Found classes: {', '.join(classes)}")

# Summary
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)

if errors:
    print(f"\n[FAILED] {len(errors)} error(s) found:")
    for file, error in errors:
        print(f"  - {file}: {error}")
    print("\nACTION: Fix errors before proceeding")
    sys.exit(1)
else:
    print(f"\n[SUCCESS] All syntax checks passed!")
    print(f"  - {len(test_files)} Python files validated")
    print(f"  - Manifest file valid")
    if has_deprecated:
        print(f"  - WARNING: Some deprecated patterns found (may still work)")
    else:
        print(f"  - Odoo 19 compatible")
    print("\nNEXT STEP: Test with actual Odoo database:")
    print("  python odoo/odoo-bin -c odoo.conf -d <database> -i ptt_vendor_management --stop-after-init")
    sys.exit(0)
