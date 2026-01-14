#!/usr/bin/env python3
"""
Safe Auto-Upgrade Script

Installs or upgrades all PTT modules in the correct order
(based on dependencies). Robust and only runs valid commands.

Usage:
    # In Odoo shell:
    exec(open('scripts/auto_upgrade.py').read())
    # OR:
    odoo-bin shell < scripts/auto_upgrade.py
"""

import time

# Module installation order (respects dependencies)
MODULES = [
    'ptt_business_core',        # Base module - no PTT dependencies
    'ptt_vendor_management',    # Depends on ptt_business_core
    'ptt_operational_dashboard', # Depends on ptt_business_core
    # 'ptt_justcall',           # Optional - uncomment if needed
]

print("=" * 80)
print("AUTO-UPGRADE SCRIPT")
print("=" * 80)
print()

for name in MODULES:
    module = env['ir.module.module'].search([('name', '=', name)], limit=1)
    if not module:
        print(f"[SKIP] Module not found in database: {name}")
        continue

    state = module.state
    print(f"[PROCESS] {name} (current state: {state})")

    try:
        if state in ('uninstalled', 'to install'):
            print(f"  -> Installing {name}...")
            module.button_install()
            time.sleep(1)
            
            # Verify state after install
            module.invalidate_recordset()
            new_state = module.state
            if new_state == 'installed':
                print(f"  [OK] Successfully installed {name}")
            else:
                print(f"  [WARN] Install triggered, but state is now: {new_state}")
                
        elif state in ('installed', 'to upgrade'):
            print(f"  -> Upgrading {name}...")
            module.button_upgrade()
            time.sleep(1)
            
            # Verify state after upgrade
            module.invalidate_recordset()
            new_state = module.state
            if new_state == 'installed':
                print(f"  [OK] Successfully upgraded {name}")
            else:
                print(f"  [WARN] Upgrade triggered, but state is now: {new_state}")
                
        else:
            print(f"  [SKIP] State is '{state}' - no action needed")
            
    except Exception as e:
        print(f"  [ERROR] Error processing {name}:")
        print(f"    {e}")
        import traceback
        traceback.print_exc()

print()
print("=" * 80)
print("AUTO-UPGRADE COMPLETE")
print("=" * 80)
print()
print("Next steps:")
print("1. Check for any errors above")
print("2. Verify modules are in 'installed' state")
print("3. Test functionality")
