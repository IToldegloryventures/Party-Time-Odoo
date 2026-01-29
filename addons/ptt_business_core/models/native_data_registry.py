# -*- coding: utf-8 -*-
"""
Native Data Registry - Single Source of Truth for PTT Modules
==============================================================

This file contains the IDs and lookup methods for ALL native Odoo records
created by the accounting team. All PTT modules MUST use this registry
to reference products, attributes, variants, and categories.

NEVER hardcode IDs elsewhere - always import from this file!

Last Updated: 2026-01-22
Verified Against: Production Database
"""

from odoo import api, models
import logging

_logger = logging.getLogger(__name__)


# ============================================================================
# NATIVE PRODUCT IDS (product.template)
# ============================================================================
# These are the products created natively by the accounting team
# DO NOT reference any other product IDs in PTT code
#
# USAGE:
#   from odoo.addons.ptt_business_core.models.native_data_registry import NativeProducts
#   product = env['product.template'].browse(NativeProducts.DJ_SERVICES)
#
#   Or for filtering:
#   products = env['product.template'].browse(NativeProducts.ALL_SELLABLE_SERVICES)

class NativeProducts:
    """Native product.template IDs from Odoo database.
    
    Last verified: 2026-01-28 from Odoo web shell.
    """
    
    # ==========================================================================
    # EVENT KICKOFF (creates project from quotation template)
    # ==========================================================================
    # Avoid relying on static IDs; use helper get_kickoff_product_id below.
    EVENT_KICKOFF = 144  # Legacy ID; kept for backward compatibility

    # ==========================================================================
    # A/V SERVICES
    # ==========================================================================
    AV_PRODUCTION_MANAGER = 51
    AV_RENTALS_AUDIO = 48
    AV_RENTALS_LED_WALL = 47
    AV_RENTALS_MISC = 49
    AV_RENTALS_MONITOR = 46
    AV_RENTALS_PROJECTOR_SCREEN = 14
    AV_TECHNICIAN = 50  # Note: Named "A/V Techician" in DB (typo)
    AV_TECHNICAL_DIRECTOR = 52
    
    # ==========================================================================
    # ENTERTAINMENT SERVICES
    # ==========================================================================
    AIRBRUSH_TATTOO = 54
    BALLOON_ARTIST = 53
    BALLOON_DECOR = 16
    BAND_SERVICES = 18
    CASINO_SERVICES = 21
    CHARACTERS = 60
    COMEDIAN = 65
    DANCERS = 27
    FACE_PAINTERS = 17
    MAGICIANS = 64
    MUSICIAN_SERVICES = 38
    PETTING_ZOO = 63
    PSYCHICS = 42
    TRADITIONAL_CARICATURE = 55
    DIGITAL_CARICATURE = 56
    
    # DJ Services (by event type)
    DJ_SERVICES_SOCIAL = 28
    DJ_SERVICES_WEDDING = 162
    DJ_SERVICES_CORPORATE = 163
    
    # MC Services (by event type)
    MC_SERVICES_SOCIAL = 61
    MC_SERVICES_WEDDING = 164
    MC_SERVICES_CORPORATE = 165
    
    # ==========================================================================
    # PHOTO/VIDEO SERVICES
    # ==========================================================================
    PHOTO_BOOTHS_RENTALS = 31
    PHOTOGRAPHY_SERVICES = 41
    VIDEOGRAPHY_SERVICES = 45
    
    # ==========================================================================
    # EVENT SERVICES
    # ==========================================================================
    BARTENDER_SERVICES = 58
    CATERING_SERVICES = 57
    DELIVER_SETUP_STRIKE = 66
    EVENT_PLANNING_SERVICES = 29
    OFFICIANT_SERVICES = 40
    WAIT_STAFF = 59
    
    # ==========================================================================
    # RENTALS
    # ==========================================================================
    DECOR_DECORATIONS = 34
    EQUIPMENT_RENTAL = 35
    FURNITURE_RENTALS = 30
    GAMES_RENTALS = 62
    INFLATABLES_RENTALS = 32
    
    # ==========================================================================
    # ADMINISTRATIVE/BILLING
    # ==========================================================================
    ADDITIONAL_INSURED = 13
    BAD_DEBT = 15
    CANCELLATION_FEES = 19
    CLIENT_CONTRACT_BS = 23
    CLIENT_DISCOUNTS = 24
    CLIENT_REFUND = 25
    CUSTOMER_DEPOSIT = 26
    DISCOUNT = 71
    INITIAL_LATE_FEE_10 = 33
    MONTHLY_LATE_FEE_15 = 39
    TIPS_GIVEN = 43
    TRAVEL_AND_EXPENSES = 67
    VARIABLE_CONSIDERATION = 44
    
    # Misc Services
    MISC_EVENT_ENTERTAINMENT_UNTAXED = 36
    MISC_EVENT_SERVICES_TAXED = 37
    
    # Odoo Standard
    SERVICE_ON_TIMESHEETS = 10
    
    # ==========================================================================
    # GROUPED LISTS (for filtering)
    # ==========================================================================
    # All sellable service IDs
    ALL_SELLABLE_SERVICES = [
        # Event Kickoff
        144,
        # A/V
        51, 48, 47, 49, 46, 14, 50, 52,
        # Entertainment
        54, 53, 16, 18, 21, 60, 65, 27, 17, 64, 38, 63, 42, 55, 56,
        # DJ Services (all event types)
        28, 162, 163,
        # MC Services (all event types)
        61, 164, 165,
        # Photo/Video
        31, 41, 45,
        # Event Services
        58, 57, 66, 29, 40, 59,
        # Rentals
        34, 35, 30, 62, 32,
        # Misc
        36, 37,
    ]
    
    # DJ Services grouped
    ALL_DJ_SERVICES = [28, 162, 163]
    
    # MC Services grouped
    ALL_MC_SERVICES = [61, 164, 165]

    # ------------------------------------------------------------------
    # Helpers (runtime-safe lookups)
    # ------------------------------------------------------------------
    @staticmethod
    def get_kickoff_product_id(env):
        """Return current kickoff product id, preferring XMLID, then default_code."""
        prod = env.ref(
            "ptt_business_core.product_event_kickoff_social_product_variant",
            raise_if_not_found=False,
        )
        if prod:
            return prod.id
        prod = env['product.product'].search([('default_code', 'in', ['EVENT-KICKOFF-STD', 'EVENT-KICKOFF'])], limit=1)
        return prod.id if prod else False

    @staticmethod
    def get_all_sellable_services(env):
        """Runtime-safe list of sellable service templates (product.template)."""
        # Prefer names/IDs listed above but fall back to active sellable services
        templates = env['product.template'].browse(NativeProducts.ALL_SELLABLE_SERVICES)
        if templates:
            return templates
        return env['product.template'].search([
            ('type', '=', 'service'),
            ('sale_ok', '=', True),
            ('active', '=', True),
        ])


