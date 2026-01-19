# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import models, fields, api, _

from odoo.addons.ptt_business_core.constants import (
    EVENT_TYPES,
    SERVICE_TYPES,
    COMMUNICATION_PREFERENCES,
)


class ProjectTemplate(models.Model):
    """Project Templates for Different Event Types"""
    _name = 'project.template'
    _description = 'Project Template for Event Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(
        string="Template Name",
        required=True,
        help="Name of the project template"
    )
    
    code = fields.Char(
        string="Template Code",
        help="Short code for the template"
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order of templates in selection lists"
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Uncheck to hide this template"
    )
    
    description = fields.Text(
        string="Description",
        help="Detailed description of this template"
    )
    
    # Template Category - matches the 3 event types from constants
    category = fields.Selection(
        selection=EVENT_TYPES,
        string="Event Category",
        required=True
    )
    
    # Default Project Settings
    default_project_name = fields.Char(
        string="Default Project Name Pattern",
        help="Pattern for project naming (e.g., 'Wedding - [CLIENT_NAME] - [EVENT_DATE]')"
    )
    
    # Project Privacy and Visibility
    privacy_visibility = fields.Selection([
        ('portal', 'Portal Users Only'),
        ('employees', 'All Internal Users'),
        ('followers', 'Followers Only'),
    ], string="Default Visibility", default='followers')
    
    # Default Duration and Scheduling
    default_project_duration = fields.Integer(
        string="Default Project Duration (Days)",
        help="Typical duration for projects using this template"
    )
    
    lead_time_days = fields.Integer(
        string="Lead Time (Days)",
        help="How many days before event date to start project"
    )
    
    # Task Template
    task_template_ids = fields.One2many(
        'project.task.template',
        'project_template_id',
        string="Task Templates",
        help="Default tasks to create for this project type"
    )
    
    # Stakeholder Template
    stakeholder_template_ids = fields.One2many(
        'project.stakeholder.template',
        'project_template_id', 
        string="Stakeholder Templates",
        help="Default stakeholders to assign for this project type"
    )
    
    # Resource Requirements
    requires_dj = fields.Boolean(string="Requires DJ/MC", default=False)
    requires_photo = fields.Boolean(string="Requires Photography", default=False)
    requires_lighting = fields.Boolean(string="Requires Lighting/AV", default=False)
    requires_decor = fields.Boolean(string="Requires Decoration", default=False)
    requires_venue_coordination = fields.Boolean(string="Requires Venue Coordination", default=True)
    
    # Color for visual identification
    color = fields.Integer(
        string="Color Index",
        help="Color for displaying this template in views"
    )
    
    def create_project_from_template(self, project_vals=None):
        """Create a project from this template"""
        if project_vals is None:
            project_vals = {}
        
        # Default project values from template
        template_vals = {
            'name': self.default_project_name or self.name,
            'privacy_visibility': self.privacy_visibility,
            'template_id': self.id,  # Link back to the template used
        }
        template_vals.update(project_vals)
        
        # Create the project
        project = self.env['project.project'].create(template_vals)
        
        # Create tasks from templates
        self._create_tasks_from_template(project)
        
        # Create stakeholders from templates
        self._create_stakeholders_from_template(project)
        
        return project
    
    def _create_tasks_from_template(self, project):
        """Create tasks from task templates"""
        task_vals_list = []
        
        for task_template in self.task_template_ids:
            task_vals = {
                'name': task_template.name,
                'description': task_template.description,
                'project_id': project.id,
                'sequence': task_template.sequence,
                'planned_hours': task_template.planned_hours,
                'user_ids': [(6, 0, task_template.user_ids.ids)] if task_template.user_ids else [],
                'tag_ids': [(6, 0, task_template.tag_ids.ids)] if task_template.tag_ids else [],
            }
            
            # Calculate dates if event date is available
            if hasattr(project, 'x_studio_event_date') and project.x_studio_event_date:
                event_date = project.x_studio_event_date
                if task_template.days_before_event:
                    task_vals['date_deadline'] = fields.Date.subtract(
                        event_date, 
                        days=task_template.days_before_event
                    )
                elif task_template.days_after_event:
                    task_vals['date_deadline'] = fields.Date.add(
                        event_date,
                        days=task_template.days_after_event
                    )
            
            task_vals_list.append(task_vals)
        
        if task_vals_list:
            self.env['project.task'].create(task_vals_list)
    
    def _create_stakeholders_from_template(self, project):
        """Create stakeholders from stakeholder templates"""
        stakeholder_vals_list = []
        
        for stakeholder_template in self.stakeholder_template_ids:
            # Skip stakeholder templates without a partner (partner_id is required)
            if not stakeholder_template.partner_id:
                continue
                
            stakeholder_vals = {
                'project_id': project.id,
                'partner_id': stakeholder_template.partner_id.id,
                'role': stakeholder_template.role,
                'responsibility': stakeholder_template.responsibility,
                'is_vendor': stakeholder_template.is_vendor,
                'is_client': stakeholder_template.is_client,
                'communication_preference': stakeholder_template.communication_preference,
            }
            stakeholder_vals_list.append(stakeholder_vals)
        
        if stakeholder_vals_list:
            self.env['project.stakeholder'].create(stakeholder_vals_list)


