# -*- coding: utf-8 -*-
"""Tests for field optimization changes in PTT Business Core 4.5.0.

Tests cover:
- Datetime conversion from Float times + Event Date
- Related vendor_name field updates
- Field aggregator definitions
"""

from datetime import datetime
from odoo.tests.common import TransactionCase, tagged
from odoo import fields


@tagged('standard', 'at_install')
class TestDatetimeConversion(TransactionCase):
    """Test Float-to-Datetime conversion on project.project.

    Verifies that ptt_setup_start_time, ptt_event_start_time, and
    ptt_event_end_time are correctly computed from Float times + Date.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()

        # Create a CRM lead with event details
        cls.crm_lead = cls.env['crm.lead'].create({
            'name': 'Test Event Lead',
            'ptt_event_name': 'Datetime Conversion Test Event',
            'ptt_event_date': fields.Date.from_string('2026-06-15'),
            'ptt_setup_time': 14.5,      # 2:30 PM
            'ptt_start_time': 18.0,      # 6:00 PM
            'ptt_end_time': 22.25,       # 10:15 PM
        })

        # Create a project linked to the CRM lead
        cls.project = cls.env['project.project'].create({
            'name': 'Datetime Test Project',
            'ptt_crm_lead_id': cls.crm_lead.id,
        })

    def test_setup_start_time_computed(self):
        """Test ptt_setup_start_time is computed from date + float time."""
        # Setup time 14.5 = 2:30 PM on 2026-06-15
        expected = datetime(2026, 6, 15, 14, 30, 0)

        self.assertEqual(
            self.project.ptt_setup_start_time,
            expected,
            "Setup start time should be 2026-06-15 14:30:00"
        )

    def test_event_start_time_computed(self):
        """Test ptt_event_start_time is computed from date + float time."""
        # Start time 18.0 = 6:00 PM on 2026-06-15
        expected = datetime(2026, 6, 15, 18, 0, 0)

        self.assertEqual(
            self.project.ptt_event_start_time,
            expected,
            "Event start time should be 2026-06-15 18:00:00"
        )

    def test_event_end_time_computed(self):
        """Test ptt_event_end_time is computed from date + float time."""
        # End time 22.25 = 10:15 PM on 2026-06-15
        expected = datetime(2026, 6, 15, 22, 15, 0)

        self.assertEqual(
            self.project.ptt_event_end_time,
            expected,
            "Event end time should be 2026-06-15 22:15:00"
        )

    def test_datetime_recomputed_on_date_change(self):
        """Test datetime fields recompute when event date changes."""
        # Change the event date on CRM lead
        self.crm_lead.ptt_event_date = fields.Date.from_string('2026-07-20')

        # Invalidate cache to force recomputation
        self.project.invalidate_recordset()

        # Check the datetime updated
        self.assertEqual(
            self.project.ptt_event_start_time.date(),
            datetime(2026, 7, 20).date(),
            "Event start time should update to new date"
        )

    def test_datetime_recomputed_on_time_change(self):
        """Test datetime fields recompute when float time changes."""
        # Change the start time on CRM lead
        self.crm_lead.ptt_start_time = 19.5  # 7:30 PM

        # Invalidate cache to force recomputation
        self.project.invalidate_recordset()

        # Check the time updated
        expected = datetime(2026, 6, 15, 19, 30, 0)
        self.assertEqual(
            self.project.ptt_event_start_time,
            expected,
            "Event start time should update to 7:30 PM"
        )

    def test_datetime_handles_missing_date(self):
        """Test datetime fields handle missing event date gracefully."""
        # Create project without CRM link (no date)
        project_no_date = self.env['project.project'].create({
            'name': 'No Date Project',
        })

        self.assertFalse(
            project_no_date.ptt_event_start_time,
            "Datetime should be False when date is missing"
        )

    def test_datetime_handles_edge_times(self):
        """Test datetime conversion handles edge cases."""
        # Midnight
        self.crm_lead.ptt_start_time = 0.0
        self.project.invalidate_recordset()
        self.assertEqual(self.project.ptt_event_start_time.hour, 0)

        # 11:59 PM
        self.crm_lead.ptt_start_time = 23.983  # ~23:59
        self.project.invalidate_recordset()
        self.assertEqual(self.project.ptt_event_start_time.hour, 23)


@tagged('standard', 'at_install')
class TestRelatedVendorName(TransactionCase):
    """Test vendor_name related field behavior.

    Verifies that vendor_name field using related='vendor_id.name'
    properly updates when the vendor is changed or renamed.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()

        # Create test vendors
        cls.vendor1 = cls.env['res.partner'].create({
            'name': 'Original Vendor Name',
            'supplier_rank': 1,
        })

        cls.vendor2 = cls.env['res.partner'].create({
            'name': 'Second Vendor',
            'supplier_rank': 1,
        })

        # Create a project
        cls.project = cls.env['project.project'].create({
            'name': 'Vendor Test Project',
        })

        # Create vendor assignment
        cls.assignment = cls.env['ptt.project.vendor.assignment'].create({
            'project_id': cls.project.id,
            'service_type': 'dj',
            'vendor_id': cls.vendor1.id,
            'estimated_cost': 1000.00,
        })

    def test_vendor_name_populated_on_create(self):
        """Test vendor_name is populated when assignment is created."""
        self.assertEqual(
            self.assignment.vendor_name,
            'Original Vendor Name',
            "Vendor name should match vendor's name on create"
        )

    def test_vendor_name_updates_on_vendor_change(self):
        """Test vendor_name updates when vendor_id is changed."""
        self.assignment.vendor_id = self.vendor2
        self.assignment.invalidate_recordset()

        self.assertEqual(
            self.assignment.vendor_name,
            'Second Vendor',
            "Vendor name should update when vendor is changed"
        )

    def test_vendor_name_updates_on_vendor_rename(self):
        """Test vendor_name updates when vendor is renamed."""
        self.vendor1.name = 'Renamed Vendor Company'
        self.assignment.invalidate_recordset()

        self.assertEqual(
            self.assignment.vendor_name,
            'Renamed Vendor Company',
            "Vendor name should update when vendor is renamed"
        )

    def test_vendor_name_empty_when_no_vendor(self):
        """Test vendor_name is empty when no vendor assigned."""
        assignment_no_vendor = self.env['ptt.project.vendor.assignment'].create({
            'project_id': self.project.id,
            'service_type': 'photography',
            'estimated_cost': 500.00,
        })

        self.assertFalse(
            assignment_no_vendor.vendor_name,
            "Vendor name should be empty when no vendor assigned"
        )