# ============================================================================
# NATIVE ATTRIBUTE IDS (product.attribute)
# ============================================================================

class NativeAttributes:
    """Native product.attribute IDs from accounting team"""
    
    # Business Attributes (used for variants)
    EVENT_TYPE = 11
    SERVICE_TIER = 10
    AV_TECHNICIAN = 9
    EQUIPMENT_RENTAL = 13
    MUSICIAN_SERVICES = 14
    PHOTOGRAPHY_RENTALS = 12
    PHOTOGRAPHY_SERVICES = 15
    PSYCHICS_TYPE = 16
    MAGICIANS_TYPE = 17
    VIDEOGRAPHY_SERVICES_TYPE = 18
    
    # Product Barcode Lookup Attributes (system)
    AGE_GROUP = 8
    BRAND = 6
    COLOR = 1
    GENDER = 2
    MANUFACTURER = 5
    MATERIAL = 3
    PATTERN = 4
    SIZE = 7


# ============================================================================
# NATIVE ATTRIBUTE VALUE IDS (product.attribute.value)
# ============================================================================

class NativeAttributeValues:
    """Native product.attribute.value IDs from accounting team"""
    
    # Event Type Values (Attribute ID: 11)
    EVENT_TYPE_SOCIAL = 7
    EVENT_TYPE_WEDDING = 8
    EVENT_TYPE_CORPORATE = 9
    
    # Service Tier Values (Attribute ID: 10)
    SERVICE_TIER_ESSENTIAL = 4
    SERVICE_TIER_CLASSIC = 5
    SERVICE_TIER_PREMIER = 6
    
    # A/V Technician Values (Attribute ID: 9)
    AV_TECH_SETUP = 1
    AV_TECH_CAMERA_OPERATOR = 2
    AV_TECH_AUDIO_ENGINEER = 3
    
    # Equipment Rental Values (Attribute ID: 13)
    EQUIPMENT_GENERATOR = 14
    EQUIPMENT_TENTS = 15
    EQUIPMENT_FURNITURE = 16
    
    # Musician Services Values (Attribute ID: 14)
    MUSICIAN_SOLO = 17
    MUSICIAN_DUET = 18
    MUSICIAN_TRIO = 19
    MUSICIAN_QUARTET = 20
    MUSICIAN_BAND = 21
    
    # Photography Rentals Values (Attribute ID: 12)
    PHOTO_BOOTH_PRINTOUTS = 10
    PHOTO_BOOTH_GREEN_SCREEN = 11
    PHOTO_BOOTH_GREEN_SCREEN_PRINTOUTS = 12
    PHOTO_BOOTH_360 = 13
    
    # Photography Services Values (Attribute ID: 15)
    PHOTO_HEAD_SHOTS = 22
    PHOTO_EVENT = 23
    
    # Psychics Type Values (Attribute ID: 16)
    PSYCHIC_PALM_READER = 24
    PSYCHIC_TAROT = 25
    PSYCHIC_HYPNOTIST = 26
    PSYCHIC_MENTALIST = 27
    
    # Magicians Type Values (Attribute ID: 17)
    MAGICIAN_STAGE = 28
    MAGICIAN_WALK_AROUND = 29
    MAGICIAN_CARD = 30
    
    # Videography Services Type Values (Attribute ID: 18)
    VIDEO_EVENT = 31
    VIDEO_HIGHLIGHT_REEL = 32
    VIDEO_CONTENT_COLLECTION = 33
    VIDEO_PROMOTIONAL_REEL = 34


