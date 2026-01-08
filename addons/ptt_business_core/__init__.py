import logging
from . import models

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """
    Pre-init cleanup: Remove orphaned/conflicting field metadata before module upgrade.
    This runs BEFORE the module upgrade to prevent errors during upgrade.
    
    NOTE: In Odoo 19, pre_init_hook receives 'cr' (database cursor), not 'env'.
    We must use raw SQL or create environment manually.
    
    Cleans up:
    1. Orphaned x_secondary_salesperson_id fields
    2. Conflicting Odoo Studio fields that have same labels as our custom fields:
       - x_studio_event_type, x_studio_event_date, x_studio_inquiry_source on crm.lead
       - x_plan2_id on project.project (conflicts with x_event_id label)
    """
    _logger.info("PTT Business Core: Running pre_init_hook cleanup")
    
    # === CLEANUP 1: Orphaned x_secondary_salesperson_id fields ===
    try:
        cr.execute("""
            DELETE FROM ir_model_fields 
            WHERE name = 'x_secondary_salesperson_id' 
            AND model IN ('project.project', 'crm.lead')
            RETURNING id
        """)
        deleted_ids = cr.fetchall()
        if deleted_ids:
            _logger.info(f"PTT Business Core: Deleted {len(deleted_ids)} orphaned x_secondary_salesperson_id field(s)")
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error cleaning x_secondary_salesperson_id: {e}")
    
    # === CLEANUP 2: Conflicting Odoo Studio fields on crm.lead ===
    # These Studio fields have same labels as our custom fields, causing registry load failure
    studio_fields_crm = [
        'x_studio_event_type',      # conflicts with x_event_type (label: Event Type)
        'x_studio_event_date',      # conflicts with x_event_date (label: Event Date)
        'x_studio_inquiry_source',  # conflicts with x_inquiry_source (label: Inquiry Source)
        'x_studio_boolean_field_297_1jckjk5dc',  # duplicate checkbox
        'x_studio_boolean_field_1vp_1jckie6sq',  # duplicate checkbox
        'x_studio_end_time_1',      # duplicate End Time
        'x_studio_end_time',        # duplicate End Time
    ]
    
    try:
        for field_name in studio_fields_crm:
            # First check if the field exists
            cr.execute("""
                SELECT id FROM ir_model_fields 
                WHERE name = %s AND model = 'crm.lead'
            """, (field_name,))
            result = cr.fetchone()
            
            if result:
                field_id = result[0]
                _logger.info(f"PTT Business Core: Removing conflicting Studio field {field_name} from crm.lead")
                
                # Delete any ir.model.data references first
                cr.execute("""
                    DELETE FROM ir_model_data 
                    WHERE model = 'ir.model.fields' AND res_id = %s
                """, (field_id,))
                
                # Delete the field definition
                cr.execute("""
                    DELETE FROM ir_model_fields WHERE id = %s
                """, (field_id,))
                
                _logger.info(f"PTT Business Core: Successfully removed {field_name}")
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error cleaning Studio fields on crm.lead: {e}")
    
    # === CLEANUP 3: Conflicting fields on project.project ===
    # x_plan2_id has same label as x_event_id (label: Event ID)
    studio_fields_project = [
        'x_plan2_id',  # conflicts with x_event_id (label: Event ID)
    ]
    
    try:
        for field_name in studio_fields_project:
            cr.execute("""
                SELECT id FROM ir_model_fields 
                WHERE name = %s AND model = 'project.project'
            """, (field_name,))
            result = cr.fetchone()
            
            if result:
                field_id = result[0]
                _logger.info(f"PTT Business Core: Removing conflicting field {field_name} from project.project")
                
                # Delete any ir.model.data references first
                cr.execute("""
                    DELETE FROM ir_model_data 
                    WHERE model = 'ir.model.fields' AND res_id = %s
                """, (field_id,))
                
                # Delete the field definition
                cr.execute("""
                    DELETE FROM ir_model_fields WHERE id = %s
                """, (field_id,))
                
                _logger.info(f"PTT Business Core: Successfully removed {field_name}")
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error cleaning fields on project.project: {e}")
    
    _logger.info("PTT Business Core: pre_init_hook cleanup completed")
    
    # === CLEANUP 4: Delete unwanted CRM stages ===
    # Delete duplicate/unwanted stages that should not exist
    unwanted_stage_names = ['Qualified', 'Quote Sent', 'Approval', 'Execution']
    try:
        for stage_name in unwanted_stage_names:
            cr.execute("""
                DELETE FROM crm_stage 
                WHERE name = %s
                AND id NOT IN (
                    SELECT res_id FROM ir_model_data 
                    WHERE model = 'crm.stage' 
                    AND module = 'crm'
                )
                RETURNING id
            """, (stage_name,))
            deleted_ids = cr.fetchall()
            if deleted_ids:
                _logger.info(f"PTT Business Core: Deleted unwanted CRM stage: {stage_name} (IDs: {[d[0] for d in deleted_ids]})")
                
                # Also delete any ir_model_data references for these deleted stages
                for stage_id_tuple in deleted_ids:
                    stage_id = stage_id_tuple[0]
                    cr.execute("""
                        DELETE FROM ir_model_data 
                        WHERE model = 'crm.stage' 
                        AND res_id = %s
                    """, (stage_id,))
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error cleaning unwanted CRM stages: {e}")
    
    # Also delete "New" stage if it exists separately from the default (should be renamed to "Intake")
    try:
        cr.execute("""
            DELETE FROM crm_stage 
            WHERE name = 'New'
            AND id NOT IN (
                SELECT res_id FROM ir_model_data 
                WHERE model = 'crm.stage' 
                AND module = 'crm'
                AND name = 'stage_lead1'
            )
            RETURNING id
        """)
        deleted_ids = cr.fetchall()
        if deleted_ids:
            _logger.info(f"PTT Business Core: Deleted duplicate 'New' stage(s) (IDs: {[d[0] for d in deleted_ids]})")
            for stage_id_tuple in deleted_ids:
                stage_id = stage_id_tuple[0]
                cr.execute("""
                    DELETE FROM ir_model_data 
                    WHERE model = 'crm.stage' 
                    AND res_id = %s
                """, (stage_id,))
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error cleaning 'New' stage: {e}")


