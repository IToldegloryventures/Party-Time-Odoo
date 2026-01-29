from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Remove deprecated templates (corporate, wedding, social) and their tasks.
    for xid in [
        "ptt_business_core.project_template_corporate",
        "ptt_business_core.project_template_wedding",
        "ptt_business_core.project_template_social",
        "project.project_template_corporate",
        "project.project_template_wedding",
    ]:
        template = env.ref(xid, raise_if_not_found=False)
        if template:
            env["project.task"].search([("project_id", "=", template.id)]).unlink()
            template.unlink()

    # Remove deprecated kickoff products.
    for xid in [
        "ptt_business_core.product_event_kickoff_corporate",
        "ptt_business_core.product_event_kickoff_wedding",
        "ptt_business_core.product_event_kickoff_social",
    ]:
        product = env.ref(xid, raise_if_not_found=False)
        if product:
            product.unlink()

    # Ensure the Standard template exists (loaded from data).
    standard_template = env.ref(
        "ptt_business_core.project_template_standard", raise_if_not_found=False
    )

    # Repoint sale order types to the Standard template (or clear if missing).
    if standard_template:
        env.cr.execute(
            """
            UPDATE sale_order_type
               SET project_template_id = %s
             WHERE project_template_id IS NULL
                OR project_template_id NOT IN (
                    SELECT id FROM project_project WHERE is_template = TRUE
                )
            """,
            (standard_template.id,),
        )
    else:
        env.cr.execute(
            """
            UPDATE sale_order_type
               SET project_template_id = NULL
             WHERE project_template_id IS NOT NULL
               AND project_template_id NOT IN (
                   SELECT id FROM project_project WHERE is_template = TRUE
               )
            """
        )
