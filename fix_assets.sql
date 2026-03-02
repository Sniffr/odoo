-- Fix missing asset bundle files by deleting stale ir_attachment records
-- Odoo will regenerate them on next page load

-- Delete compiled asset bundles (CSS/JS bundles stored as attachments)
DELETE FROM ir_attachment
WHERE url LIKE '/web/content/%';

DELETE FROM ir_attachment
WHERE res_model = 'ir.ui.view'
  AND type = 'binary'
  AND (name LIKE '%.js' OR name LIKE '%.css' OR name LIKE '%.min.js' OR name LIKE '%.min.css');

SELECT 'Asset bundles cleared. Odoo will regenerate on next request.' AS result;

