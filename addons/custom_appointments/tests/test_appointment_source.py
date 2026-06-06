from datetime import datetime

from odoo.tests.common import TransactionCase


class TestAppointmentSource(TransactionCase):

    def setUp(self):
        super().setUp()
        self.branch = self.env['custom.branch'].create({'name': 'Test Branch'})
        self.category = self.env['service.category'].create({'name': 'Lashes'})
        self.service = self.env['company.service'].create({
            'name': 'Classic Set',
            'category_id': self.category.id,
            'price': 100.0,
            'duration': 2.0,
        })
        self.staff = self.env['custom.staff.member'].create({
            'name': 'Jane',
            'branch_id': self.branch.id,
            'email': 'jane@test.com',
            'phone': '254700000000',
        })

    def _make_appointment(self, **overrides):
        vals = {
            'name': 'Test Appt',
            'customer_name': 'Alice',
            'customer_email': 'alice@test.com',
            'customer_phone': '254711111111',
            'service_id': self.service.id,
            'staff_member_id': self.staff.id,
            'branch_id': self.branch.id,
            'start': datetime(2026, 1, 1, 9, 0),
            'stop': datetime(2026, 1, 1, 11, 0),
            'price': 100.0,
        }
        vals.update(overrides)
        return self.env['custom.appointment'].create(vals)

    def test_sources_seeded(self):
        online = self.env.ref('custom_appointments.appointment_source_online')
        call_in = self.env.ref('custom_appointments.appointment_source_call_in')
        walk_in = self.env.ref('custom_appointments.appointment_source_walk_in')
        self.assertEqual(online.name, 'Online')
        self.assertEqual(call_in.name, 'Call-in')
        self.assertEqual(walk_in.name, 'Walk-in')
        self.assertTrue(online.active)

    def test_new_appointment_defaults_to_online(self):
        appt = self._make_appointment()
        online = self.env.ref('custom_appointments.appointment_source_online')
        self.assertEqual(appt.source_id, online)

    def test_explicit_source_is_preserved(self):
        call_in = self.env.ref('custom_appointments.appointment_source_call_in')
        appt = self._make_appointment(source_id=call_in.id)
        self.assertEqual(appt.source_id, call_in)

    def test_group_by_source(self):
        call_in = self.env.ref('custom_appointments.appointment_source_call_in')
        self._make_appointment()                       # Online (default)
        self._make_appointment(                        # Call-in, non-overlapping slot
            source_id=call_in.id,
            start=datetime(2026, 1, 2, 9, 0),
            stop=datetime(2026, 1, 2, 11, 0),
        )
        groups = self.env['custom.appointment'].read_group(
            [], fields=['source_id'], groupby=['source_id'])
        # Odoo 18 lazy read_group uses '<field>_count' key for single groupby
        count_key = 'source_id_count'
        counts = {g['source_id'][1]: g[count_key] for g in groups if g['source_id']}
        self.assertIn('Online', counts, 'read_group returned no Online bucket — check count key')
        self.assertEqual(counts.get('Online'), 1)
        self.assertEqual(counts.get('Call-in'), 1)

    def test_backfill_sets_online_for_null_source(self):
        from odoo.addons.custom_appointments import _backfill_appointment_source
        online = self.env.ref('custom_appointments.appointment_source_online')
        appt = self._make_appointment()
        appt.write({'source_id': False})
        self.assertFalse(appt.source_id)
        _backfill_appointment_source(self.env)
        self.assertEqual(appt.source_id, online)

    def test_source_in_use_cannot_be_deleted(self):
        from psycopg2 import IntegrityError
        from odoo.tools import mute_logger
        call_in = self.env.ref('custom_appointments.appointment_source_call_in')
        self._make_appointment(source_id=call_in.id)
        # ondelete='restrict' must block deleting a source that's still referenced.
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            call_in.unlink()
            self.env.flush_all()
