-- Check what database name Odoo thinks it's using for the filestore
SELECT key, value FROM ir_config_parameter
WHERE key IN ('web.base.url', 'database.uuid', 'database.create_date');

-- Check filestore paths in attachments
SELECT store_fname, COUNT(*)
FROM ir_attachment
WHERE store_fname IS NOT NULL
GROUP BY store_fname
ORDER BY count DESC
LIMIT 5;

-- Check if any attachment still has store_fname with content
SELECT COUNT(*) as total_with_storefile,
       MIN(store_fname) as sample
FROM ir_attachment
WHERE store_fname IS NOT NULL AND store_fname != '';

