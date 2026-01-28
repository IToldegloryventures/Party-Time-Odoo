"""
Migration script to clean up deprecated fields and models from ptt_vendor_management after refactor to Odoo 19 native workflows.
- Removes ptt_vendor_status field from res.partner
- Removes obsolete RFQ/quote models and tables
- Cleans up any other orphaned columns related to removed features

Place this script in the scripts/ directory. Odoo will auto-run it during module upgrade.
"""


def migrate(cr):
    # Remove ptt_vendor_status column from res_partner
    cr.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='res_partner' AND column_name='ptt_vendor_status'
            ) THEN
                ALTER TABLE res_partner DROP COLUMN ptt_vendor_status;
            END IF;
        END$$;
    """)

    # Remove ptt_vendor_rfq and ptt_vendor_quote_history tables if they exist
    for table in [
        'ptt_vendor_rfq',
        'ptt_vendor_quote_history',
        'ptt_vendor_rfq_partner_rel',
    ]:
        cr.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name='{table}'
                ) THEN
                    DROP TABLE {table} CASCADE;
                END IF;
            END$$;
        """)

    # Remove any other deprecated columns as needed (add more as you refactor)
    # Example: cr.execute("ALTER TABLE res_partner DROP COLUMN IF EXISTS old_field;")

    # Remove obsolete wizard tables if present
    for table in [
        'ptt_rfq_done_wizard',
        'ptt_rfq_send_wizard',
    ]:
        cr.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_name='{table}'
                ) THEN
                    DROP TABLE {table} CASCADE;
                END IF;
            END$$;
        """)

    # Add more cleanup as needed for future migrations
