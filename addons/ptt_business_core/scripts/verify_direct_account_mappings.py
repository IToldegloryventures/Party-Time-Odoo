#!/usr/bin/env python3
"""
Verify Direct Product Account Mappings

This script checks if any products have direct account mappings
(property_account_income_id or property_account_expense_id) set directly
on the product, rather than inheriting from categories.

This is important for migration safety: if products have direct mappings,
they need to be verified after converting product.product to product.template.

Usage in Odoo.sh Shell:
    odoo-bin shell -d your_database -c config.conf
    >>> exec(open('addons/ptt_business_core/scripts/verify_direct_account_mappings.py').read())
    >>> results = verify_direct_account_mappings(env)
    >>> # Or just run the report:
    >>> report_direct_account_mappings(env)
"""

import logging
_logger = logging.getLogger(__name__)


def verify_direct_account_mappings(env):
    """
    Check for products with direct account mappings.
    
    Returns:
        dict: {
            'templates_with_direct_income': [...],
            'templates_with_direct_expense': [...],
            'products_with_direct_income': [...],
            'products_with_direct_expense': [...],
            'summary': {...}
        }
    """
    ProductTemplate = env['product.template']
    ProductProduct = env['product.product']
    
    # Check product.template records
    templates_with_direct_income = ProductTemplate.search([
        ('property_account_income_id', '!=', False)
    ])
    
    templates_with_direct_expense = ProductTemplate.search([
        ('property_account_expense_id', '!=', False)
    ])
    
    # Check product.product records
    products_with_direct_income = ProductProduct.search([
        ('property_account_income_id', '!=', False)
    ])
    
    products_with_direct_expense = ProductProduct.search([
        ('property_account_expense_id', '!=', False)
    ])
    
    # Get unique products (product.product is a view of product.template)
    # So we check if templates have direct mappings
    unique_products_income = products_with_direct_income.filtered(
        lambda p: not p.product_tmpl_id.property_account_income_id
    )
    
    unique_products_expense = products_with_direct_expense.filtered(
        lambda p: not p.product_tmpl_id.property_account_expense_id
    )
    
    summary = {
        'templates_with_direct_income_count': len(templates_with_direct_income),
        'templates_with_direct_expense_count': len(templates_with_direct_expense),
        'products_with_direct_income_count': len(unique_products_income),
        'products_with_direct_expense_count': len(unique_products_expense),
        'total_templates': ProductTemplate.search_count([]),
        'total_products': ProductProduct.search_count([]),
    }
    
    return {
        'templates_with_direct_income': templates_with_direct_income,
        'templates_with_direct_expense': templates_with_direct_expense,
        'products_with_direct_income': unique_products_income,
        'products_with_direct_expense': unique_products_expense,
        'summary': summary,
    }


