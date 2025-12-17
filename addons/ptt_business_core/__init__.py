from . import models


def post_init_hook(env):
    """
    Cleanup orphaned field metadata for x_secondary_salesperson_id.
    This field was removed from the codebase but may still exist in ir.model.fields,
    causing SQL errors when Odoo tries to read it.
    """
    # Find and delete orphaned field records
    FieldModel = env['ir.model.fields']
    orphaned_fields = FieldModel.search([
        ('name', '=', 'x_secondary_salesperson_id'),
        ('model', 'in', ['project.project', 'crm.lead'])
    ])
    if orphaned_fields:
        orphaned_fields.unlink()
        env.cr.commit()


