# -*- coding: utf-8 -*-
"""Basic ACL coverage checks for key PTT models."""

from odoo.tests.common import TransactionCase


class TestSecurity(TransactionCase):
    """Ensure critical PTT models have at least one access rule."""

    def test_acl_presence(self):
        models_to_check = [
            "ptt.crm.service.line",
            "ptt.crm.vendor.estimate",
            "ptt.project.vendor.assignment",
        ]
        Access = self.env["ir.model.access"]
        for model in models_to_check:
            access = Access.search([("model_id.model", "=", model)], limit=1)
            self.assertTrue(access, f"Missing ACL for model {model}")
