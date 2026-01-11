#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to restore Odoo database dump to PostgreSQL
"""
import os
import sys
import subprocess
import psycopg2
from psycopg2 import sql

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Configuration
DUMP_FILE = r"C:\Users\ashpt\Downloads\itoldegloryventures-party-time-odoo-main-26585931_2026-01-09_031125_test_nofs\dump.sql"
DB_NAME = "test_nofs"
DB_USER = "postgres"  # PostgreSQL superuser for creating database
DB_PASSWORD = "odoo123"  # Change to your PostgreSQL postgres user password
ODOO_DB_USER = "odoo"  # Odoo database user (will be created)
ODOO_DB_PASSWORD = "odoo123"  # Password for odoo user
DB_HOST = "localhost"
DB_PORT = "5432"

def find_postgresql_bin():
    """Find PostgreSQL bin directory"""
    possible_paths = [
        r"C:\Program Files\PostgreSQL\18\bin",
        r"C:\Program Files\PostgreSQL\17\bin",
        r"C:\Program Files\PostgreSQL\16\bin",
        r"C:\Program Files\PostgreSQL\15\bin",
    ]
    
    for path in possible_paths:
        psql_path = os.path.join(path, "psql.exe")
        if os.path.exists(psql_path):
            return path
    return None

def check_postgresql_connection():
    """Check if we can connect to PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"  # Connect to default postgres database
        )
        conn.close()
        print("✓ Successfully connected to PostgreSQL")
        return True
    except psycopg2.OperationalError as e:
        print(f"✗ Cannot connect to PostgreSQL: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL service is running")
        print("2. Username and password are correct")
        print("3. PostgreSQL is listening on localhost:5432")
        return False

def verify_odoo_user():
    """Verify odoo user has correct privileges per Odoo documentation"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check user privileges
        cur.execute("""
            SELECT 
                rolname,
                rolcanlogin,
                rolcreatedb
            FROM pg_roles 
            WHERE rolname = %s
        """, (ODOO_DB_USER,))
        
        result = cur.fetchone()
        
        if result:
            username, can_login, can_create_db = result
            print(f"\nUser '{username}' privileges:")
            print(f"  - Can login: {'Yes' if can_login else 'No'}")
            print(f"  - Create database: {'Yes' if can_create_db else 'No'}")
            
            if not can_login or not can_create_db:
                print("\n⚠ User missing required privileges. Fixing...")
                if not can_login:
                    cur.execute(sql.SQL("ALTER USER {} WITH LOGIN").format(sql.Identifier(ODOO_DB_USER)))
                if not can_create_db:
                    cur.execute(sql.SQL("ALTER USER {} CREATEDB").format(sql.Identifier(ODOO_DB_USER)))
                print("✓ Privileges updated")
        else:
            print(f"✗ User '{ODOO_DB_USER}' not found")
        
        cur.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error verifying user: {e}")
        return False

def create_odoo_user():
    """Create the odoo PostgreSQL user if it doesn't exist"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if user exists
        cur.execute(
            "SELECT 1 FROM pg_roles WHERE rolname = %s",
            (ODOO_DB_USER,)
        )
        exists = cur.fetchone()
        
        if exists:
            print(f"✓ User '{ODOO_DB_USER}' already exists")
            # Verify and ensure user has required privileges
            verify_odoo_user()
        else:
            # Create user with password and privileges
            # CREATE USER automatically grants LOGIN privilege (Can login? = Yes)
            # Per Odoo docs: username=odoo, password=odoo, Can login=Yes, Create database=Yes
            cur.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD {} CREATEDB").format(
                    sql.Identifier(ODOO_DB_USER),
                    sql.Literal(ODOO_DB_PASSWORD)
                )
            )
            print(f"✓ Created user '{ODOO_DB_USER}' per Odoo documentation:")
            print(f"  - Username: {ODOO_DB_USER}")
            print(f"  - Password: {ODOO_DB_PASSWORD}")
            print(f"  - Can login: Yes ✓")
            print(f"  - Create database: Yes ✓")
        
        cur.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error creating user: {e}")
        return False

