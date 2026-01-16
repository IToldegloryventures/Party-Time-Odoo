#!/usr/bin/env python3
"""
Fix Broken Module Registrations

This script helps fix modules stuck in "to install" state by:
1. Cleaning broken module registrations from database
2. Verifying manifest files exist and are correct
3. Re-registering modules properly

Usage:
    python scripts/fix_module_registrations.py

Or run in Odoo shell:
    exec(open('scripts/fix_module_registrations.py').read())
"""

# Odoo Shell Commands to Fix Module Registrations
# =================================================

FIX_COMMANDS = """
# Step 1: Check current module states
modules = ['ptt_business_core', 'ptt_operational_dashboard', 'ptt_vendor_management', 'ptt_justcall']
for mod in modules:
    m = env['ir.module.module'].search([('name', '=', mod)], limit=1)
    if m:
        print(f"{mod}: state={m.state}, installable={m.installable}")

# Step 2: Clean broken registrations (if manifest not found)
# Only unlink if you're sure the module structure is correct
broken_modules = ['ptt_justcall']
for mod_name in broken_modules:
    mod = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)
    if mod and mod.state == 'to install':
        print(f"Found broken registration for {mod_name}")
        # Uncomment to clean:
        # mod.unlink()
        # print(f"Cleaned {mod_name}")

# Step 3: Update module list (re-scan addons)
env['ir.module.module'].update_list()

# Step 4: Verify modules are now found
for mod in modules:
    m = env['ir.module.module'].search([('name', '=', mod)], limit=1)
    if m:
        print(f"{mod}: state={m.state}, installable={m.installable}")
    else:
        print(f"{mod}: NOT FOUND - check folder structure")

# Step 5: Install modules
for mod_name in ['ptt_justcall']:
    mod = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)
    if mod and mod.state == 'to install':
        mod.button_install()
        print(f"Triggered install for {mod_name}")
"""

# Safe Odoo Shell Script
SAFE_FIX_SCRIPT = """
# Safe Module Registration Fix
# Run this in Odoo shell (odoo-bin shell)

modules_to_fix = ['ptt_justcall']

# 1. Check current state
print("=== Current Module States ===")
for mod_name in modules_to_fix:
    mod = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)
    if mod:
        print(f"{mod_name}: state={mod.state}, installable={mod.installable}")
    else:
        print(f"{mod_name}: NOT FOUND in database")

# 2. Update module list (re-scan addons path)
print("\\n=== Updating Module List ===")
env['ir.module.module'].update_list()
print("Module list updated")

# 3. Check again after update
print("\\n=== After Update List ===")
for mod_name in modules_to_fix:
    mod = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)
    if mod:
        print(f"{mod_name}: state={mod.state}, installable={mod.installable}")
    else:
        print(f"{mod_name}: STILL NOT FOUND - check addons path")

# 4. If still not found, clean and re-register
print("\\n=== Cleaning Broken Registrations ===")
for mod_name in modules_to_fix:
    mod = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)
    if mod and not mod.installable:
        print(f"Cleaning broken registration: {mod_name}")
        mod.unlink()
        print(f"Cleaned {mod_name}")

# 5. Update list again
env['ir.module.module'].update_list()

# 6. Install modules
print("\\n=== Installing Modules ===")
for mod_name in modules_to_fix:
    mod = env['ir.module.module'].search([('name', '=', mod_name)], limit=1)
    if mod:
        if mod.state == 'to install':
            mod.button_install()
            print(f"Triggered install for {mod_name}")
        else:
            print(f"{mod_name}: state is {mod.state} (not 'to install')")
    else:
        print(f"{mod_name}: Still not found after cleanup")
"""

if __name__ == '__main__':
    print("=" * 80)
    print("Module Registration Fix Script")
    print("=" * 80)
    print()
    print("This script provides Odoo shell commands to fix broken module registrations.")
    print()
    print("To use:")
    print("1. Open Odoo shell: odoo-bin shell")
    print("2. Copy and paste the SAFE_FIX_SCRIPT commands")
    print("3. Or run: exec(open('scripts/fix_module_registrations.py').read())")
    print()
    print("=" * 80)
    print("SAFE FIX SCRIPT:")
    print("=" * 80)
    print(SAFE_FIX_SCRIPT)
