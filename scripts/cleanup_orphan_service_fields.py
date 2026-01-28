"""
Script: cleanup_orphan_service_fields.py
Purpose: Remove orphaned custom service/product fields from the database schema and ensure no custom product/service fields exist in custom modules.
Usage: Run as a post-migration or pre-deployment script on staging/prod.
"""
import logging
from odoo import api, SUPERUSER_ID

ORPHAN_FIELDS = [
    'ptt_photobooth_branding',
    'ptt_casino_games',
    'ptt_casino_player_count',
    'ptt_services_already_booked',
]

MODEL = 'crm.lead'


def cleanup_orphan_service_fields(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    model = env[MODEL]
    for field in ORPHAN_FIELDS:
        if field in model._fields:
            try:
                logging.info(f"Removing field {field} from {MODEL}")
                env.cr.execute(f"ALTER TABLE {model._table} DROP COLUMN IF EXISTS {field} CASCADE;")
            except Exception as e:
                logging.error(f"Error removing field {field}: {e}")

# Odoo migration hook
# Add to __manifest__.py: 'post_init_hook': 'cleanup_orphan_service_fields'

def migrate(cr, version):
    cleanup_orphan_service_fields(cr, None)
