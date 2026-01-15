#!/usr/bin/env python3
"""
Fix and Report Manifests Script

Automatically fixes missing dependencies in manifest files based on XML references.
Also validates installable flags and generates a comprehensive report.

Usage:
    python scripts/fix_and_report_manifests.py [--dry-run] [--backup]
"""

import ast
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, Any

# Determine module root (works both locally and on server)
if Path('/home/odoo/src/user/addons').exists():
    MODULE_ROOT = Path('/home/odoo/src/user/addons')
else:
    MODULE_ROOT = Path(__file__).resolve().parent.parent / "addons"

# Match ref="module.id" pattern (external references only)
xmlid_pattern = re.compile(r"ref=['\"]([a-zA-Z0-9_]+)\.([a-zA-Z0-9_.]+)['\"]")

report_lines = []
fixes_applied = []
warnings = []
errors = []


def log(line: str, level: str = "INFO"):
    """Log a message and add to report."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "[INFO]",
        "SUCCESS": "[OK]",
        "WARNING": "[WARN]",
        "ERROR": "[ERROR]",
        "FIX": "[FIX]",
    }.get(level, "[INFO]")
    
    message = f"[{timestamp}] {prefix} {line}"
    try:
        print(message)
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        print(message.encode('ascii', 'replace').decode('ascii'))
    report_lines.append(message)


def parse_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Safely parse a manifest file (Python dict or JSON)."""
    try:
        content = manifest_path.read_text(encoding='utf-8')
        # Try ast.literal_eval first (safest)
        return ast.literal_eval(content)
    except (SyntaxError, ValueError):
        # Fall back to exec for complex manifests
        try:
            context = {}
            exec(f"manifest_data = {content}", {}, context)
            return context.get('manifest_data', {})
        except Exception as e:
            raise ValueError(f"Cannot parse manifest: {e}")


def write_manifest(manifest_path: Path, context: Dict[str, Any], backup: bool = False):
    """Write manifest back to file with proper formatting."""
    if backup:
        backup_path = manifest_path.with_suffix('.py.backup')
        backup_path.write_text(manifest_path.read_text(encoding='utf-8'))
        log(f"Created backup: {backup_path.name}", "INFO")
    
    # Format manifest as Python dict
    lines = ["{"]
    
    # Standard fields in order
    standard_fields = ['name', 'version', 'summary', 'description', 'category', 
                      'author', 'license', 'depends', 'data', 'assets', 
                      'installable', 'application', 'auto_install']
    
    # Add standard fields first
    for key in standard_fields:
        if key in context:
            value = context[key]
            if isinstance(value, str) and '\n' in value:
                # Multi-line string
                lines.append(f'    "{key}": """{value}""",')
            elif isinstance(value, list):
                # List - format nicely
                if value:
                    lines.append(f'    "{key}": [')
                    for item in value:
                        lines.append(f'        "{item}",')
                    lines.append('    ],')
                else:
                    lines.append(f'    "{key}": [],')
            elif isinstance(value, dict):
                # Dict - format nicely
                lines.append(f'    "{key}": {{')
                for k, v in value.items():
                    if isinstance(v, list):
                        lines.append(f'        "{k}": [')
                        for item in v:
                            lines.append(f'            "{item}",')
                        lines.append('        ],')
                    else:
                        lines.append(f'        "{k}": {repr(v)},')
                lines.append('    },')
            else:
                lines.append(f'    "{key}": {repr(value)},')
    
    # Add any remaining fields
    for key, value in context.items():
        if key not in standard_fields:
            lines.append(f'    "{key}": {repr(value)},')
    
    lines.append("}")
    
    manifest_path.write_text('\n'.join(lines), encoding='utf-8')


def find_external_dependencies(module_path: Path, module_name: str) -> Set[str]:
    """Find all external module dependencies from XML files."""
    external_refs = set()
    
    for folder in ['views', 'security']:
        folder_path = module_path / folder
        if not folder_path.exists():
            continue
            
        for xml_file in folder_path.glob("*.xml"):
            try:
                content = xml_file.read_text(encoding='utf-8')
                for match in xmlid_pattern.findall(content):
                    prefix = match[0]  # Module name
                    # Skip if same module or path reference
                    if prefix != module_name and not prefix.startswith('/'):
                        # Filter out XML ID patterns (view_, model_, action_)
                        if not prefix.startswith(('view_', 'model_', 'action_', 'ir_')):
                            external_refs.add(prefix)
            except Exception as e:
                log(f"Error reading {xml_file.name}: {e}", "WARNING")
                warnings.append(f"{module_name}: Error reading {xml_file.name}")
    
    return external_refs


