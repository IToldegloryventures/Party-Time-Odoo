#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script to verify Odoo shell can connect and access the database
"""
import sys
import os

# Add odoo to path
sys.path.insert(0, 'odoo')

try:
    import odoo
    from odoo import api, SUPERUSER_ID
    
    # Initialize Odoo environment
    odoo.tools.config.parse_config(['-c', 'odoo.conf'])
    
    # Create database connection
    db_name = 'test_nofs'
    
    with odoo.api.Environment.manage():
        registry = odoo.registry(db_name)
        with registry.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            
            # Test database access
            users = env['res.users'].search([])
            print(f'✓ Odoo shell connection successful!')
            print(f'✓ Found {len(users)} users in database')
            print(f'✓ Database: {db_name}')
            print(f'✓ Environment ready for shell commands')
            
            # Test a simple query
            admin_user = env['res.users'].search([('login', '=', 'admin')], limit=1)
            if admin_user:
                print(f'✓ Admin user found: {admin_user.name}')
            
except Exception as e:
    print(f'✗ Error: {e}')
    import traceback
    traceback.print_exc()
