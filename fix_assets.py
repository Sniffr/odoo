#!/usr/bin/env python3
"""
Fix missing Odoo asset bundles by clearing stale ir_attachment records.
Run this inside the Odoo container or from a machine with psycopg2 installed.
"""
import psycopg2
import sys

DB_HOST = "db"
DB_PORT = 5432
DB_NAME = "revive"
DB_USER = "odoo"
DB_PASS = "odoo_password"

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    conn.autocommit = True
    cur = conn.cursor()

    # Check current count
    cur.execute("SELECT COUNT(*) FROM ir_attachment WHERE url LIKE '/web/content/%'")
    count = cur.fetchone()[0]
    print(f"Found {count} asset bundle attachments with /web/content/ URLs")

    # Delete asset bundles - these are regenerated automatically
    cur.execute("""
        DELETE FROM ir_attachment
        WHERE url LIKE '/web/content/%'
    """)
    deleted = cur.rowcount
    print(f"Deleted {deleted} stale /web/content/ attachments")

    # Also clear compiled JS/CSS bundles stored as binary attachments
    cur.execute("""
        DELETE FROM ir_attachment
        WHERE res_model = 'ir.ui.view'
        AND type = 'binary'
        AND (name LIKE '%.js' OR name LIKE '%.css' OR name LIKE '%.min.js' OR name LIKE '%.min.css')
    """)
    deleted2 = cur.rowcount
    print(f"Deleted {deleted2} compiled JS/CSS bundle attachments")

    cur.close()
    conn.close()
    print("Done! Restart Odoo server or visit /?debug=assets to regenerate assets.")

except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)

