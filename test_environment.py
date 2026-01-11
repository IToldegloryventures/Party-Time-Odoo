#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify Odoo local environment setup
"""
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

print("=" * 60)
print("Odoo Local Environment Test")
print("=" * 60)

# Test 1: Python version
print("\n[1] Python Version:")
print(f"    Python {sys.version}")
if sys.version_info >= (3, 10):
    print("    ✓ Python 3.10+ (required)")
else:
    print("    ✗ Python 3.10+ required")

# Test 2: Odoo import
print("\n[2] Odoo Module Import:")
try:
    sys.path.insert(0, 'odoo')
    import odoo
    print(f"    ✓ Odoo imported successfully")
    print(f"    Version: Odoo {odoo.release.version}")
    print(f"    Path: {odoo.__file__}")
except Exception as e:
    print(f"    ✗ Failed to import Odoo: {e}")

# Test 3: PostgreSQL connection
print("\n[3] PostgreSQL Connection:")
try:
    import psycopg2
    print(f"    ✓ psycopg2 version: {psycopg2.__version__}")
    
    # Test connection
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='odoo123',
            database='postgres'
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        pg_version = cur.fetchone()[0]
        print(f"    ✓ PostgreSQL connection successful")
        print(f"    PostgreSQL version: {pg_version.split(',')[0]}")
        cur.close()
        conn.close()
    except psycopg2.OperationalError as e:
        print(f"    ✗ Cannot connect to PostgreSQL: {e}")
        print("    Note: Make sure PostgreSQL service is running")
except ImportError:
    print("    ✗ psycopg2 not installed")

# Test 4: Odoo user exists
print("\n[4] Odoo Database User:")
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='odoo123',
        database='postgres'
    )
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_roles WHERE rolname = 'odoo';")
    exists = cur.fetchone()
    if exists:
        print("    ✓ User 'odoo' exists")
        
        # Check privileges
        cur.execute("""
            SELECT rolcanlogin, rolcreatedb 
            FROM pg_roles 
            WHERE rolname = 'odoo'
        """)
        can_login, can_create_db = cur.fetchone()
        print(f"    - Can login: {'Yes' if can_login else 'No'}")
        print(f"    - Create database: {'Yes' if can_create_db else 'No'}")
    else:
        print("    ✗ User 'odoo' does not exist")
        print("    Run: python restore_database.py (will create user)")
    cur.close()
    conn.close()
except Exception as e:
    print(f"    ⚠ Could not check user: {e}")

# Test 5: Configuration file
print("\n[5] Configuration File:")
if os.path.exists('odoo.conf'):
    print("    ✓ odoo.conf exists")
    with open('odoo.conf', 'r') as f:
        config = f.read()
        if 'db_user = odoo' in config:
            print("    ✓ Uses 'odoo' user (not postgres)")
        if 'addons_path' in config:
            print("    ✓ addons_path configured")
else:
    print("    ✗ odoo.conf not found")

# Test 6: Directory structure
print("\n[6] Directory Structure:")
checks = [
    ('addons', 'Custom modules directory'),
    ('odoo', 'Odoo source directory'),
    ('odoo/addons', 'Odoo core modules'),
]
for path, desc in checks:
    if os.path.exists(path):
        print(f"    ✓ {path}/ - {desc}")
    else:
        print(f"    ✗ {path}/ - {desc} missing")

# Test 7: Odoo-bin wrapper
print("\n[7] Odoo-bin Wrapper:")
if os.path.exists('odoo-bin'):
    print("    ✓ odoo-bin wrapper exists at root")
else:
    print("    ✗ odoo-bin wrapper missing")

print("\n" + "=" * 60)
print("Test Complete")
print("=" * 60)
print("\nTo test Odoo shell:")
print("  python odoo-bin shell -d test_nofs -c odoo.conf")
print("\nTo run Odoo server:")
print("  python odoo-bin -c odoo.conf")
