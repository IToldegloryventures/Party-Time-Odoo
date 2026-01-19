#!/usr/bin/env python3
"""
Analyze Duplicate Studio Fields on crm.lead
============================================
Run this in Odoo.sh shell to identify which duplicate fields should be kept/removed.

Usage in Odoo.sh:
1. Go to your build > Shell
2. Run: odoo-bin shell -d <database_name>
3. Paste this script content

This script will:
- Identify duplicate-labeled fields
- Check which ones have actual data
- Check which ones are used in views
- Recommend which to keep/remove
"""

# Run this in Odoo shell
def analyze_duplicate_fields():
    from odoo import api, SUPERUSER_ID
    from odoo.tools import config
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    print("\n" + "="*70)
    print("DUPLICATE STUDIO FIELD ANALYSIS - crm.lead")
    print("="*70)
    
    # Known duplicates from warnings
    duplicate_sets = [
        {
            'label': 'New CheckBox',
            'fields': ['x_studio_boolean_field_297_1jckjk5dc', 'x_studio_boolean_field_1vp_1jckie6sq'],
        },
        {
            'label': 'End Time',
            'fields': ['x_studio_end_time', 'x_studio_end_time_1'],
        },
    ]
    
    Lead = env['crm.lead']
    IrModelFields = env['ir.model.fields']
    IrUiView = env['ir.ui.view']
    
    for dup_set in duplicate_sets:
        print(f"\n{'='*70}")
        print(f"ANALYZING: '{dup_set['label']}' fields")
        print("="*70)
        
        for field_name in dup_set['fields']:
            print(f"\n--- Field: {field_name} ---")
            
            # Check if field exists in model
            if field_name not in Lead._fields:
                print(f"  STATUS: Field NOT FOUND in model (may already be deleted)")
                continue
            
            field = Lead._fields[field_name]
            print(f"  Type: {field.type}")
            print(f"  String/Label: {field.string}")
            
            # Get field definition from ir.model.fields
            field_def = IrModelFields.search([
                ('model', '=', 'crm.lead'),
                ('name', '=', field_name)
            ], limit=1)
            
            if field_def:
                print(f"  Created by Module: {field_def.modules or 'Studio (None)'}")
                print(f"  Store: {field_def.store}")
                print(f"  Required: {field_def.required}")
            
            # Count records with non-null values
            try:
                count_with_data = Lead.search_count([(field_name, '!=', False)])
                print(f"  Records with data: {count_with_data}")
            except Exception as e:
                print(f"  Records with data: ERROR - {e}")
            
            # Check if used in views
            views_using = IrUiView.search([
                ('arch_db', 'ilike', field_name)
            ])
            if views_using:
                print(f"  Used in {len(views_using)} view(s):")
                for v in views_using[:5]:  # Show first 5
                    print(f"    - {v.name} ({v.type})")
            else:
                print(f"  Used in views: NONE")
    
    # Also check for ALL x_studio fields on crm.lead for reference
    print(f"\n{'='*70}")
    print("ALL x_studio FIELDS ON crm.lead")
    print("="*70)
    
    all_studio_fields = IrModelFields.search([
        ('model', '=', 'crm.lead'),
        ('name', 'like', 'x_studio_%')
    ], order='name')
    
    print(f"\nTotal x_studio fields: {len(all_studio_fields)}")
    print("\nField Name                                    | Label                    | Type     | Has Data")
    print("-" * 100)
    
    for f in all_studio_fields:
        # Count data
        try:
            if f.name in Lead._fields:
                count = Lead.search_count([(f.name, '!=', False)])
            else:
                count = "N/A"
        except:
            count = "ERR"
        
        print(f"{f.name[:45]:<45} | {(f.field_description or '')[:24]:<24} | {f.ttype:<8} | {count}")
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    print("""
Based on the analysis above:
1. KEEP fields that have data and are used in views
2. REMOVE fields that have NO data and are NOT used in views
3. For duplicates with same data, keep the one with the simpler name

To remove a field, run:
    env['ir.model.fields'].search([('model', '=', 'crm.lead'), ('name', '=', 'FIELD_NAME')]).unlink()
    env.cr.commit()
""")

# Execute
analyze_duplicate_fields()
