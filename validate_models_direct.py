#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Direct model validation - checks field definitions without database
"""
import sys
import os
import re

files_to_check = {
    'project_project.py': 'addons/ptt_business_core/models/project_project.py',
    'project_task.py': 'addons/ptt_business_core/models/project_task.py',
    'purchase_order.py': 'addons/ptt_business_core/models/purchase_order.py',
    'ptt_vendor_rfq.py': 'addons/ptt_vendor_management/models/ptt_vendor_rfq.py',
}

print("=" * 80)
print("MODEL FIELD VALIDATION")
print("=" * 80)

errors = []
warnings = []

for model_name, file_path in files_to_check.items():
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    
    if not os.path.exists(full_path):
        errors.append(f"{model_name}: File not found at {file_path}")
        continue
    
    print(f"\n{'='*80}")
    print(f"Checking: {model_name}")
    print(f"File: {file_path}")
    print(f"{'='*80}")
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check for related fields with index=True and store=True
        for line_num, line in enumerate(lines, 1):
            # Look for field definitions with related, store=True, and index=True
            if 'related=' in line and 'store=True' in line and 'index=True' in line:
                # Check if this is a field definition
                if 'fields.' in line or any(f'fields.{ftype}(' in line for ftype in ['Char', 'Date', 'Many2one', 'Integer', 'Float', 'Boolean', 'Text', 'Selection']):
                    # Extract field name if possible
                    field_match = re.search(r'(\w+)\s*=\s*fields\.', line)
                    field_name = field_match.group(1) if field_match else 'unknown'
                    
                    # Extract related path
                    related_match = re.search(r'related=["\']([^"\']+)["\']', line)
                    related_path = related_match.group(1) if related_match else 'unknown'
                    
                    error_msg = f"{model_name}: Line {line_num} - Related field '{field_name}' has store=True and index=True"
                    errors.append(error_msg)
                    print(f"  [ERROR] {error_msg}")
                    print(f"          Related path: {related_path}")
                    print(f"          Fix: Remove 'index=True' - Odoo indexes stored fields automatically")
        
        # Also check multi-line field definitions
        for i, line in enumerate(lines):
            if 'related=' in line and 'fields.' in line:
                # Check if index=True appears in nearby lines
                check_range = min(10, len(lines) - i)
                field_content = '\n'.join(lines[i:i+check_range])
                
                if 'store=True' in field_content and 'index=True' in field_content:
                    # Make sure it's the same field definition
                    if field_content.count('fields.') == 1:  # Single field definition
                        field_match = re.search(r'(\w+)\s*=\s*fields\.', line)
                        field_name = field_match.group(1) if field_match else 'unknown'
                        
                        related_match = re.search(r'related=["\']([^"\']+)["\']', field_content)
                        related_path = related_match.group(1) if related_match else 'unknown'
                        
                        error_msg = f"{model_name}: Line {i+1} - Related field '{field_name}' has store=True and index=True (multi-line)"
                        if error_msg not in errors:
                            errors.append(error_msg)
                            print(f"  [ERROR] {error_msg}")
                            print(f"          Related path: {related_path}")
                            print(f"          Fix: Remove 'index=True'")
        
        print(f"  [OK] File parsed successfully")
        
    except Exception as e:
        errors.append(f"{model_name}: Error reading file - {str(e)}")
        print(f"  [ERROR] {e}")
        import traceback
        traceback.print_exc()

# Summary
print(f"\n{'='*80}")
print("VALIDATION SUMMARY")
print(f"{'='*80}")

if errors:
    print(f"\n[ERRORS FOUND] ({len(errors)}):")
    for error in errors:
        print(f"  - {error}")
    print(f"\n[ACTION REQUIRED] These errors need to be fixed!")
else:
    print(f"\n[SUCCESS] No errors found!")
    print(f"         All related fields are properly configured.")

if warnings:
    print(f"\n[WARNINGS] ({len(warnings)}):")
    for warning in warnings:
        print(f"  - {warning}")

print(f"\n{'='*80}")
