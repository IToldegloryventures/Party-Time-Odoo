# Run this in Odoo shell (odoo-bin shell -d database_name)
# Copy and paste this entire block into the Odoo shell

import re

# Check views first (safe - view only)
print("Checking views...")
views = env['ir.ui.view'].sudo().search([('arch_db', 'ilike', 'x_plan2_id')])
print(f"Found {len(views)} views in ir_ui_view containing x_plan2_id:")
for v in views:
    print(f"  - ID: {v.id}, Name: {v.name}, Model: {v.model}")

custom_views = env['ir.ui.view.custom'].sudo().search([('arch', 'ilike', 'x_plan2_id')])
print(f"\nFound {len(custom_views)} custom views containing x_plan2_id:")
for v in custom_views:
    print(f"  - ID: {v.id}, User: {v.user_id.name}, Ref: {v.ref_id.name}")

# Fix ir_ui_view
print("\nFixing ir_ui_view...")
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

# Fix custom views
print("\nFixing ir_ui_view_custom...")
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
            print(f"  ✓ Fixed custom view {custom_view.id} (User: {custom_view.user_id.name})")
            custom_fixed_count += 1
    except Exception as e:
        print(f"  ✗ Error fixing custom view {custom_view.id}: {e}")

print(f"Fixed {custom_fixed_count} custom views")

# Commit changes
env.cr.commit()

print("\n✓ Done! Refresh your browser and try creating the project template again.")
