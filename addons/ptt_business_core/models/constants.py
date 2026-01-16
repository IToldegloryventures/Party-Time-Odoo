"""
Shared constants for PTT Business Core module.

Reference: https://www.odoo.com/documentation/19.0/contributing/development/coding_guidelines.html
- Favor readability over conciseness
- Avoid duplication (DRY principle)
"""

# Service tier options - aligned with product variants
# Used by: ptt.crm.service.line, res.partner, product.template.attribute.value
SERVICE_TIERS = [
    ("essentials", "Essentials"),
    ("classic", "Classic"),
    ("premier", "Premier"),
]

# SERVICE_TYPES - Expanded to match QuickBooks categories
# Reference: User's QuickBooks export with Income Account mapping
# DO NOT add duplicates - use QuickBooks naming where different
SERVICE_TYPES = [
    # Entertainment (Income Acct 4231-4239)
    ("dj", "DJ & MC Services"),
    ("band", "Band Services"),
    ("musicians", "Musicians (Solo/Duo)"),
    ("dancers_characters", "Dancers & Characters"),
    ("casino", "Casino Services"),
    
    # Photo/Video (Income Acct 4220s)
    ("photography", "Photography"),
    ("videography", "Videography"),
    ("photobooth", "Photo Booth"),
    
    # Artists (Income Acct 4225, 4234)
    ("caricature", "Caricature Artist"),
    ("balloon_face_painters", "Balloon & Face Painters"),
    
    # Food & Beverage (Income Acct 4221)
    ("catering", "Catering & Bartender Services"),
    
    # Rentals & Equipment (Income Acct 4211-4215)
    ("av_rentals", "A/V Rentals"),
    ("lighting", "Lighting Rentals"),
    ("balloon_decor", "Balloon Decor"),
    ("misc_rental", "Misc Event Rental"),
    
    # Services (Income Acct 4200s)
    ("coordination", "Event Planning Services"),
    ("transportation", "Transportation"),
    ("staffing", "Staffing"),
    ("venue_sourcing", "Venue Sourcing"),
    
    # Insurance & Adjustments (Income Acct 4239, 4320-4390)
    ("insurance", "Additional Insured Coverage Extension"),
    ("deposit", "Customer Deposit / Retainer"),
    ("discount", "Client Discounts"),
    ("refund", "Client Refund"),
    ("cancellation", "Cancellation Event Fees"),
    ("bad_debt", "Bad Debt"),
    
    ("other", "Other"),
]
