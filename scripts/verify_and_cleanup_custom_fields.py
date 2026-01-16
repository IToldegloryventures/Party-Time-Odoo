#!/usr/bin/env python3
"""
Comprehensive script to verify and clean up custom fields (x_*) that were added directly via SQL.

This script:
1. Scans all PostgreSQL columns starting with 'x_'
2. Checks if each field is registered in ir_model_fields
3. Checks if each field is used in any views (ir_ui_view.arch_db, ir_ui_view_custom.arch)
4. Then:
   - ✅ If registered in ir_model_fields → leaves it as-is
   - ⚠️ If used in views but not registered → registers it in ir_model_fields
   - 🧹 If not registered and not used → DROPs the column

Run this in Odoo shell: odoo-bin shell -d <db> -c odoo.conf
Then paste the code below the separator line.
"""

import logging

_logger = logging.getLogger(__name__)

# ===================================================================
# COPY EVERYTHING BELOW INTO ODOO SHELL
# ===================================================================

print("=" * 80)
print("CUSTOM FIELDS VERIFICATION AND CLEANUP")
print("=" * 80)
print()

# Step 1: Find all x_ columns in the database
print("Step 1: Scanning for custom fields (x_*) in database...")
cr.execute("""
    SELECT 
        table_name,
        column_name,
        data_type,
        udt_name,
        character_maximum_length,
        is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'public'
        AND column_name LIKE 'x_%'
        AND table_name NOT LIKE 'ir_%'  -- Exclude Odoo system tables
        AND table_name NOT LIKE 'res_%'
    ORDER BY table_name, column_name
""")

all_columns = cr.fetchall()
print(f"Found {len(all_columns)} custom field columns in database\n")

# Step 2: Build a map of table_name -> model_name
# In Odoo: model name uses dots, table name uses underscores
# e.g., 'project.project' -> 'project_project'
print("Step 2: Building table-to-model mapping...")

# Use the registry to get accurate table-to-model mapping
table_to_model = {}
try:
    # Get all models from registry
    for model_name in env.registry:
        try:
            model_class = env.registry[model_name]
            if hasattr(model_class, '_table') and model_class._table:
                table_to_model[model_class._table] = model_name
        except Exception:
            pass
except Exception:
    pass

# Also query ir_model as fallback
cr.execute("SELECT model FROM ir_model WHERE model IS NOT NULL")
all_models = [row[0] for row in cr.fetchall()]
for model in all_models:
    table = model.replace('.', '_')
    if table not in table_to_model:
        table_to_model[table] = model

print(f"Mapped {len(table_to_model)} tables to models\n")

# Step 3: For each column, check registration and usage
print("Step 3: Analyzing each custom field...")
print("-" * 80)

results = {
    'registered': [],      # ✅ Registered in ir_model_fields
    'used_not_registered': [],  # ⚠️ Used in views but not registered
    'orphaned': []         # 🧹 Not registered and not used
}

# Initialize deletion summary tracking
deletion_summary = {
    'deleted': [],
    'failed': [],
    'errors': []
}

