"""
Apply variant pricing to products with [UPDATED] in their names.

Run this in Odoo shell to manually trigger the pricing configuration.
"""

# Copy the SERVICE_PRICING config from __init__.py
SERVICE_PRICING = {
    'DJ Services [UPDATED]': {
        'Event Type': {'Social': 0.0, 'Corporate': 0.0, 'Wedding': 50.0},
        'Service Tier': {'Essentials': 0.0, 'Classic': 125.0, 'Premier': 300.0}
    }
}

# Find Event Type and Service Tier attributes
event_type_attr = env['product.attribute'].search([('name', '=', 'Event Type')], limit=1)
service_tier_attr = env['product.attribute'].search([('name', '=', 'Service Tier')], limit=1)

if not event_type_attr or not service_tier_attr:
    print("ERROR: Event Type or Service Tier attributes not found!")
else:
    # Find all templates with both attributes
    all_templates = env['product.template'].search([
        ('attribute_line_ids.attribute_id', 'in', [event_type_attr.id, service_tier_attr.id])
    ])
    
    # Filter to only those with BOTH attributes
    services = env['product.template']
    for template in all_templates:
        has_event_type = any(line.attribute_id.id == event_type_attr.id for line in template.attribute_line_ids)
        has_service_tier = any(line.attribute_id.id == service_tier_attr.id for line in template.attribute_line_ids)
        if has_event_type and has_service_tier:
            services |= template
    
    total_updated = 0
    services_configured = []
    
    for service in services.sorted('name'):
        service_name = service.name
        service_config = SERVICE_PRICING.get(service_name)
        
        # If not found and product has [UPDATED] suffix, try matching without it
        if not service_config and '[UPDATED]' in service_name:
            base_name = service_name.replace(' [UPDATED]', '')
            service_config = SERVICE_PRICING.get(f"{base_name} [UPDATED]") or SERVICE_PRICING.get(base_name)
        
        # Skip if no explicit configuration
        if not service_config:
            continue
        
        service_updated = 0
        
        # Update Event Type pricing
        if 'Event Type' in service_config:
            event_type_line = service.attribute_line_ids.filtered(lambda l: l.attribute_id.name == 'Event Type')
            if event_type_line:
                for ptav in event_type_line.product_template_value_ids:
                    attr_value_name = ptav.product_attribute_value_id.name
                    if attr_value_name in service_config['Event Type']:
                        expected_extra = service_config['Event Type'][attr_value_name]
                        ptav.write({'price_extra': expected_extra})
                        service_updated += 1
                        print(f"Set {service_name} - Event Type {attr_value_name}: ${expected_extra}")
        
        # Update Service Tier pricing
        if 'Service Tier' in service_config:
            service_tier_line = service.attribute_line_ids.filtered(lambda l: l.attribute_id.name == 'Service Tier')
            if service_tier_line:
                for ptav in service_tier_line.product_template_value_ids:
                    attr_value_name = ptav.product_attribute_value_id.name
                    if attr_value_name in service_config['Service Tier']:
                        expected_extra = service_config['Service Tier'][attr_value_name]
                        ptav.write({'price_extra': expected_extra})
                        service_updated += 1
                        print(f"Set {service_name} - Service Tier {attr_value_name}: ${expected_extra}")
        
        if service_updated > 0:
            total_updated += service_updated
            services_configured.append(service_name)
    
    if total_updated > 0:
        print(f"\n✅ Configured pricing for {len(services_configured)} service(s): {', '.join(services_configured)}")
        print(f"✅ Updated {total_updated} price_extra values total!")
    else:
        print("No pricing updates needed.")
