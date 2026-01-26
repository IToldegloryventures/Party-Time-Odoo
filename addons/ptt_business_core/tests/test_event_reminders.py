# -*- coding: utf-8 -*-
"""Tests for Event Reminder Cron Jobs feature.

Feature 3: Event Reminder Cron Jobs
- 10-day reminder sends email to project managers
- 3-day urgent reminder for final preparations
- Identifies incomplete tasks and missing information
"""

from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase


class TestEventReminders(TransactionCase):
    """Test event reminder cron job functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        # Create test partner (client)
        cls.partner = cls.env['res.partner'].create({
            'name': 'Event Reminder Test Client',
            'email': 'client@example.com',
        })
        
        # Create test user (project manager)
        cls.pm_user = cls.env['res.users'].create({
            'name': 'Test Project Manager',
            'login': 'test_pm_reminder',
            'email': 'pm@partytimetexas.com',
        })
        
        # Create test vendor partner
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Test DJ Vendor',
            'email': 'vendor@example.com',
            'supplier_rank': 1,
        })
    
    def _create_project_for_date(self, event_date, **kwargs):
        """Helper to create a project with specific event date via CRM lead."""
        lead_vals = {
            'name': 'Test Event Lead',
            'partner_id': self.partner.id,
            'user_id': self.pm_user.id,
            'ptt_event_name': 'Test Event',
            'ptt_event_date': event_date,
            'ptt_event_type': 'corporate',
            'ptt_venue_name': 'Test Venue',
            'ptt_venue_address': '123 Test St',
            'ptt_guest_count': 100,
            'ptt_start_time': '8.0',
            'ptt_setup_time': '7.0',
        }
        lead_vals.update(kwargs)
        lead = self.env['crm.lead'].create(lead_vals)
        lead.action_create_project()
        return lead.ptt_project_id
    
    def test_find_projects_10_days_out(self):
        """Test finding projects with events 10 days from now."""
        target_date = fields.Date.today() + timedelta(days=10)
        project = self._create_project_for_date(target_date)
        
        # Project should be found
        projects = self.env['project.project'].search([
            ('ptt_event_date', '=', target_date),
            ('active', '=', True),
        ])
        
        self.assertIn(project, projects)
    
    def test_find_projects_3_days_out(self):
        """Test finding projects with events 3 days from now."""
        target_date = fields.Date.today() + timedelta(days=3)
        project = self._create_project_for_date(target_date)
        
        # Project should be found
        projects = self.env['project.project'].search([
            ('ptt_event_date', '=', target_date),
            ('active', '=', True),
        ])
        
        self.assertIn(project, projects)
    
    def test_project_not_found_wrong_date(self):
        """Test that projects with different dates are not found."""
        # Create project for 5 days out (not 10 or 3)
        target_date = fields.Date.today() + timedelta(days=5)
        project = self._create_project_for_date(target_date)
        
        # Search for 10-day projects
        ten_day_date = fields.Date.today() + timedelta(days=10)
        projects = self.env['project.project'].search([
            ('ptt_event_date', '=', ten_day_date),
            ('active', '=', True),
        ])
        
        self.assertNotIn(project, projects)
    
    def test_get_missing_information_complete(self):
        """Test missing info check with complete project."""
        target_date = fields.Date.today() + timedelta(days=10)
        # Note: ptt_event_start_time is a computed Datetime field (from Date + Selection time)
        # It cannot be set directly - only through CRM Lead's Selection time fields
        project = self._create_project_for_date(target_date)
        
        missing = project._get_missing_information()
        
        # Should not have basic missing info (venue, address, guest count set)
        self.assertNotIn('Venue name not set', [str(m) for m in missing])
        self.assertNotIn('Guest count not set', [str(m) for m in missing])
    
    def test_get_missing_information_incomplete(self):
        """Test missing info check with incomplete project."""
        target_date = fields.Date.today() + timedelta(days=10)
        project = self._create_project_for_date(
            target_date,
            ptt_venue_name=False,
            ptt_venue_address=False,
            ptt_guest_count=0,
        )
        
        missing = project._get_missing_information()
        
        # Should flag missing info
        missing_strs = [str(m) for m in missing]
        self.assertTrue(any('Venue name' in m for m in missing_strs))
        self.assertTrue(any('Guest count' in m for m in missing_strs))
    
    def test_get_incomplete_tasks(self):
        """Test getting incomplete tasks for a project."""
        target_date = fields.Date.today() + timedelta(days=10)
        project = self._create_project_for_date(target_date)
        
        # Create some tasks
        open_stage = self.env['project.task.type'].create({
            'name': 'To Do',
            'fold': False,
        })
        done_stage = self.env['project.task.type'].create({
            'name': 'Done',
            'fold': True,
        })
        
        task_open = self.env['project.task'].create({
            'name': 'Incomplete Task',
            'project_id': project.id,
            'stage_id': open_stage.id,
        })
        task_done = self.env['project.task'].create({
            'name': 'Completed Task',
            'project_id': project.id,
            'stage_id': done_stage.id,
        })
        
        incomplete = project._get_incomplete_tasks()
        
        self.assertIn(task_open, incomplete)
        self.assertNotIn(task_done, incomplete)
    
    def test_cron_method_exists(self):
        """Test that cron methods exist and are callable."""
        Project = self.env['project.project']
        
        # These should exist and not raise
        self.assertTrue(hasattr(Project, '_cron_send_event_reminders_10_day'))
        self.assertTrue(hasattr(Project, '_cron_send_event_reminders_3_day'))
        self.assertTrue(callable(getattr(Project, '_cron_send_event_reminders_10_day')))
        self.assertTrue(callable(getattr(Project, '_cron_send_event_reminders_3_day')))
    
    @patch('odoo.addons.mail.models.mail_template.MailTemplate.send_mail')
    def test_send_reminders_calls_template(self, mock_send_mail):
        """Test that reminders trigger email sending."""
        target_date = fields.Date.today() + timedelta(days=10)
        project = self._create_project_for_date(target_date)
        
        # Mock the template lookup to return a mock template
        mock_send_mail.return_value = True
        
        # Use existing template if present; otherwise create a test-only one with a unique XMLID
        template = self.env.ref(
            'ptt_business_core.email_template_event_reminder_10_day',
            raise_if_not_found=False,
        ) or self.env['mail.template'].create({
            'name': 'Test 10-Day Reminder',
            'model_id': self.env.ref('project.model_project_project').id,
        })
        self.env['ir.model.data']._update(
            'ptt_business_core', 'email_template_event_reminder_10_day_test', {
                'model': 'mail.template',
                'res_id': template.id,
                'noupdate': True,
            }, noupdate=True, mode='init'
        )
        
        # Call the cron method
        self.env['project.project']._cron_send_event_reminders_10_day()
        
        # Verify send_mail was called
        mock_send_mail.assert_called()
    
    def test_no_error_when_no_projects(self):
        """Test cron doesn't error when no projects match."""
        # Don't create any projects - just run cron
        # Should complete without error
        self.env['project.project']._cron_send_event_reminders_10_day()
        self.env['project.project']._cron_send_event_reminders_3_day()


