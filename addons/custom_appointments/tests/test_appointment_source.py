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
