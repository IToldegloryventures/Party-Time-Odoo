# -*- coding: utf-8 -*-
# Part of Party Time Texas Event Management System
# Email Safety Override - Prevents accidental emails during migration

import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

# ============================================================
# EMAIL KILL SWITCH
# Set to True to BLOCK all outgoing emails
# Set to False to allow normal email operation
# ============================================================
BLOCK_ALL_EMAILS = False  # Production: emails enabled
# ============================================================


class MailMail(models.Model):
    """Override mail.mail to optionally block all email sending."""
    _inherit = "mail.mail"

    def send(self, auto_commit=False, raise_exception=False):
        """Block email sending if kill switch is enabled."""
        if BLOCK_ALL_EMAILS:
            _logger.warning(
                "EMAIL BLOCKED by ptt_business_core kill switch! "
                "Would have sent %d email(s). Set BLOCK_ALL_EMAILS=False to enable.",
                len(self)
            )
            # Mark as sent without actually sending (prevents re-attempts)
            self.write({'state': 'sent'})
            return True
        
        return super().send(auto_commit=auto_commit, raise_exception=raise_exception)
