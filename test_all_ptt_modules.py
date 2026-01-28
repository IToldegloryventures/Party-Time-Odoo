#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive test for ALL PTT modules
Tests: ptt_business_core, ptt_dashboard, ptt_enhanced_sales, ptt_project_management, ptt_vendor_management
"""
import sys
import os
import re

# Add Odoo to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'odoo'))

print("=" * 80)
print("COMPREHENSIVE PTT MODULES VALIDATION - ALL 5 MODULES")
print("=" * 80)

# All PTT modules to test
PTT_MODULES = [
    'ptt_business_core',
    'ptt_dashboard',
    'ptt_enhanced_sales',
    'ptt_project_management',
    'ptt_vendor_management',
]

results = {}

# Test each module
for module_name in PTT_MODULES:
    print(f"\n{'='*80}")
    print(f"TESTING MODULE: {module_name.upper()}")
    print(f"{'='*80}")
    
    module_path = os.path.join('addons', module_name)
    module_results = {
        'exists': False,
        'manifest': False,
        'syntax_errors': [],
        'deprecated_patterns': [],
        'missing_encoding': [],
        'model_errors': [],
    }
    
    # Check if module exists
    if not os.path.exists(module_path):
        print(f"  [ERROR] Module directory not found: {module_path}")
        module_results['exists'] = False
        results[module_name] = module_results
        continue
    
    module_results['exists'] = True
    print(f"  [OK] Module directory found")
    
    # Check manifest
    manifest_path = os.path.join(module_path, '__manifest__.py')
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_code = f.read()
            manifest = eval(manifest_code)
            
            required = ['name', 'version', 'depends', 'data', 'installable']
            missing = [k for k in required if k not in manifest]
            
            if missing:
                print(f"  [ERROR] Manifest missing keys: {missing}")
                module_results['manifest'] = False
            else:
                print(f"  [OK] Manifest valid - Version: {manifest.get('version')}")
                module_results['manifest'] = True
        except Exception as e:
            print(f"  [ERROR] Manifest error: {e}")
            module_results['manifest'] = False
    else:
        print(f"  [ERROR] Manifest file not found")
        module_results['manifest'] = False
    
    # Find all Python files
    python_files = []
    for root, dirs, files in os.walk(module_path):
        # Skip migrations and __pycache__
        if 'migrations' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py') and file != '__manifest__.py':
                python_files.append(os.path.join(root, file))
    
    print(f"  Found {len(python_files)} Python files")
    
    # Test each Python file
    for py_file in python_files:
        rel_path = os.path.relpath(py_file, module_path)
        
        # Check syntax
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                code = f.read()
            compile(code, py_file, 'exec')
        except SyntaxError as e:
            print(f"  [ERROR] {rel_path}: Syntax error - {e}")
            module_results['syntax_errors'].append((rel_path, f"Syntax: {e}"))
        except Exception as e:
            print(f"  [ERROR] {rel_path}: {e}")
            module_results['syntax_errors'].append((rel_path, str(e)))
        
        # Check encoding declaration
        with open(py_file, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
            if not first_line.startswith('#') or 'coding' not in first_line.lower():
                # Check if it's an __init__.py (usually don't need encoding)
                if '__init__.py' not in py_file:
                    module_results['missing_encoding'].append(rel_path)
        
        # Check for deprecated patterns
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        deprecated_checks = {
            '@api.multi': '@api.multi (deprecated in Odoo 19)',
            '@api.one': '@api.one (deprecated in Odoo 19)',
            'fields.Date.context_today': 'fields.Date.context_today (deprecated)',
            'fields.Datetime.context_today': 'fields.Datetime.context_today (deprecated)',
        }
        
        for pattern, message in deprecated_checks.items():
            if pattern in content:
                if rel_path not in [x[0] for x in module_results['deprecated_patterns']]:
                    module_results['deprecated_patterns'].append((rel_path, message))
    
    # Check for model definitions
    models_path = os.path.join(module_path, 'models')
    if os.path.exists(models_path):
        model_files = [f for f in os.listdir(models_path) if f.endswith('.py') and f != '__init__.py']
        print(f"  Found {len(model_files)} model files")
        
        for model_file in model_files:
            model_path = os.path.join(models_path, model_file)
            try:
                with open(model_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for model class definition
                if '_name' in content and 'models.Model' in content:
                    # Extract model name
                    name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
                    if name_match:
                        model_name = name_match.group(1)
                        # Check if class exists
                        class_match = re.search(r'class\s+(\w+).*models\.Model', content)
                        if class_match:
                            print(f"    [OK] Model: {model_name} ({class_match.group(1)})")
                        else:
                            print(f"    [WARNING] Model {model_name} found but class name unclear")
            except Exception as e:
                module_results['model_errors'].append((model_file, str(e)))
    
    results[module_name] = module_results

# Summary Report
print(f"\n{'='*80}")
print("COMPREHENSIVE VALIDATION SUMMARY - ALL PTT MODULES")
print(f"{'='*80}\n")

total_modules = len(PTT_MODULES)
modules_ok = 0
modules_with_errors = 0

for module_name in PTT_MODULES:
    result = results.get(module_name, {})
    
    if not result.get('exists'):
        print(f"[{module_name}] [NOT FOUND]")
        modules_with_errors += 1
        continue
    
    errors = []
    warnings = []
    
    if not result.get('manifest'):
        errors.append("Invalid manifest")
    
    if result.get('syntax_errors'):
        errors.append(f"{len(result['syntax_errors'])} syntax error(s)")
        for file, error in result['syntax_errors']:
            warnings.append(f"  - {file}: {error}")
    
    if result.get('deprecated_patterns'):
        warnings.append(f"{len(result['deprecated_patterns'])} deprecated pattern(s)")
        for file, pattern in result['deprecated_patterns']:
            warnings.append(f"  - {file}: {pattern}")
    
    if result.get('missing_encoding'):
        warnings.append(f"{len(result['missing_encoding'])} file(s) missing encoding")
    
    if result.get('model_errors'):
        errors.append(f"{len(result['model_errors'])} model error(s)")
    
    if errors:
        print(f"[{module_name}] [FAILED]")
        for error in errors:
            print(f"  ERROR: {error}")
        modules_with_errors += 1
    else:
        print(f"[{module_name}] [PASSED]")
        modules_ok += 1
    
    if warnings:
        for warning in warnings:
            print(f"  WARNING: {warning}")

print(f"\n{'='*80}")
print("FINAL RESULTS")
print(f"{'='*80}")
print(f"Total Modules Tested: {total_modules}")
print(f"[PASSED] {modules_ok}")
print(f"[FAILED] {modules_with_errors}")

if modules_with_errors == 0:
    print(f"\n[SUCCESS] All {total_modules} PTT modules are ready for Odoo 19!")
    sys.exit(0)
else:
    print(f"\n[WARNING] {modules_with_errors} module(s) need fixes before deployment")
    sys.exit(1)