def report_direct_account_mappings(env):
    """
    Print a detailed report of products with direct account mappings.
    """
    results = verify_direct_account_mappings(env)
    summary = results['summary']
    
    _logger.info("=" * 80)
    _logger.info("DIRECT PRODUCT ACCOUNT MAPPINGS VERIFICATION")
    _logger.info("=" * 80)
    _logger.info(f"\nSUMMARY:")
    _logger.info(f"  Total Templates: {summary['total_templates']}")
    _logger.info(f"  Total Products: {summary['total_products']}")
    _logger.info(f"\n  Templates with Direct Income Account: {summary['templates_with_direct_income_count']}")
    _logger.info(f"  Templates with Direct Expense Account: {summary['templates_with_direct_expense_count']}")
    _logger.info(f"  Products with Direct Income Account: {summary['products_with_direct_income_count']}")
    _logger.info(f"  Products with Direct Expense Account: {summary['products_with_direct_expense_count']}")
    
    # Report templates with direct income mappings
    if results['templates_with_direct_income']:
        _logger.info(f"\n{'='*80}")
        _logger.info(f"TEMPLATES WITH DIRECT INCOME ACCOUNT MAPPINGS ({len(results['templates_with_direct_income'])})")
        _logger.info("=" * 80)
        for template in results['templates_with_direct_income']:
            category_account = template.categ_id.property_account_income_categ_id
            direct_account = template.property_account_income_id
            _logger.info(f"\n  Template: {template.name} (ID: {template.id})")
            _logger.info(f"    Direct Income Account: {direct_account.code if direct_account else 'None'} - {direct_account.name if direct_account else ''}")
            _logger.info(f"    Category: {template.categ_id.name}")
            _logger.info(f"    Category Income Account: {category_account.code if category_account else 'None'} - {category_account.name if category_account else ''}")
            if direct_account and category_account and direct_account.id != category_account.id:
                _logger.info(f"    ⚠️  WARNING: Direct account differs from category account!")
    
    # Report templates with direct expense mappings
    if results['templates_with_direct_expense']:
        _logger.info(f"\n{'='*80}")
        _logger.info(f"TEMPLATES WITH DIRECT EXPENSE ACCOUNT MAPPINGS ({len(results['templates_with_direct_expense'])})")
        _logger.info("=" * 80)
        for template in results['templates_with_direct_expense']:
            category_account = template.categ_id.property_account_expense_categ_id
            direct_account = template.property_account_expense_id
            _logger.info(f"\n  Template: {template.name} (ID: {template.id})")
            _logger.info(f"    Direct Expense Account: {direct_account.code if direct_account else 'None'} - {direct_account.name if direct_account else ''}")
            _logger.info(f"    Category: {template.categ_id.name}")
            _logger.info(f"    Category Expense Account: {category_account.code if category_account else 'None'} - {category_account.name if category_account else ''}")
            if direct_account and category_account and direct_account.id != category_account.id:
                _logger.info(f"    ⚠️  WARNING: Direct account differs from category account!")
    
    # Report products with direct income mappings (not from template)
    if results['products_with_direct_income']:
        _logger.info(f"\n{'='*80}")
        _logger.info(f"PRODUCT VARIANTS WITH DIRECT INCOME ACCOUNT MAPPINGS ({len(results['products_with_direct_income'])})")
        _logger.info("=" * 80)
        for product in results['products_with_direct_income']:
            template_account = product.product_tmpl_id.property_account_income_id
            category_account = product.categ_id.property_account_income_categ_id
            direct_account = product.property_account_income_id
            _logger.info(f"\n  Product: {product.name} (ID: {product.id})")
            _logger.info(f"    Template: {product.product_tmpl_id.name}")
            _logger.info(f"    Direct Income Account: {direct_account.code if direct_account else 'None'} - {direct_account.name if direct_account else ''}")
            _logger.info(f"    Template Income Account: {template_account.code if template_account else 'None'} - {template_account.name if template_account else ''}")
            _logger.info(f"    Category Income Account: {category_account.code if category_account else 'None'} - {category_account.name if category_account else ''}")
    
    # Report products with direct expense mappings (not from template)
    if results['products_with_direct_expense']:
        _logger.info(f"\n{'='*80}")
        _logger.info(f"PRODUCT VARIANTS WITH DIRECT EXPENSE ACCOUNT MAPPINGS ({len(results['products_with_direct_expense'])})")
        _logger.info("=" * 80)
        for product in results['products_with_direct_expense']:
            template_account = product.product_tmpl_id.property_account_expense_id
            category_account = product.categ_id.property_account_expense_categ_id
            direct_account = product.property_account_expense_id
            _logger.info(f"\n  Product: {product.name} (ID: {product.id})")
            _logger.info(f"    Template: {product.product_tmpl_id.name}")
            _logger.info(f"    Direct Expense Account: {direct_account.code if direct_account else 'None'} - {direct_account.name if direct_account else ''}")
            _logger.info(f"    Template Expense Account: {template_account.code if template_account else 'None'} - {template_account.name if template_account else ''}")
            _logger.info(f"    Category Expense Account: {category_account.code if category_account else 'None'} - {category_account.name if category_account else ''}")
    
    # Final verdict
    _logger.info(f"\n{'='*80}")
    _logger.info("MIGRATION SAFETY VERDICT")
    _logger.info("=" * 80)
    
    total_risks = (
        summary['templates_with_direct_income_count'] +
        summary['templates_with_direct_expense_count'] +
        summary['products_with_direct_income_count'] +
        summary['products_with_direct_expense_count']
    )
    
    if total_risks == 0:
        _logger.info("✅ SAFE: No products have direct account mappings.")
        _logger.info("   All products inherit accounts from categories.")
        _logger.info("   Migration should preserve all account mappings.")
    else:
        _logger.info(f"⚠️  WARNING: {total_risks} product(s) have direct account mappings.")
        _logger.info("   These mappings should be verified after migration.")
        _logger.info("   If products are converted to templates, verify that:")
        _logger.info("   1. Direct account mappings are preserved")
        _logger.info("   2. Accounts still match category accounts (if expected)")
        _logger.info("   3. Variants inherit correct accounts from template")
    
    _logger.info("=" * 80)
    
    return results