# ============================================================================
# NATIVE CATEGORY IDS (product.category)
# ============================================================================

class NativeCategories:
    """Native product.category IDs"""
    
    ALL = 1  # "All" - root category
    EXPENSES = 2
    GOODS = 1  # Same as ALL in standard Odoo
    SERVICES = 3
    EVENT_ENTERTAINMENT = 4  # Child of Services


# ============================================================================
# HELPER MODEL FOR RUNTIME LOOKUPS
# ============================================================================

class NativeDataRegistry(models.AbstractModel):
    """
    Helper model for looking up native records at runtime.
    Use this when you need to look up by name rather than ID.
    """
    _name = 'ptt.native.data.registry'
    _description = 'Native Data Registry Helper'
    
    @api.model
    def get_product_by_name(self, name):
        """
        Get a native product by name.
        Returns False if not found or if it's a PTT-created product.
        """
        product = self.env['product.template'].search([
            ('name', '=', name),
            ('active', '=', True)
        ], limit=1)
        
        if not product:
            return False
            
        # Check it's not a PTT-created product
        ext_id = self.env['ir.model.data'].search([
            ('model', '=', 'product.template'),
            ('res_id', '=', product.id),
            ('module', '=', 'ptt_business_core')
        ], limit=1)
        
        if ext_id:
            _logger.warning(
                "Attempted to get PTT-created product '%s' - use native product instead!",
                name
            )
            return False
            
        return product
    
    @api.model
    def get_attribute_by_name(self, name):
        """
        Get a native attribute by name.
        Returns False if not found or if it's a PTT-created attribute.
        """
        attr = self.env['product.attribute'].search([
            ('name', '=', name),
        ], limit=1)

        if not attr:
            return False

        ext_id = self.env['ir.model.data'].search([
            ('model', '=', 'product.attribute'),
            ('res_id', '=', attr.id),
            ('module', '=', 'ptt_business_core')
        ], limit=1)

        if ext_id:
            _logger.warning(
                "Attempted to get PTT-created attribute '%s' - "
                "use native attribute instead!",
                name
            )
            return False

        return attr

    @api.model
    def get_attribute_value_by_name(self, attribute_name, value_name):
        """
        Get a native attribute value by attribute name and value name.
        """
        attr = self.get_attribute_by_name(attribute_name)
        if not attr:
            return False

        value = self.env['product.attribute.value'].search([
            ('attribute_id', '=', attr.id),
            ('name', '=', value_name),
        ], limit=1)

        return value or False
    
    @api.model
    def get_event_type_values(self):
        """Get all native Event Type attribute values."""
        AttrValue = self.env['product.attribute.value']
        return {
            'social': AttrValue.browse(NativeAttributeValues.EVENT_TYPE_SOCIAL),
            'wedding': AttrValue.browse(NativeAttributeValues.EVENT_TYPE_WEDDING),
            'corporate': AttrValue.browse(NativeAttributeValues.EVENT_TYPE_CORPORATE),
        }

    @api.model
    def get_service_tier_values(self):
        """Get all native Service Tier attribute values."""
        AttrValue = self.env['product.attribute.value']
        return {
            'essential': AttrValue.browse(NativeAttributeValues.SERVICE_TIER_ESSENTIAL),
            'classic': AttrValue.browse(NativeAttributeValues.SERVICE_TIER_CLASSIC),
            'premier': AttrValue.browse(NativeAttributeValues.SERVICE_TIER_PREMIER),
        }
    
    @api.model
    def get_sellable_services(self):
        """Get all native sellable service products."""
        Product = self.env['product.template']
        return Product.browse(NativeProducts.ALL_SELLABLE_SERVICES)

    @api.model
    def is_native_product(self, product_id):
        """Check if a product is native (not PTT-created)."""
        ext_id = self.env['ir.model.data'].search([
            ('model', '=', 'product.template'),
            ('res_id', '=', product_id),
            ('module', '=', 'ptt_business_core')
        ], limit=1)
        return not bool(ext_id)


