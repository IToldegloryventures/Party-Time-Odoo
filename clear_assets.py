#!/usr/bin/env python3
"""Clear cached Odoo assets to fix styling issues"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    user='odoo',
    password='odoo123',
    database='test_nofs'
)
cur = conn.cursor()

# Clear cached assets
cur.execute("""
    DELETE FROM ir_attachment 
    WHERE name LIKE '%assets%' 
       OR url LIKE '/web/assets/%'
       OR name LIKE '%.assets.%'
""")
deleted = cur.rowcount
print(f'Cleared {deleted} cached asset attachments')

conn.commit()
conn.close()
print('Done! Restart Odoo to regenerate assets.')
