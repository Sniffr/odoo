-- Fix missing columns that the custom_appointments module added
-- These columns exist in the Python models but not in the database

-- 1. Add missing columns to res_partner
ALTER TABLE res_partner
    ADD COLUMN IF NOT EXISTS appointment_count integer DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_paid_amount numeric DEFAULT 0;

-- 2. Add missing user_id column to custom_staff_member
ALTER TABLE custom_staff_member
    ADD COLUMN IF NOT EXISTS user_id integer REFERENCES res_users(id) ON DELETE SET NULL;

-- 3. Check for any other potentially missing columns in custom_appointments tables
-- (Add display_name if not present - it's a stored computed field)
ALTER TABLE custom_staff_member
    ADD COLUMN IF NOT EXISTS display_name varchar;

-- Report what we did
SELECT
    'res_partner.appointment_count' as col,
    EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='res_partner' AND column_name='appointment_count') as exists
UNION ALL
SELECT
    'res_partner.total_paid_amount',
    EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='res_partner' AND column_name='total_paid_amount')
UNION ALL
SELECT
    'custom_staff_member.user_id',
    EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='custom_staff_member' AND column_name='user_id')
UNION ALL
SELECT
    'custom_staff_member.display_name',
    EXISTS(SELECT 1 FROM information_schema.columns WHERE table_name='custom_staff_member' AND column_name='display_name');

