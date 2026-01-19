# -*- coding: utf-8 -*-
# Part of Party Time Texas Event Management System
# Shared constants for consistent service types across all PTT modules

# =============================================================================
# SERVICE TYPES
# =============================================================================
# Service categories offered by Party Time Texas (aligned to QuickBooks export)
SERVICE_TYPES = [
    # Entertainment
    ("dj", "DJ & MC Services"),
    ("band", "Band Services"),
    ("musicians", "Musicians (Solo/Duo)"),
    ("dancers_characters", "Dancers & Characters"),
    ("casino", "Casino Services"),

    # Photo/Video
    ("photography", "Photography"),
    ("videography", "Videography"),
    ("photobooth", "Photo Booth"),

    # Artists
    ("caricature", "Caricature Artist"),
    ("balloon_face_painters", "Balloon & Face Painters"),

    # Food & Beverage
    ("catering", "Catering & Bartender Services"),

    # Rentals & Equipment
    ("av_rentals", "A/V Rentals"),
    ("lighting", "Lighting Rentals"),
    ("balloon_decor", "Balloon Decor"),
    ("misc_rental", "Misc Event Rental"),

    # Services
    ("coordination", "Event Planning Services"),
    ("transportation", "Transportation"),
    ("staffing", "Staffing"),
    ("venue_sourcing", "Venue Sourcing"),

    # Insurance & Adjustments
    ("insurance", "Additional Insured Coverage Extension"),
    ("deposit", "Customer Deposit / Retainer"),
    ("discount", "Client Discounts"),
    ("refund", "Client Refund"),
    ("cancellation", "Cancellation Event Fees"),
    ("bad_debt", "Bad Debt"),

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
# SERVICE TIERS
# =============================================================================
# Pricing tiers for services - matches product variant attributes
# Maps to: product_attributes.xml Service Tier attribute values
SERVICE_TIERS = [
    ("essentials", "Essentials"),
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
    ("pending", "Pending"),
    ("quoted", "Quoted"),
    ("contracted", "Contracted"),
    ("confirmed", "Confirmed"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
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
# STAKEHOLDER STATUS
# =============================================================================
STAKEHOLDER_STATUS = [
    ("pending", "Pending Confirmation"),
    ("confirmed", "Confirmed"),
    ("unavailable", "Unavailable"),
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