class TestVendorConfirmation(TransactionCase):
    """Test vendor confirmation checking for reminders."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test data."""
        super().setUpClass()
        
        cls.partner = cls.env['res.partner'].create({
            'name': 'Vendor Check Client',
            'email': 'vclient@example.com',
        })
        
        cls.vendor = cls.env['res.partner'].create({
            'name': 'Check DJ Vendor',
            'email': 'vdj@example.com',
            'supplier_rank': 1,
        })
        
        cls.pm_user = cls.env['res.users'].create({
            'name': 'Vendor Check PM',
            'login': 'test_vc_pm',
            'email': 'vcpm@example.com',
        })
    
    def test_get_unconfirmed_vendors(self):
        """Test getting unconfirmed vendor assignments."""
        project = self.env['project.project'].create({
            'name': 'Vendor Check Project',
            'partner_id': self.partner.id,
            'user_id': self.pm_user.id,
            'ptt_event_date': fields.Date.today() + timedelta(days=10),
        })
        
        # Create vendor assignments with different statuses
        VendorAssignment = self.env['ptt.project.vendor.assignment']
        
        # Check if status field exists
        if 'status' in VendorAssignment._fields:
            pending = VendorAssignment.create({
                'project_id': project.id,
                'vendor_id': self.vendor.id,
                'service_type': 'dj',
                'status': 'pending',
            })
            confirmed = VendorAssignment.create({
                'project_id': project.id,
                'vendor_id': self.vendor.id,
                'service_type': 'lighting',
                'status': 'confirmed',
            })
            
            unconfirmed = project._get_unconfirmed_vendors()
            
            self.assertIn(pending, unconfirmed)
            self.assertNotIn(confirmed, unconfirmed)
