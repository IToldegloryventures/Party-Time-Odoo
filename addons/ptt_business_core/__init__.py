# -*- coding: utf-8 -*-
# Part of Party Time Texas Event Management System

from . import models


def _register_field_xmlids(env):
    """
    Register XML IDs for custom fields so they can be referenced by other modules.
    
    Odoo auto-creates ir.model.fields records for Python-defined fields,
    but doesn't always assign XML IDs that other modules can use via ref().
    
    This function creates ir.model.data entries that link our custom field
    names to their ir.model.fields records.
    """
    IrModelData = env['ir.model.data']
    IrModelFields = env['ir.model.fields']
    
    # Fields that need XML ID registration for ptt_dashboard
    fields_to_register = [
        # (model, field_name, xml_id_name)
        ('project.project', 'ptt_event_date', 'field_project_project__ptt_event_date'),
    ]
    
    for model_name, field_name, xml_id_name in fields_to_register:
        # Find the existing ir.model.fields record
        field_record = IrModelFields.search([
            ('model', '=', model_name),
            ('name', '=', field_name)
        ], limit=1)
        
        if field_record:
            # Check if XML ID already exists
            existing = IrModelData.search([
                ('module', '=', 'ptt_business_core'),
                ('name', '=', xml_id_name)
            ], limit=1)
            
            if not existing:
                # Create the XML ID reference
                IrModelData.create({
                    'module': 'ptt_business_core',
                    'name': xml_id_name,
                    'model': 'ir.model.fields',
                    'res_id': field_record.id,
                    'noupdate': True,
                })


def post_init_hook(env):
    """Post-installation hook to set up field XML IDs."""
    _register_field_xmlids(env)
