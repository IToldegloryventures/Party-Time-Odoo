#!/usr/bin/env python3
"""
Verify Module Structure for Odoo 19

Checks that all custom modules have:
- __manifest__.py (not __openerp__.py)
- __init__.py
- Correct folder structure
"""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ADDONS_DIR = PROJECT_ROOT / "addons"

# Custom modules to check
CUSTOM_MODULES = [
    'ptt_justcall',
    'ptt_event_management',
    'ptt_business_core',
    'ptt_operational_dashboard',
    'ptt_vendor_management',
    'ppt_event_management',  # Check this duplicate too
]

def check_module_structure(module_name):
    """Check if module has correct Odoo 19 structure.
    
    Reference: Official Odoo 19 module structure requirements
    """
    module_path = ADDONS_DIR / module_name
    
    if not module_path.exists():
        return {
            'exists': False,
            'errors': [f"Module folder does not exist: {module_path}"]
        }
    
    errors = []
    warnings = []
    info = []
    
    # === REQUIRED FILES ===
    
    # Check __manifest__.py (REQUIRED)
    manifest_file = module_path / "__manifest__.py"
    openerp_file = module_path / "__openerp__.py"
    
    if not manifest_file.exists():
        if openerp_file.exists():
            errors.append(f"[ERROR] Has __openerp__.py but needs __manifest__.py (Odoo 19 requirement)")
        else:
            errors.append(f"[ERROR] Missing __manifest__.py (REQUIRED)")
    else:
        # Check manifest content
        try:
            with open(manifest_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "'installable'" not in content and '"installable"' not in content:
                    warnings.append("[WARN] Manifest missing 'installable' key (should be True)")
                if "'name'" not in content and '"name"' not in content:
                    errors.append("[ERROR] Manifest missing 'name' key (REQUIRED)")
                if "'version'" not in content and '"version"' not in content:
                    warnings.append("[WARN] Manifest missing 'version' key (recommended)")
                if "'depends'" not in content and '"depends"' not in content:
                    warnings.append("[WARN] Manifest missing 'depends' key (recommended)")
        except Exception as e:
            errors.append(f"[ERROR] Error reading manifest: {e}")
    
    # Check __init__.py (REQUIRED)
    init_file = module_path / "__init__.py"
    if not init_file.exists():
        errors.append(f"[ERROR] Missing __init__.py (REQUIRED)")
    
    # === OPTIONAL BUT RECOMMENDED STRUCTURE ===
    
    # Check models folder
    models_dir = module_path / "models"
    models_init = models_dir / "__init__.py" if models_dir.exists() else None
    
    if models_dir.exists():
        if not models_init or not models_init.exists():
            warnings.append("[WARN] models/ folder exists but missing models/__init__.py")
        else:
            info.append("[OK] models/ folder with __init__.py")
    else:
        warnings.append("[WARN] No 'models' folder (OK if module only has views/controllers)")
    
    # Check views folder
    views_dir = module_path / "views"
    if views_dir.exists():
        xml_files = list(views_dir.glob("*.xml"))
        if xml_files:
            info.append(f"[OK] views/ folder with {len(xml_files)} XML file(s)")
        else:
            warnings.append("[WARN] views/ folder exists but no XML files")
    else:
        warnings.append("[WARN] No 'views' folder (OK if module only has models)")
    
    # Check security folder
    security_dir = module_path / "security"
    access_csv = security_dir / "ir.model.access.csv" if security_dir.exists() else None
    
    if security_dir.exists():
        if not access_csv or not access_csv.exists():
            warnings.append("[WARN] security/ folder exists but missing ir.model.access.csv")
        else:
            info.append("[OK] security/ folder with ir.model.access.csv")
    else:
        # Check if module has models (then security is required)
        if models_dir.exists():
            warnings.append("[WARN] Module has models/ but no security/ folder (may need ir.model.access.csv)")
    
    # Check controllers folder
    controllers_dir = module_path / "controllers"
    controllers_init = controllers_dir / "__init__.py" if controllers_dir.exists() else None
    
    if controllers_dir.exists():
        if not controllers_init or not controllers_init.exists():
            warnings.append("[WARN] controllers/ folder exists but missing controllers/__init__.py")
        else:
            info.append("[OK] controllers/ folder with __init__.py")
    
    # Check static/description for icon
    static_desc = module_path / "static" / "description"
    if static_desc.exists():
        icon = static_desc / "icon.png"
        if icon.exists():
            info.append("[OK] static/description/icon.png exists")
        else:
            warnings.append("[WARN] static/description/ exists but no icon.png")
    
    return {
        'exists': True,
        'errors': errors,
        'warnings': warnings,
        'info': info,
        'path': str(module_path)
    }

def main():
    print("=" * 80)
    print("Module Structure Verification")
    print("=" * 80)
    print()
    
    all_ok = True
    
    for module_name in CUSTOM_MODULES:
        print(f"\n[CHECK] Checking: {module_name}")
        result = check_module_structure(module_name)
        
        if not result['exists']:
            print(f"  {result['errors'][0]}")
            all_ok = False
            continue
        
        # Print errors (critical)
        if result['errors']:
            all_ok = False
            for error in result['errors']:
                print(f"  {error}")
        
        # Print warnings (non-critical)
        if result['warnings']:
            for warning in result['warnings']:
                print(f"  {warning}")
        
        # Print info (good things)
        if result.get('info'):
            for info_msg in result['info']:
                print(f"  {info_msg}")
        
        # Summary
        if not result['errors']:
            if result['warnings']:
                print(f"  [OK] Structure OK (with warnings)")
            else:
                print(f"  [OK] Structure OK")
        else:
            print(f"  [ERROR] Structure has critical issues")
        
        print(f"  Path: {result['path']}")
    
    print("\n" + "=" * 80)
    if all_ok:
        print("[OK] All modules have correct structure!")
    else:
        print("[ERROR] Some modules have issues - fix before deploying")
    print("=" * 80)
    
    # Check for duplicate modules
    print("\n[CHECK] Checking for duplicate modules...")
    if (ADDONS_DIR / "ppt_event_management").exists() and (ADDONS_DIR / "ptt_event_management").exists():
        print("  [WARN] WARNING: Both 'ppt_event_management' and 'ptt_event_management' exist!")
        print("     This may cause confusion. Consider removing one.")
        print("     Recommended: Keep 'ptt_event_management' (single 'p')")

if __name__ == '__main__':
    main()
