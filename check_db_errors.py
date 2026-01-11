#!/usr/bin/env python3
"""Check database for outstanding errors."""
import psycopg2
from psycopg2.extras import RealDictCursor

conn = psycopg2.connect(host='localhost', port='5432', user='odoo', password='odoo123', dbname='test_nofs')
cur = conn.cursor(cursor_factory=RealDictCursor)

print('=== CHECKING DATABASE FOR OUTSTANDING ERRORS ===')
print()

# Check for modules in error state
print('1. PTT Modules status:')
cur.execute("""
    SELECT name, state FROM ir_module_module 
    WHERE name LIKE 'ptt%'
    ORDER BY name
""")
ptt_mods = cur.fetchall()
if ptt_mods:
    for mod in ptt_mods:
        print(f'   - {mod["name"]}: {mod["state"]}')
else:
    print('   No PTT modules found')
print()

# Check for invalid views
print('2. Views for PTT models:')
cur.execute("""
    SELECT v.name, v.model, v.type 
    FROM ir_ui_view v 
    WHERE v.active = true 
    AND (v.model LIKE 'ptt.%' OR v.name LIKE '%ptt%')
    ORDER BY v.model, v.type
""")
views = cur.fetchall()
if views:
    print(f'   Found {len(views)} PTT views:')
    for v in views[:10]:
        print(f'   - {v["name"]} ({v["model"]}, {v["type"]})')
else:
    print('   No PTT-specific views found')
print()

# Check for orphaned Studio fields
print('3. Studio fields on key models (may need cleanup):')
cur.execute("""
    SELECT model, name, ttype 
    FROM ir_model_fields 
    WHERE name LIKE 'x_studio%' 
    AND model IN ('crm.lead', 'project.project', 'project.task', 'sale.order')
    ORDER BY model, name
""")
studio_fields = cur.fetchall()
if studio_fields:
    print(f'   Found {len(studio_fields)} Studio fields:')
    for f in studio_fields[:15]:
        print(f'   - {f["model"]}.{f["name"]} ({f["ttype"]})')
    if len(studio_fields) > 15:
        print(f'   ... and {len(studio_fields) - 15} more')
else:
    print('   No orphaned Studio fields found')
print()

# Check PTT custom models status
print('4. PTT Custom Models:')
cur.execute("""
    SELECT model, name FROM ir_model 
    WHERE model LIKE 'ptt.%'
    ORDER BY model
""")
models = cur.fetchall()
if models:
    for m in models:
        print(f'   - {m["model"]}: {m["name"]}')
else:
    print('   No PTT models found')
print()

# Check for views referencing non-existent actions
print('5. Views referencing removed fields/actions:')
cur.execute("""
    SELECT v.name, v.model 
    FROM ir_ui_view v 
    WHERE v.active = true 
    AND v.arch_db::text LIKE '%x_plan2_id%'
""")
plan2_views = cur.fetchall()
if plan2_views:
    print(f'   Found {len(plan2_views)} views with x_plan2_id:')
    for v in plan2_views:
        print(f'   - {v["name"]} ({v["model"]})')
else:
    print('   No views referencing x_plan2_id')

# Check for action_create_project_from_lead references
cur.execute("""
    SELECT v.name, v.model
    FROM ir_ui_view v 
    WHERE v.active = true 
    AND v.arch_db::text LIKE '%action_create_project_from_lead%'
""")
proj_views = cur.fetchall()
if proj_views:
    print(f'   Found {len(proj_views)} views with action_create_project_from_lead:')
    for v in proj_views:
        print(f'   - {v["name"]} ({v["model"]})')
else:
    print('   No views referencing action_create_project_from_lead')
print()

# Check for duplicate label fields (Studio issue)
print('6. Fields with duplicate labels (Studio issue):')
cur.execute("""
    SELECT f.model, f.name, f.field_description
    FROM ir_model_fields f
    WHERE f.model = 'crm.lead'
    AND f.field_description IN (
        SELECT field_description 
        FROM ir_model_fields 
        WHERE model = 'crm.lead' 
        GROUP BY field_description 
        HAVING COUNT(*) > 1
    )
    AND f.name LIKE 'x_studio%'
    ORDER BY f.field_description, f.name
""")
dup_fields = cur.fetchall()
if dup_fields:
    print(f'   Found {len(dup_fields)} fields with duplicate labels:')
    for f in dup_fields:
        print(f'   - {f["name"]}: "{f["field_description"]}"')
else:
    print('   No duplicate label Studio fields')
print()

conn.close()
print('=== CHECK COMPLETE ===')
