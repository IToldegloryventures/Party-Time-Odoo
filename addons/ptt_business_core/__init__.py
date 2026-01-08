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
    
    # === CLEANUP 4: DELETE unwanted CRM stages (don't fold, actually delete them) ===
    # Delete all unwanted duplicate stages completely
    # ONLY keep: Intake, Qualification, Approval, Proposal Sent, Contract Sent, Booked, Closed/Won, Lost
    wanted_stage_names = ['Intake', 'Qualification', 'Approval', 'Proposal Sent', 'Contract Sent', 'Booked', 'Closed/Won', 'Lost']
    unwanted_stage_names = ['Qualified', 'Quote Sent', 'Execution', 'New', 'Proposition']
    try:
        # First, get IDs of stages to delete (but keep the default Odoo stages we're renaming)
        for stage_name in unwanted_stage_names:
            # Get all stages with this name
            cr.execute("""
                SELECT id FROM crm_stage WHERE name = %s
            """, (stage_name,))
            stage_ids = [row[0] for row in cr.fetchall()]
            
            if not stage_ids:
                continue
                
            # Get default Odoo stage IDs that we're renaming (don't delete these)
            cr.execute("""
                SELECT res_id FROM ir_model_data 
                WHERE model = 'crm.stage' 
                AND module = 'crm'
                AND name IN ('stage_lead1', 'stage_lead2', 'stage_lead3', 'stage_lead4')
            """)
            default_stage_ids = [row[0] for row in cr.fetchall()]
            
            # Delete stages that are NOT the default Odoo stages
            stages_to_delete = [sid for sid in stage_ids if sid not in default_stage_ids]
            
            if stages_to_delete:
                # Move any leads/opportunities in these stages to "Intake" stage first
                # Find or create "Intake" stage
                cr.execute("""
                    SELECT id FROM crm_stage 
                    WHERE name = 'Intake' 
                    ORDER BY id LIMIT 1
                """)
                intake_stage = cr.fetchone()
                if not intake_stage:
                    # If Intake doesn't exist, use the first default stage
                    cr.execute("""
                        SELECT res_id FROM ir_model_data 
                        WHERE model = 'crm.stage' 
                        AND module = 'crm'
                        AND name = 'stage_lead1'
                    """)
                    intake_stage = cr.fetchone()
                
                if intake_stage:
                    intake_stage_id = intake_stage[0]
                    # Move leads from deleted stages to Intake
                    cr.execute("""
                        UPDATE crm_lead 
                        SET stage_id = %s 
                        WHERE stage_id = ANY(%s)
                    """, (intake_stage_id, stages_to_delete))
                
                # Delete ir_model_data references first
                cr.execute("""
                    DELETE FROM ir_model_data 
                    WHERE model = 'crm.stage' 
                    AND res_id = ANY(%s)
                """, (stages_to_delete,))
                
                # Now delete the stages themselves
                cr.execute("""
                    DELETE FROM crm_stage 
                    WHERE id = ANY(%s)
                """, (stages_to_delete,))
                
                _logger.info(f"PTT Business Core: Deleted {len(stages_to_delete)} unwanted CRM stage(s): {stage_name} (IDs: {stages_to_delete})")
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error cleaning unwanted CRM stages: {e}")
        import traceback
        _logger.error(traceback.format_exc())


