#!/usr/bin/env python3
"""
Module Dependency Audit Script

Examines all modules for view references that require dependencies
and produces a list of suggested dependencies.

Usage:
    python scripts/dependency_audit.py
    # OR on server:
    odoo-bin shell < scripts/dependency_audit.py
"""

import re
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
print("MODULE DEPENDENCY AUDIT")
print("=" * 80)

for module in sorted(MODULE_ROOT.iterdir()):
    if not module.is_dir():
        continue
    
    # Skip design-themes and odoo core
    if module.name in ['design-themes', 'odoo']:
        continue

    manifest = module / '__manifest__.py'
    if not manifest.exists():
        print(f"\n[SKIP] {module.name} (missing manifest)")
        continue

    print(f"\n[MODULE] {module.name}")

    # Collect all external module prefixes referenced in XML
    dependencies = set()

    # Scan XML files
    views_dir = module / 'views'
    security_dir = module / 'security'
    
    xml_files = []
    if views_dir.exists():
        xml_files.extend(views_dir.glob('*.xml'))
    if security_dir.exists():
        xml_files.extend(security_dir.glob('*.xml'))
    
    for xml in xml_files:
        try:
            text = xml.read_text(encoding='utf-8')
            for match in xmlid_pattern.findall(text):
                prefix = match[0]  # First group is the module name
                # Skip if it's the same module or a path
                if prefix != module.name and not prefix.startswith('/'):
                    # Only add known Odoo modules (filter out XML ID patterns)
                    # Common Odoo modules don't start with 'view_', 'model_', 'action_'
                    if not prefix.startswith(('view_', 'model_', 'action_', 'ir_')):
                        dependencies.add(prefix)
        except Exception as e:
            print(f"  [WARN] Error reading {xml.name}: {e}")

    if dependencies:
        print("  Referenced modules in XML:")
        for d in sorted(dependencies):
            print(f"    - {d}")
        print(f"  Suggested 'depends': {list(sorted(dependencies))}")
    else:
        print("  [OK] No external module dependencies detected in XML")

print("\n" + "=" * 80)
print("AUDIT COMPLETE")
print("=" * 80)
