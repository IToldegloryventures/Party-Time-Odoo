#!/usr/bin/env python3
"""
Cleanup Duplicate Studio Fields on crm.lead
============================================
Run this ONLY AFTER running analyze_duplicate_studio_fields.py first!

This script will remove the duplicate fields that are NOT in use.
Review the analysis output first to confirm which fields to remove.

Usage in Odoo.sh:
1. Go to your build > Shell
2. Run: odoo-bin shell -d <database_name>
3. Paste this script content
"""

def cleanup_duplicate_fields():
    from odoo import api, SUPERUSER_ID
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    IrModelFields = env['ir.model.fields']
    Lead = env['crm.lead']
    
    print("\n" + "="*70)
    print("STUDIO FIELD CLEANUP - crm.lead")
    print("="*70)
    
    # Fields to REMOVE (the duplicates that should be deleted)
    # These are the ones with ugly auto-generated names that are likely unused
    fields_to_remove = [
        # Duplicate "New CheckBox" - keep neither if unused, or remove the uglier name
        'x_studio_boolean_field_297_1jckjk5dc',
        'x_studio_boolean_field_1vp_1jckie6sq',
        # Duplicate "End Time" - keep x_studio_end_time, remove x_studio_end_time_1
        'x_studio_end_time_1',
    ]
    
    print(f"\nFields scheduled for removal: {len(fields_to_remove)}")
    
    for field_name in fields_to_remove:
        print(f"\n--- Processing: {field_name} ---")
        
        # First check if field has any data
        if field_name in Lead._fields:
            try:
                count = Lead.search_count([(field_name, '!=', False)])
                if count > 0:
                    print(f"  WARNING: Field has {count} records with data!")
                    print(f"  SKIPPING removal to prevent data loss.")
                    print(f"  To force removal, manually delete after backing up data.")
                    continue
                else:
                    print(f"  OK: No data in this field")
            except Exception as e:
                print(f"  ERROR checking data: {e}")
                continue
        
        # Find and delete the field definition
        field_def = IrModelFields.search([
            ('model', '=', 'crm.lead'),
            ('name', '=', field_name)
        ], limit=1)
        
        if field_def:
            try:
                field_def.unlink()
                print(f"  DELETED: {field_name}")
            except Exception as e:
                print(f"  ERROR deleting: {e}")
        else:
            print(f"  NOT FOUND: Field may already be deleted")
    
    # Commit the changes
    env.cr.commit()
    
    print("\n" + "="*70)
    print("CLEANUP COMPLETE")
    print("="*70)
    print("\nRestart the Odoo server for changes to take effect.")
    print("The duplicate label warnings should be gone after restart.")

# Execute
cleanup_duplicate_fields()
