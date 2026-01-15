# Copy-paste this entire block into Odoo shell (odoo-bin shell)
# ============================================================================
# VALIDATION SCRIPT FOR ODOO SHELL
# ============================================================================

print("=" * 80)
print("Validating Custom Models (ptt.* and x_*)")
print("=" * 80)

# 1. Find all custom models
ptt_models = [m for m in env.registry.models if m.startswith('ptt.') or m.startswith('x_')]
print(f"\nFound {len(ptt_models)} custom models to validate\n")

errors_found = False

# 2. Validate field definitions and relationships
for model_name in sorted(ptt_models):
    try:
        model = env[model_name]
        for field_name, field in model._fields.items():
            if hasattr(field, 'comodel_name') and field.comodel_name:
                try:
                    test_model = env[field.comodel_name]
                except KeyError:
                    print(f"[ERROR] {model_name}.{field_name}: comodel_name '{field.comodel_name}' not found in registry")
                    errors_found = True
                except Exception as e:
                    print(f"[ERROR] {model_name}.{field_name}: comodel_name '{field.comodel_name}' → {type(e).__name__}: {e}")
                    errors_found = True
    except Exception as model_error:
        print(f"[MODEL ERROR] {model_name} → {model_error}")
        errors_found = True

# 3. Check views
print("\n" + "=" * 80)
print("Checking Views")
print("=" * 80)

try:
    broken_views = env['ir.ui.view'].search(['|', ('arch_db', '=', False), ('arch_fs', '=', False)])
    if broken_views:
        print(f"⚠️  Found {len(broken_views)} views without arch_db/arch_fs (normal for DB views)")
    else:
        print("✅ All views have arch definitions")
except Exception as e:
    print(f"[WARNING] Could not check views: {e}")

# 4. Check view inheritance
print("\n" + "=" * 80)
print("Checking View Inherit IDs")
print("=" * 80)

try:
    ptt_views = env['ir.ui.view'].search([('name', 'ilike', 'ptt.%'), ('inherit_id', '!=', False)])
    invalid_inherit = []
    for view in ptt_views:
        try:
            if view.inherit_id:
                _ = view.inherit_id.name
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

# 5. Summary
print("\n" + "=" * 80)
print("Summary")
print("=" * 80)

if not errors_found:
    print(f"✅ All {len(ptt_models)} custom models validated successfully!")
    print("✅ No critical errors found")
else:
    print(f"\n❌ Found errors in custom models")