@tagged('standard', 'at_install')
class TestFieldAggregators(TransactionCase):
    """Test field aggregator definitions.

    Verifies that monetary fields have proper aggregator definitions
    for group-by operations in views.
    """

    def test_project_monetary_fields_have_aggregators(self):
        """Test project monetary fields have sum aggregators."""
        Project = self.env['project.project']

        # Check aggregator attribute on fields
        fields_to_check = [
            'ptt_total_estimated_cost',
            'ptt_total_actual_cost',
            'ptt_cost_variance',
            'ptt_client_total',
            'ptt_actual_margin',
        ]

        for field_name in fields_to_check:
            field = Project._fields.get(field_name)
            self.assertIsNotNone(field, f"Field {field_name} should exist")
            self.assertEqual(
                field.aggregator,
                'sum',
                f"Field {field_name} should have aggregator='sum'"
            )

    def test_project_margin_percent_has_avg_aggregator(self):
        """Test margin percent field has avg aggregator."""
        Project = self.env['project.project']
        field = Project._fields.get('ptt_margin_percent')

        self.assertEqual(
            field.aggregator,
            'avg',
            "Margin percent should have aggregator='avg'"
        )

    def test_crm_monetary_fields_have_aggregators(self):
        """Test CRM lead monetary fields have sum aggregators."""
        CrmLead = self.env['crm.lead']

        fields_to_check = [
            'ptt_service_lines_total',
            'ptt_estimated_vendor_total',
            'ptt_estimated_client_total',
            'ptt_estimated_margin',
        ]

        for field_name in fields_to_check:
            field = CrmLead._fields.get(field_name)
            self.assertIsNotNone(field, f"Field {field_name} should exist")
            self.assertEqual(
                field.aggregator,
                'sum',
                f"Field {field_name} should have aggregator='sum'"
            )

    def test_crm_margin_percent_has_avg_aggregator(self):
        """Test CRM margin percent field has avg aggregator."""
        CrmLead = self.env['crm.lead']
        field = CrmLead._fields.get('ptt_margin_percent')

        self.assertEqual(
            field.aggregator,
            'avg',
            "CRM margin percent should have aggregator='avg'"
        )
