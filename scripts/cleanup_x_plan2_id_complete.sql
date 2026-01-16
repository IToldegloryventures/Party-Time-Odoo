-- ===================================================================
-- COMPLETE x_plan2_id CLEANUP - Run after DELETE FROM ir_model_fields
-- ===================================================================
-- This script cleans up any remaining references after field deletion
-- ===================================================================

BEGIN;

-- Clean up ir_model_data references (metadata entries)
DELETE FROM ir_model_data 
WHERE model = 'ir.model.fields' 
AND res_id IN (
    SELECT id FROM ir_model_fields WHERE name = 'x_plan2_id' AND model = 'project.project'
);

-- Verify the field is completely removed
DO $$
DECLARE
    field_count INT;
    data_count INT;
BEGIN
    SELECT COUNT(*) INTO field_count 
    FROM ir_model_fields 
    WHERE name = 'x_plan2_id' AND model = 'project.project';
    
    SELECT COUNT(*) INTO data_count
    FROM ir_model_data
    WHERE model = 'ir.model.fields'
    AND name LIKE '%x_plan2_id%';
    
    RAISE NOTICE 'Remaining field records: %', field_count;
    RAISE NOTICE 'Remaining data records: %', data_count;
    
    IF field_count = 0 AND data_count = 0 THEN
        RAISE NOTICE '✓ Field completely removed!';
    ELSE
        RAISE NOTICE '⚠ Some records may still exist';
    END IF;
END $$;

COMMIT;

-- ===================================================================
-- Verification query (run after the script)
-- ===================================================================
-- Check if field still exists:
-- SELECT id, name, model FROM ir_model_fields WHERE name = 'x_plan2_id' AND model = 'project.project';
--
-- Check ir_model_data:
-- SELECT * FROM ir_model_data WHERE model = 'ir.model.fields' AND name LIKE '%x_plan2_id%';
-- ===================================================================
