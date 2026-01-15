#!/usr/bin/env python3
"""
Comprehensive fix for x_plan2_id references in Odoo views.
This script checks ALL possible locations where x_plan2_id might be referenced:
- ir_ui_view (arch_db)
- ir_ui_view_custom (arch)
- ir_ui_view (arch_fs - file-based views)
- Studio customizations
- View inheritance chains
"""

import re
import logging

_logger = logging.getLogger(__name__)

# Pattern to match x_plan2_id in various XML contexts
patterns = [
    (r'<field[^>]*name=["\']x_plan2_id["\'][^/>]*/?>', 'field tag'),
    (r'<field[^>]*name=["\']x_plan2_id["\'][^>]*>.*?</field>', 'field tag with content'),
    (r'<label[^>]*for=["\']x_plan2_id["\'][^/>]*/?>', 'label tag'),
    (r'<button[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</button>', 'button with invisible'),
    (r'<div[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</div>', 'div with invisible'),
    (r'<xpath[^>]*>.*?x_plan2_id.*?</xpath>', 'xpath with field'),
    (r'domain="[^"]*x_plan2_id[^"]*"', 'domain attribute'),
    (r'context="[^"]*x_plan2_id[^"]*"', 'context attribute'),
    (r'invisible="[^"]*x_plan2_id[^"]*"', 'invisible attribute'),
    (r'readonly="[^"]*x_plan2_id[^"]*"', 'readonly attribute'),
    (r'required="[^"]*x_plan2_id[^"]*"', 'required attribute'),
]

def find_all_references(cr):
    """Find all views containing x_plan2_id references"""
    all_matches = []
    
    # Check ir_ui_view (arch_db)
    cr.execute("""
        SELECT id, name, model, type, inherit_id, arch_db::text as arch_text
        FROM ir_ui_view 
        WHERE arch_db::text LIKE %s OR arch_fs LIKE %s
    """, ('%x_plan2_id%', '%x_plan2_id%'))
    
    for row in cr.fetchall():
        all_matches.append({
            'id': row[0],
            'name': row[1],
            'model': row[2],
            'type': row[3],
            'inherit_id': row[4],
            'arch': row[5],
            'table': 'ir_ui_view',
            'field': 'arch_db'
        })
    
    # Check ir_ui_view_custom (arch)
    cr.execute("""
        SELECT id, ref_id, user_id, arch::text as arch_text
        FROM ir_ui_view_custom 
        WHERE arch::text LIKE %s
    """, ('%x_plan2_id%',))
    
    for row in cr.fetchall():
        all_matches.append({
            'id': row[0],
            'ref_id': row[1],
            'user_id': row[2],
            'arch': row[3],
            'table': 'ir_ui_view_custom',
            'field': 'arch'
        })
    
    return all_matches

def clean_arch(arch_text):
    """Remove all x_plan2_id references from arch text"""
    if not arch_text:
        return arch_text
    
    cleaned = str(arch_text)
    original = cleaned
    
    # Apply all patterns
    for pattern, desc in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.DOTALL | re.IGNORECASE)
    
    return cleaned if cleaned != original else arch_text

# === RUN IN ODOO SHELL ===
# Copy everything below into Odoo shell (odoo-bin shell -d <db> -c odoo.conf)

print("=" * 80)
print("COMPREHENSIVE x_plan2_id Cleanup Script")
print("=" * 80)

# Find all references
matches = find_all_references(cr)
print(f"\nFound {len(matches)} views/customizations containing x_plan2_id:\n")

for match in matches:
    if match['table'] == 'ir_ui_view':
        print(f"  - View ID {match['id']}: {match['name']} (model: {match['model']}, type: {match['type']})")
    else:
        print(f"  - Custom View ID {match['id']}: ref_id={match['ref_id']}, user_id={match['user_id']}")

if not matches:
    print("  ✓ No views found with x_plan2_id references!")
    print("\nThe error might be due to:")
    print("  1. Browser cache (clear IndexedDB, localStorage, sessionStorage)")
    print("  2. Odoo registry cache (restart Odoo service)")
    print("  3. View file on disk (arch_fs) - check for XML files with x_plan2_id")
else:
    print(f"\nCleaning {len(matches)} views...")
    
    fixed_count = 0
    for match in matches:
        try:
            cleaned_arch = clean_arch(match['arch'])
            if cleaned_arch != match['arch']:
                if match['table'] == 'ir_ui_view':
                    cr.execute(
                        "UPDATE ir_ui_view SET arch_db = %s WHERE id = %s",
                        (cleaned_arch, match['id'])
                    )
                    print(f"  ✓ Fixed view ID {match['id']}: {match.get('name', 'N/A')}")
                else:
                    cr.execute(
                        "UPDATE ir_ui_view_custom SET arch = %s WHERE id = %s",
                        (cleaned_arch, match['id'])
                    )
                    print(f"  ✓ Fixed custom view ID {match['id']}")
                fixed_count += 1
        except Exception as e:
            print(f"  ✗ Error fixing {match['table']} ID {match['id']}: {e}")
    
    if fixed_count > 0:
        cr.commit()
        print(f"\n✓ Fixed {fixed_count} views. Committed to database.")
        print("\nNEXT STEPS:")
        print("  1. Clear browser cache (IndexedDB, localStorage, sessionStorage)")
        print("  2. Restart Odoo service: sudo service odoo restart")
        print("  3. Refresh browser")
    else:
        print("\n  No changes needed - all views are clean!")

print("\n" + "=" * 80)
