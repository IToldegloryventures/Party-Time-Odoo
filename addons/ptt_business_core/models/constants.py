"""
Shared constants for PTT Business Core module.

Centralizes repeated definitions to avoid duplication per Odoo coding guidelines.
Reference: https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html
- "Favor readability over conciseness... avoid duplication"

These constants are used across multiple models:
- ptt.crm.service.line
- ptt.crm.vendor.assignment  
- ptt.project.vendor.assignment
"""

# Service type options for Selection fields
# Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#odoo.fields.Selection
SERVICE_TYPES = [
    ("dj", "DJ & MC Services"),
    ("photovideo", "Photo/Video"),
    ("live_entertainment", "Live Entertainment"),
    ("lighting", "Lighting/AV"),
    ("decor", "Decor/Thematic Design"),
    ("photobooth", "Photo Booth"),
    ("caricature", "Caricature Artist"),
    ("casino", "Casino Services"),
    ("catering", "Catering & Bartender Services"),
    ("transportation", "Transportation"),
    ("rentals", "Rentals (Other)"),
    ("staffing", "Staffing"),
    ("venue_sourcing", "Venue Sourcing"),
    ("coordination", "Event Planning Services"),
    ("other", "Other"),
]
