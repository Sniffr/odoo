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

    def test_feedback_token_generated_on_create(self):
        appt = self._make_appointment()
        fb = self.env['custom.appointment.feedback'].create({
            'appointment_id': appt.id,
        })
        self.assertTrue(fb.access_token)
        self.assertEqual(fb.state, 'pending')

    def test_feedback_appointment_unique(self):
        from psycopg2 import IntegrityError
        from odoo.tools import mute_logger
        appt = self._make_appointment()
        Feedback = self.env['custom.appointment.feedback']
        Feedback.create({'appointment_id': appt.id})
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            Feedback.create({'appointment_id': appt.id})
            self.env.flush_all()

    def test_feedback_settings_defaults(self):
        s = self.env['custom.appointment.settings'].get_settings()
        self.assertFalse(s.enable_feedback_requests)
        self.assertEqual(s.feedback_channel, 'both')
        self.assertEqual(s.feedback_first_delay_minutes, 5)
        self.assertEqual(s.feedback_repeat_interval_minutes, 1440)
        self.assertEqual(s.feedback_max_requests, 3)
        self.assertTrue(s.feedback_ask_staff_rating)
        self.assertTrue(s.feedback_ask_comments)
        self.assertFalse(s.feedback_reward_enabled)
        self.assertEqual(s.feedback_reward_discount_type, 'percentage')
        self.assertEqual(s.feedback_reward_validity_days, 30)
        self.assertEqual(s.feedback_reward_code_prefix, 'LASH-')

    def test_backfill_creates_feedback_when_enabled(self):
        self.settings.write({'enable_feedback_requests': True})
        appt = self._make_appointment()
        appt.action_complete()
        Feedback = self.env['custom.appointment.feedback']
        Feedback.cron_send_feedback_requests()
        fb = Feedback.search([('appointment_id', '=', appt.id)])
        self.assertEqual(len(fb), 1)
        self.assertEqual(fb.customer_email, 'alice@test.com')
        self.assertEqual(fb.staff_member_id, self.staff)
        self.assertEqual(fb.state, 'pending')

    def test_backfill_skipped_when_disabled(self):
        self.settings.write({'enable_feedback_requests': False})
        appt = self._make_appointment()
        appt.action_complete()
        Feedback = self.env['custom.appointment.feedback']
        Feedback.cron_send_feedback_requests()
        self.assertFalse(Feedback.search([('appointment_id', '=', appt.id)]))

    def test_backfill_no_duplicate(self):
        self.settings.write({'enable_feedback_requests': True})
        appt = self._make_appointment()
        appt.action_complete()
        Feedback = self.env['custom.appointment.feedback']
        Feedback.cron_send_feedback_requests()
        Feedback.cron_send_feedback_requests()
        self.assertEqual(len(Feedback.search([('appointment_id', '=', appt.id)])), 1)

    def _completed_feedback(self, minutes_ago):
        """Helper: completed appointment + pending feedback with completed_date in the past."""
        self.settings.write({'enable_feedback_requests': True})
        appt = self._make_appointment()
        appt.action_complete()
        appt.completed_date = fields.Datetime.now() - timedelta(minutes=minutes_ago)
        fb = self.env['custom.appointment.feedback']._create_for_appointment(appt)
        return appt, fb

    def test_first_request_sent_when_due(self):
        appt, fb = self._completed_feedback(minutes_ago=10)  # delay default 5
        self.env['custom.appointment.feedback']._send_due_requests(self.settings)
        self.assertEqual(fb.request_count, 1)
        self.assertTrue(fb.last_request_date)
        sms = self.env['sms.sms'].search([('number', '=', '254711111111')])
        self.assertTrue(sms)
        self.assertIn('feedback', sms[0].body.lower())

    def test_first_request_not_sent_when_too_early(self):
        appt, fb = self._completed_feedback(minutes_ago=2)  # delay default 5
        self.env['custom.appointment.feedback']._send_due_requests(self.settings)
        self.assertEqual(fb.request_count, 0)

    def test_request_expires_at_max(self):
        appt, fb = self._completed_feedback(minutes_ago=10)
        fb.write({'request_count': 3, 'last_request_date': fields.Datetime.now() - timedelta(days=10)})
        self.env['custom.appointment.feedback']._send_due_requests(self.settings)
        self.assertEqual(fb.state, 'expired')

    def test_cancelled_appointment_not_requested(self):
        appt, fb = self._completed_feedback(minutes_ago=10)
        appt.write({'state': 'cancelled'})
        self.env['custom.appointment.feedback']._send_due_requests(self.settings)
        self.assertEqual(fb.request_count, 0)
