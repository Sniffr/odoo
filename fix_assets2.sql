-- More aggressive asset bundle cleanup for DB restored from 'revive' -> 'lashes'
-- The filestore path changed so all cached binary attachments are invalid

-- 1. Delete ALL binary attachments tied to ir.ui.view (asset bundles)
DELETE FROM ir_attachment
WHERE res_model = 'ir.ui.view'
  AND type = 'binary';

-- 2. Delete any attachment whose store_fname references the old 'revive' filestore
-- (These files don't exist in the 'lashes' filestore)
DELETE FROM ir_attachment
WHERE store_fname IS NOT NULL
  AND type = 'binary'
  AND res_model IN ('ir.ui.view', 'ir.attachment')
  AND (name LIKE '%.js' OR name LIKE '%.css' OR name LIKE '%.map');

-- 3. Also clear menu cache attachments
DELETE FROM ir_attachment
WHERE name LIKE 'ir.ui.menu%'
  AND type = 'binary';

-- Report
SELECT 'Done. Remaining ir_attachment count: ' || COUNT(*)::text AS result FROM ir_attachment;

