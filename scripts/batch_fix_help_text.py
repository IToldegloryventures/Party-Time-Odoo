#!/usr/bin/env python3
"""
Batch Add Help Text to Fields

This script systematically adds help text to fields missing it.
Uses intelligent templates based on field names and types.

Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#field-attributes
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
ADDONS_DIR = PROJECT_ROOT / "addons"

# Help text templates by field name pattern
HELP_TEMPLATES = {
    # Date fields
    'date': {
        'event_date': "Scheduled date for the event. Used for calendar views and event planning.",
        'due_date': "Due date for this item. Used for scheduling and prioritization.",
        'date_of_call': "Date of the initial inquiry call.",
        'confirmed_date': "Date when this was confirmed.",
        'signature_date': "Date when the document was signed.",
    },
    # Char fields
    'char': {
        'venue_name': "Name of the venue where the event will be held.",
        'venue': "Name of the venue where the event will be held.",
        'event_name': "Name or title of the event.",
        'name': "Name or title of this record.",
        'cfo_name': "Name of the Chief Financial Officer or finance contact person.",
        'contact_name': "Name of the contact person.",
        'phone': "Phone number for contacting this person or organization.",
        'email': "Email address for contacting this person or organization.",
        'address': "Physical address or location.",
        'notes': "Additional notes or comments about this record.",
        'description': "Detailed description or additional information.",
    },
    # Integer fields
    'integer': {
        'guest_count': "Expected number of guests/attendees for the event. Used to calculate per-person pricing.",
        'estimated_guest_count': "Expected number of guests/attendees for the event. Used to calculate per-person pricing.",
        'count': "Count or quantity of items.",
        'sequence': "Display order for this record. Lower numbers appear first.",
    },
    # Float fields
    'float': {
        'total_hours': "Total duration of the event in hours (e.g., 4.5 for 4 hours 30 minutes).",
        'hours': "Duration in hours.",
        'amount': "Monetary amount or value.",
        'price': "Price or cost value.",
    },
    # Boolean fields
    'boolean': {
        'venue_booked': "Indicates whether a specific venue has already been booked for this event.",
        'booked': "Indicates whether this item has been booked or confirmed.",
        'active': "If unchecked, this record will be hidden.",
        'required': "Indicates whether this field or item is required.",
    },
    # Selection fields
    'selection': {
        'event_type': "Type of event being planned. Used for categorization, reporting, and template selection.",
        'status': "Current status of this record.",
        'priority': "Priority level for this item.",
        'location_type': "Type of location for the event. Affects equipment needs and weather contingency planning.",
    },
}


def get_help_text(field_name: str, field_type: str) -> str:
    """Get appropriate help text for a field.
    
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#field-attributes
    """
    # Try exact match first
    templates = HELP_TEMPLATES.get(field_type, {})
    for key, help_text in templates.items():
        if key in field_name.lower():
            return help_text
    
    # Try partial matches
    field_lower = field_name.lower()
    if 'date' in field_lower:
        return "Date field for scheduling and planning."
    elif 'name' in field_lower:
        return "Name or title for this record."
    elif 'count' in field_lower:
        return "Count or quantity value."
    elif 'hours' in field_lower or 'time' in field_lower:
        return "Time or duration value."
    elif 'phone' in field_lower:
        return "Phone number for contact purposes."
    elif 'email' in field_lower:
        return "Email address for contact purposes."
    elif 'notes' in field_lower or 'description' in field_lower:
        return "Additional notes or detailed description."
    elif 'amount' in field_lower or 'price' in field_lower or 'cost' in field_lower:
        return "Monetary amount or value."
    elif 'type' in field_lower:
        return "Type or category classification."
    elif 'status' in field_lower:
        return "Current status or state of this record."
    elif 'active' in field_lower:
        return "If unchecked, this record will be hidden."
    elif 'required' in field_lower:
        return "Indicates whether this field or item is required."
    
    # Generic fallback
    generic = {
        'date': "Date field for scheduling and planning.",
        'char': "Text field for storing information.",
        'text': "Multi-line text field for detailed information.",
        'integer': "Numeric field for counting or quantities.",
        'float': "Decimal field for precise measurements.",
        'boolean': "Checkbox field for yes/no options.",
        'selection': "Dropdown field for selecting from predefined options.",
        'many2one': "Link to another record.",
        'one2many': "List of related records.",
        'many2many': "Multiple related records.",
    }
    
    return generic.get(field_type, "Field for storing data.")


def detect_field_type(line: str) -> str:
    """Detect field type from field definition line."""
    if 'fields.Date' in line:
        return 'date'
    elif 'fields.Datetime' in line:
        return 'datetime'
    elif 'fields.Integer' in line:
        return 'integer'
    elif 'fields.Float' in line:
        return 'float'
    elif 'fields.Boolean' in line:
        return 'boolean'
    elif 'fields.Selection' in line:
        return 'selection'
    elif 'fields.Text' in line:
        return 'text'
    elif 'fields.Many2one' in line:
        return 'many2one'
    elif 'fields.One2many' in line:
        return 'one2many'
    elif 'fields.Many2many' in line:
        return 'many2many'
    elif 'fields.Char' in line:
        return 'char'
    return 'char'  # default


def add_help_to_field(file_path: Path, field_name: str, field_start_line: int, 
                      field_type: str, dry_run: bool = True) -> bool:
    """Add help text to a field definition.
    
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#field-attributes
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Get help text
        help_text = get_help_text(field_name, field_type)
        
        # Find the field definition (may span multiple lines)
        line_idx = field_start_line - 1
        field_lines = []
        paren_count = 0
        found_opening = False
        
        # Collect all lines of the field definition
        for i in range(line_idx, len(lines)):
            line = lines[i]
            field_lines.append((i, line))
            
            # Count parentheses to find end of field definition
            paren_count += line.count('(') - line.count(')')
            if '(' in line:
                found_opening = True
            if found_opening and paren_count == 0 and ')' in line:
                break
        
        # Check if help already exists
        field_content = ''.join(line for _, line in field_lines)
        if 'help=' in field_content:
            return False  # Already has help
        
        # Find insertion point (before closing parenthesis)
        last_line_idx, last_line = field_lines[-1]
        
        # Insert help parameter
        if last_line.strip().endswith(')'):
            # Single line or last line ends with )
            indent = '    ' * (last_line.count('    ') - 1)
            # Remove closing )
            new_last_line = last_line.rstrip()[:-1]
            if not new_last_line.strip().endswith(','):
                new_last_line += ','
            new_last_line += f'\n{indent}help="{help_text}",\n{indent})'
            lines[last_line_idx] = new_last_line
        else:
            # Multi-line - add before closing
            indent = '    ' * (last_line.count('    '))
            lines.insert(last_line_idx, f'{indent}help="{help_text}",\n')
        
        if not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        
        return True
        
    except Exception as e:
        print(f"Error adding help to {file_path}:{field_start_line}: {e}")
        return False