# Quick check function for products we're converting
def check_conversion_targets(env):
    """
    Check if any of the products we're converting have direct account mappings.
    
    Products being converted:
    - DJ Services
    - Band Services
    - Casino Services
    - Catering Services
    - Photography Services
    - Videography Services
    - Photo Booths Rentals
    - Event Planning Services
    - Balloon & Face Painters
    - Dancers & Characters
    - Caricature Artist
    """
    conversion_targets = [
        'DJ Services',
        'Band Services',
        'Casino Services',
        'Catering Services',
        'Photography Services',
        'Videography Services',
        'Photo Booths Rentals',
        'Event Planning Services',
        'Balloon & Face Painters',
        'Dancers & Characters',
        'Caricature Artist',
    ]
    
    _logger.info("=" * 80)
    _logger.info("CHECKING CONVERSION TARGET PRODUCTS")
    _logger.info("=" * 80)
    
    ProductTemplate = env['product.template']
    risks_found = []
    
    for product_name in conversion_targets:
        templates = ProductTemplate.search([('name', 'ilike', product_name)])
        if not templates:
            _logger.info(f"  ⚠️  {product_name}: NOT FOUND")
            continue
        
        for template in templates:
            has_direct_income = bool(template.property_account_income_id)
            has_direct_expense = bool(template.property_account_expense_id)
            category_income = template.categ_id.property_account_income_categ_id
            
            if has_direct_income or has_direct_expense:
                risks_found.append({
                    'name': template.name,
                    'id': template.id,
                    'direct_income': template.property_account_income_id.code if has_direct_income else None,
                    'direct_expense': template.property_account_expense_id.code if has_direct_expense else None,
                    'category_income': category_income.code if category_income else None,
                })
                _logger.info(f"  ⚠️  {template.name} (ID: {template.id}):")
                if has_direct_income:
                    _logger.info(f"      Direct Income: {template.property_account_income_id.code} - {template.property_account_income_id.name}")
                if has_direct_expense:
                    _logger.info(f"      Direct Expense: {template.property_account_expense_id.code} - {template.property_account_expense_id.name}")
                if category_income:
                    _logger.info(f"      Category Income: {category_income.code} - {category_income.name}")
            else:
                _logger.info(f"  ✅ {template.name} (ID: {template.id}): No direct mappings (inherits from category)")
    
    if risks_found:
        _logger.info(f"\n⚠️  FOUND {len(risks_found)} product(s) with direct account mappings that need verification after migration.")
    else:
        _logger.info(f"\n✅ All conversion target products inherit accounts from categories - SAFE!")
    
    _logger.info("=" * 80)
    
    return risks_found


# Auto-run if executed directly
if __name__ == '__main__':
    # This will be run in Odoo shell context
    # Uncomment to auto-run:
    # report_direct_account_mappings(env)
    # check_conversion_targets(env)
    pass
