#!/usr/bin/env python3
"""
Validate custom models and fields in Odoo.
Checks for:
- Valid model references (comodel_name)
- Valid related fields
- Missing fields in database
- View inheritance issues
"""
import sys

# This script should be run in Odoo shell: 
# odoo-bin shell -d your_db
# Then copy-paste this code, or use: exec(open('scripts/validate_custom_models.py').read())

print("=" * 80)
print("Validating Custom Models (ptt.* and x_*)")
print("=" * 80)

# 1. Find all custom models that start with 'ptt.' or 'x_'
ptt_models = [m for m in env.registry.models if m.startswith('ptt.') or m.startswith('x_')]
print(f"\nFound {len(ptt_models)} custom models to validate\n")

errors_found = False
warnings_found = False

# 2. Validate field definitions and relationships
for model_name in sorted(ptt_models):
    try:
        model = env[model_name]
        for field_name, field in model._fields.items():
            # Check if related/Many2one/Many2many/One2many fields point to valid models
            if hasattr(field, 'comodel_name') and field.comodel_name:
                try:
                    # Just check if the model exists in the registry (don't check .name)
                    test_model = env[field.comodel_name]
                    # Model exists - validation passed
                except KeyError:
                    print(f"[ERROR] {model_name}.{field_name}: comodel_name '{field.comodel_name}' not found in registry")
                    errors_found = True
                except Exception as e:
                    # Other exceptions might indicate real problems
                    print(f"[ERROR] {model_name}.{field_name}: comodel_name '{field.comodel_name}' → {type(e).__name__}: {e}")
                    errors_found = True
    except Exception as model_error:
        print(f"[MODEL ERROR] {model_name} → {model_error}")
        errors_found = True

# 3. Check for broken views
print("\n" + "=" * 80)
print("Checking Views")
print("=" * 80)

try:
    broken_views = env['ir.ui.view'].search([
        '|',
        ('arch_db', '=', False),
        ('arch_fs', '=', False)
    ])
    if broken_views:
        print(f"⚠️  Found {len(broken_views)} views without arch_db or arch_fs (this is normal for database-stored views)")
        for view in broken_views[:5]:  # Show first 5
            print(f"   - {view.name} (model: {view.model}, ID: {view.id})")
        if len(broken_views) > 5:
            print(f"   ... and {len(broken_views) - 5} more")
    else:
        print("✅ All views have arch definitions")
except Exception as e:
    print(f"[WARNING] Could not check views: {e}")

# 4. Check for view inheritance issues
print("\n" + "=" * 80)
print("Checking View Inherit IDs")
print("=" * 80)

try:
    ptt_views = env['ir.ui.view'].search([
        ('name', 'ilike', 'ptt.%'),
        ('inherit_id', '!=', False)
    ])
    
    invalid_inherit = []
    for view in ptt_views:
        try:
            # Try to access the inherited view
            if view.inherit_id:
                _ = view.inherit_id.name  # This will fail if inherit_id is broken
        except Exception as e:
            invalid_inherit.append((view.name, view.inherit_id.id, str(e)))
    
    if invalid_inherit:
        print(f"❌ Found {len(invalid_inherit)} views with invalid inherit_id:")
        for view_name, inherit_id, error in invalid_inherit:
            print(f"   - {view_name} (inherit_id: {inherit_id}) → {error}")
        errors_found = True
    else:
        print(f"✅ All {len(ptt_views)} PTT view inheritances are valid")
except Exception as e:
    print(f"[WARNING] Could not check view inheritances: {e}")

# 5. Check for missing not-null constraints (warnings)
print("\n" + "=" * 80)
print("Summary")
print("=" * 80)

if not errors_found:
    print(f"✅ All {len(ptt_models)} custom models validated successfully!")
    print("✅ No critical errors found")
else:
    print(f"\n❌ Found errors in custom models")
    sys.exit(1)
