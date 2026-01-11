#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test to verify database connection"""
import sys
import psycopg2

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='odoo',
        password='odoo123',
        database='test_nofs'
    )
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM res_users')
    count = cur.fetchone()[0]
    print(f'✓ Database connection successful')
    print(f'✓ Found {count} users in database')
    
    # Check if database has Odoo tables
    cur.execute("""
        SELECT COUNT(*) 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name LIKE 'res_%'
    """)
    table_count = cur.fetchone()[0]
    print(f'✓ Found {table_count} Odoo tables (res_*)')
    
    cur.close()
    conn.close()
    print('\n✓ All database checks passed!')
except Exception as e:
    print(f'✗ Error: {e}')