# ============================================================================
# QUICK REFERENCE DICTIONARIES
# ============================================================================

# Product name to ID mapping (for quick lookups)
# Names match EXACTLY as they appear in Odoo database (including trailing spaces)
PRODUCT_NAME_TO_ID = {
    # Event Kickoff
    '** Event Kickoff': 144,
    # A/V Services
    'A/V Production Manager': 51,
    'A/V Rentals - Audio': 48,
    'A/V Rentals - LED Wall Panel': 47,
    'A/V Rentals - Misc': 49,
    'A/V Rentals - Monitor': 46,
    'A/V Rentals - Projector and Screen': 14,
    'A/V Techician': 50,  # Note: typo in DB
    'A/V Technical Director': 52,
    # Entertainment
    'Airbrush Tattoo': 54,
    'Balloon Artist': 53,
    'Balloon Décor': 16,
    'Band Services ': 18,  # trailing space in DB
    'Bartender Services': 58,
    'Casino Services ': 21,  # trailing space in DB
    'Catering Services': 57,
    'Characters': 60,
    'Comedian': 65,
    'Dancers': 27,
    'Digital Caricature Artist': 56,
    'Traditional Caricature Artist': 55,
    'Face Painters': 17,
    'Magicians': 64,
    'Musician Services ': 38,  # trailing space in DB
    'Petting Zoo': 63,
    'Psychics': 42,
    # DJ Services (by event type)
    'DJ Services (Social)': 28,
    'DJ Services (Wedding)': 162,
    'DJ Services (Corporate)': 163,
    # MC Services (by event type)
    'MC Services (Social)': 61,
    'MC Services (Wedding)': 164,
    'MC Services (Corporate)': 165,
    # Photo/Video
    'Photo Booths Rentals': 31,
    'Photography Services': 41,
    'Videography Services': 45,
    # Event Services
    'Event Planning Services ': 29,  # trailing space in DB
    'Officiant Services': 40,
    'Wait Staff': 59,
    'Deliver, Setup, Strike': 66,
    # Rentals
    'Décor & Decorations': 34,
    'Equipment Rental': 35,
    'Furniture Rentals ': 30,  # trailing space in DB
    'Games Rentals': 62,
    'Inflatables Rentals': 32,
    # Administrative/Billing
    'Additional Insured Coverage Extension': 13,
    'Bad Debt': 15,
    'Cancellation Event Fees ': 19,  # trailing space in DB
    'Client Contract - BS ': 23,  # trailing space in DB
    'Client Discounts ': 24,  # trailing space in DB
    'Client Refund ': 25,  # trailing space in DB
    'Customer Deposit / Retainer ': 26,  # trailing space in DB
    'Discount': 71,
    'Initial 10% Late Fee ': 33,  # trailing space in DB
    'Monthly 1.5% Late Fee': 39,
    'Tips Given': 43,
    'Travel and Expenses': 67,
    'Variable Consideration (Performance Bonus & Penalties)': 44,
    # Misc Services
    'Misc Event Entertainment Services (Untaxed) ': 36,  # trailing space in DB
    'Misc Event Services (Taxed) ': 37,  # trailing space in DB
    # Odoo Standard
    'Service on Timesheets': 10,
}

# Event Type value name to ID mapping
EVENT_TYPE_NAME_TO_ID = {
    'Social': 7,
    'Wedding': 8,
    'Corporate': 9,
}

# Service Tier value name to ID mapping
SERVICE_TIER_NAME_TO_ID = {
    'Essential': 4,
    'Classic': 5,
    'Premier': 6,
}
