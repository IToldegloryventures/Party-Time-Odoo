import logging
import re
import traceback
from . import models

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Post-init hook: Clean up orphaned database objects and configure DJ variants.
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
    
    # === FIX BROKEN PROJECTS (Missing company_id or partner_id) ===
    # CRITICAL: Odoo 19 requires company_id and partner_id to prevent frontend OwlError
    # Projects without these fields will crash the Projects app
    try:
        _logger.info("PTT Business Core: Fixing projects with missing company_id or partner_id")
        _fix_broken_projects(env)
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error fixing broken projects: {e}")
        _logger.exception("PTT Business Core: Project fix failed")
    
    # === CONFIGURE VARIANT PRICING FOR ALL SERVICES ===
    # Automatically configure price_extra for all services with Event Type/Service Tier attributes
    try:
        _logger.info("PTT Business Core: Configuring variant pricing for all services")
        _configure_all_service_variants(env)
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error configuring variant pricing: {e}")
        _logger.exception("PTT Business Core: Variant pricing configuration failed")
    
    # === CONFIGURE DJ SERVICE VARIANTS ===
    # Configure DJ-specific variant fields (min_hours, guest_count, package_includes, etc.)
    try:
        _logger.info("PTT Business Core: Configuring DJ Service Variant Fields")
        _configure_dj_variants(env)
    except Exception as e:
        _logger.warning(f"PTT Business Core: Error configuring DJ variants: {e}")
        _logger.exception("PTT Business Core: DJ variant configuration failed")
    
    # NOTE: Account mappings are NOT set automatically
    # Odoo preserves existing account mappings when converting product.product → product.template
    # Accounting team should verify mappings after migration
    
    _logger.info("PTT Business Core: post_init_hook cleanup completed")


def _fix_broken_projects(env):
    """
    Fix project.project records with missing company_id or partner_id.
    
    Odoo 19 requires company_id and partner_id to prevent frontend OwlError.
    Projects without these fields will crash the Projects app.
    """
    fixed_count = 0
    
    # Fix projects missing company_id
    projects_no_company = env['project.project'].search([('company_id', '=', False)])
    if projects_no_company:
        for project in projects_no_company:
            # Set company_id from template's company or default company
            project.write({'company_id': env.company.id})
            fixed_count += 1
            _logger.info(f"PTT Business Core: Fixed project {project.name} (ID: {project.id}) - set company_id")
    
    # Fix projects missing partner_id (set to False if not available - prevents OwlError)
    projects_no_partner = env['project.project'].search([
        ('partner_id', '=', False),
        ('is_template', '=', False)  # Templates don't need partner_id
    ])
    if projects_no_partner:
        # Ensure partner_id is explicitly False (not None) for Odoo 19
        projects_no_partner.write({'partner_id': False})
        fixed_count += len(projects_no_partner)
        _logger.info(f"PTT Business Core: Fixed {len(projects_no_partner)} projects - set partner_id to False")
    
    if fixed_count > 0:
        _logger.info(f"PTT Business Core: ✅ Fixed {fixed_count} project(s) with missing company_id or partner_id")
    else:
        _logger.info("PTT Business Core: All projects already have company_id and partner_id set")


