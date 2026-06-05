from datetime import datetime, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestAppointmentFeedback(TransactionCase):

    def setUp(self):
        super().setUp()
        self.settings = self.env['custom.appointment.settings'].get_settings()
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

    def _make_appointment(self):
        return self.env['custom.appointment'].create({
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
        })

    def test_fixtures_load(self):
        appt = self._make_appointment()
        self.assertEqual(appt.state, 'draft')

    def test_completed_date_stamped_on_action_complete(self):
        appt = self._make_appointment()
        self.assertFalse(appt.completed_date)
        appt.action_complete()
        self.assertEqual(appt.state, 'completed')
        self.assertTrue(appt.completed_date)

    def test_completed_date_stamped_on_write(self):
        appt = self._make_appointment()
        appt.write({'state': 'completed'})
        self.assertTrue(appt.completed_date)