def find_fields_missing_help() -> Dict[Path, List[Tuple[str, int, str]]]:
    """Find all fields missing help text.
    
    Returns:
        Dict mapping file paths to list of (field_name, line_num, field_type)
    """
    results = {}
    
    for py_file in ADDONS_DIR.rglob("*.py"):
        if "migrations" in str(py_file) or "__pycache__" in str(py_file):
            continue
        
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            missing_help = []
            
            # Find field definitions
            for i, line in enumerate(lines, 1):
                # Match field definition pattern
                field_match = re.search(r'(\w+)\s*=\s*fields\.(\w+)', line)
                if field_match and ('ptt_' in line or 'ppt_' in line):
                    field_name = field_match.group(1)
                    field_type = detect_field_type(line)
                    
                    # Check if help exists in this field definition
                    # Look ahead up to 10 lines for closing parenthesis
                    field_content = line
                    for j in range(i, min(i + 10, len(lines))):
                        field_content += '\n' + lines[j]
                        if ')' in lines[j] and not lines[j].strip().startswith('#'):
                            break
                    
                    if 'help=' not in field_content:
                        missing_help.append((field_name, i, field_type))
            
            if missing_help:
                results[py_file] = missing_help
                
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    return results


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch add help text to fields')
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
    print("Batch Help Text Addition Tool")
    print("=" * 80)
    print(f"Mode: {'DRY RUN (preview only)' if args.dry_run else 'EXECUTE (applying fixes)'}")
    print()
    print("Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#field-attributes")
    print()
    
    # Find fields missing help
    print("Finding fields missing help text...")
    missing_help = find_fields_missing_help()
    
    total_fields = sum(len(v) for v in missing_help.values())
    print(f"Found {total_fields} fields missing help text in {len(missing_help)} files")
    print()
    
    # Process files
    files_to_process = [Path(args.file)] if args.file else missing_help.keys()
    fixed_count = 0
    
    for file_path in files_to_process:
        if file_path not in missing_help:
            continue
            
        print(f"Processing: {file_path}")
        for field_name, line_num, field_type in missing_help[file_path]:
            help_text = get_help_text(field_name, field_type)
            print(f"  Line {line_num}: {field_name} ({field_type})")
            print(f"    Help: {help_text[:60]}...")
            
            if add_help_to_field(file_path, field_name, line_num, field_type, args.dry_run):
                fixed_count += 1
                if not args.dry_run:
                    print(f"    [OK] Added help text")
            print()
    
    print("=" * 80)
    print(f"Summary: {fixed_count} fields processed")
    if args.dry_run:
        print("Run with --execute to apply changes")


if __name__ == '__main__':
    main()