def create_database():
    """Create the database if it doesn't exist"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database="postgres"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        # Check if database exists
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (DB_NAME,)
        )
        exists = cur.fetchone()
        
        if exists:
            print(f"⚠ Database '{DB_NAME}' already exists")
            response = input("Do you want to drop and recreate it? (yes/no): ")
            if response.lower() == 'yes':
                # Terminate existing connections
                cur.execute(
                    sql.SQL("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = {}")
                    .format(sql.Literal(DB_NAME))
                )
                cur.execute(
                    sql.SQL("DROP DATABASE {}").format(sql.Identifier(DB_NAME))
                )
                print(f"✓ Dropped existing database '{DB_NAME}'")
            else:
                print("Keeping existing database. Exiting.")
                conn.close()
                return False
        
        # Create database owned by odoo user (not postgres)
        cur.execute(
            sql.SQL("CREATE DATABASE {} WITH OWNER = {}").format(
                sql.Identifier(DB_NAME),
                sql.Identifier(ODOO_DB_USER)
            )
        )
        print(f"✓ Created database '{DB_NAME}' owned by user '{ODOO_DB_USER}'")
        
        cur.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"✗ Error creating database: {e}")
        return False

def restore_dump():
    """Restore the SQL dump file"""
    pg_bin = find_postgresql_bin()
    
    if not pg_bin:
        print("✗ Could not find PostgreSQL bin directory")
        print("Please ensure PostgreSQL is installed and psql.exe is available")
        return False
    
    psql_path = os.path.join(pg_bin, "psql.exe")
    
    if not os.path.exists(psql_path):
        print(f"✗ psql.exe not found at {psql_path}")
        return False
    
    if not os.path.exists(DUMP_FILE):
        print(f"✗ Dump file not found: {DUMP_FILE}")
        return False
    
    print(f"\nRestoring dump file: {DUMP_FILE}")
    print("This may take a few minutes...")
    
    # Use odoo user for restore (Odoo requires non-postgres user)
    # Set PGPASSWORD environment variable
    env = os.environ.copy()
    env['PGPASSWORD'] = ODOO_DB_PASSWORD
    
    # Build psql command - use odoo user
    cmd = [
        psql_path,
        "-h", DB_HOST,
        "-p", DB_PORT,
        "-U", ODOO_DB_USER,
        "-d", DB_NAME,
        "-f", DUMP_FILE
    ]
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ Database restored successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Error restoring database:")
        print(e.stderr)
        return False

def main():
    print("=" * 60)
    print("Odoo Database Restore Script")
    print("=" * 60)
    print(f"\nDatabase: {DB_NAME}")
    print(f"Dump file: {DUMP_FILE}")
    print(f"PostgreSQL superuser (for setup): {DB_USER}")
    print(f"Odoo database user: {ODOO_DB_USER}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print("\n" + "-" * 60)
    
    # Step 1: Check connection
    print("\n[Step 1] Checking PostgreSQL connection...")
    if not check_postgresql_connection():
        sys.exit(1)
    
    # Step 2: Create odoo user
    print("\n[Step 2] Creating Odoo PostgreSQL user...")
    if not create_odoo_user():
        sys.exit(1)
    
    # Step 3: Create database
    print("\n[Step 3] Creating database...")
    if not create_database():
        sys.exit(1)
    
    # Step 4: Restore dump
    print("\n[Step 4] Restoring database dump...")
    if not restore_dump():
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✓ Database restoration completed successfully!")
    print("=" * 60)
    print(f"\nNext steps:")
    print(f"1. Configure Odoo to use database: {DB_NAME}")
    print(f"2. Set filestore path in Odoo config:")
    print(f"   C:\\Users\\ashpt\\Downloads\\itoldegloryventures-party-time-odoo-main-26585931_2026-01-09_031125_test_nofs\\filestore")
    print(f"\nTo run Odoo with this database:")
    print(f"  cd odoo")
    print(f"  python odoo-bin -d {DB_NAME} -r {ODOO_DB_USER} -w {ODOO_DB_PASSWORD} --addons-path=addons,../addons")

if __name__ == "__main__":
    main()
