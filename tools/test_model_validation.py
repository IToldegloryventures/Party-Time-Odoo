#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test model validation for ptt_business_core and ptt_vendor_management
This script loads Odoo and validates the models to find actual errors.
"""
import sys
import os

# Add Odoo to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'odoo'))

# Set up minimal Odoo environment
os.environ.setdefault('ODOO_RC', '/dev/null')

try:
    import odoo
    from odoo import api, SUPERUSER_ID
    from odoo.tools import config
    
    # Configure Odoo
    config['addons_path'] = 'addons,odoo/addons'
    config['without_demo'] = True
    config['test_enable'] = False
    
    # Initialize Odoo
    odoo.tools.config.parse_config(['--addons-path=addons,odoo/addons', '--without-demo=all'])
    
    # Register models
    odoo.modules.registry.Registry.new('test_db')
    
    print("=" * 80)
    print("MODEL VALIDATION TEST")
    print("=" * 80)
    
    # Test each model
    models_to_test = [
        ('project.project', 'ptt_business_core'),
        ('project.task', 'ptt_business_core'),
        ('purchase.order', 'ptt_business_core'),
        ('ptt.vendor.rfq', 'ptt_vendor_management'),
    ]
    
    errors_found = []
    
    for model_name, module_name in models_to_test:
        print(f"\n{'='*80}")
        print(f"Testing: {model_name} (from {module_name})")
        print(f"{'='*80}")
        
        try:
            # Try to get the model
            env = odoo.api.Environment(odoo.registry('test_db'), SUPERUSER_ID, {})
            model = env.get(model_name)
            
            if model is None:
                errors_found.append(f"{model_name}: Model not found")
                print(f"  ❌ ERROR: Model '{model_name}' not found")
                continue
            
            print(f"  ✅ Model found: {model._name}")
            
            # Check for ptt_event_id field
            if 'ptt_event_id' in model._fields:
                field = model._fields['ptt_event_id']
                print(f"  ✅ Field 'ptt_event_id' exists")
                print(f"     - Type: {field.type}")
                print(f"     - Related: {getattr(field, 'related', 'N/A')}")
                print(f"     - Store: {getattr(field, 'store', False)}")
                print(f"     - Index: {getattr(field, 'index', False)}")
                
                # Check if related field path is valid
                if hasattr(field, 'related') and field.related:
                    related_path = field.related
                    print(f"     - Related path: {related_path}")
                    
                    # Validate related path
                    try:
                        # Try to access the related field
                        test_record = model.browse([1]) if model.search([], limit=1) else None
                        if test_record:
                            try:
                                value = test_record[0].ptt_event_id
                                print(f"     - ✅ Related path is accessible")
                            except Exception as e:
                                errors_found.append(f"{model_name}.ptt_event_id: Related path error - {str(e)}")
                                print(f"     - ❌ ERROR accessing related path: {e}")
                    except Exception as e:
                        print(f"     - ⚠️  Could not test related path (no records): {e}")
            else:
                errors_found.append(f"{model_name}: Field 'ptt_event_id' not found")
                print(f"  ❌ ERROR: Field 'ptt_event_id' not found in model")
            
        except Exception as e:
            errors_found.append(f"{model_name}: {str(e)}")
            print(f"  ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    
    if errors_found:
        print(f"\n❌ ERRORS FOUND ({len(errors_found)}):")
        for error in errors_found:
            print(f"  - {error}")
    else:
        print("\n✅ No errors found - all models validated successfully!")
    
except ImportError as e:
    print(f"ERROR: Could not import Odoo: {e}")
    print("\nTrying alternative validation method...")
    
    # Alternative: Direct Python validation
    import ast
    import re
    
    files_to_check = [
        'addons/ptt_business_core/models/project_project.py',
        'addons/ptt_business_core/models/project_task.py',
        'addons/ptt_business_core/models/purchase_order.py',
        'addons/ptt_vendor_management/models/ptt_vendor_rfq.py',
    ]
    
    print("\n" + "=" * 80)
    print("ALTERNATIVE: AST VALIDATION")
    print("=" * 80)
    
    for file_path in files_to_check:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if not os.path.exists(full_path):
            print(f"\n❌ File not found: {file_path}")
            continue
        
        print(f"\nChecking: {file_path}")
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content, filename=file_path)
            
            # Check for related fields with index=True
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr in ['Char', 'Date', 'Many2one', 'Integer', 'Float']:
                        # Check if this is a related field with index=True
                        has_related = False
                        has_store = False
                        has_index = False
                        
                        for keyword in node.keywords:
                            if keyword.arg == 'related':
                                has_related = True
                            elif keyword.arg == 'store' and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                                has_store = True
                            elif keyword.arg == 'index' and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                                has_index = True
                        
                        if has_related and has_store and has_index:
                            print(f"  ⚠️  WARNING: Related field with store=True and index=True found")
                            print(f"     Location: Line {node.lineno}")
                            print(f"     Recommendation: Remove index=True (Odoo indexes stored fields automatically)")
            
            print(f"  ✅ Syntax valid")
            
        except SyntaxError as e:
            print(f"  ❌ Syntax error: {e}")
        except Exception as e:
            print(f"  ❌ Error: {e}")
