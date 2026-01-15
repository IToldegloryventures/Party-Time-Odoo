import logging
import re
import traceback
from . import models

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Post-init hook: Clean up orphaned database objects.
    Runs AFTER the module is installed with full ORM/env access.
    """
    _logger.info("PTT Business Core: Running post_init_hook cleanup")
    
    # Clean up any orphaned views referencing deleted fields
    try:
        deleted_fields = [
            'x_plan2_id', 'x_days_until_event', 'x_target_margin', 'x_target_margin_price',
            'x_contract_status', 'x_contract_signed_date', 'x_crm_lead_id', 'x_sales_rep_id',
            'x_event_name', 'x_sale_order_count', 'x_lead_type', 'x_inquiry_source',
            'x_followup_email_sent', 'x_proposal_sent', 'x_next_contact_date', 'x_budget_range',
            'x_services_already_booked', 'x_project_id', 'x_invoice_count', 'x_invoice_total',
            'x_invoice_paid', 'x_invoice_remaining', 'x_invoice_payment_status',
            'x_has_project', 'x_project_task_count', 'company_currency',
            'x_project_event_id', 'x_project_event_name', 'x_project_event_date', 'x_project_event_time',
            'x_project_event_type', 'x_project_venue', 'x_project_client_name', 'x_project_guest_count',
            'x_project_crm_lead_id', 'x_project_sales_rep_id', 'x_is_event_task',
        ]
        
        for field_name in deleted_fields:
            views_to_fix = env['ir.ui.view'].sudo().search([
                ('arch_db', 'ilike', field_name)
            ])
            for view in views_to_fix:
                try:
                    if view.arch_db:
                        new_arch = view.arch_db
                        new_arch = re.sub(rf'<field[^>]*name=["\']{ field_name}["\'][^/>]*/?>', '', new_arch)
                        new_arch = re.sub(rf'<field[^>]*name=["\']{ field_name}["\'][^>]*>.*?</field>', '', new_arch, flags=re.DOTALL)
                        new_arch = re.sub(rf'<label[^>]*for=["\']{ field_name}["\'][^/>]*/?>', '', new_arch)
                        if new_arch != view.arch_db:
                            view.sudo().write({'arch_db': new_arch})
                            _logger.info(f"PTT Business Core: Cleaned {field_name} from view {view.id}")
                except Exception as e:
                    _logger.warning(f"PTT Business Core: Error cleaning view {view.id}: {e}")
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error in post_init_hook: {e}")
    
    _logger.info("PTT Business Core: post_init_hook cleanup completed")


def pre_init_hook(cr):
    """
    Pre-init cleanup: Remove orphaned/conflicting field metadata before module upgrade.
    Runs BEFORE the module upgrade to prevent errors during upgrade.
    
    NOTE: In Odoo 19, pre_init_hook receives 'cr' (database cursor), not 'env'.
    
    Odoo 19 Guideline Compliance:
    - Uses savepoints to isolate operations for better error handling
    - Does NOT call cr.commit() or cr.rollback() manually
    - Framework handles transaction commits at RPC boundaries
    Reference: https://www.odoo.com/documentation/19.0/developer/howtos/backend.html#database-cursor-and-transactions
    """
    from psycopg2 import ProgrammingError, DatabaseError
    
    _logger.info("PTT Business Core: Running pre_init_hook cleanup")
    
    # === COMPREHENSIVE FIELD CLEANUP ===
    # All fields that were removed from the codebase
    fields_to_remove = {
        'sale.order': ['x_contract_status', 'x_contract_signed_date'],
        'sale.order.line': ['x_target_margin', 'x_target_margin_price'],
        'project.project': [
            'x_crm_lead_id', 'x_sales_rep_id', 'x_event_name', 'x_contract_status',
            'x_sale_order_count', 'x_plan2_id', 'x_days_until_event',
        ],
        'project.task': [
            'x_project_event_id', 'x_project_event_name', 'x_project_event_date',
            'x_project_event_time', 'x_project_event_type', 'x_project_venue',
            'x_project_client_name', 'x_project_guest_count', 'x_project_crm_lead_id',
            'x_project_sales_rep_id', 'x_is_event_task', 'x_days_until_event',
        ],
        'crm.lead': [
            'x_lead_type', 'x_inquiry_source', 'x_event_name', 'x_followup_email_sent',
            'x_proposal_sent', 'x_next_contact_date', 'x_budget_range', 'x_services_already_booked',
            'x_project_id', 'x_invoice_count', 'x_invoice_total', 'x_invoice_paid',
            'x_invoice_remaining', 'x_invoice_payment_status', 'x_has_project',
            'x_project_task_count', 'company_currency',
        ],
        'res.partner': [],
    }
    
    # Use savepoint to isolate each field deletion operation
    for model, field_names in fields_to_remove.items():
        for field_name in field_names:
            with cr.savepoint():
                try:
                    cr.execute("""
                        SELECT id FROM ir_model_fields 
                        WHERE name = %s AND model = %s
                    """, (field_name, model))
                    result = cr.fetchone()
                    if result:
                        field_id = result[0]
                        _logger.info(f"PTT Business Core: Removing field {field_name} from {model}")
                        cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.model.fields' AND res_id = %s", (field_id,))
                        cr.execute("DELETE FROM ir_model_fields WHERE id = %s", (field_id,))
                except (ProgrammingError, DatabaseError) as e:
                    _logger.warning(f"PTT Business Core: Error removing {field_name} from {model}: {e}")
                except Exception as e:
                    _logger.warning(f"PTT Business Core: Unexpected error removing {field_name} from {model}: {e}")
    
    # === CLEANUP VIEWS REFERENCING DELETED FIELDS ===
    all_deleted_fields = []
    for field_list in fields_to_remove.values():
        all_deleted_fields.extend(field_list)
    
    # Use savepoint to isolate each field's view cleanup operation
    for field_name in all_deleted_fields:
        with cr.savepoint():
            try:
                # Clean ir_ui_view (arch_db)
                cr.execute("""
                    SELECT id, arch_db FROM ir_ui_view 
                    WHERE arch_db::text LIKE %s
                """, (f'%{field_name}%',))
                views_to_fix = cr.fetchall()
                for view_id, arch_db in views_to_fix:
                    if arch_db:
                        new_arch = str(arch_db)
                        new_arch = re.sub(rf'<field[^>]*name=["\']{ field_name}["\'][^/>]*/?>', '', new_arch)
                        new_arch = re.sub(rf'<field[^>]*name=["\']{ field_name}["\'][^>]*>.*?</field>', '', new_arch, flags=re.DOTALL)
                        new_arch = re.sub(rf'<label[^>]*for=["\']{ field_name}["\'][^/>]*/?>', '', new_arch)
                        new_arch = re.sub(rf'<button[^>]*invisible="[^"]*{ field_name}[^"]*"[^>]*>.*?</button>', '', new_arch, flags=re.DOTALL)
                        new_arch = re.sub(rf'<div[^>]*invisible="[^"]*{ field_name}[^"]*"[^>]*>.*?</div>', '', new_arch, flags=re.DOTALL)
                        if new_arch != str(arch_db):
                            cr.execute("UPDATE ir_ui_view SET arch_db = %s WHERE id = %s", (new_arch, view_id))
                            _logger.info(f"PTT Business Core: Cleaned {field_name} from view {view_id}")
                
                # Clean ir_ui_view_custom (Studio customizations)
                cr.execute("""
                    SELECT id, arch FROM ir_ui_view_custom 
                    WHERE arch::text LIKE %s
                """, (f'%{field_name}%',))
                custom_views_to_fix = cr.fetchall()
                for view_id, arch in custom_views_to_fix:
                    if arch:
                        new_arch = str(arch)
                        new_arch = re.sub(rf'<field[^>]*name=["\']{ field_name}["\'][^/>]*/?>', '', new_arch)
                        new_arch = re.sub(rf'<field[^>]*name=["\']{ field_name}["\'][^>]*>.*?</field>', '', new_arch, flags=re.DOTALL)
                        new_arch = re.sub(rf'<label[^>]*for=["\']{ field_name}["\'][^/>]*/?>', '', new_arch)
                        new_arch = re.sub(rf'<button[^>]*invisible="[^"]*{ field_name}[^"]*"[^>]*>.*?</button>', '', new_arch, flags=re.DOTALL)
                        new_arch = re.sub(rf'<div[^>]*invisible="[^"]*{ field_name}[^"]*"[^>]*>.*?</div>', '', new_arch, flags=re.DOTALL)
                        if new_arch != str(arch):
                            cr.execute("UPDATE ir_ui_view_custom SET arch = %s WHERE id = %s", (new_arch, view_id))
                            _logger.info(f"PTT Business Core: Cleaned {field_name} from custom view {view_id}")
            except (ProgrammingError, DatabaseError) as e:
                _logger.warning(f"PTT Business Core: Database error cleaning views for {field_name}: {e}")
            except Exception as e:
                _logger.warning(f"PTT Business Core: Unexpected error cleaning views for {field_name}: {e}")
    
    # === DELETE PTT VIEWS THAT MAY HAVE STALE REFERENCES ===
    ptt_view_names = [
        ('ptt_business_core', 'view_sale_order_form_ptt'),
        ('ptt_business_core', 'view_sale_order_form_line_ptt'),
        ('ptt_business_core', 'view_crm_lead_form_ptt'),
        ('ptt_business_core', 'view_project_form_ptt'),
        ('ptt_business_core', 'view_task_form_ptt'),
        ('ptt_business_core', 'view_partner_form_ptt'),
    ]
    
    # Use savepoint to isolate each view deletion operation
    for module, view_name in ptt_view_names:
        with cr.savepoint():
            try:
                cr.execute("""
                    SELECT v.id FROM ir_ui_view v
                    JOIN ir_model_data d ON d.res_id = v.id AND d.model = 'ir.ui.view'
                    WHERE d.module = %s AND d.name = %s
                """, (module, view_name))
                result = cr.fetchone()
                if result:
                    view_id = result[0]
                    cr.execute("DELETE FROM ir_ui_view WHERE id = %s", (view_id,))
                    cr.execute("DELETE FROM ir_model_data WHERE module = %s AND name = %s", (module, view_name))
                    _logger.info(f"PTT Business Core: Deleted stale view {module}.{view_name}")
            except (ProgrammingError, DatabaseError) as e:
                _logger.warning(f"PTT Business Core: Database error deleting view {module}.{view_name}: {e}")
            except Exception as e:
                _logger.warning(f"PTT Business Core: Unexpected error deleting view {module}.{view_name}: {e}")
    
    # === CLEANUP STUDIO FIELDS ===
    studio_fields = [
        ('crm.lead', 'x_studio_event_type'),
        ('crm.lead', 'x_studio_event_date'),
        ('crm.lead', 'x_studio_inquiry_source'),
        ('crm.lead', 'x_studio_boolean_field_297_1jckjk5dc'),
        ('crm.lead', 'x_studio_boolean_field_1vp_1jckie6sq'),
        ('crm.lead', 'x_studio_end_time_1'),
        ('crm.lead', 'x_studio_end_time'),
        ('project.project', 'x_plan2_id'),
    ]
    
    # Use savepoint to isolate each Studio field deletion operation
    for model, field_name in studio_fields:
        with cr.savepoint():
            try:
                cr.execute("""
                    SELECT id FROM ir_model_fields 
                    WHERE name = %s AND model = %s
                """, (field_name, model))
                result = cr.fetchone()
                if result:
                    field_id = result[0]
                    _logger.info(f"PTT Business Core: Removing Studio field {field_name} from {model}")
                    cr.execute("DELETE FROM ir_model_data WHERE model = 'ir.model.fields' AND res_id = %s", (field_id,))
                    cr.execute("DELETE FROM ir_model_fields WHERE id = %s", (field_id,))
            except (ProgrammingError, DatabaseError) as e:
                _logger.warning(f"PTT Business Core: Database error removing Studio field {field_name}: {e}")
            except Exception as e:
                _logger.warning(f"PTT Business Core: Unexpected error removing Studio field {field_name}: {e}")
    
    _logger.info("PTT Business Core: pre_init_hook cleanup completed")
