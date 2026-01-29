from odoo import api, SUPERUSER_ID


def post_init_hook(cr, registry):
    """Normalize service products for task creation.

    - Keep Event Kickoff as the sole project creator (project_only) with its template.
    - Set every other active, sellable service to `task_in_project` so a task
      is auto-created and attached to the parent project.
    - Clear project/template links on those services (task name will default to
      the sale line/product name).
    - Archive legacy kickoff variants if present.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    Product = env['product.template']
    Task = env['project.task']
    Project = env['project.project']

    # ------------------------------------------------------------------
    # Ensure every lead has an event type (field is required=True)
    # ------------------------------------------------------------------
    try:
        default_event_type = env.ref(
            "ptt_enhanced_sales.event_type_social", raise_if_not_found=False
        ) or env['sale.order.type'].search([], limit=1)
        if default_event_type:
            env.cr.execute(
                """
                UPDATE crm_lead
                   SET ptt_event_type_id = %s
                 WHERE ptt_event_type_id IS NULL
                """,
                (default_event_type.id,),
            )
            # Enforce NOT NULL if data is now clean
            env.cr.execute(
                """
                ALTER TABLE crm_lead
                ALTER COLUMN ptt_event_type_id SET NOT NULL
                """
            )
    except Exception:
        # If any issue occurs, skip constraint hardening; data is still updated
        pass

    # Clean up orphaned XMLID created in earlier versions (no longer shipped)
    try:
        env['ir.model.data'].search([
            ('module', '=', 'ptt_business_core'),
            ('name', '=', 'product_event_kickoff_social_product_variant'),
        ]).unlink()
    except Exception:
        # Best-effort cleanup; shouldn't block install/upgrade
        pass

    # Identify the main kickoff product
    kickoff = Product.search([
        ('type', '=', 'service'),
        ('active', '=', True),
        ('sale_ok', '=', True),
        '|',
        ('default_code', 'in', ['EVENT-KICKOFF', 'EVENT-KICKOFF-STD']),
        ('name', 'ilike', 'Event Kickoff'),
    ], limit=1)

    # Legacy variants to archive
    legacy_kickoffs = Product.search([
        ('default_code', 'in', ['EVENT-KICKOFF-CORP', 'EVENT-KICKOFF-SOCL', 'EVENT-KICKOFF-WEDD'])
    ])
    if legacy_kickoffs:
        legacy_kickoffs.write({'active': False, 'sale_ok': False})

    # All other active, sellable services
    services = Product.search([
        ('type', '=', 'service'),
        ('active', '=', True),
        ('sale_ok', '=', True),
    ])
    others = services - kickoff
    if others:
        others.write({
            'service_tracking': 'task_in_project',
            'project_template_id': False,
            'project_id': False,
        })

    # Ensure kickoff stays project_only (don’t touch its template)
    if kickoff:
        kickoff.write({'service_tracking': 'project_only'})

    # ------------------------------------------------------------------
    # Build service task templates project and one task per service
    # ------------------------------------------------------------------
    template_project = env.ref(
        "ptt_enhanced_sales.service_task_template_project", raise_if_not_found=False
    )
    if not template_project:
        template_project = Project.create({
            "name": "Service Task Templates",
            "is_template": False,
        })
        # store XMLID for future ref lookups
        env["ir.model.data"].create({
            "name": "service_task_template_project",
            "module": "ptt_enhanced_sales",
            "model": "project.project",
            "res_id": template_project.id,
            "noupdate": True,
        })

    # Ensure one template task per service (excluding kickoff)
    for prod in others:
        exists = Task.search_count([
            ("project_id", "=", template_project.id),
            ("ptt_service_product_id", "=", prod.product_variant_id.id),
        ])
        if not exists:
            Task.create({
                "name": prod.display_name,
                "project_id": template_project.id,
                "ptt_service_product_id": prod.product_variant_id.id,
            })
