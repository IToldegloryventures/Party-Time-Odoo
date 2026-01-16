-- ===================================================================
-- COMPREHENSIVE x_plan2_id CLEANUP SQL SCRIPT
-- Run this directly in PostgreSQL (psql)
-- ===================================================================
-- This script checks ALL possible locations where x_plan2_id might be referenced
-- ===================================================================

BEGIN;

-- ===================================================================
-- STEP 1: Check and fix ir_ui_view (arch_db)
-- ===================================================================
DO $$
DECLARE
    view_record RECORD;
    original_arch TEXT;
    new_arch TEXT;
    fixed_count INT := 0;
BEGIN
    RAISE NOTICE 'Checking ir_ui_view (arch_db)...';
    
    FOR view_record IN 
        SELECT id, name, model, arch_db::text as arch_text
        FROM ir_ui_view 
        WHERE arch_db::text LIKE '%x_plan2_id%'
    LOOP
        original_arch := view_record.arch_text;
        new_arch := original_arch;
        
        -- Remove field tags
        new_arch := REGEXP_REPLACE(new_arch, '<field[^>]*name=["'']x_plan2_id["''][^/>]*/?>', '', 'g');
        new_arch := REGEXP_REPLACE(new_arch, '<field[^>]*name=["'']x_plan2_id["''][^>]*>.*?</field>', '', 'gs');
        new_arch := REGEXP_REPLACE(new_arch, '<label[^>]*for=["'']x_plan2_id["''][^/>]*/?>', '', 'g');
        new_arch := REGEXP_REPLACE(new_arch, '<button[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</button>', '', 'gs');
        new_arch := REGEXP_REPLACE(new_arch, '<div[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</div>', '', 'gs');
        new_arch := REGEXP_REPLACE(new_arch, '<xpath[^>]*>.*?<field[^>]*name=["'']x_plan2_id["''][^>]*>.*?</field>.*?</xpath>', '', 'gs');
        
        IF new_arch != original_arch THEN
            UPDATE ir_ui_view SET arch_db = new_arch::text WHERE id = view_record.id;
            RAISE NOTICE '  Fixed view ID % (%)', view_record.id, view_record.name;
            fixed_count := fixed_count + 1;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Fixed % views in ir_ui_view', fixed_count;
END $$;

-- ===================================================================
-- STEP 2: Check and fix ir_ui_view_custom (Studio customizations)
-- ===================================================================
DO $$
DECLARE
    view_record RECORD;
    original_arch TEXT;
    new_arch TEXT;
    fixed_count INT := 0;
BEGIN
    RAISE NOTICE 'Checking ir_ui_view_custom (Studio customizations)...';
    
    FOR view_record IN 
        SELECT id, ref_id, user_id, arch::text as arch_text
        FROM ir_ui_view_custom 
        WHERE arch::text LIKE '%x_plan2_id%'
    LOOP
        original_arch := view_record.arch_text;
        new_arch := original_arch;
        
        -- Remove field tags
        new_arch := REGEXP_REPLACE(new_arch, '<field[^>]*name=["'']x_plan2_id["''][^/>]*/?>', '', 'g');
        new_arch := REGEXP_REPLACE(new_arch, '<field[^>]*name=["'']x_plan2_id["''][^>]*>.*?</field>', '', 'gs');
        new_arch := REGEXP_REPLACE(new_arch, '<label[^>]*for=["'']x_plan2_id["''][^/>]*/?>', '', 'g');
        new_arch := REGEXP_REPLACE(new_arch, '<button[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</button>', '', 'gs');
        new_arch := REGEXP_REPLACE(new_arch, '<div[^>]*invisible="[^"]*x_plan2_id[^"]*"[^>]*>.*?</div>', '', 'gs');
        
        IF new_arch != original_arch THEN
            UPDATE ir_ui_view_custom SET arch = new_arch::text WHERE id = view_record.id;
            RAISE NOTICE '  Fixed custom view ID % (ref_id: %, user_id: %)', view_record.id, view_record.ref_id, view_record.user_id;
            fixed_count := fixed_count + 1;
        END IF;
    END LOOP;
    
    RAISE NOTICE 'Fixed % custom views', fixed_count;
END $$;

-- ===================================================================
-- STEP 3: Check for any remaining references (report)
-- ===================================================================
DO $$
DECLARE
    view_count INT;
    custom_count INT;
BEGIN
    SELECT COUNT(*) INTO view_count FROM ir_ui_view WHERE arch_db::text LIKE '%x_plan2_id%';
    SELECT COUNT(*) INTO custom_count FROM ir_ui_view_custom WHERE arch::text LIKE '%x_plan2_id%';
    
    RAISE NOTICE '=== FINAL REPORT ===';
    RAISE NOTICE 'Remaining views in ir_ui_view: %', view_count;
    RAISE NOTICE 'Remaining views in ir_ui_view_custom: %', custom_count;
    
    IF view_count = 0 AND custom_count = 0 THEN
        RAISE NOTICE '✓ Database is clean!';
    ELSE
        RAISE NOTICE '⚠ Some references may still exist. Check the counts above.';
    END IF;
END $$;

COMMIT;

-- ===================================================================
-- VERIFICATION QUERIES (run after the script)
-- ===================================================================
-- Check ir_ui_view:
-- SELECT id, name, model, type FROM ir_ui_view WHERE arch_db::text LIKE '%x_plan2_id%';
--
-- Check ir_ui_view_custom:
-- SELECT id, ref_id, user_id FROM ir_ui_view_custom WHERE arch::text LIKE '%x_plan2_id%';
--
-- Check if field still exists:
-- SELECT id, name, model FROM ir_model_fields WHERE name = 'x_plan2_id' AND model = 'project.project';
-- ===================================================================
