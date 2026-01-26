from odoo import api, SUPERUSER_ID


def _drop_column_if_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    if cr.fetchone():
        cr.execute(f'ALTER TABLE "{table}" DROP COLUMN "{column}"')


def migrate(cr, version):
    # Ensure event type defaults to 'corporate' where null before enforcing NOT NULL.
    cr.execute("UPDATE crm_lead SET ptt_event_type = 'corporate' WHERE ptt_event_type IS NULL")
    # Enforce NOT NULL on event type to match required=True
    cr.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'crm_lead' AND column_name = 'ptt_event_type'
            ) THEN
                ALTER TABLE crm_lead ALTER COLUMN ptt_event_type SET NOT NULL;
            END IF;
        END$$;
        """
    )

    # Deduplicate email template XMLID if previous test runs created a duplicate.
    cr.execute(
        """
        WITH dups AS (
            SELECT id,
                   ROW_NUMBER() OVER (PARTITION BY module, name ORDER BY id) AS rn
            FROM ir_model_data
            WHERE module = 'ptt_business_core'
              AND name = 'email_template_event_reminder_10_day'
        )
        DELETE FROM ir_model_data
        WHERE id IN (SELECT id FROM dups WHERE rn > 1)
        """
    )

    # Remove legacy ptt_event_id columns that are no longer used.
    for table, column in (
        ("crm_lead", "ptt_event_id"),
        ("project_project", "ptt_event_id"),
        ("project_task", "ptt_event_id"),
        ("sale_order", "ptt_event_id"),
        ("purchase_order", "ptt_event_id"),
    ):
        _drop_column_if_exists(cr, table, column)

    # Clean up model field metadata.
    cr.execute(
        """
        DELETE FROM ir_model_fields
         WHERE name = 'ptt_event_id'
           AND model IN (
                'crm.lead',
                'project.project',
                'project.task',
                'sale.order',
                'purchase.order'
           )
        """
    )

    # Drop the unused sequence record and its ir.model.data entry.
    cr.execute(
        "DELETE FROM ir_model_data WHERE module = 'ptt_business_core' AND name = 'seq_ptt_event_id'"
    )
    cr.execute("DELETE FROM ir_sequence WHERE code = 'ptt.event.id'")

    # Invalidate caches for cleaned fields.
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['ir.model.fields'].clear_caches()
