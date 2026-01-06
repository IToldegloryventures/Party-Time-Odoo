# Party Time Texas - PTT Home Dashboard Hub
## Project Status & Task Summary
**Last Updated:** January 6, 2026
**Branch:** staging (DO NOT touch main branch)

---

## 🎯 PROJECT OVERVIEW

We are building a **PTT Home Dashboard Hub** - a unified "home" page for Party Time Texas in Odoo 19, similar to ClickUp's home page. It serves as a smart aggregation layer that pulls data from standard Odoo apps and provides one-click deep links to native Odoo forms.

**CRITICAL RULES:**
- DO NOT modify any standard Odoo views, accounting, or finance fields
- All data must be PULLED from native Odoo apps (no duplication)
- Every item must be clickable and open the native Odoo form
- This is a standalone app in the Odoo apps grid

---

## ✅ COMPLETED FEATURES

### 1. Home Page Layout (Grid-based, no overlap)
- **Row 1:** Event Tasks (full width) - Tasks from CRM-linked projects
  - Categories: Overdue, Today, Upcoming, Unscheduled
  - Equal-width boxes using `minmax(0, 1fr)`
- **Row 2:** Three columns
  - Other Tasks (with "Add Task" button for quick task creation)
  - Personal To-Do list
  - Assigned Comments (@mentions)
- **Row 3:** Agenda Calendar (full width at bottom)
  - Shows user's CRM events for next 14 days

### 2. Navigation Bar
- Apps button (grid icon) to return to Odoo main menu
- PTT Logo (needs image file - see PENDING TASKS)
- Tabs: Home | Sales Dashboard | Commission | Event Calendar
- User name display
- Refresh button

### 3. Event Calendar (Full Page)
- Shows ALL company-wide CRM events by default
- "My Events" toggle filter
- Stage-based color coding with legend
- Day panel on right showing selected date's events
- Click event → opens CRM Lead form

