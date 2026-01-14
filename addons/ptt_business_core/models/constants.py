"""
Shared constants for PTT Business Core module.

Centralizes repeated definitions to avoid duplication per Odoo coding guidelines.
Reference: https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html
- "Favor readability over conciseness... avoid duplication"

These constants are used across multiple models:
- ptt.crm.service.line
- ptt.crm.vendor.assignment  
- ptt.project.vendor.assignment
- res.partner (via ptt_vendor_management)
"""

# =============================================================================
# SERVICE TIERS - Used for vendor matching and product variants
# =============================================================================
# MIGRATION NOTE (v19.0.5.0.0): Changed from gold/silver/bronze/platinum to:
# - essentials: Basic service level
# - classic: Standard service level  
# - premier: Premium service level
# Reference: Internal meeting Jan 2026 - aligns with pricing calculator
SERVICE_TIERS = [
    ("essentials", "Essentials"),
    ("classic", "Classic"),
    ("premier", "Premier"),
]

# =============================================================================
# SERVICE TYPES - Aligned with QuickBooks categories (Jan 2026)
# =============================================================================
# Reference: https://www.odoo.com/documentation/19.0/developer/reference/backend/orm.html#odoo.fields.Selection
# Categories from QuickBooks: Event Entertainment, Event Services, Rental Equipment, Adjustments
SERVICE_TYPES = [
    # === Event Entertainment (Income 4230s) ===
    ("dj", "DJ & MC Services"),
    ("band", "Band Services"),
    ("musician", "Musician Services"),
    ("dancer", "Dancers & Characters"),
    ("balloon_face", "Balloon & Face Painters"),
    ("psychic", "Psychics & Magicians"),
    ("casino", "Casino Services"),
    ("event_planning", "Event Planning Services"),
    
    # === Event Services (Income 4220s) ===
    ("catering", "Catering & Bartender Services"),
    ("photography", "Photography Services"),
    ("videography", "Videography Services"),
    ("caricature", "Caricature Artist"),
    
    # === Rental Equipment, Décor & Decorations (Income 4210s) ===
    ("balloon_decor", "Balloon Décor"),
    ("furniture", "Furniture Rentals"),
    ("decor", "Misc Décor & Decorations"),
    ("inflatables", "Inflatables & Games Rentals"),
    ("av_rental", "A/V Rentals"),
    ("lighting", "Lighting Rentals"),
    ("photobooth", "Green Screen & Photo Booths Rentals"),
    ("misc_rental", "Misc Equipment Rental"),
    
    # === Other Services ===
    ("transportation", "Transportation"),
    ("staffing", "Staffing"),
    ("venue_sourcing", "Venue Sourcing"),
    ("other", "Other"),
]
