# Run this code directly in Odoo shell:
# odoo-bin shell -d your_database_name -c odoo.conf
# Then paste this code:

import re

field_name = 'x_plan2_id'
views_to_fix = env['ir.ui.view'].sudo().search([('arch_db', 'ilike', field_name)])

print(f"Found {len(views_to_fix)} view(s) referencing {field_name}.")

fixed_count = 0
for view in views_to_fix:
    try:
        original_arch = view.arch_db or ''
        if not original_arch:
            continue
            
        new_arch = str(original_arch)
        original_new_arch = new_arch
        
        # Remove field tags
        new_arch = re.sub(rf'<field[^>]*name=["\']{field_name}["\'][^/>]*/?>', '', new_arch)
        new_arch = re.sub(rf'<field[^>]*name=["\']{field_name}["\'][^>]*>.*?</field>', '', new_arch, flags=re.DOTALL)
        new_arch = re.sub(rf'<label[^>]*for=["\']{field_name}["\'][^/>]*/?>', '', new_arch)
        new_arch = re.sub(rf'<button[^>]*invisible="[^"]*{field_name}[^"]*"[^>]*>.*?</button>', '', new_arch, flags=re.DOTALL)
        new_arch = re.sub(rf'<div[^>]*invisible="[^"]*{field_name}[^"]*"[^>]*>.*?</div>', '', new_arch, flags=re.DOTALL)
        new_arch = re.sub(rf'<xpath[^>]*>.*?<field[^>]*name=["\']{field_name}["\'][^>]*>.*?</field>.*?</xpath>', '', new_arch, flags=re.DOTALL)
        
        if new_arch != original_new_arch:
            view.write({'arch_db': new_arch})
            print(f"✓ Fixed view {view.id} ({view.name}) - {view.model}")
            fixed_count += 1
    except Exception as e:
        print(f"✗ Error fixing view {view.id}: {e}")

print(f"\n✓ Successfully fixed {fixed_count} view(s). Please refresh your browser.")