### 4. PTT CRM Stages (Official Pipeline)
Hardcoded stages with colors:
| Stage | Color | Purpose |
|-------|-------|---------|
| New | Teal (#17A2B8) | Fresh inquiries |
| Qualified | Orange (#F97316) | Contacted & qualified |
| Approval | Yellow (#FFC107) | Awaiting approval |
| Quote Sent | Purple (#6F42C1) | Proposal sent |
| Booked | Green (#28A745) | Confirmed (is_won=True) |
| Lost | Red (#DC3545) | Lost opportunity |

File: `data/crm_stages.xml` - Creates these stages in CRM on module update

### 5. Sales Dashboard
- Date range filter (This Month, Last Month, Quarter, Year, Custom)
- KPI Cards:
  - Total Booked Amount (from CRM leads in "Booked" stage)
  - Total Paid (paid invoices)
  - Outstanding/Overdue amounts
- Sales Rep Cards showing per-rep performance:
  - Avatar with initials
  - Booked amount & count
  - Lead count
  - Conversion rate with progress bar

### 6. Task Management
- **Event Tasks (My Work):** Tasks from projects linked to CRM leads
- **Other Tasks (Assigned to Me):** Standalone/non-event tasks
- **Add Task Button:** Quick task creation with assignee dropdown
- No overlap between sections (proper domain filtering)

### 7. Backend Services
- `ptt.home.data` - Abstract model for data aggregation
- `ptt.personal.todo` - Personal to-do items model
- `project_task_inherit.py` - Adds `x_task_category` computed field
- `project_project_inherit.py` - Adds `x_event_date` and `x_crm_lead_id` fields

### 8. Security
- Access rules in `ir.model.access.csv`
- Record rule for personal todos (users see only their own)
- Security groups defined in `ptt_security.xml`

---

## 🔄 PENDING TASKS (IN PROGRESS)

### 1. Logo Image (BLOCKED - file access issues)
**Status:** Code is ready, need to add image files
**Files needed:**
- `addons/ptt_operational_dashboard/static/description/icon.png` - Odoo app icon (128x128 square)
- `addons/ptt_operational_dashboard/static/src/img/logo.png` - Dashboard header logo

**Code already updated:**
- `home_navigation.xml` - Uses `<img>` tag for logo
- `home.scss` - Has `.ptt-logo-img` styles

**To complete:**
1. Save Party Time Texas logo (black background, gold "TX PARTY TIME" text)
2. Copy to both paths above
3. Test in browser

### 2. Role-Based Dashboard Views (NOT STARTED)
**Requirement:** 
- Regular users see only their own tasks/projects
- Managers/Executives (CEO, COO) see master view with everything

**To implement:**
- Add security groups for "PTT Dashboard User" vs "PTT Dashboard Manager"
- Modify backend methods to check user groups
- Show/hide "All Company" toggle based on permissions

---

## 📁 KEY FILES

### Python Models
- `models/ptt_home_data.py` - Main data aggregation service
- `models/ptt_personal_todo.py` - Personal to-do model
- `models/project_task_inherit.py` - Task category field
- `models/project_project_inherit.py` - Event date & CRM link fields

### Frontend Components
- `static/src/home_controller.js/xml` - Main controller
- `static/src/components/home_navigation.js/xml` - Top nav bar
- `static/src/components/my_work_section.js/xml` - Event tasks
- `static/src/components/assigned_tasks.js/xml` - Other tasks + Add Task
- `static/src/components/personal_todo.js/xml` - Personal to-dos
- `static/src/components/assigned_comments.js/xml` - @mentions
- `static/src/components/agenda_calendar.js/xml` - Agenda widget
- `static/src/components/event_calendar_full.js/xml` - Full calendar
- `static/src/components/sales_dashboard.js/xml` - Sales KPIs

### Styles
- `static/src/home.scss` - All dashboard styles

### Data Files
- `data/crm_stages.xml` - PTT CRM pipeline stages
- `security/ir.model.access.csv` - Access control
- `security/ptt_security.xml` - Groups & record rules

---

## 🔧 TECHNICAL NOTES

### Odoo 19 Specifics
- Use `import { user } from "@web/core/user";` (not `useService("user")`)
- XML search views: No `<group expand="0">` wrapper, flatten filters
- Use `minmax(0, 1fr)` in CSS grid to prevent content overflow
- JSON fields in migrations need `json.dumps()` for proper formatting

### Git Workflow
- All work on `staging` branch
- DO NOT touch `main` branch
- Odoo.sh auto-deploys from staging

### Module Dependencies
```python
"depends": [
    "base", "web", "mail", "project", "crm", 
    "sale", "account", "analytic", "sale_project"
]
```

---

## 📋 FUTURE FEATURES (NOT STARTED)

1. **Commission Dashboard** - Currently placeholder, needs full implementation
2. **Notifications/Alerts** - Real-time updates
3. **Dashboard Widgets** - Customizable widget placement
4. **Export/Reports** - PDF/Excel exports from dashboard
5. **Mobile Optimization** - Responsive design improvements

---

## 🐛 KNOWN ISSUES

1. **Logo not displaying** - Image files not yet added (see Pending Tasks)
2. **OneDrive sync issues** - User experiencing file access problems due to cloud sync

---

## 📞 CONTEXT FOR CONTINUATION

The user (Ashton) is the developer/owner of Party Time Texas, a tent/event rental company. They are following Odoo 19 official tutorials and want all code aligned with those docs.

**Key memories to respect:**
- Follow Odoo 19 Server Framework 101 tutorials
- Security: Use ir.model.access.csv with proper format
- Models: One model per file, use _name and _description
- Views: Actions before menus in manifest

**User preferences:**
- Don't push to GitHub after every change - wait for explicit "push" request
- Keep UI clean and user-friendly
- Everything must link back to native Odoo apps

