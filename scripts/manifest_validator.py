#!/usr/bin/env python3
"""
Manifest Validator Script

Validates that every module:
- Has installable: True
- Lists dependencies based on XML references

Usage:
    python scripts/manifest_validator.py
    # OR on server:
    odoo-bin shell < scripts/manifest_validator.py
"""

import re
import ast
from pathlib import Path

# For Odoo shell, use server path
# For local, use project path
import os
if os.path.exists('/home/odoo/src/user/addons'):
    # Running on server
    MODULE_ROOT = Path('/home/odoo/src/user/addons')
else:
    # Running locally
    MODULE_ROOT = Path(__file__).parent.parent / "addons"

# Match ref="module.id" pattern (external references)
# Only match if there's a dot separator (module.id format)
xmlid_pattern = re.compile(r"ref=['\"]([a-zA-Z0-9_]+)\.([a-zA-Z0-9_.]+)['\"]")

print("=" * 80)
print("MANIFEST VALIDATION")
print("=" * 80)

errors_found = 0

for module in sorted(MODULE_ROOT.iterdir()):
    if not module.is_dir():
        continue
    
    # Skip design-themes and odoo core
    if module.name in ['design-themes', 'odoo']:
        continue

    manifest = module / '__manifest__.py'
    print(f"\n[MODULE] {module.name}")

    if not manifest.exists():
        print("  [ERROR] No manifest file found!")
        errors_found += 1
        continue

    try:
        # Parse manifest as Python dict literal
        manifest_content = manifest.read_text(encoding='utf-8')
        # Use ast.literal_eval for safe parsing of dict literals
        context = ast.literal_eval(manifest_content)
    except SyntaxError:
        # If literal_eval fails, try exec with assignment
        try:
            context = {}
            exec(f"manifest_data = {manifest_content}", {}, context)
            context = context.get('manifest_data', {})
        except Exception as e:
            print(f"  [ERROR] Invalid manifest, error during parse: {e}")
            errors_found += 1
            continue
    except Exception as e:
        print(f"  [ERROR] Invalid manifest, error during parse: {e}")
        errors_found += 1
        continue

    # Check installable - handle both True and explicit True value
    installable = context.get('installable')
    if installable is None or installable is False:
        print("  [ERROR] installable is missing or false")
        errors_found += 1
    else:
        print(f"  [OK] installable = {installable}")

    # Grab declared depends - handle both list and None
    depends_list = context.get('depends', [])
    declared = set(depends_list) if depends_list else set()
    print(f"  Declared dependencies: {sorted(declared) if declared else 'None'}")

    # Find XML references
    xml_deps = set()
    views_dir = module / 'views'
    security_dir = module / 'security'
    
    xml_files = []
    if views_dir.exists():
        xml_files.extend(views_dir.glob('*.xml'))
    if security_dir.exists():
        xml_files.extend(security_dir.glob('*.xml'))
    
    for xmlfile in xml_files:
        try:
            text = xmlfile.read_text(encoding='utf-8')
            for match in xmlid_pattern.findall(text):
                prefix = match[0]  # First group is the module name
                if prefix != module.name and not prefix.startswith('/'):
                    # Only add known Odoo modules (filter out XML ID patterns)
                    # Common Odoo modules don't start with 'view_', 'model_', 'action_'
                    if not prefix.startswith(('view_', 'model_', 'action_', 'ir_')):
                        xml_deps.add(prefix)
        except Exception as e:
            print(f"  [WARN] Error reading {xmlfile.name}: {e}")

    if xml_deps:
        print(f"  XML references external modules: {sorted(xml_deps)}")
        missing = xml_deps - declared
        if missing:
            print(f"  [ERROR] Missing in manifest depends: {sorted(missing)}")
            errors_found += 1
        else:
            print("  [OK] All XML references present in depends")
    else:
        print("  [OK] No external XML references found")

print("\n" + "=" * 80)
if errors_found == 0:
    print("[SUCCESS] All manifests validated - no errors found!")
else:
    print(f"[ERROR] Found {errors_found} validation error(s)")
print("=" * 80)