class ProjectTaskTemplate(models.Model):
    """Task Templates for Project Templates"""
    _name = 'project.task.template'
    _description = 'Project Task Template'
    _order = 'sequence, name'

    name = fields.Char(
        string="Task Name",
        required=True
    )
    
    description = fields.Text(
        string="Task Description"
    )
    
    project_template_id = fields.Many2one(
        'project.template',
        string="Project Template",
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10
    )
    
    planned_hours = fields.Float(
        string="Planned Hours"
    )
    
    # Scheduling relative to event date
    days_before_event = fields.Integer(
        string="Days Before Event",
        help="Schedule this task X days before the event date"
    )
    
    days_after_event = fields.Integer(
        string="Days After Event",
        help="Schedule this task X days after the event date"
    )
    
    # Default assignments
    user_ids = fields.Many2many(
        'res.users',
        string="Default Assignees"
    )
    
    tag_ids = fields.Many2many(
        'project.tags',
        string="Default Tags"
    )
    
    # Task characteristics
    is_milestone = fields.Boolean(
        string="Is Milestone",
        default=False
    )
    
    requires_vendor = fields.Boolean(
        string="Requires Vendor",
        help="This task requires vendor coordination"
    )
    
    vendor_category = fields.Selection(
        selection=SERVICE_TYPES,
        string="Vendor Category"
    )


class ProjectStakeholderTemplate(models.Model):
    """Stakeholder Templates for Project Templates"""
    _name = 'project.stakeholder.template'
    _description = 'Project Stakeholder Template'
    _order = 'sequence, role'

    project_template_id = fields.Many2one(
        'project.template',
        string="Project Template",
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10
    )
    
    # Default partner (can be overridden when creating project)
    partner_id = fields.Many2one(
        'res.partner',
        string="Default Partner",
        help="Default partner for this role (can be changed per project)"
    )
    
    role = fields.Char(
        string="Role",
        required=True,
        help="Role of this stakeholder (e.g., Event Coordinator, DJ, Photographer)"
    )
    
    responsibility = fields.Text(
        string="Responsibility",
        help="Description of this stakeholder's responsibilities"
    )
    
    # Stakeholder Type
    is_vendor = fields.Boolean(
        string="Is Vendor",
        default=False
    )
    
    is_client = fields.Boolean(
        string="Is Client",
        default=False
    )
    
    is_internal = fields.Boolean(
        string="Is Internal Team",
        default=True
    )
    
    # Communication
    communication_preference = fields.Selection(
        selection=COMMUNICATION_PREFERENCES,
        string="Preferred Communication",
        default='email'
    )
    
    # Service Category for Vendors - uses SERVICE_TYPES from constants.py
    vendor_category = fields.Selection(
        selection=SERVICE_TYPES,
        string="Vendor Category"
    )
    
    # Requirements
    required_for_event = fields.Boolean(
        string="Required for Event",
        default=True,
        help="This stakeholder is required for the event to proceed"
    )
