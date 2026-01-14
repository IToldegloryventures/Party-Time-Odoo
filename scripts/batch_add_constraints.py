#!/usr/bin/env python3
"""
Batch Add Constraints to Fields

This script systematically adds @api.constrains() decorators to fields
that need validation based on field type and name patterns.

Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Set

PROJECT_ROOT = Path(__file__).parent.parent
ADDONS_DIR = PROJECT_ROOT / "addons"


def detect_field_type(line: str) -> str:
    """Detect field type from field definition line."""
    if 'fields.Date' in line or 'fields.Datetime' in line:
        return 'date'
    elif 'fields.Integer' in line:
        return 'integer'
    elif 'fields.Float' in line:
        return 'float'
    elif 'fields.Char' in line:
        return 'char'
    return 'char'


def needs_constraint(field_name: str, field_type: str) -> Tuple[bool, str]:
    """Determine if a field needs a constraint and what type.
    
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
    
    Returns:
        (needs_constraint, constraint_type)
    """
    field_lower = field_name.lower()
    
    # Date fields - prevent past dates
    if field_type == 'date' and ('date' in field_lower or 'deadline' in field_lower):
        if 'event' in field_lower or 'due' in field_lower:
            return (True, 'date_not_past')
    
    # Integer fields - prevent negatives
    if field_type == 'integer' and ('count' in field_lower or 'quantity' in field_lower):
        return (True, 'positive_integer')
    
    # Float fields - prevent zero/negative
    if field_type == 'float' and ('hours' in field_lower or 'duration' in field_lower):
        return (True, 'positive_float')
    
    # Char fields - format validation
    if field_type == 'char' and 'time' in field_lower:
        return (True, 'time_format')
    
    if field_type == 'char' and 'email' in field_lower:
        return (True, 'email_format')
    
    if field_type == 'char' and 'phone' in field_lower:
        return (True, 'phone_format')
    
    return (False, '')


def generate_constraint_code(field_name: str, constraint_type: str) -> str:
    """Generate constraint method code.
    
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
    """
    constraint_templates = {
        'date_not_past': f'''    @api.constrains('{field_name}')
    def _check_{field_name}_not_past(self):
        """Ensure {field_name} is not in the past.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
        """
        from odoo.exceptions import ValidationError
        today = fields.Date.today()
        for record in self:
            if record.{field_name} and record.{field_name} < today:
                raise ValidationError(
                    _("{field_name} (%s) cannot be in the past. Please enter a future date.") 
                    % record.{field_name}
                )
''',
        'positive_integer': f'''    @api.constrains('{field_name}')
    def _check_{field_name}_positive(self):
        """Ensure {field_name} is not negative.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
        """
        from odoo.exceptions import ValidationError
        for record in self:
            if record.{field_name} < 0:
                raise ValidationError(
                    _("{field_name} cannot be negative. Got: %s. Please enter 0 or a positive number.") 
                    % record.{field_name}
                )
''',
        'positive_float': f'''    @api.constrains('{field_name}')
    def _check_{field_name}_positive(self):
        """Ensure {field_name} is positive.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
        """
        from odoo.exceptions import ValidationError
        for record in self:
            if record.{field_name} and record.{field_name} <= 0:
                raise ValidationError(
                    _("{field_name} must be greater than 0. Got: %s. Please enter a positive number.") 
                    % record.{field_name}
                )
''',
        'time_format': f'''    @api.constrains('{field_name}')
    def _check_{field_name}_format(self):
        """Validate {field_name} is in HH:MM format.
        
        Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
        """
        import re
        from odoo.exceptions import ValidationError
        TIME_PATTERN = re.compile(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$')
        for record in self:
            if record.{field_name} and not TIME_PATTERN.match(record.{field_name}):
                raise ValidationError(
                    _("{field_name} must be in HH:MM format (e.g., 09:30, 14:00). Got: %s") 
                    % record.{field_name}
                )
''',
    }
    
    return constraint_templates.get(constraint_type, '')


def find_fields_needing_constraints() -> Dict[Path, List[Tuple[str, int, str, str]]]:
    """Find all fields that need constraints.
    
    Returns:
        Dict mapping file paths to list of (field_name, line_num, field_type, constraint_type)
    """
    results = {}
    
    for py_file in ADDONS_DIR.rglob("*.py"):
        if "migrations" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            fields_needing_constraints = []
            existing_constraints = set()
            
            # Find existing constraints
            for line in lines:
                constraint_match = re.search(r"@api\.constrains\(['\"]([^'\"]+)['\"]", line)
                if constraint_match:
                    existing_constraints.add(constraint_match.group(1))
            
            # Find field definitions
            for i, line in enumerate(lines, 1):
                field_match = re.search(r'(\w+)\s*=\s*fields\.(\w+)', line)
                if field_match and ('ptt_' in line or 'ppt_' in line):
                    field_name = field_match.group(1)
                    field_type = detect_field_type(line)
                    
                    # Skip if constraint already exists
                    if field_name in existing_constraints:
                        continue
                    
                    needs_const, constraint_type = needs_constraint(field_name, field_type)
                    if needs_const:
                        fields_needing_constraints.append((field_name, i, field_type, constraint_type))
            
            if fields_needing_constraints:
                results[py_file] = fields_needing_constraints
                
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return results


def add_constraint_to_file(file_path: Path, field_name: str, constraint_code: str, 
                           dry_run: bool = True) -> bool:
    """Add constraint method to a model file.
    
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Check if constraint already exists
        if f'_check_{field_name}' in content:
            return False
        
        # Check if ValidationError is imported
        needs_validation_import = 'from odoo.exceptions import ValidationError' not in content
        needs_fields_import = 'from odoo import' in content and 'fields' not in content.split('from odoo import')[1].split('\n')[0]
        
        # Find insertion point - after last field definition, before action methods
        insertion_line = len(lines) - 1
        
        # Look for existing constraints section or action methods
        for i, line in enumerate(lines):
            if '# === CONSTRAINTS ===' in line:
                insertion_line = i + 1
                break
            elif '# === ACTION' in line or 'def action_' in line:
                insertion_line = i
                break
        
        # Insert constraint code
        indent = '    '
        constraint_lines = [indent + line for line in constraint_code.strip().split('\n')]
        
        if insertion_line < len(lines):
            lines.insert(insertion_line, '')
            lines.insert(insertion_line + 1, '\n'.join(constraint_lines))
        else:
            lines.append('')
            lines.append('\n'.join(constraint_lines))
        
        # Add imports if needed
        if needs_validation_import:
            # Find import line
            for i, line in enumerate(lines):
                if 'from odoo import' in line and 'ValidationError' not in line:
                    # Add ValidationError to imports
                    if 'exceptions' not in line:
                        lines[i] = line.rstrip() + ', ValidationError'
                    else:
                        lines[i] = line.replace('from odoo import', 'from odoo import ValidationError,')
                    break
        
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
        
        return True
        
    except Exception as e:
        print(f"Error adding constraint to {file_path}: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch add constraints to fields')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview changes without applying (default)')
    parser.add_argument('--execute', action='store_true',
                       help='Actually apply the fixes')
    parser.add_argument('--file', type=str,
                       help='Process only this specific file')
    
    args = parser.parse_args()
    
    if args.execute:
        args.dry_run = False
    
    print("=" * 80)
    print("Batch Constraint Addition Tool")
    print("=" * 80)
    print(f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'EXECUTE (applying fixes)'}")
    print()
    print("Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#constraints-and-indexes")
    print()
    
    # Find fields needing constraints
    print("Finding fields needing constraints...")
    fields_needing = find_fields_needing_constraints()
    
    total_fields = sum(len(v) for v in fields_needing.values())
    print(f"Found {total_fields} fields needing constraints in {len(fields_needing)} files")
    print()
    
    # Process files
    files_to_process = [Path(args.file)] if args.file else fields_needing.keys()
    fixed_count = 0
    
    for file_path in files_to_process:
        if file_path not in fields_needing:
            continue
            
        print(f"Processing: {file_path}")
        for field_name, line_num, field_type, constraint_type in fields_needing[file_path]:
            print(f"  Line {line_num}: {field_name} ({field_type}) → {constraint_type}")
            
            constraint_code = generate_constraint_code(field_name, constraint_type)
            if constraint_code:
                if add_constraint_to_file(file_path, field_name, constraint_code, args.dry_run):
                    fixed_count += 1
                    if not args.dry_run:
                        print(f"    [OK] Added constraint")
            print()
    
    print("=" * 80)
    print(f"Summary: {fixed_count} constraints added")
    if args.dry_run:
        print("Run with --execute to apply changes")


if __name__ == '__main__':
    main()
