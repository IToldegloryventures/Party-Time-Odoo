# -*- coding: utf-8 -*-
# Part of Party Time Texas Event Management System
# Shared constants for consistent service types across all PTT modules
# FIXED: Separated DJ and MC Services per QuickBooks structure

# =============================================================================
# SERVICE TYPES - Matches QuickBooks Product List
# =============================================================================
SERVICE_TYPES = [
    # Entertainment - DJ & MC SEPARATED
    ("dj", "DJ Services"),
    ("mc", "MC Services"),
    ("band", "Band Services"),
    ("musicians", "Musician Services"),
    ("dancers", "Dancers"),
    ("characters", "Characters"),
    ("casino", "Casino Services"),
    ("psychics", "Psychics"),
    ("magicians", "Magicians"),
    ("comedian", "Comedian"),

    # Photo/Video
    ("photography", "Photography Services"),
    ("videography", "Videography Services"),
    ("photobooth", "Photo Booths Rentals"),

    # Artists
    ("caricature_traditional", "Traditional Caricature Artist"),
    ("caricature_digital", "Digital Caricature Artist"),
    ("balloon_artist", "Balloon Artist"),
    ("face_painters", "Face Painters"),
    ("airbrush_tattoo", "Airbrush Tattoo"),

    # Food & Beverage
    ("catering", "Catering Services"),
    ("bartender", "Bartender Services"),
    ("wait_staff", "Wait Staff"),

    # A/V & Equipment
    ("av_projector", "A/V Rentals - Projector and Screen"),
    ("av_monitor", "A/V Rentals - Monitor"),
    ("av_led_wall", "A/V Rentals - LED Wall Panel"),
    ("av_audio", "A/V Rentals - Audio"),
    ("av_misc", "A/V Rentals - Misc"),
    ("av_technician", "A/V Technician"),
    ("av_production_mgr", "A/V Production Manager"),
    ("av_technical_dir", "A/V Technical Director"),

    # Rentals
    ("balloon_decor", "Balloon Decor"),
    ("furniture_rentals", "Furniture Rentals"),
    ("inflatables", "Inflatables Rentals"),
    ("games", "Games Rentals"),
    ("equipment_rental", "Equipment Rental"),
    ("decor", "Decor & Decorations"),

    # Services
    ("event_planning", "Event Planning Services"),
    ("officiant", "Officiant Services"),
    ("petting_zoo", "Petting Zoo"),
    ("deliver_setup_strike", "Deliver, Setup, Strike"),
    ("travel_expenses", "Travel and Expenses"),

    # Insurance & Adjustments
    ("insurance", "Additional Insured Coverage Extension"),
    ("deposit", "Customer Deposit / Retainer"),
    ("discount", "Client Discounts"),
    ("refund", "Client Refund"),
    ("cancellation", "Cancellation Event Fees"),
    ("bad_debt", "Bad Debt"),
    ("late_fee_initial", "Initial 10% Late Fee"),
    ("late_fee_monthly", "Monthly 1.5% Late Fee"),
    ("tips", "Tips Given"),
    ("variable_consideration", "Variable Consideration"),

    # Misc
    ("misc_taxed", "Misc Event Services (Taxed)"),
    ("misc_untaxed", "Misc Event Entertainment Services (Untaxed)"),
    ("other", "Other"),
]

# =============================================================================
# EVENT TYPES
# =============================================================================
# Only 3 event types matching product variant attributes
# Maps to: product_attributes.xml Event Type attribute values
EVENT_TYPES = [
    ("corporate", "Corporate"),
    ("social", "Social"),
    ("wedding", "Wedding"),
]

# =============================================================================
# SERVICE TIERS - For product variants
# =============================================================================
SERVICE_TIERS = [
    ("essential", "Essential"),
    ("classic", "Classic"),
    ("premier", "Premier"),
]

# =============================================================================
# CONTACT & LEAD MANAGEMENT
# =============================================================================
CONTACT_METHODS = [
    ("call", "Phone Call"),
    ("text", "Text Message"),
    ("email", "Email"),
]

LEAD_TYPES = [
    ("individual", "Individual"),
    ("business", "Business"),
]

# =============================================================================
# LOCATION TYPES
# =============================================================================
LOCATION_TYPES = [
    ("indoor", "Indoor"),
    ("outdoor", "Outdoor"),
    ("combination", "Combination"),
]

# =============================================================================
# VENDOR MANAGEMENT
# =============================================================================
VENDOR_ASSIGNMENT_STATUS = [
    ("pending", "Pending"),         # Assignment created, WO not sent
    ("sent", "Work Order Sent"),    # WO emailed to vendor, awaiting response
    ("confirmed", "Accepted"),      # Vendor accepted via portal
    ("declined", "Declined"),       # Vendor declined via portal
    ("in_progress", "In Progress"), # Work has started
    ("completed", "Completed"),     # Work finished
]

# =============================================================================
# PAYMENT STATUS
# =============================================================================
PAYMENT_STATUS = [
    ("not_paid", "Not Paid"),
    ("partial", "Partially Paid"),
    ("paid", "Paid"),
    ("overdue", "Overdue"),
]

# =============================================================================
# COMMUNICATION PREFERENCES
# =============================================================================
COMMUNICATION_PREFERENCES = [
    ("email", "Email"),
    ("phone", "Phone"),
    ("text", "Text Message"),
    ("portal", "Portal"),
]

# =============================================================================
# EVENT STATUS
# =============================================================================
EVENT_STATUS = [
    ("planning", "Planning"),
    ("confirmed", "Confirmed"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]

# =============================================================================
# PERFORMANCE RATINGS
# =============================================================================
PERFORMANCE_RATINGS = [
    ("1", "Poor"),
    ("2", "Below Average"),
    ("3", "Average"),
    ("4", "Good"),
    ("5", "Excellent"),
]
