#!/usr/bin/env python3
"""
Initialize Variant Pricing for All Services

Run this in Odoo.sh shell to initialize price_extra values for all services.
This ensures prices update dynamically when selecting Event Type and Service Tier.

Usage:
    odoo-bin shell
    >>> exec(open('addons/ptt_business_core/scripts/init_variant_pricing.py').read())
    >>> init_all_variant_pricing(env)
"""

def init_all_variant_pricing(env):
    """Initialize price_extra for all services with Event Type and Service Tier attributes."""
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
    
    # Find Event Type and Service Tier attributes
    event_type_attr = env['product.attribute'].search([('name', '=', 'Event Type')], limit=1)
    service_tier_attr = env['product.attribute'].search([('name', '=', 'Service Tier')], limit=1)
    
    if not event_type_attr or not service_tier_attr:
        print("ERROR: Event Type or Service Tier attributes not found!")
        return
    
    # Find all templates with both attributes
    all_templates = env['product.template'].search([
        ('attribute_line_ids.attribute_id', 'in', [event_type_attr.id, service_tier_attr.id])
    ])
    
    services = env['product.template']
    for template in all_templates:
        has_event_type = any(line.attribute_id.id == event_type_attr.id for line in template.attribute_line_ids)
        has_service_tier = any(line.attribute_id.id == service_tier_attr.id for line in template.attribute_line_ids)
        if has_event_type and has_service_tier:
            services |= template
    
    print(f"\n{'='*80}")
    print(f"INITIALIZING VARIANT PRICING FOR {len(services)} SERVICE(S)")
    print(f"{'='*80}\n")
    
    total_updated = 0
    for service in services.sorted('name'):
        print(f"Service: {service.name}")
        service_updated = 0
        
        # Update Event Type pricing
        event_type_line = service.attribute_line_ids.filtered(lambda l: l.attribute_id.name == 'Event Type')
        if event_type_line:
            for ptav in event_type_line.product_template_value_ids:
                attr_name = ptav.product_attribute_value_id.name
                if attr_name in PRICE_EXTRAS:
                    expected = PRICE_EXTRAS[attr_name]
                    if ptav.price_extra != expected:
                        ptav.write({'price_extra': expected})
                        print(f"  ✅ {attr_name}: ${ptav.price_extra:.2f}")
                        service_updated += 1
                    else:
                        print(f"  ✓  {attr_name}: ${ptav.price_extra:.2f} (already set)")
        
        # Update Service Tier pricing
        service_tier_line = service.attribute_line_ids.filtered(lambda l: l.attribute_id.name == 'Service Tier')
        if service_tier_line:
            for ptav in service_tier_line.product_template_value_ids:
                attr_name = ptav.product_attribute_value_id.name
                if attr_name in PRICE_EXTRAS:
                    expected = PRICE_EXTRAS[attr_name]
                    if ptav.price_extra != expected:
                        ptav.write({'price_extra': expected})
                        print(f"  ✅ {attr_name}: ${ptav.price_extra:.2f}")
                        service_updated += 1
                    else:
                        print(f"  ✓  {attr_name}: ${ptav.price_extra:.2f} (already set)")
        
        if service_updated > 0:
            total_updated += service_updated
        print()
    
    print(f"{'='*80}")
    print(f"COMPLETE: Updated {total_updated} price_extra value(s) across {len(services)} service(s)")
    print(f"{'='*80}")
    print("\n💡 Pricing should now update dynamically in the product configurator!")
    print("   Example: DJ Services (Wedding, Classic) = $300 + $50 + $125 = $475")
