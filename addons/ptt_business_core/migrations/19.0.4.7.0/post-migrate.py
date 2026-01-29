from odoo import SUPERUSER_ID, api


def _unlink_records(env, model, xmlids):
    for xid in xmlids:
        rec = env.ref(xid, raise_if_not_found=False)
        if rec:
            rec.unlink()


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # Remove deprecated project templates and their tasks
    deprecated_templates = [
        "ptt_business_core.project_template_corporate",
        "ptt_business_core.project_template_wedding",
        "project.project_template_corporate",  # fallback if renamed upstream
        "project.project_template_wedding",
    ]
    for xid in deprecated_templates:
        template = env.ref(xid, raise_if_not_found=False)
        if template:
            env["project.task"].search([("project_id", "=", template.id)]).unlink()
            template.unlink()

    # Remove kickoff products linked to removed templates
    _unlink_records(
        env,
        "product.template",
        [
            "ptt_business_core.product_event_kickoff_corporate",
            "ptt_business_core.product_event_kickoff_wedding",
        ],
    )

    # Repoint sale order types to the remaining Social template.
    social_template = env.ref(
        "ptt_business_core.project_template_social", raise_if_not_found=False
    )
    if social_template:
        env.cr.execute(
            """
            UPDATE sale_order_type
            SET project_template_id = %s
            WHERE project_template_id IS NULL
               OR project_template_id NOT IN (
                   SELECT id FROM project_project WHERE is_template = TRUE
               )
            """,
            (social_template.id,),
        )
    else:
        # If social template somehow missing, just clear broken links.
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

    # Ensure the canonical To Do stage exists (idempotent safeguard).
    todo = env.ref(
        "ptt_business_core.task_stage_todo_default", raise_if_not_found=False
    )
    if not todo:
        todo = env["project.task.type"].create({"name": "To Do", "sequence": 1})
        env["ir.model.data"].create(
            {
                "name": "task_stage_todo_default",
                "model": "project.task.type",
                "module": "ptt_business_core",
                "res_id": todo.id,
                "noupdate": True,
            }
        )
