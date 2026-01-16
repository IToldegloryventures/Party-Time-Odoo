"""
Pre-migration script to remove conflicting Odoo Studio fields.

This fixes the "Two fields have the same label" error that prevents registry loading.
Conflicting fields (created via Odoo Studio) have the same labels as our custom module fields:
- x_studio_event_type vs x_event_type (label: Event Type) on crm.lead
- x_studio_event_date vs x_event_date (label: Event Date) on crm.lead
- x_studio_inquiry_source vs x_inquiry_source (label: Inquiry Source) on crm.lead
- x_plan2_id vs x_event_id (label: Event ID) on project.project
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Remove conflicting Studio fields before module upgrade."""
    _logger.info("PTT Business Core v19.0.1.2.1: Running pre-migration cleanup")
    
    # === CLEANUP 1: Conflicting Odoo Studio fields on crm.lead ===
    studio_fields_crm = [
        'x_studio_event_type',      # conflicts with x_event_type (label: Event Type)
        'x_studio_event_date',      # conflicts with x_event_date (label: Event Date)
        'x_studio_inquiry_source',  # conflicts with x_inquiry_source (label: Inquiry Source)
        'x_studio_boolean_field_297_1jckjk5dc',  # duplicate checkbox
        'x_studio_boolean_field_1vp_1jckie6sq',  # duplicate checkbox
        'x_studio_end_time_1',      # duplicate End Time
        'x_studio_end_time',        # duplicate End Time
    ]
    
    for field_name in studio_fields_crm:
        try:
            # Check if the field exists
            cr.execute("""
                SELECT id FROM ir_model_fields 
                WHERE name = %s AND model = 'crm.lead'
            """, (field_name,))
            result = cr.fetchone()
            
            if result:
                field_id = result[0]
                _logger.info(f"Removing conflicting field {field_name} from crm.lead (id={field_id})")
                
                # Delete any ir.model.data references first
                cr.execute("""
                    DELETE FROM ir_model_data 
                    WHERE model = 'ir.model.fields' AND res_id = %s
                """, (field_id,))
                
                # Delete the field definition
                cr.execute("""
                    DELETE FROM ir_model_fields WHERE id = %s
                """, (field_id,))
                
                _logger.info(f"Successfully removed {field_name} from crm.lead")
        except Exception as e:
            _logger.warning(f"Error removing {field_name} from crm.lead: {e}")
    
    # === CLEANUP 2: Conflicting fields on project.project ===
    studio_fields_project = [
        'x_plan2_id',  # conflicts with x_event_id (label: Event ID)
    ]
    
    for field_name in studio_fields_project:
        try:
            cr.execute("""
                SELECT id FROM ir_model_fields 
                WHERE name = %s AND model = 'project.project'
            """, (field_name,))
            result = cr.fetchone()
            
            if result:
                field_id = result[0]
                _logger.info(f"Removing conflicting field {field_name} from project.project (id={field_id})")
                
                # Delete any ir.model.data references first
                cr.execute("""
                    DELETE FROM ir_model_data 
                    WHERE model = 'ir.model.fields' AND res_id = %s
                """, (field_id,))
                
                # Delete the field definition
                cr.execute("""
                    DELETE FROM ir_model_fields WHERE id = %s
                """, (field_id,))
                
                _logger.info(f"Successfully removed {field_name} from project.project")
        except Exception as e:
            _logger.warning(f"Error removing {field_name} from project.project: {e}")
    
    # === CLEANUP 3: Orphaned x_secondary_salesperson_id fields ===
    try:
        cr.execute("""
            DELETE FROM ir_model_fields 
            WHERE name = 'x_secondary_salesperson_id' 
            AND model IN ('project.project', 'crm.lead')
            RETURNING id
        """)
        deleted_ids = cr.fetchall()
        if deleted_ids:
            _logger.info(f"Deleted {len(deleted_ids)} orphaned x_secondary_salesperson_id field(s)")
    except Exception as e:
        _logger.warning(f"Error cleaning x_secondary_salesperson_id: {e}")
    
    _logger.info("PTT Business Core v19.0.1.2.1: Pre-migration cleanup completed")
