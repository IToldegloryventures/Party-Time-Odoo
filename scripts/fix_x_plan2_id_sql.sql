-- ============================================
-- SQL Script to Remove x_plan2_id from Views
-- Run these commands in order on your Odoo database
-- ============================================

-- STEP 1: Check which views contain x_plan2_id (VIEW ONLY - safe)
SELECT id, name, model, type 
FROM ir_ui_view 
WHERE arch_db::text LIKE '%x_plan2_id%'
ORDER BY id;

-- STEP 2: Check custom views (Studio/user customizations)
SELECT id, ref_id, user_id 
FROM ir_ui_view_custom 
WHERE arch::text LIKE '%x_plan2_id%'
ORDER BY id;

-- STEP 3: Preview what will be changed (VIEW ONLY - safe)
SELECT 
    id,
    name,
    model,
    arch_db
FROM ir_ui_view 
WHERE arch_db::text LIKE '%x_plan2_id%';

-- STEP 4: Fix views in ir_ui_view
UPDATE ir_ui_view 
SET arch_db = REGEXP_REPLACE(
    REGEXP_REPLACE(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    arch_db::text,
                    '<field[^>]*name=["\']x_plan2_id["\'][^/>]*/?>',
                    '',
                    'g'
                ),
                '<field[^>]*name=["\']x_plan2_id["\'][^>]*>.*?</field>',
                '',
                'gs'
            ),
            '<label[^>]*for=["\']x_plan2_id["\'][^/>]*/?>',
            '',
            'g'
        ),
        '<button[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</button>',
        '',
        'gs'
    ),
    '<div[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</div>',
    '',
    'gs'
)::text
WHERE arch_db::text LIKE '%x_plan2_id%';

-- STEP 5: Fix custom views (ir_ui_view_custom)
UPDATE ir_ui_view_custom 
SET arch = REGEXP_REPLACE(
    REGEXP_REPLACE(
        REGEXP_REPLACE(
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                    arch::text,
                    '<field[^>]*name=["\']x_plan2_id["\'][^/>]*/?>',
                    '',
                    'g'
                ),
                '<field[^>]*name=["\']x_plan2_id["\'][^>]*>.*?</field>',
                '',
                'gs'
            ),
            '<label[^>]*for=["\']x_plan2_id["\'][^/>]*/?>',
            '',
            'g'
        ),
        '<button[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</button>',
        '',
        'gs'
    ),
    '<div[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</div>',
    '',
    'gs'
)::text
WHERE arch::text LIKE '%x_plan2_id%';

-- STEP 6: Verify all references are removed (should return 0 rows)
SELECT COUNT(*) as remaining_references
FROM (
    SELECT id FROM ir_ui_view WHERE arch_db::text LIKE '%x_plan2_id%'
    UNION ALL
    SELECT id FROM ir_ui_view_custom WHERE arch::text LIKE '%x_plan2_id%'
) AS remaining;

-- STEP 7: Clear Odoo cache (recommended after fixing)
-- This ensures the changes are picked up immediately
-- Note: This requires database superuser or specific permissions
-- If you don't have permissions, just restart Odoo server
-- DELETE FROM ir_attachment WHERE res_model = 'ir.ui.view' AND res_field = 'arch_db';
