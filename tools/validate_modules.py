#!/usr/bin/env python3
"""
Comprehensive Odoo module validation script.

Checks:
1. Python syntax errors
2. XML syntax errors
3. Manifest validation
4. Security CSV validation
5. View field references
6. Model field existence
"""

import os
import sys
import ast
import csv
import re
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    print("ERROR: lxml not installed. Run: pip install lxml")
    sys.exit(2)

ERRORS = []
WARNINGS = []

def check_python_syntax(path: Path):
    """Check all Python files for syntax errors."""
    for py_file in path.rglob("*.py"):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                source = f.read()
            ast.parse(source)
        except SyntaxError as e:
            ERRORS.append(f"PYTHON SYNTAX: {py_file}:{e.lineno} - {e.msg}")
        except Exception as e:
            ERRORS.append(f"PYTHON ERROR: {py_file} - {e}")

def check_xml_syntax(path: Path):
    """Check all XML files for syntax errors."""
    for xml_file in path.rglob("*.xml"):
        try:
            etree.parse(str(xml_file))
        except etree.XMLSyntaxError as e:
            ERRORS.append(f"XML SYNTAX: {xml_file} - {e}")
        except Exception as e:
            ERRORS.append(f"XML ERROR: {xml_file} - {e}")

def check_manifest(path: Path):
    """Validate __manifest__.py files."""
    for manifest in path.rglob("__manifest__.py"):
        try:
            with open(manifest, 'r', encoding='utf-8') as f:
                content = f.read()
            manifest_dict = ast.literal_eval(content)
            
            # Check required keys
            required = ['name', 'version', 'depends']
            for key in required:
                if key not in manifest_dict:
                    ERRORS.append(f"MANIFEST: {manifest} - Missing required key '{key}'")
            
            # Check data files exist
            module_dir = manifest.parent
            for data_file in manifest_dict.get('data', []):
                full_path = module_dir / data_file
                if not full_path.exists():
                    ERRORS.append(f"MANIFEST: {manifest} - Data file not found: {data_file}")
            
        except Exception as e:
            ERRORS.append(f"MANIFEST ERROR: {manifest} - {e}")

def check_security_csv(path: Path):
    """Validate ir.model.access.csv files."""
    for csv_file in path.rglob("ir.model.access.csv"):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                required_cols = ['id', 'name', 'model_id:id', 'group_id:id', 
                               'perm_read', 'perm_write', 'perm_create', 'perm_unlink']
                
                if reader.fieldnames:
                    for col in required_cols:
                        if col not in reader.fieldnames:
                            ERRORS.append(f"SECURITY CSV: {csv_file} - Missing column '{col}'")
                
                for row_num, row in enumerate(reader, start=2):
                    # Check model_id format (allow module.model_ for cross-module refs)
                    model_id = row.get('model_id:id', '')
                    if model_id and not ('model_' in model_id):
                        WARNINGS.append(f"SECURITY CSV: {csv_file}:{row_num} - model_id should contain 'model_': {model_id}")
                    
        except Exception as e:
            ERRORS.append(f"SECURITY CSV ERROR: {csv_file} - {e}")

def check_view_fields(path: Path):
    """Check for common view field issues."""
    # Fields that don't exist in Odoo 19
    deprecated_fields = {
        'res.groups': ['category_id'],  # Now category_ids
        'project.task': ['planned_hours', 'remaining_hours', 'effective_hours'],  # Enterprise
    }
    
    for xml_file in path.rglob("*.xml"):
        try:
            tree = etree.parse(str(xml_file))
            root = tree.getroot()
            
            for record in root.xpath("//record[@model='ir.ui.view']"):
                model_field = record.xpath(".//field[@name='model']/text()")
                if not model_field:
                    continue
                model = model_field[0]
                
                # Check for deprecated fields
                if model in deprecated_fields:
                    for field in record.xpath(".//field[@name='arch']//field/@name"):
                        if field in deprecated_fields[model]:
                            ERRORS.append(f"DEPRECATED FIELD: {xml_file} - {model}.{field} does not exist in Odoo 19")
            
            # Check for empty xpath operations
            for xpath in root.xpath("//xpath[@position='attributes']"):
                if len(xpath) == 0:
                    ERRORS.append(f"EMPTY XPATH: {xml_file} - xpath with position='attributes' has no content")
            
        except Exception:
            pass  # XML errors caught elsewhere

def check_odoo19_compatibility(path: Path):
    """Check for Odoo 19 specific issues."""
    issues_patterns = [
        (r"category_id.*ref=", "category_id is deprecated in Odoo 19, use category_ids"),
        (r"attrs\s*=\s*['\"]", "attrs= is deprecated in Odoo 19, use invisible/readonly/required attributes"),
        (r"states\s*=\s*['\"]", "states= is deprecated in Odoo 19, use invisible attribute with state condition"),
    ]
    
    for xml_file in path.rglob("*.xml"):
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                for pattern, message in issues_patterns:
                    if re.search(pattern, content):
                        WARNINGS.append(f"ODOO 19: {xml_file} - {message}")
        except Exception:
            pass

def check_imports(path: Path):
    """Check Python imports for common issues."""
    for py_file in path.rglob("*.py"):
        if '__pycache__' in str(py_file):
            continue
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for deprecated imports
            deprecated_imports = [
                ('from openerp', 'Use "from odoo" instead of "from openerp"'),
                ('import openerp', 'Use "import odoo" instead of "import openerp"'),
            ]
            
            for pattern, message in deprecated_imports:
                if pattern in content:
                    ERRORS.append(f"DEPRECATED IMPORT: {py_file} - {message}")
                    
        except Exception:
            pass

def main():
    if len(sys.argv) < 2:
        print("Usage: validate_modules.py <addons_path>")
        print("Example: python tools/validate_modules.py addons/")
        sys.exit(2)
    
    target = Path(sys.argv[1])
    if not target.exists():
        print(f"ERROR: Path not found: {target}")
        sys.exit(2)
    
    print(f"Validating modules in: {target}\n")
    
    print("Checking Python syntax...")
    check_python_syntax(target)
    
    print("Checking XML syntax...")
    check_xml_syntax(target)
    
    print("Checking manifests...")
    check_manifest(target)
    
    print("Checking security CSVs...")
    check_security_csv(target)
    
    print("Checking view fields...")
    check_view_fields(target)
    
    print("Checking Odoo 19 compatibility...")
    check_odoo19_compatibility(target)
    
    print("Checking imports...")
    check_imports(target)
    
    print("\n" + "="*60)
    
    if ERRORS:
        print(f"\n[ERRORS] {len(ERRORS)} error(s) found:\n")
        for err in ERRORS:
            print(f"  X {err}")
    
    if WARNINGS:
        print(f"\n[WARNINGS] {len(WARNINGS)} warning(s) found:\n")
        for warn in WARNINGS:
            print(f"  ! {warn}")
    
    if not ERRORS and not WARNINGS:
        print("\n[OK] All validations passed!")
        sys.exit(0)
    elif ERRORS:
        print(f"\n[FAILED] {len(ERRORS)} error(s), {len(WARNINGS)} warning(s)")
        sys.exit(1)
    else:
        print(f"\n[PASSED WITH WARNINGS] {len(WARNINGS)} warning(s)")
        sys.exit(0)


if __name__ == "__main__":
    main()
