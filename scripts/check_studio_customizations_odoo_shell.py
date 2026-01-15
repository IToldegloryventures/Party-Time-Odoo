# Run this in Odoo shell (odoo-bin shell -d database_name)
# Copy and paste this entire block into the Odoo shell

print("=" * 80)
print("Checking Studio Customizations for project.project")
print("=" * 80)

# Check for Studio customizations that reference x_plan2_id
print("\n[STEP 1] Checking ir_ui_view_custom for x_plan2_id references...")
custom_views = env['ir.ui.view.custom'].sudo().search([
    ('arch', 'ilike', 'x_plan2_id')
])
print(f"Found {len(custom_views)} custom views with x_plan2_id:")

for v in custom_views:
    print(f"\n  Custom View ID: {v.id}")
    print(f"    User: {v.user_id.name if v.user_id else 'N/A'} (ID: {v.user_id.id if v.user_id else 'N/A'})")
    print(f"    Ref View: {v.ref_id.name if v.ref_id else 'N/A'} (ID: {v.ref_id.id if v.ref_id else 'N/A'})")
    print(f"    Model: {v.ref_id.model if v.ref_id else 'N/A'}")
    if v.ref_id:
        print(f"    View Type: {v.ref_id.type if v.ref_id else 'N/A'}")

# Check for Studio customizations for project.project views specifically
print("\n[STEP 2] Checking ir_ui_view_custom for project.project views...")
project_custom_views = env['ir.ui.view.custom'].sudo().search([
    ('ref_id.model', '=', 'project.project')
])
print(f"Found {len(project_custom_views)} custom views for project.project:")

for v in project_custom_views:
    has_x_plan2_id = 'x_plan2_id' in (v.arch or '')
    status = "⚠ CONTAINS x_plan2_id" if has_x_plan2_id else "✓ Clean"
    print(f"\n  Custom View ID: {v.id} - {status}")
    print(f"    User: {v.user_id.name if v.user_id else 'N/A'} (ID: {v.user_id.id if v.user_id else 'N/A'})")
    print(f"    Ref View: {v.ref_id.name if v.ref_id else 'N/A'} (ID: {v.ref_id.id if v.ref_id else 'N/A'})")
    print(f"    View Type: {v.ref_id.type if v.ref_id else 'N/A'}")

# Check all views that inherit project.project views
print("\n[STEP 3] Checking views that inherit project.project views...")
project_views = env['ir.ui.view'].sudo().search([
    ('model', '=', 'project.project')
])
print(f"Found {len(project_views)} views for project.project model")

# Check if any project.project views have x_plan2_id
project_views_with_x_plan2_id = env['ir.ui.view'].sudo().search([
    ('model', '=', 'project.project'),
    ('arch_db', 'ilike', 'x_plan2_id')
])
print(f"Found {len(project_views_with_x_plan2_id)} project.project views with x_plan2_id:")
for v in project_views_with_x_plan2_id:
    print(f"  - View ID: {v.id}, Name: {v.name}, Type: {v.type}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Custom views with x_plan2_id: {len(custom_views)}")
print(f"Project.project custom views: {len(project_custom_views)}")
print(f"Project.project views with x_plan2_id: {len(project_views_with_x_plan2_id)}")

if len(custom_views) == 0 and len(project_views_with_x_plan2_id) == 0:
    print("\n✓ Database appears clean!")
    print("\nIf error persists, this is likely a browser cache issue.")
    print("Try:")
    print("  1. Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)")
    print("  2. Clear IndexedDB (F12 > Application > Storage > IndexedDB > Delete)")
    print("  3. Clear localStorage and sessionStorage")
    print("  4. Restart Odoo service")
else:
    print("\n⚠ Found references that need cleaning!")
    print("Run the cleanup script to fix them.")
print("=" * 80)