def _configure_all_service_variants(env):
    """
    Configure variant pricing (price_extra) for services with Event Type and Service Tier attributes.
    This runs automatically on module install/upgrade.
    
    Uses the same logic as the staging branch: directly sets price_extra on attribute values
    by matching attribute value names (Social, Corporate, Wedding, Essentials, Classic, Premier).
    """
    # =============================================================
    # Price Extras Configuration (from staging branch logic)
    # Matches attribute value names directly - works for all services with these attributes
    # =============================================================
    PRICE_EXTRAS = {
        # Event Type extras (from Social base)
        'Social': 0.0,
        'Corporate': 0.0,
        'Wedding': 50.0,
        # Service Tier extras (from Essential base)
        'Essentials': 0.0,
        'Classic': 125.0,
        'Premier': 300.0,
    }
    
    # Find DJ Services [UPDATED] template by XML ID (same as staging branch)
    dj_template = env.ref('ptt_business_core.product_template_dj_services', raise_if_not_found=False)
    
    total_updated = 0
    
    if dj_template:
        # Update price_extra on product.template.attribute.value records (staging branch logic)
        _logger.info(f"PTT Business Core: Configuring pricing for {dj_template.name}")
        for ptav in dj_template.attribute_line_ids.product_template_value_ids:
            attr_value_name = ptav.product_attribute_value_id.name
            if attr_value_name in PRICE_EXTRAS:
                expected_extra = PRICE_EXTRAS[attr_value_name]
                if ptav.price_extra != expected_extra:
                    ptav.write({'price_extra': expected_extra})
                    total_updated += 1
                    _logger.info(f"PTT Business Core: Set {dj_template.name} - {attr_value_name}: ${expected_extra}")
    
    if total_updated > 0:
        _logger.info(f"PTT Business Core: ✅ Updated {total_updated} price_extra values for DJ Services")
    else:
        _logger.info("PTT Business Core: ℹ️ DJ Services pricing already configured or not found")
    
    if total_updated > 0:
        _logger.info(f"PTT Business Core: ✅ Configured pricing for {len(services_configured)} service(s): {', '.join(services_configured)}")
    else:
        _logger.info("PTT Business Core: ℹ️ No services with explicit pricing configuration found. Use the wizard to configure pricing.")
    
    # Log services without configuration (check all services, not just those with config)
    services_with_config = set(services_configured)
    services_without_config = [s.name for s in services if s.name not in services_with_config]
    if services_without_config:
        _logger.info(f"PTT Business Core: ℹ️ {len(services_without_config)} service(s) without explicit pricing (defaults to $0.00): {', '.join(services_without_config)}")
        _logger.info("PTT Business Core: 💡 Use Products > Configuration > 'Configure Variant Pricing' to set pricing for these services")


