#!/usr/bin/env python3
"""
Odoo Shell Script to Fix Blank Database Screen

Run this in Odoo shell:
    odoo-bin shell -d your_database_name < fix_blank_database.py

Or copy-paste the commands below into Odoo shell.
"""

# === FIX 1: Clear user home actions pointing to PTT dashboard ===
print("Step 1: Clearing user home actions pointing to PTT dashboard...")

# Find the PTT home hub action
ptt_action = env.ref('ptt_operational_dashboard.action_ptt_home_hub', raise_if_not_found=False)
if ptt_action:
    # Clear any users that have this action as their home action
    users = env['res.users'].search([('action_id', '=', ptt_action.id)])
    if users:
        users.write({'action_id': False})
        print(f"✓ Cleared home action for {len(users)} user(s)")
    else:
        print("✓ No users found with PTT dashboard as home action")
else:
    print("⚠ PTT action not found (may already be fixed)")

# === FIX 2: Ensure default Odoo home action is correct ===
print("\nStep 2: Verifying Odoo default home action...")

default_action = env.ref('base.action_client_base_menu', raise_if_not_found=False)
if default_action:
    if default_action.tag != 'menu':
        default_action.write({'tag': 'menu', 'name': 'Menu'})
        print("✓ Restored default home action")
    else:
        print("✓ Default home action is already correct")
else:
    print("⚠ Could not find default home action")

# === FIX 3: Clear browser session storage (if accessible) ===
print("\nStep 3: Database fixes complete!")
print("\nIMPORTANT: After updating the module, please:")
print("  1. Clear your browser cache and cookies for the Odoo.sh domain")
print("  2. Or use an incognito/private window")
print("  3. Or clear browser sessionStorage: Open browser console and run:")
print("     sessionStorage.clear(); localStorage.clear(); location.reload();")

print("\n✓ All database fixes applied!")
print("\nNext step: Update the module via Apps menu or:")
print("  odoo-bin -u ptt_operational_dashboard -d your_database_name")

