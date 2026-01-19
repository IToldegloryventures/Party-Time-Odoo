# Part of Party Time Texas Event Management System
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class SaleOrderLine(models.Model):
    """Extend sale.order.line to include event details when creating projects.
    
    In Odoo 19, projects are created from sale order lines via the
    _timesheet_create_project() method. We extend this to:
    1. Include PTT event-specific fields when creating the project
    2. Create standard post-booking tasks for all events
    3. Create service-specific tasks based on services in the sale order
    """
    _inherit = 'sale.order.line'

    def _timesheet_create_project_prepare_values(self):
        """Extend project creation values with event-specific fields from the sale order.
        
        This is the proper Odoo 19 hook point for including custom fields when
        creating a project from a sale order line.
        """
        values = super()._timesheet_create_project_prepare_values()
        
        order = self.order_id
        if order.event_type_id or order.event_name:
            # Add Party Time Texas event fields
            event_vals = {
                'ptt_event_name': order.event_name,
                'ptt_guest_count': order.event_guest_count,
                'ptt_venue_name': order.event_venue,
                'ptt_setup_start_time': order.setup_time,
                'ptt_teardown_deadline': order.breakdown_time,
                'ptt_total_hours': order.event_duration,
            }
            
            if order.event_type_id:
                event_vals['ptt_event_type_id'] = order.event_type_id.id
            
            # Handle event_date (Datetime) -> project date fields
            if order.event_date:
                event_vals['ptt_event_date'] = order.event_date.date() if hasattr(order.event_date, 'date') else order.event_date
                event_vals['ptt_event_start_time'] = order.event_date
                if order.event_duration:
                    event_vals['ptt_event_end_time'] = fields.Datetime.add(order.event_date, hours=order.event_duration)
            
            # Link to CRM opportunity if available
            if order.opportunity_id:
                event_vals['ptt_crm_lead_id'] = order.opportunity_id.id
            
            values.update(event_vals)
        
        return values

    def _timesheet_create_project(self):
        """Override to create standard event tasks after project creation.
        
        This method is called when a sale order line with service_tracking
        'project_only' or 'task_in_project' is confirmed. We extend it to
        create the standard post-booking tasks for all events.
        """
        # Call parent to create the project
        project = super()._timesheet_create_project()
        
        # Check if this is an Event Kickoff product (creates project with standard tasks)
        if project and self.product_id.default_code == 'EVENT-KICKOFF':
            self._create_standard_event_tasks(project)
            self._create_service_specific_tasks(project)
        
        return project
    
    def _create_standard_event_tasks(self, project):
        """Create the 9 standard post-booking tasks for all event types.
        
        These tasks are the core workflow for every event, regardless of
        which specific services are included.
        """
        task_vals_list = []
        sequence = 0
        
        standard_tasks = [
            {
                'name': '1. Confirm Booking with Client',
                'description': '''• Send confirmation email stating contract signed + retainer received
• Reiterate event date, venue, time, and agreed services''',
            },
            {
                'name': '2. Collect Tier-3 Fulfillment Details',
                'description': '''• Venue access info (load-in times, restrictions, contacts)
• Rider / Equipment Setup specifications
• Vendor needs, power, staging, logistics
• Special requests (e.g. backup, transportation)''',
            },
            {
                'name': '3. Review Client Deliverables Checklist',
                'description': '''• Song selections (first dance, special requests)
• Timeline (ceremony, reception, breaks)
• Venue logistics (floor plan, layout)
• Contact point on event day
• Guest count confirmation''',
            },
            {
                'name': '4. Coordinate Vendor Assignments',
                'description': '''• Assign internal vendor(s) to event
• Provide vendors with relevant task list, rider info, schedule
• Confirm vendors' availability, rates, and contracts''',
            },
            {
                'name': '5. Vendor Brief & Confirmation',
                'description': '''• Confirm vendor requirements for equipment, load-in, contact person
• Confirm required documents (COI, contract, tax info)
• Confirm vendor acceptance''',
            },
            {
                'name': '6. Prepare Event Resources & Logistics',
                'description': '''• Inventory / equipment prep
• Transport / loading plan
• Backup gear / redundancy checks
• Power & staging setup plan''',
            },
            {
                'name': '7. Client Communications & Check-Ins',
                'description': '''• Execute appropriate check-ins
• Confirm all logistics 1-2 weeks prior
• Issue reminders for outstanding client tasks (song lists, special requests)''',
            },
            {
                'name': '8. Final Payment Check & Invoice Follow-up',
                'description': '''• Review invoice balance and confirm full payment status
• Flag and follow up on unpaid balances
• Update system status to "Final Payment Received"''',
            },
            {
                'name': '9. Post-Event Closure / Review',
                'description': '''• Confirm event ended as scheduled
• Gather client feedback / survey link
• Document lessons learned or special notes for future events''',
            },
        ]
        
        for task in standard_tasks:
            task_vals_list.append({
                'name': task['name'],
                'description': task['description'],
                'project_id': project.id,
                'sale_line_id': self.id,
                'partner_id': self.order_id.partner_id.id,
                'sequence': sequence,
            })
            sequence += 10
        
        if task_vals_list:
            self.env['project.task'].create(task_vals_list)
    
    def _create_service_specific_tasks(self, project):
        """Create service-specific placeholder tasks based on services in the sale order.
        
        These tasks are created as placeholders for each service type that was
        included in the sale order, giving the project manager a starting point
        for service-specific coordination.
        """
        task_vals_list = []
        sequence = 100  # Start after standard tasks
        order = self.order_id
        
        service_tasks = {
            'service_dj': [
                ('DJ: Music Consultation', 'Discuss music preferences, must-play/do-not-play lists, MC requirements'),
                ('DJ: Equipment Setup', 'Setup sound system, speakers, DJ booth per venue specs'),
                ('DJ: Event Service', 'Perform DJ services during event'),
                ('DJ: Equipment Breakdown', 'Pack and remove all DJ equipment'),
            ],
            'service_photo': [
                ('Photo: Pre-Event Consultation', 'Shot list review, timeline coordination, location scouting'),
                ('Photo: Event Coverage', 'Capture event photos per agreed timeline'),
                ('Photo: Post-Processing', 'Edit and process event photos'),
                ('Photo: Delivery', 'Deliver final photos to client'),
            ],
            'service_lighting': [
                ('Lighting: Design Review', 'Review lighting design and color scheme'),
                ('Lighting: Setup', 'Install lighting fixtures and test'),
                ('Lighting: Operation', 'Operate lighting during event'),
                ('Lighting: Breakdown', 'Remove lighting equipment'),
            ],
            'service_decor': [
                ('Decor: Design Finalization', 'Finalize decor design and materials'),
                ('Decor: Setup', 'Install decorations at venue'),
                ('Decor: Event Maintenance', 'Monitor and maintain decor during event'),
                ('Decor: Breakdown', 'Remove all decorations'),
            ],
            'service_photobooth': [
                ('Photo Booth: Setup', 'Install photo booth equipment and props'),
                ('Photo Booth: Operation', 'Staff and operate booth during event'),
                ('Photo Booth: Breakdown', 'Pack and remove photo booth'),
            ],
            'service_casino': [
                ('Casino: Setup', 'Setup casino tables and equipment'),
                ('Casino: Operation', 'Staff and operate casino games'),
                ('Casino: Breakdown', 'Remove casino equipment'),
            ],
            'service_staffing': [
                ('Staffing: Coordination', 'Assign and brief event staff'),
                ('Staffing: Event Day', 'Event staffing service'),
            ],
            'service_live': [
                ('Live Entertainment: Coordination', 'Coordinate with performers, confirm setlist'),
                ('Live Entertainment: Soundcheck', 'Performer soundcheck and setup'),
                ('Live Entertainment: Performance', 'Live performance during event'),
            ],
        }
        
        for service_field, tasks in service_tasks.items():
            if getattr(order, service_field, False):
                for task_name, task_desc in tasks:
                    task_vals_list.append({
                        'name': task_name,
                        'description': task_desc,
                        'project_id': project.id,
                        'sale_line_id': self.id,
                        'partner_id': self.order_id.partner_id.id,
                        'sequence': sequence,
                    })
                    sequence += 10
        
        if task_vals_list:
            self.env['project.task'].create(task_vals_list)