def _configure_dj_variants(env):
    """
    Configure DJ service variants with variant-specific fields (min_hours, guest_count, etc.).
    This runs automatically on module install/upgrade.
    
    NOTE: Pricing (price_extra) is now handled by _configure_all_service_variants().
    """

    # =============================================================
    # STEP 2: Configure variant-specific fields
    # =============================================================

    # DJ Variant Configuration Data (from PTT_Event Pricing spreadsheet)
    # Each key is (event_type_name, tier_name) tuple
    DJ_CONFIG = {
        # === SOCIAL EVENT TIERS ===
        ('Social', 'Essentials'): {
            'min_hours': 2.0,
            'guest_min': 1,
            'guest_max': 100,
            'price_min': 300.0,
            'price_max': 400.0,
            'cost_min': 150.0,
            'cost_max': 225.0,
            'includes': '''<ul>
                <li>2 hours of music</li>
                <li>Curated playlist</li>
                <li>Basic audio setup (1-2 speakers)</li>
                <li>DJ controller</li>
                <li>Microphone</li>
            </ul>''',
        },
        ('Social', 'Classic'): {
            'min_hours': 2.0,
            'guest_min': 101,
            'guest_max': 175,
            'price_min': 425.0,
            'price_max': 600.0,
            'cost_min': 200.0,
            'cost_max': 325.0,
            'includes': '''<ul>
                <li>2 hours of music</li>
                <li>Dance floor lighting</li>
                <li>Intro announcements</li>
            </ul>''',
        },
        ('Social', 'Premier'): {
            'min_hours': 2.0,
            'guest_min': 176,
            'guest_max': 0,  # 0 = unlimited (250+)
            'price_min': 600.0,
            'price_max': 675.0,
            'cost_min': 300.0,
            'cost_max': 425.0,
            'includes': '''<ul>
                <li>2 hours of music</li>
                <li>Dance floor lighting</li>
                <li>Crowd engagement</li>
                <li>MC Services available as add-on</li>
            </ul>''',
        },
        
        # === CORPORATE EVENT TIERS ===
        ('Corporate', 'Essentials'): {
            'min_hours': 2.0,
            'guest_min': 1,
            'guest_max': 100,
            'price_min': 300.0,
            'price_max': 400.0,
            'cost_min': 150.0,
            'cost_max': 225.0,
            'includes': '''<ul>
                <li>2 hours background/dance music</li>
                <li>Announcements</li>
                <li>1-2 speakers</li>
                <li>Wireless microphone</li>
            </ul>''',
        },
        ('Corporate', 'Classic'): {
            'min_hours': 2.0,
            'guest_min': 101,
            'guest_max': 250,
            'price_min': 425.0,
            'price_max': 600.0,
            'cost_min': 200.0,
            'cost_max': 325.0,
            'includes': '''<ul>
                <li>2 hours networking + dance mix</li>
                <li>Dance lights</li>
                <li>Professional DJ services</li>
                <li>MC Services available as add-on</li>
            </ul>''',
        },
        ('Corporate', 'Premier'): {
            'min_hours': 2.0,
            'guest_min': 251,
            'guest_max': 500,
            'price_min': 600.0,
            'price_max': 675.0,
            'cost_min': 300.0,
            'cost_max': 425.0,
            'includes': '''<ul>
                <li>2 hours DJ performance</li>
                <li>Scripted MC services</li>
                <li>Stage presence</li>
                <li>Walk-on music</li>
            </ul>''',
        },
        
        # === WEDDING EVENT TIERS ===
        ('Wedding', 'Essentials'): {
            'min_hours': 3.0,  # Weddings require more hours
            'guest_min': 50,
            'guest_max': 350,
            'price_min': 350.0,
            'price_max': 450.0,
            'cost_min': 200.0,
            'cost_max': 300.0,
            'includes': '''<ul>
                <li>3 hours ceremony or reception</li>
                <li>Curated music selection</li>
                <li>Lav/handheld microphone</li>
            </ul>''',
        },
        ('Wedding', 'Classic'): {
            'min_hours': 4.0,
            'guest_min': 101,
            'guest_max': 250,
            'price_min': 475.0,
            'price_max': 625.0,
            'cost_min': 250.0,
            'cost_max': 350.0,
            'includes': '''<ul>
                <li>4 hours reception coverage</li>
                <li>Professional DJ services</li>
                <li>Dance floor lights</li>
                <li>Wireless microphone</li>
                <li>MC Services available as add-on</li>
            </ul>''',
        },
        ('Wedding', 'Premier'): {
            'min_hours': 5.0,
            'guest_min': 251,
            'guest_max': 500,
            'price_min': 650.0,
            'price_max': 700.0,
            'cost_min': 300.0,
            'cost_max': 450.0,
            'includes': '''<ul>
                <li>5 hours ceremony and reception</li>
                <li>Scripted MC services</li>
                <li>Dance floor lighting</li>
                <li>Subwoofer for enhanced bass</li>
                <li>Wireless microphone</li>
            </ul>''',
        },
    }

    if not dj_template:
        _logger.warning("PTT Business Core: DJ & MC Services template not found. Skipping variant configuration.")
        return

    configured_count = 0
    for variant in dj_template.product_variant_ids:
        # Extract attribute values from variant
        attr_values = variant.product_template_attribute_value_ids
        event_type = None
        tier = None
        
        for av in attr_values:
            if av.attribute_id.name == 'Event Type':
                event_type = av.name
            elif av.attribute_id.name == 'Service Tier':
                tier = av.name
        
        # Look up configuration
        key = (event_type, tier)
        if key in DJ_CONFIG:
            config = DJ_CONFIG[key]
            variant.write({
                'ptt_min_hours': config['min_hours'],
                'ptt_guest_count_min': config['guest_min'],
                'ptt_guest_count_max': config['guest_max'],
                'ptt_price_per_hour_min': config['price_min'],
                'ptt_price_per_hour_max': config['price_max'],
                'ptt_cost_per_hour_min': config['cost_min'],
                'ptt_cost_per_hour_max': config['cost_max'],
                'ptt_package_includes': config['includes'],
            })
            configured_count += 1

    _logger.info(f"PTT Business Core: Successfully configured {configured_count} DJ service variants")


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