def update_manifest_dependencies(
    module_path: Path,
    manifest_path: Path,
    context: Dict[str, Any],
    missing_deps: Set[str],
    dry_run: bool = False,
    backup: bool = False
) -> bool:
    """Update manifest with missing dependencies."""
    depends = set(context.get("depends", []))
    new_deps = missing_deps - depends
    
    if not new_deps:
        return False
    
    if dry_run:
        log(f"Would add dependencies: {sorted(new_deps)}", "FIX")
        return False
    
    # Add missing dependencies
    depends.update(new_deps)
    context["depends"] = sorted(list(depends))
    
    # Write updated manifest
    write_manifest(manifest_path, context, backup=backup)
    
    log(f"Added dependencies: {sorted(new_deps)}", "SUCCESS")
    fixes_applied.append(f"{module_path.name}: Added {sorted(new_deps)}")
    return True


def fix_installable_flag(
    module_path: Path,
    manifest_path: Path,
    context: Dict[str, Any],
    dry_run: bool = False,
    backup: bool = False
) -> bool:
    """Fix missing or False installable flag."""
    installable = context.get("installable")
    
    if installable is None or installable is False:
        if dry_run:
            log("Would set installable: True", "FIX")
            return False
        
        context["installable"] = True
        write_manifest(manifest_path, context, backup=backup)
        log("Set installable: True", "SUCCESS")
        fixes_applied.append(f"{module_path.name}: Set installable=True")
        return True
    
    return False


def main():
    """Main function to scan and fix all manifests."""
    # Parse command line arguments
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    backup = "--backup" in sys.argv or "-b" in sys.argv
    
    if dry_run:
        log("DRY RUN MODE - No files will be modified", "WARNING")
    
    log("=" * 80)
    log("MANIFEST FIX AND REPORT")
    log("=" * 80)
    log(f"Module root: {MODULE_ROOT}")
    log(f"Dry run: {dry_run}")
    log(f"Backup: {backup}")
    log("")
    
    modules_processed = 0
    modules_fixed = 0
    
    for module in sorted(MODULE_ROOT.iterdir()):
        if not module.is_dir():
            continue
        
        # Skip design-themes and odoo core
        if module.name in ['design-themes', 'odoo']:
            continue
        
        modules_processed += 1
        log(f"\n[MODULE] {module.name}")
        
        manifest_path = module / "__manifest__.py"
        if not manifest_path.exists():
            log("No __manifest__.py found", "ERROR")
            errors.append(f"{module.name}: Missing __manifest__.py")
            continue
        
        try:
            context = parse_manifest(manifest_path)
        except Exception as e:
            log(f"Cannot parse manifest: {e}", "ERROR")
            errors.append(f"{module.name}: Parse error - {e}")
            continue
        
        # Check installable flag
        installable = context.get("installable")
        if not installable:
            log("installable is missing or False", "WARNING")
            warnings.append(f"{module.name}: installable is False or missing")
            fix_installable_flag(module, manifest_path, context, dry_run, backup)
        
        # Get declared dependencies
        declared_deps = set(context.get("depends", []))
        log(f"Declared dependencies: {sorted(declared_deps) if declared_deps else 'None'}")
        
        # Find external XML references
        external_refs = find_external_dependencies(module, module.name)
        
        if not external_refs:
            log("No external XML dependencies found", "SUCCESS")
            continue
        
        log(f"XML references external modules: {sorted(external_refs)}")
        
        # Check for missing dependencies
        missing_deps = external_refs - declared_deps
        if missing_deps:
            log(f"Missing in manifest: {sorted(missing_deps)}", "ERROR")
            errors.append(f"{module.name}: Missing dependencies {sorted(missing_deps)}")
            
            if update_manifest_dependencies(module, manifest_path, context, missing_deps, dry_run, backup):
                modules_fixed += 1
        else:
            log("All XML dependencies present in manifest", "SUCCESS")
    
    # Generate summary
    log("")
    log("=" * 80)
    log("SUMMARY")
    log("=" * 80)
    log(f"Modules processed: {modules_processed}")
    log(f"Modules fixed: {modules_fixed}")
    log(f"Warnings: {len(warnings)}")
    log(f"Errors: {len(errors)}")
    log(f"Fixes applied: {len(fixes_applied)}")
    
    if fixes_applied:
        log("")
        log("Fixes Applied:", "SUCCESS")
        for fix in fixes_applied:
            log(f"  - {fix}", "SUCCESS")
    
    if warnings:
        log("")
        log("Warnings:", "WARNING")
        for warning in warnings:
            log(f"  - {warning}", "WARNING")
    
    if errors:
        log("")
        log("Errors:", "ERROR")
        for error in errors:
            log(f"  - {error}", "ERROR")
    
    # Write report file
    report_path = MODULE_ROOT.parent / "manifest_audit_report.txt"
    report_path.write_text("\n".join(report_lines), encoding='utf-8')
    log("")
    log(f"Report written to: {report_path}", "SUCCESS")
    
    # Exit with error code if there were errors
    if errors and not dry_run:
        sys.exit(1)


if __name__ == "__main__":
    main()
