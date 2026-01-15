#!/usr/bin/env python3
"""
Analyze Model Errors - Field Level

This script analyzes each model file to identify:
- Missing model dependencies
- Invalid field references
- Broken computed fields
- Missing @api.depends
- Invalid comodel_name references
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
ADDONS_DIR = PROJECT_ROOT / "addons"

# Models that should exist in Odoo
STANDARD_MODELS = {
    'res.partner', 'res.users', 'crm.lead', 'sale.order', 'account.move',
    'project.project', 'project.task', 'purchase.order', 'product.template',
    'product.product', 'mail.message', 'mail.activity', 'ir.model',
    'ir.model.fields', 'ir.ui.view', 'ir.actions.act_window',
}

# Custom models (PTT modules)
CUSTOM_MODELS = {
    'ptt.project.vendor.assignment', 'ptt.crm.service.line',
    'ptt.crm.vendor.assignment', 'ptt.personal.todo', 'ptt.home.data',
    'ptt.dashboard.config', 'ptt.dashboard.widget', 'ptt.sales.rep',
    'ptt.vendor.service.tag', 'ptt.document.type', 'ptt.vendor.document',
    'justcall.config', 'justcall.call', 'justcall.user.mapping',
}

def extract_model_name(file_path: Path) -> str:
    """Extract model name from Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for _name or _inherit
        name_match = re.search(r"_name\s*=\s*['\"]([^'\"]+)['\"]", content)
        if name_match:
            return name_match.group(1)
        
        inherit_match = re.search(r"_inherit\s*=\s*['\"]([^'\"]+)['\"]", content)
        if inherit_match:
            return inherit_match.group(1)
            
    except Exception:
        pass
    return None

def find_field_definitions(content: str) -> List[Dict]:
    """Find all field definitions in Python code."""
    fields = []
    
    # Pattern: field_name = fields.Type(...)
    pattern = re.compile(r'(\w+)\s*=\s*fields\.(\w+)\([^)]*\)', re.MULTILINE | re.DOTALL)
    
    for match in pattern.finditer(content):
        field_name = match.group(1)
        field_type = match.group(2)
        
        # Get full field definition (may span multiple lines)
        start = match.start()
        end = content.find(')', start) + 1
        
        field_def = content[start:end]
        
        fields.append({
            'name': field_name,
            'type': field_type,
            'definition': field_def,
            'line': content[:start].count('\n') + 1,
        })
    
    return fields

def check_field_dependencies(field_def: str, model_name: str) -> List[str]:
    """Check if field has missing dependencies."""
    errors = []
    
    # Check Many2one, One2many, Many2many comodel_name
    comodel_pattern = re.compile(r"comodel_name\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
    comodel_match = comodel_pattern.search(field_def)
    
    if comodel_match:
        comodel = comodel_match.group(1)
        if comodel not in STANDARD_MODELS and comodel not in CUSTOM_MODELS:
            errors.append(f"Unknown comodel_name: {comodel}")
    
    # Check related fields
    related_pattern = re.compile(r"related\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
    related_match = related_pattern.search(field_def)
    
    if related_match:
        related_path = related_match.group(1)
        # Check if related model exists
        parts = related_path.split('.')
        if len(parts) > 0:
            related_model = parts[0]
            if related_model not in STANDARD_MODELS and related_model not in CUSTOM_MODELS:
                errors.append(f"Unknown related model: {related_model}")
    
    return errors

def check_computed_fields(content: str, model_name: str) -> List[Dict]:
    """Check computed fields for missing @api.depends."""
    issues = []
    
    # Find all computed fields
    compute_pattern = re.compile(
        r'(\w+)\s*=\s*fields\.\w+\([^)]*compute\s*=\s*["\'](\w+)["\']',
        re.MULTILINE
    )
    
    for match in compute_pattern.finditer(content):
        field_name = match.group(1)
        compute_method = match.group(2)
        
        # Find @api.depends
        depends_pattern = re.compile(
            rf'@api\.depends\(([^)]+)\)\s+def\s+{compute_method}\(self\):',
            re.MULTILINE | re.DOTALL
        )
        
        depends_match = depends_pattern.search(content, 0, match.end() + 500)
        
        if not depends_match:
            issues.append({
                'field': field_name,
                'method': compute_method,
                'error': 'Missing @api.depends() decorator',
                'line': content[:match.start()].count('\n') + 1,
            })
    
    return issues

def analyze_model_file(file_path: Path) -> Dict:
    """Analyze a single model file for errors."""
    errors = {
        'file': str(file_path),
        'model': None,
        'field_errors': [],
        'computed_errors': [],
        'import_errors': [],
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract model name
        errors['model'] = extract_model_name(file_path)
        
        # Find field definitions
        fields = find_field_definitions(content)
        
        # Check each field
        for field in fields:
            field_errors = check_field_dependencies(field['definition'], errors['model'])
            if field_errors:
                errors['field_errors'].append({
                    'field': field['name'],
                    'type': field['type'],
                    'line': field['line'],
                    'errors': field_errors,
                })
        
        # Check computed fields
        computed_issues = check_computed_fields(content, errors['model'])
        errors['computed_errors'] = computed_issues
        
        # Check imports
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and 'justcall' in node.module.lower():
                        errors['import_errors'].append(f"Import from justcall: {node.module}")
        except SyntaxError:
            pass
            
    except Exception as e:
        errors['parse_error'] = str(e)
    
    return errors

def main():
    print("=" * 80)
    print("Model Error Analysis - Field Level")
    print("=" * 80)
    print()
    
    # Modules to analyze (excluding justcall)
    modules_to_analyze = [
        'ptt_business_core',
        'ptt_operational_dashboard',
        'ptt_vendor_management',
    ]
    
    all_errors = []
    
    for module_name in modules_to_analyze:
        module_path = ADDONS_DIR / module_name / "models"
        
        if not module_path.exists():
            continue
        
        print(f"\n{'=' * 80}")
        print(f"MODULE: {module_name}")
        print(f"{'=' * 80}")
        
        for model_file in module_path.glob("*.py"):
            if model_file.name == "__init__.py":
                continue
            
            errors = analyze_model_file(model_file)
            
            if errors['field_errors'] or errors['computed_errors'] or errors.get('parse_error'):
                print(f"\n📄 {model_file.name}")
                print(f"   Model: {errors['model']}")
                
                if errors.get('parse_error'):
                    print(f"   ❌ Parse Error: {errors['parse_error']}")
                
                if errors['field_errors']:
                    print(f"   ⚠️  Field Errors ({len(errors['field_errors'])}):")
                    for fe in errors['field_errors']:
                        print(f"      - {fe['field']} ({fe['type']}) - Line {fe['line']}")
                        for err in fe['errors']:
                            print(f"        ❌ {err}")
                
                if errors['computed_errors']:
                    print(f"   ⚠️  Computed Field Issues ({len(errors['computed_errors'])}):")
                    for ce in errors['computed_errors']:
                        print(f"      - {ce['field']} (compute={ce['method']}) - Line {ce['line']}")
                        print(f"        ❌ {ce['error']}")
                
                all_errors.append(errors)
            else:
                print(f"\n[OK] {model_file.name} - No errors found")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total files with errors: {len(all_errors)}")
    
    # Group by error type
    field_error_count = sum(len(e['field_errors']) for e in all_errors)
    computed_error_count = sum(len(e['computed_errors']) for e in all_errors)
    
    print(f"Field errors: {field_error_count}")
    print(f"Computed field issues: {computed_error_count}")
    
    if all_errors:
        print("\n⚠️  See details above for each model file")

if __name__ == '__main__':
    main()
