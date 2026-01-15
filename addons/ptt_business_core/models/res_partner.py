from odoo import models, fields, api


class ResPartner(models.Model):
    """Extend res.partner for PTT business core.
    
    NOTE: Vendor management fields have been moved to ptt_vendor_management module.
    This module contains only core business partner fields.
    """
    _inherit = "res.partner"
