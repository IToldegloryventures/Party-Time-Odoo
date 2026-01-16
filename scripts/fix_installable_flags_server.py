#!/usr/bin/env python3
"""
Fix installable flags on Odoo.sh server

This script fixes manifest files on the server to set installable=True
for all PTT modules.

Run this in Odoo shell on the server:
    exec(open('/tmp/fix_installable.py').read())
"""

# Odoo Shell Script to Fix installable Flags
FIX_INSTALLABLE_SCRIPT = """
# Fix installable flags in manifest files on server
import ast
from pathlib import Path

MODULE_ROOT = Path('/home/odoo/src/user/addons')
MODULES_TO_FIX = [
    'ptt_business_core',
    'ptt_operational_dashboard',
    'ptt_vendor_management',
    'ptt_justcall',
]

print("=" * 80)
print("Fixing installable flags in manifest files")
print("=" * 80)

for module_name in MODULES_TO_FIX:
    module_path = MODULE_ROOT / module_name
    manifest_path = module_path / '__manifest__.py'
    
    if not manifest_path.exists():
        print(f"\\n❌ {module_name}: Manifest file not found")
        continue
    
    try:
        # Read current manifest
        content = manifest_path.read_text()
        
        # Check if installable is already True
        context = {}
        exec(content, {}, context)
        current_installable = context.get('installable')
        
        if current_installable is True:
            print(f"\\n✅ {module_name}: Already installable=True")
            continue
        
        # Fix installable flag
        print(f"\\n🔧 Fixing {module_name}...")
        
        # Method 1: Simple string replacement (safest)
        if "'installable':" in content or '"installable":' in content:
            # Replace existing installable
            import re
            content = re.sub(
                r"['\"]installable['\"]\s*:\s*(False|None|0|'')",
                "'installable': True",
                content
            )
            # Also handle if it's missing
            if "'installable': True" not in content and '"installable": True' not in content:
                # Add before closing brace
                if content.strip().endswith('}'):
                    content = content.rstrip()[:-1] + "    'installable': True,\n}"
        else:
            # Add installable if missing
            if content.strip().endswith('}'):
                content = content.rstrip()[:-1] + "    'installable': True,\n}"
        
        # Write back
        manifest_path.write_text(content)
        print(f"  ✅ Fixed: Set installable=True")
        
        # Verify
        context = {}
        exec(content, {}, context)
        if context.get('installable') is True:
            print(f"  ✅ Verified: installable=True")
        else:
            print(f"  ⚠️  Warning: Still not True after fix")
            
    except Exception as e:
        print(f"\\n❌ {module_name}: Error fixing manifest: {e}")

print("\\n" + "=" * 80)
print("Done! Now run: env['ir.module.module'].update_list()")
print("=" * 80)
"""

# Alternative: Fix via database (if manifest files are correct but DB is wrong)
FIX_DATABASE_SCRIPT = """
# Fix installable flags in database
modules = env['ir.module.module'].search([('name', 'like', 'ptt_%')])

print("=" * 80)
print("Fixing installable flags in database")
print("=" * 80)

for mod in modules:
    print(f"\\nModule: {mod.name}")
    print(f"  Current state: {mod.state}")
    
    # Update module list to refresh from manifest
    env['ir.module.module'].update_list()
    
    # Re-search to get updated module
    mod = env['ir.module.module'].search([('name', '=', mod.name)], limit=1)
    if mod:
        print(f"  After update_list: state={mod.state}")
        if mod.state == 'uninstalled':
            print(f"  ✅ Module is now installable")
        else:
            print(f"  ⚠️  Module state: {mod.state}")

print("\\n" + "=" * 80)
print("Done!")
print("=" * 80)
"""

if __name__ == '__main__':
    print("=" * 80)
    print("Fix installable Flags - Server Script")
    print("=" * 80)
    print()
    print("Copy this script to server and run in Odoo shell:")
    print()
    print(FIX_INSTALLABLE_SCRIPT)
