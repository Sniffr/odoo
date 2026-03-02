#!/bin/bash
# Fix Odoo missing asset bundles
# Run this script on the server or copy-paste the commands manually

echo "=== Fixing Odoo Asset Bundles ==="

# Clear stale asset bundle attachments from the database
# Odoo will regenerate them on next page load
psql -U odoo -d revive << 'SQL'
-- Show current asset bundle count
SELECT 'Before cleanup:' as status, COUNT(*) as count
FROM ir_attachment
WHERE url LIKE '/web/content/%';

-- Delete stale compiled asset bundles
DELETE FROM ir_attachment
WHERE url LIKE '/web/content/%';

DELETE FROM ir_attachment
WHERE res_model = 'ir.ui.view'
  AND type = 'binary'
  AND (name LIKE '%.js' OR name LIKE '%.css');

SELECT 'Cleanup complete. Asset bundles will regenerate on next request.' as status;
SQL

echo "=== Done! Now restart Odoo or visit http://localhost:8069/web?debug=assets ==="

