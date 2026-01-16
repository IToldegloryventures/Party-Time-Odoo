from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PttVariantPricingConfig(models.TransientModel):
    """
    Wizard to configure variant pricing (price_extra) for all services.
    
    This wizard allows easy editing of Event Type and Service Tier pricing
    for all products that have these attributes.
    """
    _name = 'ptt.variant.pricing.config'
    _description = 'Variant Pricing Configuration'

    service_line_ids = fields.One2many(
        'ptt.variant.pricing.config.line',
        'config_id',
        string='Service Pricing',
        help='Configure pricing for each service'
    )

    @api.model
    def _get_all_services_with_variants(self):
        """Find all product templates with Event Type and Service Tier attributes."""
        # Find Event Type and Service Tier attribute IDs
        event_type_attr = self.env['product.attribute'].search([
            ('name', '=', 'Event Type')
        ], limit=1)
        service_tier_attr = self.env['product.attribute'].search([
            ('name', '=', 'Service Tier')
        ], limit=1)
        
        if not event_type_attr or not service_tier_attr:
            return self.env['product.template']
        
        # Find all templates that have both attributes
        templates = self.env['product.template'].search([
            ('attribute_line_ids.attribute_id', 'in', [event_type_attr.id, service_tier_attr.id])
        ])
        
        # Filter to only those with BOTH attributes
        result = self.env['product.template']
        for template in templates:
            has_event_type = any(
                line.attribute_id.id == event_type_attr.id 
                for line in template.attribute_line_ids
            )
            has_service_tier = any(
                line.attribute_id.id == service_tier_attr.id 
                for line in template.attribute_line_ids
            )
            if has_event_type and has_service_tier:
                result |= template
        
        return result.sorted('name')

    @api.model
    def default_get(self, fields_list):
        """Load all services with variant pricing."""
        res = super().default_get(fields_list)
        
        services = self._get_all_services_with_variants()
        lines = []
        
        for service in services:
            # Get Event Type attribute line
            event_type_line = service.attribute_line_ids.filtered(
                lambda l: l.attribute_id.name == 'Event Type'
            )
            service_tier_line = service.attribute_line_ids.filtered(
                lambda l: l.attribute_id.name == 'Service Tier'
            )
            
            if not event_type_line or not service_tier_line:
                continue
            
            # Get attribute values
            event_type_values = event_type_line.product_template_value_ids
            service_tier_values = service_tier_line.product_template_value_ids
            
            # Helper to get price_extra safely
            def get_price_extra(values, attr_name):
                matched = values.filtered(lambda v: v.product_attribute_value_id.name == attr_name)
                if matched:
                    # Get price_extra from first matched record
                    return matched[0].price_extra
                return 0.0
            
            lines.append((0, 0, {
                'service_id': service.id,
                'service_name': service.name,
                'event_type_social_extra': get_price_extra(event_type_values, 'Social'),
                'event_type_corporate_extra': get_price_extra(event_type_values, 'Corporate'),
                'event_type_wedding_extra': get_price_extra(event_type_values, 'Wedding'),
                'tier_essentials_extra': get_price_extra(service_tier_values, 'Essentials'),
                'tier_classic_extra': get_price_extra(service_tier_values, 'Classic'),
                'tier_premier_extra': get_price_extra(service_tier_values, 'Premier'),
            }))
        
        res['service_line_ids'] = lines
        return res

    def action_save(self):
        """Save price_extra values to product.template.attribute.value records."""
        for line in self.service_line_ids:
            service = line.service_id
            
            # Update Event Type attribute values
            event_type_line = service.attribute_line_ids.filtered(
                lambda l: l.attribute_id.name == 'Event Type'
            )
            if event_type_line:
                for ptav in event_type_line.product_template_value_ids:
                    attr_name = ptav.product_attribute_value_id.name
                    if attr_name == 'Social':
                        ptav.price_extra = line.event_type_social_extra
                    elif attr_name == 'Corporate':
                        ptav.price_extra = line.event_type_corporate_extra
                    elif attr_name == 'Wedding':
                        ptav.price_extra = line.event_type_wedding_extra
            
            # Update Service Tier attribute values
            service_tier_line = service.attribute_line_ids.filtered(
                lambda l: l.attribute_id.name == 'Service Tier'
            )
            if service_tier_line:
                for ptav in service_tier_line.product_template_value_ids:
                    attr_name = ptav.product_attribute_value_id.name
                    if attr_name == 'Essentials':
                        ptav.price_extra = line.tier_essentials_extra
                    elif attr_name == 'Classic':
                        ptav.price_extra = line.tier_classic_extra
                    elif attr_name == 'Premier':
                        ptav.price_extra = line.tier_premier_extra
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Variant pricing has been updated for all services.'),
                'type': 'success',
                'sticky': False,
            }
        }


class PttVariantPricingConfigLine(models.TransientModel):
    """Individual service pricing configuration line."""
    _name = 'ptt.variant.pricing.config.line'
    _description = 'Variant Pricing Configuration Line'

    config_id = fields.Many2one(
        'ptt.variant.pricing.config',
        string='Configuration',
        required=True,
        ondelete='cascade'
    )
    service_id = fields.Many2one(
        'product.template',
        string='Service',
        required=True,
        readonly=True
    )
    service_name = fields.Char(
        string='Service Name',
        readonly=True
    )
    
    # Event Type pricing
    event_type_social_extra = fields.Float(
        string='Social Extra',
        default=0.0,
        help='Additional price for Social event type. Base price + this = total.',
    )
    event_type_corporate_extra = fields.Float(
        string='Corporate Extra',
        default=0.0,
        help='Additional price for Corporate event type. Base price + this = total.',
    )
    event_type_wedding_extra = fields.Float(
        string='Wedding Extra',
        default=50.0,
        help='Additional price for Wedding event type. Base price + this = total.',
    )
    
    # Service Tier pricing
    tier_essentials_extra = fields.Float(
        string='Essentials Extra',
        default=0.0,
        help='Additional price for Essentials tier. Base price + this = total.',
    )
    tier_classic_extra = fields.Float(
        string='Classic Extra',
        default=125.0,
        help='Additional price for Classic tier. Base price + this = total.',
    )
    tier_premier_extra = fields.Float(
        string='Premier Extra',
        default=300.0,
        help='Additional price for Premier tier. Base price + this = total.',
    )
    
    # NOTE: For transient models, use lambda for defaults (method references don't bind correctly)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        readonly=True,
        help='Company currency for monetary fields.',
    )