for col_info in all_columns:
    table_name = col_info[0]
    column_name = col_info[1]
    data_type = col_info[2]
    udt_name = col_info[3]
    max_length = col_info[4]
    is_nullable = col_info[5]
    
    # Try to find the model for this table
    model_name = table_to_model.get(table_name)
    if not model_name:
        # Try reverse: if table_name ends with known patterns, guess the model
        # This is a fallback for tables we haven't seen
        print(f"  ⚠️  WARNING: Could not map table '{table_name}' to model for field '{column_name}'")
        # Try to infer model name
        model_name = table_name.replace('_', '.')
        # Check if this model exists
        cr.execute("SELECT id FROM ir_model WHERE model = %s", (model_name,))
        if not cr.fetchone():
            print(f"     → Skipping '{table_name}.{column_name}' (unknown model)")
            continue
    
    # Check if field is registered in ir_model_fields
    cr.execute("""
        SELECT id, name, model, ttype, state, field_description
        FROM ir_model_fields
        WHERE model = %s AND name = %s
    """, (model_name, column_name))
    
    field_registration = cr.fetchone()
    is_registered = field_registration is not None
    
    # Check if field is used in views
    cr.execute("""
        SELECT COUNT(*) FROM ir_ui_view
        WHERE arch_db::text LIKE %s
    """, (f'%{column_name}%',))
    view_count = cr.fetchone()[0]
    
    cr.execute("""
        SELECT COUNT(*) FROM ir_ui_view_custom
        WHERE arch::text LIKE %s
    """, (f'%{column_name}%',))
    custom_view_count = cr.fetchone()[0]
    
    is_used_in_views = (view_count + custom_view_count) > 0
    
    # Categorize the field
    field_info = {
        'table': table_name,
        'model': model_name,
        'column': column_name,
        'data_type': data_type,
        'udt_name': udt_name,
        'max_length': max_length,
        'is_nullable': is_nullable,
        'view_count': view_count,
        'custom_view_count': custom_view_count,
        'field_registration': field_registration
    }
    
    if is_registered:
        results['registered'].append(field_info)
        print(f"  ✅ {model_name}.{column_name} - Registered in ir_model_fields")
    elif is_used_in_views:
        results['used_not_registered'].append(field_info)
        print(f"  ⚠️  {model_name}.{column_name} - Used in {view_count + custom_view_count} view(s) but NOT registered")
    else:
        results['orphaned'].append(field_info)
        print(f"  🧹 {model_name}.{column_name} - Orphaned (not registered, not used)")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"✅ Registered fields: {len(results['registered'])}")
print(f"⚠️  Used but not registered: {len(results['used_not_registered'])}")
print(f"🧹 Orphaned fields (candidates for deletion): {len(results['orphaned'])}")
print()

# Step 4: Handle used but not registered fields
if results['used_not_registered']:
    print("=" * 80)
    print("STEP 4: Registering fields that are used but not registered")
    print("=" * 80)
    
    # Map PostgreSQL types to Odoo field types
    def infer_odoo_field_type(udt_name, data_type, max_length):
        """Infer Odoo field type from PostgreSQL type"""
        type_map = {
            'bool': 'boolean',
            'int4': 'integer',
            'int8': 'integer',
            'numeric': 'float',
            'float8': 'float',
            'float4': 'float',
            'text': 'text',
            'varchar': 'char',
            'date': 'date',
            'timestamp': 'datetime',
        }
        
        # Check udt_name first
        if udt_name in type_map:
            base_type = type_map[udt_name]
            if base_type == 'char' and max_length and max_length > 255:
                return 'text'
            return base_type
        
        # Fallback to data_type
        data_type_lower = data_type.lower()
        if 'int' in data_type_lower:
            return 'integer'
        elif 'bool' in data_type_lower:
            return 'boolean'
        elif 'numeric' in data_type_lower or 'float' in data_type_lower or 'double' in data_type_lower:
            return 'float'
        elif 'date' in data_type_lower and 'time' not in data_type_lower:
            return 'date'
        elif 'timestamp' in data_type_lower or 'time' in data_type_lower:
            return 'datetime'
        elif 'text' in data_type_lower:
            return 'text'
        else:
            return 'char'  # Default to char
    
    IrModelFields = env['ir.model.fields']
    
    for field_info in results['used_not_registered']:
        model_name = field_info['model']
        column_name = field_info['column']
        
        # Check if model exists in ir_model
        cr.execute("SELECT id FROM ir_model WHERE model = %s", (model_name,))
        model_row = cr.fetchone()
        if not model_row:
            print(f"  ⚠️  Skipping {model_name}.{column_name} - model not found in ir_model")
            continue
        
        model_id = model_row[0]
        
        # Infer field type
        ttype = infer_odoo_field_type(
            field_info['udt_name'],
            field_info['data_type'],
            field_info['max_length']
        )
        
        # Create field registration
        try:
            field_desc = column_name.replace('x_', '').replace('_', ' ').title()
            field_vals = {
                'name': column_name,
                'model': model_name,
                'model_id': model_id,
                'field_description': field_desc,
                'ttype': ttype,
                'state': 'manual',
            }
            
            # Add size for char fields
            if ttype == 'char' and field_info['max_length']:
                field_vals['size'] = field_info['max_length']
            
            field = IrModelFields.create(field_vals)
            print(f"  ✅ Registered {model_name}.{column_name} as {ttype} field (ID: {field.id})")
            cr.commit()
        except Exception as e:
            print(f"  ❌ Failed to register {model_name}.{column_name}: {e}")
            cr.rollback()

