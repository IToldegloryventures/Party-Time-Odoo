#!/usr/bin/env python3
"""
Emergency fix script to remove x_plan2_id field references from views.

This script removes the x_plan2_id field from any views that still reference it,
fixing the error: "project.project"."x_plan2_id" field is undefined.

Run this script via Odoo shell:
    odoo-bin shell -d your_database -c odoo.conf < scripts/fix_x_plan2_id_view.py

Or run interactively:
    odoo-bin shell -d your_database -c odoo.conf
    >>> exec(open('scripts/fix_x_plan2_id_view.py').read())
"""

import re
import logging

_logger = logging.getLogger(__name__)

# Get the environment (this will be available when run via Odoo shell)
try:
    env = env  # noqa: F821
except NameError:
    print("ERROR: This script must be run via Odoo shell.")
    print("Usage: odoo-bin shell -d your_database -c odoo.conf < scripts/fix_x_plan2_id_view.py")
    exit(1)

def fix_x_plan2_id_views():
    """Remove x_plan2_id field references from all views."""
    field_name = 'x_plan2_id'
    model_name = 'project.project'
    
    _logger.info(f"Searching for views referencing {field_name}...")
    
    # Search for views that reference this field
    views_to_fix = env['ir.ui.view'].sudo().search([
        '|',
        ('arch_db', 'ilike', field_name),
        ('arch_fs', 'ilike', field_name),
    ])
    
    if not views_to_fix:
        print(f"No views found referencing {field_name}.")
        return
    
    print(f"Found {len(views_to_fix)} view(s) referencing {field_name}.")
    
    fixed_count = 0
    for view in views_to_fix:
        try:
            original_arch = view.arch_db or ''
            if not original_arch:
                continue
                
            new_arch = str(original_arch)
            original_new_arch = new_arch
            
            # Remove field tags (self-closing)
            new_arch = re.sub(rf'<field[^>]*name=["\']{field_name}["\'][^/>]*/?>', '', new_arch)
            # Remove field tags (with content)
            new_arch = re.sub(rf'<field[^>]*name=["\']{field_name}["\'][^>]*>.*?</field>', '', new_arch, flags=re.DOTALL)
            # Remove label tags
            new_arch = re.sub(rf'<label[^>]*for=["\']{field_name}["\'][^/>]*/?>', '', new_arch)
            # Remove button tags with invisible attributes referencing the field
            new_arch = re.sub(rf'<button[^>]*invisible="[^"]*{field_name}[^"]*"[^>]*>.*?</button>', '', new_arch, flags=re.DOTALL)
            # Remove div tags with invisible attributes referencing the field
            new_arch = re.sub(rf'<div[^>]*invisible="[^"]*{field_name}[^"]*"[^>]*>.*?</div>', '', new_arch, flags=re.DOTALL)
            # Remove xpath expressions referencing the field
            new_arch = re.sub(rf'<xpath[^>]*>.*?<field[^>]*name=["\']{field_name}["\'][^>]*>.*?</field>.*?</xpath>', '', new_arch, flags=re.DOTALL)
            
            if new_arch != original_new_arch:
                view.write({'arch_db': new_arch})
                print(f"✓ Fixed view {view.id} ({view.name}) - {view.model}")
                fixed_count += 1
            else:
                print(f"  Skipped view {view.id} ({view.name}) - {view.model} (no changes needed)")
                
        except Exception as e:
            print(f"✗ Error fixing view {view.id} ({view.name}): {e}")
            _logger.error(f"Error fixing view {view.id}: {e}", exc_info=True)
    
    if fixed_count > 0:
        print(f"\n✓ Successfully fixed {fixed_count} view(s).")
        print("Please refresh your browser and try creating the project template again.")
    else:
        print("\nNo views were modified.")
    
    # Also check if the field still exists in ir_model_fields (should have been removed by pre_init_hook)
    field_exists = env['ir.model.fields'].sudo().search([
        ('name', '=', field_name),
        ('model', '=', model_name),
    ])
    
    if field_exists:
        print(f"\nWARNING: Field {field_name} still exists in ir_model_fields!")
        print("This field should have been removed by the pre_init_hook.")
        print("Consider updating the module to run the cleanup hooks.")
    else:
        print(f"\n✓ Field {field_name} does not exist in ir_model_fields (as expected).")

# Run the fix
if __name__ == '__main__':
    fix_x_plan2_id_views()
else:
    # When executed via exec() in Odoo shell
    fix_x_plan2_id_views()
