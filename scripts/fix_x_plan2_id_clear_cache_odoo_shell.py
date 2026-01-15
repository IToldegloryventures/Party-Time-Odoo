# Run this in Odoo shell (odoo-bin shell -d database_name)
# Copy and paste this entire block into the Odoo shell

import re

print("=" * 80)
print("x_plan2_id Cleanup + Cache Clear Script")
print("=" * 80)

# === STEP 1: Check ir_ui_view ===
print("\n[STEP 1] Checking ir_ui_view (arch_db)...")
views = env['ir.ui.view'].sudo().search([('arch_db', 'ilike', 'x_plan2_id')])
print(f"Found {len(views)} views in ir_ui_view containing x_plan2_id")
for v in views:
    print(f"  - ID: {v.id}, Name: {v.name}, Model: {v.model}, Type: {v.type}")

# === STEP 2: Check ir_ui_view_custom (Studio customizations) ===
print("\n[STEP 2] Checking ir_ui_view_custom (Studio customizations)...")
custom_views = env['ir.ui.view.custom'].sudo().search([('arch', 'ilike', 'x_plan2_id')])
print(f"Found {len(custom_views)} custom views containing x_plan2_id")
for v in custom_views:
    print(f"  - ID: {v.id}, User: {v.user_id.name if v.user_id else 'N/A'}, Ref: {v.ref_id.name if v.ref_id else 'N/A'}")

# === STEP 3: Check arch_fs (file-based views) ===
print("\n[STEP 3] Checking ir_ui_view (arch_fs - file-based views)...")
file_views = env['ir.ui.view'].sudo().search([('arch_fs', 'ilike', 'x_plan2_id')])
print(f"Found {len(file_views)} file-based views containing x_plan2_id")
for v in file_views:
    print(f"  - ID: {v.id}, Name: {v.name}, File: {v.arch_fs}")

# === STEP 4: Fix ir_ui_view ===
if views:
    print("\n[STEP 4] Fixing ir_ui_view...")
    fixed_count = 0
    for view in views:
        try:
            original_arch = view.arch_db or ''
            if not original_arch:
                continue
                
            new_arch = str(original_arch)
            original_new_arch = new_arch
            
            # Remove field tags
            new_arch = re.sub(r'<field[^>]*name=["\']x_plan2_id["\'][^/>]*/?>', '', new_arch)
            new_arch = re.sub(r'<field[^>]*name=["\']x_plan2_id["\'][^>]*>.*?</field>', '', new_arch, flags=re.DOTALL)
            new_arch = re.sub(r'<label[^>]*for=["\']x_plan2_id["\'][^/>]*/?>', '', new_arch)
            new_arch = re.sub(r'<button[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</button>', '', new_arch, flags=re.DOTALL)
            new_arch = re.sub(r'<div[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</div>', '', new_arch, flags=re.DOTALL)
            new_arch = re.sub(r'<xpath[^>]*>.*?<field[^>]*name=["\']x_plan2_id["\'][^>]*>.*?</field>.*?</xpath>', '', new_arch, flags=re.DOTALL)
            
            if new_arch != original_new_arch:
                view.write({'arch_db': new_arch})
                print(f"  ✓ Fixed view {view.id} ({view.name})")
                fixed_count += 1
        except Exception as e:
            print(f"  ✗ Error fixing view {view.id}: {e}")
    
    print(f"Fixed {fixed_count} views in ir_ui_view")
else:
    print("\n[STEP 4] No views to fix in ir_ui_view")

# === STEP 5: Fix ir_ui_view_custom ===
if custom_views:
    print("\n[STEP 5] Fixing ir_ui_view_custom...")
    custom_fixed_count = 0
    for custom_view in custom_views:
        try:
            original_arch = custom_view.arch or ''
            if not original_arch:
                continue
                
            new_arch = str(original_arch)
            original_new_arch = new_arch
            
            # Remove field tags
            new_arch = re.sub(r'<field[^>]*name=["\']x_plan2_id["\'][^/>]*/?>', '', new_arch)
            new_arch = re.sub(r'<field[^>]*name=["\']x_plan2_id["\'][^>]*>.*?</field>', '', new_arch, flags=re.DOTALL)
            new_arch = re.sub(r'<label[^>]*for=["\']x_plan2_id["\'][^/>]*/?>', '', new_arch)
            new_arch = re.sub(r'<button[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</button>', '', new_arch, flags=re.DOTALL)
            new_arch = re.sub(r'<div[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</div>', '', new_arch, flags=re.DOTALL)
            
            if new_arch != original_new_arch:
                custom_view.write({'arch': new_arch})
                print(f"  ✓ Fixed custom view {custom_view.id} (User: {custom_view.user_id.name if custom_view.user_id else 'N/A'})")
                custom_fixed_count += 1
        except Exception as e:
            print(f"  ✗ Error fixing custom view {custom_view.id}: {e}")
    
    print(f"Fixed {custom_fixed_count} custom views")
else:
    print("\n[STEP 5] No custom views to fix")

# === STEP 6: Commit changes ===
if views or custom_views:
    env.cr.commit()
    print("\n[STEP 6] ✓ Changes committed to database")
else:
    print("\n[STEP 6] No changes needed - database is clean")

# === STEP 7: Clear Odoo registry cache ===
print("\n[STEP 7] Clearing Odoo registry cache...")
try:
    env.registry.clear_cache()
    print("  ✓ Registry cache cleared")
except Exception as e:
    print(f"  ✗ Error clearing cache: {e}")

# === SUMMARY ===
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
total_found = len(views) + len(custom_views) + len(file_views)
if total_found == 0:
    print("✓ Database is clean - no views found with x_plan2_id")
    print("\nIf the error persists, try:")
    print("  1. Clear browser cache (IndexedDB, localStorage, sessionStorage)")
    print("  2. Restart Odoo service: sudo service odoo restart")
    print("  3. Refresh browser")
else:
    print(f"Found {total_found} views with x_plan2_id references")
    print(f"Fixed {len([v for v in views if v.arch_db]) + len([v for v in custom_views if v.arch])} views")
    print("\nNEXT STEPS:")
    print("  1. Restart Odoo service: sudo service odoo restart")
    print("  2. Clear browser cache (IndexedDB, localStorage, sessionStorage)")
    print("  3. Refresh browser")
print("=" * 80)
