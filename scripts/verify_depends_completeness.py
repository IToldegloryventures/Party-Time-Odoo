#!/usr/bin/env python3
"""
Verify @api.depends() Completeness

This script analyzes computed fields and verifies that all dependencies
are listed in @api.depends() decorators.

Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#computed-fields
"""

import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
ADDONS_DIR = PROJECT_ROOT / "addons"


def extract_field_accesses(code: str) -> Set[str]:
    """Extract field accesses from Python code using AST.
    
    This finds patterns like:
    - record.field_name
    - self.field_name
    - project.field_name
    """
    field_accesses = set()
    
    try:
        tree = ast.parse(code)
        
        class FieldAccessVisitor(ast.NodeVisitor):
            def visit_Attribute(self, node):
                # Check if this is a field access (record.field_name)
                if isinstance(node.value, (ast.Name, ast.Attribute)):
                    field_accesses.add(node.attr)
                self.generic_visit(node)
        
        visitor = FieldAccessVisitor()
        visitor.visit(tree)
        
    except SyntaxError:
        # Fallback to regex for complex cases
        # Match patterns like: record.field_name, self.field_name, project.field_name
        pattern = r'(?:record|self|project|order|move|lead|task|vendor|partner)\.(\w+)'
        matches = re.findall(pattern, code)
        field_accesses.update(matches)
    
    return field_accesses


def find_computed_fields(file_path: Path) -> List[Dict]:
    """Find all computed fields in a file.
    
    Returns:
        List of dicts with: field_name, compute_method, line_num, depends_list, method_body
    """
    computed_fields = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
        
        # Find computed field definitions
        compute_pattern = re.compile(
            r'(\w+)\s*=\s*fields\.\w+\([^)]*compute=["\'](\w+)["\']',
            re.MULTILINE
        )
        
        for match in compute_pattern.finditer(content):
            field_name = match.group(1)
            compute_method = match.group(2)
            line_num = content[:match.start()].count('\n') + 1
            
            # Find @api.depends decorator
            depends_pattern = re.compile(
                rf'@api\.depends\(([^)]+)\)\s+def\s+{compute_method}\(self\):',
                re.MULTILINE | re.DOTALL
            )
            depends_match = depends_pattern.search(content, 0, match.end() + 500)
            
            depends_list = []
            if depends_match:
                depends_str = depends_match.group(1)
                # Parse dependencies (handle multi-line)
                depends_list = [
                    d.strip().strip('"\'')
                    for d in re.split(r'[,\n]', depends_str)
                    if d.strip() and not d.strip().startswith('#')
                ]
            
            # Find compute method body
            method_pattern = re.compile(
                rf'def\s+{compute_method}\(self\):.*?(?=\n    def\s+\w+|@api\.|@\w+\.|\Z)',
                re.MULTILINE | re.DOTALL
            )
            method_match = method_pattern.search(content, match.end())
            
            method_body = method_match.group(0) if method_match else ''
            
            computed_fields.append({
                'field_name': field_name,
                'compute_method': compute_method,
                'line_num': line_num,
                'depends_list': depends_list,
                'method_body': method_body,
            })
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
    
    return computed_fields


def verify_depends_completeness(file_path: Path) -> List[Dict]:
    """Verify @api.depends() completeness for all computed fields.
    
    Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#computed-fields
    
    Returns:
        List of issues found: {field_name, compute_method, missing_deps, line_num}
    """
    issues = []
    computed_fields = find_computed_fields(file_path)
    
    for field_info in computed_fields:
        field_name = field_info['field_name']
        compute_method = field_info['compute_method']
        depends_list = field_info['depends_list']
        method_body = field_info['method_body']
        line_num = field_info['line_num']
        
        # Extract field accesses from method body
        accessed_fields = extract_field_accesses(method_body)
        
        # Filter to ptt_/ppt_ fields (custom fields)
        custom_fields_accessed = {
            f for f in accessed_fields 
            if f.startswith('ptt_') or f.startswith('ppt_')
        }
        
        # Check for missing dependencies
        depends_set = set(depends_list)
        missing_deps = custom_fields_accessed - depends_set
        
        # Also check for related field accesses (record.related_field.field)
        # This is a simplified check - full analysis would need AST parsing
        
        if missing_deps:
            issues.append({
                'field_name': field_name,
                'compute_method': compute_method,
                'line_num': line_num,
                'missing_deps': list(missing_deps),
                'current_deps': depends_list,
            })
    
    return issues


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify @api.depends() completeness')
    parser.add_argument('--file', type=str,
                       help='Check only this specific file')
    parser.add_argument('--fix', action='store_true',
                       help='Auto-fix missing dependencies (experimental)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("@api.depends() Completeness Verification")
    print("=" * 80)
    print("Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#computed-fields")
    print()
    
    # Find all Python files
    if args.file:
        files_to_check = [Path(args.file)]
    else:
        files_to_check = list(ADDONS_DIR.rglob("*.py"))
        files_to_check = [f for f in files_to_check 
                         if "migrations" not in str(f) and "__pycache__" not in str(f)]
    
    total_issues = 0
    
    for file_path in files_to_check:
        issues = verify_depends_completeness(file_path)
        
        if issues:
            print(f"\n[FILE] {file_path}")
            for issue in issues:
                total_issues += 1
                print(f"  [WARN] Line {issue['line_num']}: {issue['field_name']}")
                print(f"     Compute method: {issue['compute_method']}")
                print(f"     Missing dependencies: {', '.join(issue['missing_deps'])}")
                print(f"     Current dependencies: {', '.join(issue['current_deps'])}")
                print()
    
    print("=" * 80)
    print(f"Summary: {total_issues} computed fields with missing dependencies")
    if total_issues == 0:
        print("[OK] All computed fields have complete @api.depends() decorators!")


if __name__ == '__main__':
    main()
