import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """
    Pre-migration script to remove orphaned sales rep field definitions.
    These fields were removed from code but their definitions still exist in ir_model_fields,
    causing Odoo to try to query columns that don't exist.
    """
    _logger.info("PTT Business Core 19.0.1.2.2: Cleaning up orphaned sales rep field definitions")

    # Remove orphaned field definitions from ir_model_fields
    # These fields no longer exist in code but their registry entries remain
    orphaned_fields = [
        ('x_primary_sales_rep_id', 'res.partner'),
        ('x_secondary_sales_rep_id', 'res.partner'),
        ('x_secondary_sales_rep_id', 'crm.lead'),
    ]

    for field_name, model_name in orphaned_fields:
        try:
            cr.execute("""
                SELECT id FROM ir_model_fields 
                WHERE name = %s AND model = %s
            """, (field_name, model_name))
            result = cr.fetchone()

            if result:
                field_id = result[0]
                _logger.info(f"Removing orphaned field {field_name} from {model_name} (id={field_id})")
                
                # Delete ir.model.data references first
                cr.execute("""
                    DELETE FROM ir_model_data 
                    WHERE model = 'ir.model.fields' AND res_id = %s
                """, (field_id,))
                
                # Delete the field definition
                cr.execute("""
                    DELETE FROM ir_model_fields WHERE id = %s
                """, (field_id,))
                
                _logger.info(f"Successfully removed {field_name} from {model_name}")
        except Exception as e:
            _logger.warning(f"Error removing {field_name} from {model_name}: {e}")

    _logger.info("PTT Business Core 19.0.1.2.2: Pre-migration cleanup completed")
