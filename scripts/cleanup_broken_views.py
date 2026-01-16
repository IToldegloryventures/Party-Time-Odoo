# Run this in Odoo.sh shell to clean up broken views
# Copy-paste into: odoo-bin shell -d your_db

print("=" * 80)
print("Cleaning up broken view references")
print("=" * 80)

# 1. Find any views that reference the non-existent view_project_filter
broken_views = env['ir.ui.view'].search([
    ('name', 'ilike', 'ptt.%'),
    ('model', '=', 'project.project'),
    ('arch_db', 'ilike', '%view_project_filter%')
])

if broken_views:
    print(f"\nFound {len(broken_views)} views with broken references:")
    for view in broken_views:
        print(f"  - {view.name} (ID: {view.id}, XML ID: {view.xml_id})")
    
    # Delete broken views
    view_ids = broken_views.ids
    broken_views.unlink()
    print(f"\n✅ Deleted {len(view_ids)} broken view(s)")
else:
    print("\n✅ No broken views found with old view_project_filter reference")

# 2. Check for views with invalid inherit_id
print("\n" + "=" * 80)
print("Checking for views with invalid inherit_id")
print("=" * 80)

ptt_views = env['ir.ui.view'].search([
    ('name', 'ilike', 'ptt.%'),
    ('inherit_id', '!=', False)
])

invalid_inherit = []
for view in ptt_views:
    try:
        if view.inherit_id:
            _ = view.inherit_id.name
    except Exception as e:
        invalid_inherit.append(view)

if invalid_inherit:
    print(f"\n⚠️  Found {len(invalid_inherit)} views with invalid inherit_id:")
    for view in invalid_inherit:
        print(f"  - {view.name} (ID: {view.id}, inherit_id: {view.inherit_id.id})")
    print("\nThese views should be fixed by upgrading the module.")
else:
    print("\n✅ All PTT views have valid inherit_id references")

# 3. Clear view cache
print("\n" + "=" * 80)
print("Clearing view cache")
print("=" * 80)

env.registry.clear_cache()
print("✅ View cache cleared")

print("\n" + "=" * 80)
print("Next steps:")
print("=" * 80)
print("1. Exit shell")
print("2. Upgrade module: odoo-bin -u ptt_operational_dashboard -d your_db")
print("   OR restart Odoo.sh and let it rebuild automatically")
