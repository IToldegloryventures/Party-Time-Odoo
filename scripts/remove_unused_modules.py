#!/usr/bin/env python3
"""
Remove Unused Modules Script

Helps identify and remove modules that are not needed for functional build.
"""

# Odoo Shell Script to Remove Unused Modules
REMOVE_UNUSED_SCRIPT = """
# Remove unused/duplicate modules
import shutil
from pathlib import Path

MODULE_ROOT = Path('/home/odoo/src/user/addons')

# Modules to remove (all duplicates already cleaned up)
MODULES_TO_REMOVE = [
    # 'ptt_justcall',  # Uncomment if not using JustCall
]

print("=" * 80)
print("Removing Unused Modules")
print("=" * 80)

for module_name in MODULES_TO_REMOVE:
    module_path = MODULE_ROOT / module_name
    
    if not module_path.exists():
        print(f"\\n⚠️  {module_name}: Already removed")
        continue
    
    try:
        print(f"\\n🗑️  Removing {module_name}...")
        
        # Option 1: Remove from filesystem (keeps in database for now)
        # shutil.rmtree(module_path)
        # print(f"  ✅ Removed from filesystem")
        
        # Option 2: Just unlink from database (safer)
        mod = env['ir.module.module'].search([('name', '=', module_name)], limit=1)
        if mod:
            mod.unlink()
            print(f"  ✅ Removed from database")
        else:
            print(f"  ⚠️  Not found in database")
            
    except Exception as e:
        print(f"  ❌ Error removing {module_name}: {e}")

print("\\n" + "=" * 80)
print("Done!")
print("=" * 80)
"""

if __name__ == '__main__':
    print(REMOVE_UNUSED_SCRIPT)
