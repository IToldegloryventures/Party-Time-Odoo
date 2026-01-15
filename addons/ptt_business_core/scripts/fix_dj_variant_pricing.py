#!/usr/bin/env python3
"""
Fix DJ Service Variant Pricing

Manually set price_extra values on DJ service attribute values.
Run this in Odoo.sh shell if prices aren't updating when selecting variants.

Usage:
    odoo-bin shell
    >>> exec(open('addons/ptt_business_core/scripts/fix_dj_variant_pricing.py').read())
    >>> fix_dj_variant_pricing(env)
"""

PRICE_EXTRAS = {
    # Event Type extras (from Social base)
    'Social': 0.0,
    'Corporate': 0.0,
    'Wedding': 50.0,
    # Service Tier extras (from Essential base)
    'Essentials': 0.0,
    'Classic': 125.0,
    'Premier': 300.0,
}

def fix_dj_variant_pricing(env):
    """Manually fix DJ service variant pricing."""
    dj_template = env.ref('ptt_business_core.product_template_dj_services', raise_if_not_found=False)
    
    if not dj_template:
        print("ERROR: DJ Services template not found!")
        return
    
    print(f"Found DJ template: {dj_template.name} (ID: {dj_template.id})")
    print(f"Base price: ${dj_template.list_price}")
    print("\n" + "="*80)
    print("SETTING PRICE_EXTRAS ON ATTRIBUTE VALUES")
    print("="*80)
    
    updated_count = 0
    for attribute_line in dj_template.attribute_line_ids:
        print(f"\nAttribute Line: {attribute_line.attribute_id.name}")
        for ptav in attribute_line.product_template_value_ids:
            attr_value_name = ptav.product_attribute_value_id.name
            if attr_value_name in PRICE_EXTRAS:
                expected_extra = PRICE_EXTRAS[attr_value_name]
                old_extra = ptav.price_extra
                ptav.write({'price_extra': expected_extra})
                updated_count += 1
                status = "✅ UPDATED" if old_extra != expected_extra else "✓ OK"
                print(f"  {status} {attr_value_name}: ${old_extra} → ${expected_extra}")
            else:
                print(f"  ⚠️  {attr_value_name}: Not in PRICE_EXTRAS dict")
    
    print("\n" + "="*80)
    print(f"COMPLETE: Updated {updated_count} attribute value(s)")
    print("="*80)
    print("\nExpected prices after fix:")
    print("  Social + Essentials = $300 + $0 + $0 = $300")
    print("  Social + Classic = $300 + $0 + $125 = $425")
    print("  Social + Premier = $300 + $0 + $300 = $600")
    print("  Wedding + Essentials = $300 + $50 + $0 = $350")
    print("  Wedding + Classic = $300 + $50 + $125 = $475")
    print("  Wedding + Premier = $300 + $50 + $300 = $650")
