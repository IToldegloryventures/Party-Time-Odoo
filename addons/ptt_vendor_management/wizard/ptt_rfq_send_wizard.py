# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PttRfqSendWizard(models.TransientModel):
    """Wizard to select vendors and send RFQ invitations."""
    _name = "ptt.rfq.send.wizard"
    _description = "Send RFQ Wizard"

    rfq_id = fields.Many2one(
        "ptt.vendor.rfq",
        string="RFQ",
        required=True,
        readonly=True,
    )
    
    vendor_ids = fields.Many2many(
        "res.partner",
        "ptt_rfq_send_wizard_vendor_rel",
        "wizard_id",
        "partner_id",
        string="Select Vendors",
        domain="[('supplier_rank', '>', 0), ('is_company', '=', True)]",
        required=True,
    )
    
    service_type = fields.Selection(
        related="rfq_id.service_type",
        string="Service Type",
        readonly=True,
    )
    
    @api.model
    def default_get(self, fields_list):
        """Pre-populate with vendors already selected on RFQ."""
        res = super().default_get(fields_list)
        if self.env.context.get('active_id'):
            rfq = self.env['ptt.vendor.rfq'].browse(self.env.context['active_id'])
            res['rfq_id'] = rfq.id
            if rfq.vendor_ids:
                res['vendor_ids'] = [(6, 0, rfq.vendor_ids.ids)]
        return res
    
    def action_send(self):
        """Send RFQ invitations to selected vendors."""
        self.ensure_one()
        
        if not self.vendor_ids:
            raise UserError(_("Please select at least one vendor to invite."))
        
        # Update RFQ with selected vendors
        self.rfq_id.vendor_ids = self.vendor_ids
        
        # Call the send method
        return self.rfq_id.action_send_invitations()
