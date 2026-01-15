"""
Pre-migration script for PTT Business Core v19.0.5.0.0

BREAKING CHANGE: Tier field values migrated from gold/silver/bronze/platinum 
to essentials/classic/premier.

Affected tables:
- ptt_crm_service_line.tier
- res_partner.ptt_vendor_tier (in ptt_vendor_management)

Migration mapping:
- bronze → essentials
- silver → classic  
- gold → premier
- platinum → premier (highest tier maps to premier)

Reference: https://www.odoo.com/documentation/19.0/developer/reference/upgrades/upgrade_scripts.html
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Migrate tier values from old to new naming convention."""
    if not version:
        return
    
    _logger.info("PTT Business Core: Starting tier migration (gold/silver/bronze → essentials/classic/premier)")
    
    # Migration mapping
    tier_mapping = {
        'bronze': 'essentials',
        'silver': 'classic',
        'gold': 'premier',
        'platinum': 'premier',  # Platinum maps to Premier (highest tier)
    }
    
    # === Migrate ptt_crm_service_line.tier ===
    _logger.info("Migrating ptt_crm_service_line.tier...")
    
    # Check if table exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'ptt_crm_service_line'
        );
    """)
    if cr.fetchone()[0]:
        for old_val, new_val in tier_mapping.items():
            cr.execute("""
                UPDATE ptt_crm_service_line 
                SET tier = %s 
                WHERE tier = %s
            """, (new_val, old_val))
            updated = cr.rowcount
            if updated > 0:
                _logger.info(f"  - Updated {updated} records: {old_val} → {new_val}")
    else:
        _logger.info("  - Table ptt_crm_service_line does not exist, skipping")
    
    # === Migrate res_partner.ptt_vendor_tier ===
    _logger.info("Migrating res_partner.ptt_vendor_tier...")
    
    # Check if column exists
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'res_partner' 
            AND column_name = 'ptt_vendor_tier'
        );
    """)
    if cr.fetchone()[0]:
        for old_val, new_val in tier_mapping.items():
            cr.execute("""
                UPDATE res_partner 
                SET ptt_vendor_tier = %s 
                WHERE ptt_vendor_tier = %s
            """, (new_val, old_val))
            updated = cr.rowcount
            if updated > 0:
                _logger.info(f"  - Updated {updated} vendors: {old_val} → {new_val}")
    else:
        _logger.info("  - Column ptt_vendor_tier does not exist on res_partner, skipping")
    
    _logger.info("PTT Business Core: Tier migration complete")