# Step 5: Automatically delete orphaned fields (not registered, not used in views)
if results['orphaned']:
    print()
    print("=" * 80)
    print("STEP 5: Automatically deleting orphaned fields")
    print("=" * 80)
    print(f"Found {len(results['orphaned'])} orphaned fields to delete")
    print()
    
    # Import psycopg2.sql for safe identifier quoting
    import psycopg2.sql
    
    print("Dropping orphaned columns...")
    for field_info in results['orphaned']:
        table_name = field_info['table']
        column_name = field_info['column']
        model_name = field_info['model']
        
        try:
            # Use psycopg2.sql.Identifier for safe SQL identifier quoting
            query = psycopg2.sql.SQL("ALTER TABLE {} DROP COLUMN IF EXISTS {}").format(
                psycopg2.sql.Identifier(table_name),
                psycopg2.sql.Identifier(column_name)
            )
            cr.execute(query)
            
            deletion_summary['deleted'].append({
                'model': model_name,
                'table': table_name,
                'column': column_name,
                'data_type': field_info['data_type']
            })
            print(f"  ✅ Deleted: {model_name}.{column_name} ({table_name}.{column_name})")
        except Exception as e:
            error_msg = str(e)
            deletion_summary['failed'].append({
                'model': model_name,
                'table': table_name,
                'column': column_name,
                'error': error_msg
            })
            deletion_summary['errors'].append(f"{model_name}.{column_name}: {error_msg}")
            print(f"  ❌ Failed: {model_name}.{column_name} ({table_name}.{column_name}) - {error_msg}")
    
    # Commit all successful deletions
    if deletion_summary['deleted']:
        try:
            cr.commit()
            print(f"\n✅ Successfully deleted {len(deletion_summary['deleted'])} orphaned columns. Changes committed.")
        except Exception as e:
            cr.rollback()
            print(f"\n❌ Error committing deletions: {e}")
            deletion_summary['errors'].append(f"Commit error: {e}")
    elif deletion_summary['failed']:
        print(f"\n⚠️  No columns were successfully deleted. {len(deletion_summary['failed'])} failures occurred.")
else:
    print()
    print("=" * 80)
    print("STEP 5: Orphaned fields cleanup")
    print("=" * 80)
    print("✅ No orphaned fields found - nothing to delete.")

print()
print("=" * 80)
print("FINAL SUMMARY REPORT")
print("=" * 80)
print(f"✅ Registered fields: {len(results['registered'])} (left as-is)")
if results['used_not_registered']:
    print(f"⚠️  Fields registered during cleanup: {len(results['used_not_registered'])} (were used but not registered)")
print(f"🧹 Orphaned fields processed: {len(results['orphaned'])}")
print()

# Deletion Summary
if deletion_summary['deleted'] or deletion_summary['failed']:
    print("=" * 80)
    print("DELETION SUMMARY")
    print("=" * 80)
    
    if deletion_summary['deleted']:
        print(f"\n✅ SUCCESSFULLY DELETED ({len(deletion_summary['deleted'])} columns):")
        for item in deletion_summary['deleted']:
            print(f"   - {item['model']}.{item['column']} ({item['table']}.{item['column']}) - {item['data_type']}")
    
    if deletion_summary['failed']:
        print(f"\n❌ FAILED DELETIONS ({len(deletion_summary['failed'])} columns):")
        for item in deletion_summary['failed']:
            print(f"   - {item['model']}.{item['column']} ({item['table']}.{item['column']})")
            print(f"     Error: {item['error']}")
    
    if deletion_summary['errors']:
        print(f"\n⚠️  ERRORS ENCOUNTERED ({len(deletion_summary['errors'])}):")
        for error in deletion_summary['errors']:
            print(f"   - {error}")
else:
    print("✅ No deletions required - no orphaned fields found.")

print()
print("=" * 80)
print("VERIFICATION AND CLEANUP COMPLETE")
print("=" * 80)
