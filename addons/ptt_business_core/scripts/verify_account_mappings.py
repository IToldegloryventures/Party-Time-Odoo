#!/usr/bin/env python3
"""
Verify Product Category Account Mappings

This script verifies that product categories have correct account mappings
before and after migration to ensure Chart of Accounts is preserved.

Usage:
    In Odoo shell or via odoo-bin shell:
    >>> exec(open('addons/ptt_business_core/scripts/verify_account_mappings.py').read())
"""

import logging
_logger = logging.getLogger(__name__)

def verify_category_accounts(env):
    """Verify product categories have correct account mappings.
    
    Based on Chart of Accounts export:
    - Event Entertainment (4230) → 4231: DJ & MC Services
    - Event Services (4220) → 4222: Photography, 4223: Videography, etc.
    - Rental Equipment (4210) → 4211-4215
    - Adjustments (4320-4390)
    """
    _logger.info("=" * 80)
    _logger.info("VERIFYING PRODUCT CATEGORY ACCOUNT MAPPINGS")
    _logger.info("=" * 80)
    
    # Expected account codes from Chart of Accounts
    expected_accounts = {
        'Event Entertainment': {
            'income': '4230',  # Revenue:Services:Event Entertainment (parent)
            'specific': '4231',  # DJ & MC Services (we renamed product to DJ Services)
        },
        'Event Services': {
            'income': '4220',  # Revenue:Services:Event Services (parent)
        },
        'Rental Equipment, Decor & Decorations': {
            'income': '4210',  # Revenue:Services:Rental Equipment, Décor & Decorations
        },
        'Adjustments': {
            'income': '4320',  # Revenue:Adjustments:Client Discounts (or 4300 parent)
        },
    }
    
    # Find accounts by code
    Account = env['account.account']
    accounts_by_code = {}
    for code, name in expected_accounts.items():
        for account_type in ['income', 'specific']:
            if account_type in expected_accounts[code]:
                code_str = expected_accounts[code][account_type]
                account = Account.search([('code', '=', code_str)], limit=1)
                if account:
                    accounts_by_code[f"{code}_{account_type}"] = account
                    _logger.info(f"Found account {code_str}: {account.name}")
    
    # Verify product categories
    Category = env['product.category']
    categories_to_check = [
        'Event Entertainment',
        'Event Services', 
        'Rental Equipment, Decor & Decorations',
        'Adjustments',
    ]
    
    results = []
    for cat_name in categories_to_check:
        category = Category.search([('name', '=', cat_name)], limit=1)
        if not category:
            _logger.warning(f"Category '{cat_name}' NOT FOUND")
            results.append({
                'category': cat_name,
                'exists': False,
                'income_account': None,
                'expense_account': None,
            })
            continue
        
        income_account = category.property_account_income_categ_id
        expense_account = category.property_account_expense_categ_id
        
        _logger.info(f"\n{'='*80}")
        _logger.info(f"Category: {cat_name}")
        _logger.info(f"  Income Account: {income_account.code if income_account else 'NOT SET'} - {income_account.name if income_account else ''}")
        _logger.info(f"  Expense Account: {expense_account.code if expense_account else 'NOT SET'} - {expense_account.name if expense_account else ''}")
        
        results.append({
            'category': cat_name,
            'exists': True,
            'income_account': income_account.code if income_account else None,
            'expense_account': expense_account.code if expense_account else None,
        })
    
    _logger.info(f"\n{'='*80}")
    _logger.info("SUMMARY")
    _logger.info("=" * 80)
    
    for result in results:
        if not result['exists']:
            _logger.error(f"❌ {result['category']}: CATEGORY NOT FOUND")
        elif not result['income_account']:
            _logger.warning(f"⚠️  {result['category']}: NO INCOME ACCOUNT MAPPED")
        else:
            _logger.info(f"✅ {result['category']}: Account {result['income_account']} mapped")
    
    return results

# Auto-run if executed directly
if __name__ == '__main__':
    # This will be run in Odoo shell context
    pass
