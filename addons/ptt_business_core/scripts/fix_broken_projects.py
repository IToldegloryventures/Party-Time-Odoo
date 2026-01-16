"""
Fix broken projects missing company_id or partner_id that cause OwlError.

Run this in Odoo shell:
    odoo-bin shell
    
Then paste this entire script.
"""

# Fix projects missing company_id
projects_no_company = env['project.project'].search([('company_id', '=', False)])
print(f"Found {len(projects_no_company)} projects without company_id")
if projects_no_company:
    for project in projects_no_company:
        # Try to get company from sale order
        if project.sale_order_id and project.sale_order_id.company_id:
            project.company_id = project.sale_order_id.company_id.id
            print(f"  ✅ Set company_id for {project.name} (from sale order)")
        else:
            # Use default company
            project.company_id = env.company.id
            print(f"  ✅ Set company_id for {project.name} (default company)")
    print(f"\n✅ Fixed {len(projects_no_company)} projects without company_id")

# Fix projects missing partner_id (set to False if no partner exists)
projects_no_partner = env['project.project'].search([('partner_id', '=', False)])
# Only fix if they have sale_order_id but partner_id is None (not set)
projects_to_fix = projects_no_partner.filtered(lambda p: p.sale_order_id and p.sale_order_id.partner_id)
print(f"\nFound {len(projects_to_fix)} projects without partner_id (but have sale order)")
if projects_to_fix:
    for project in projects_to_fix:
        project.partner_id = project.sale_order_id.partner_id.id
        print(f"  ✅ Set partner_id for {project.name} (from sale order)")

# Fix projects missing user_id (set to False if not assigned)
projects_no_user = env['project.project'].search([('user_id', '=', False)])
print(f"\nFound {len(projects_no_user)} projects without user_id")
if projects_no_user:
    # These are OK - user_id is optional
    print(f"  ℹ️  user_id is optional, but ensuring they're explicitly set to False")
    for project in projects_no_user:
        # Only update if they have a sale order with a user
        if project.sale_order_id and project.sale_order_id.user_id:
            project.user_id = project.sale_order_id.user_id.id
            print(f"  ✅ Set user_id for {project.name} (from sale order)")
        # Otherwise leave as False (it's OK)

# Ensure all projects have type_ids (task stages)
projects_no_stages = env['project.project'].search([('type_ids', '=', False)])
print(f"\nFound {len(projects_no_stages)} projects without task stages")
if projects_no_stages:
    task_stages = env['project.task.type'].search([])
    if task_stages:
        for project in projects_no_stages:
            project.type_ids = [(6, 0, task_stages.ids)]
            print(f"  ✅ Set type_ids for {project.name}")
    else:
        # Create default stages if none exist
        default_stages = env['project.task.type'].create([
            {'name': 'To Do', 'sequence': 5},
            {'name': 'In Progress', 'sequence': 10},
            {'name': 'Done', 'sequence': 15},
            {'name': 'Cancelled', 'sequence': 20, 'fold': True},
        ])
        for project in projects_no_stages:
            project.type_ids = [(6, 0, default_stages.ids)]
            print(f"  ✅ Set type_ids for {project.name} (created default stages)")

print("\n" + "=" * 80)
print("✅ PROJECT FIX COMPLETE")
print("=" * 80)
print("\nTry opening the Projects app now - it should work!")
