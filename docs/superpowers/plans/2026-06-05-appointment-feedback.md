# Appointment Customer Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After an appointment is completed, automatically request customer feedback (admin-configurable fields, timing, repeat cadence) and reward each submission with a unique single-use promo code.

**Architecture:** A new `custom.appointment.feedback` model (one record per completed appointment) holds tracking state + the submitted answers. A cron every 15 min backfills feedback records for completed appointments and sends due requests via SMS/email with a tokenized public link. The public page submits answers through a model method that also generates a `custom.appointment.promo` reward. All feedback config lives on the existing `custom.appointment.settings` singleton, exposed as a new tab on the Communication Settings page.

**Tech Stack:** Odoo 18 (Python models, QWeb/XML views, HTTP controllers), PostgreSQL, Docker Compose. Tests use Odoo's `TransactionCase` run inside the container.

**Reference spec:** `docs/superpowers/specs/2026-06-05-appointment-feedback-design.md`

---

## File Structure

**New files:**
- `addons/custom_appointments/models/appointment_feedback.py` — `custom.appointment.feedback` model + cron + submit/reward logic
- `addons/custom_appointments/templates/email/feedback_request.html` — request email body
- `addons/custom_appointments/templates/email/feedback_reward.html` — reward email body
- `addons/custom_appointments/views/appointment_feedback_views.xml` — admin list/form/search/action/menu + appointment smart button
- `addons/custom_appointments/views/feedback_website_templates.xml` — public form / thank-you / invalid QWeb pages
- `addons/custom_appointments/tests/__init__.py` — test package
- `addons/custom_appointments/tests/test_feedback.py` — unit tests

**Modified files:**
- `addons/custom_appointments/models/__init__.py` — import new model
- `addons/custom_appointments/models/appointment.py` — add `completed_date`, stamp on completion, feedback smart-button glue
- `addons/custom_appointments/models/appointment_settings.py` — feedback config fields
- `addons/custom_appointments/views/appointment_settings_views.xml` — notebook tabs + Feedback tab
- `addons/custom_appointments/controllers/main.py` — public feedback route
- `addons/custom_appointments/data/cron_jobs.xml` — feedback cron
- `addons/custom_appointments/security/ir.model.access.csv` — feedback access rules
- `addons/custom_appointments/__manifest__.py` — register new view files

---

## Test Harness Conventions

All commands run from repo root `/Users/sidneymalingu/PycharmProjects/odoo`. The test database is **`feedback_test`** (separate from production `LashesByShazz`), installed without demo data for deterministic fixtures.

**Per-task test command** (used after Task 0 installs the module):

```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo --config=/etc/odoo/odoo-local.conf \
  -d feedback_test --without-demo=all \
  -u custom_appointments --test-enable \
  --test-tags /custom_appointments \
  --stop-after-init --no-http --log-level=test
```

Look for a final log line like `custom_appointments tested ... 0 failed, 0 error(s)`. A failing test prints `FAIL`/`ERROR` with a traceback above that line.

---

## Task 0: Bring up containers, create test DB, scaffold tests

**Files:**
- Create: `addons/custom_appointments/tests/__init__.py`
- Create: `addons/custom_appointments/tests/test_feedback.py`

- [ ] **Step 1: Start the stack**

Run:
```bash
docker compose -f docker-compose-local.yml up -d db odoo
```
Expected: `db` and `odoo` containers report `Started`/`Running`.

- [ ] **Step 2: Create the test package**

Create `addons/custom_appointments/tests/__init__.py`:
```python
from . import test_feedback
```

- [ ] **Step 3: Add a trivial smoke test**

Create `addons/custom_appointments/tests/test_feedback.py`:
```python
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
```

- [ ] **Step 4: Install the module on the test DB and run the smoke test**

Run:
```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo --config=/etc/odoo/odoo-local.conf \
  -d feedback_test --without-demo=all \
  -i custom_appointments --test-enable \
  --test-tags /custom_appointments \
  --stop-after-init --no-http --log-level=test
```
Expected: ends with `0 failed, 0 error(s)` and `test_fixtures_load` listed as passed.

- [ ] **Step 5: Commit**

```bash
git add addons/custom_appointments/tests/
git commit -m "test: scaffold feedback test harness"
```

---

## Task 1: Stamp `completed_date` on appointment completion

**Files:**
- Modify: `addons/custom_appointments/models/appointment.py` (field near line 30-37; `write` at lines 254-258)
- Test: `addons/custom_appointments/tests/test_feedback.py`

- [ ] **Step 1: Write the failing test**

Add to `TestAppointmentFeedback` in `tests/test_feedback.py`:
```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run the per-task test command (see Test Harness Conventions).
Expected: FAIL/ERROR — `'custom.appointment' object has no attribute 'completed_date'`.

- [ ] **Step 3: Add the field**

In `addons/custom_appointments/models/appointment.py`, after the `duration` field (line 32), add:
```python
    completed_date = fields.Datetime(string='Completed On', readonly=True, copy=False)
```

- [ ] **Step 4: Stamp it in `write`**

Replace the existing `write` method (lines 254-258):
```python
    def write(self, vals):
        result = super(Appointment, self).write(vals)
        if any(field in vals for field in ['name', 'start', 'stop', 'description', 'user_id']):
            self._update_calendar_event()
        return result
```
with:
```python
    def write(self, vals):
        if vals.get('state') == 'completed' and 'completed_date' not in vals:
            vals = dict(vals, completed_date=fields.Datetime.now())
        result = super(Appointment, self).write(vals)
        if any(field in vals for field in ['name', 'start', 'stop', 'description', 'user_id']):
            self._update_calendar_event()
        return result
```
(`action_complete` already calls `self.state = 'completed'`, which routes through `write`, so it is covered automatically.)

- [ ] **Step 5: Run to verify it passes**

Run the per-task test command.
Expected: `0 failed, 0 error(s)`; both new tests pass.

- [ ] **Step 6: Commit**

```bash
git add addons/custom_appointments/models/appointment.py addons/custom_appointments/tests/test_feedback.py
git commit -m "feat: stamp appointment completed_date on completion"
```

---

## Task 2: Create `custom.appointment.feedback` model

**Files:**
- Create: `addons/custom_appointments/models/appointment_feedback.py`
- Modify: `addons/custom_appointments/models/__init__.py`
- Modify: `addons/custom_appointments/security/ir.model.access.csv`
- Test: `addons/custom_appointments/tests/test_feedback.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_feedback.py`:
```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run the per-task test command.
Expected: ERROR — model `custom.appointment.feedback` does not exist.

- [ ] **Step 3: Create the model file**

Create `addons/custom_appointments/models/appointment_feedback.py`:
```python
from odoo import models, fields, api
from datetime import timedelta
import secrets
import logging

_logger = logging.getLogger(__name__)


class AppointmentFeedback(models.Model):
    _name = 'custom.appointment.feedback'
    _description = 'Customer Appointment Feedback'
    _order = 'create_date desc'

    appointment_id = fields.Many2one(
        'custom.appointment', string='Appointment',
        required=True, ondelete='cascade', index=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    customer_name = fields.Char(string='Customer Name')
    customer_email = fields.Char(string='Customer Email')
    customer_phone = fields.Char(string='Customer Phone')
    staff_member_id = fields.Many2one('custom.staff.member', string='Staff Member')
    service_id = fields.Many2one('company.service', string='Service')
    branch_id = fields.Many2one('custom.branch', string='Branch')

    access_token = fields.Char(string='Access Token', index=True, copy=False)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('expired', 'Expired'),
    ], string='Status', default='pending', required=True, index=True)

    request_count = fields.Integer(string='Requests Sent', default=0)
    last_request_date = fields.Datetime(string='Last Request Sent')
    submitted_date = fields.Datetime(string='Submitted On')

    # Curated answer fields (1-5 ratings: 0 = unanswered)
    staff_rating = fields.Integer(string='Staff Rating')
    service_rating = fields.Integer(string='Service Rating')
    recommend_score = fields.Selection(
        [(str(n), str(n)) for n in range(0, 11)],
        string='Recommend Score (NPS)')
    cleanliness_rating = fields.Integer(string='Cleanliness Rating')
    comfort_rating = fields.Integer(string='Comfort Rating')
    value_rating = fields.Integer(string='Value Rating')
    comments = fields.Text(string='Comments')

    reward_promo_id = fields.Many2one('custom.appointment.promo', string='Reward Promo Code')

    _sql_constraints = [
        ('appointment_unique', 'unique(appointment_id)',
         'Feedback already exists for this appointment.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('access_token'):
                vals['access_token'] = secrets.token_urlsafe(24)
        return super().create(vals_list)
```

- [ ] **Step 4: Register the model import**

In `addons/custom_appointments/models/__init__.py`, add after the `promo_code` line:
```python
from . import appointment_feedback
```

- [ ] **Step 5: Add access rules**

Append to `addons/custom_appointments/security/ir.model.access.csv`:
```csv
access_custom_appointment_feedback_user,custom.appointment.feedback.user,model_custom_appointment_feedback,base.group_user,1,1,1,1
access_custom_appointment_feedback_public,custom.appointment.feedback.public,model_custom_appointment_feedback,base.group_public,1,1,0,0
```

- [ ] **Step 6: Run to verify it passes**

Run the per-task test command.
Expected: `0 failed, 0 error(s)`; both new tests pass.

- [ ] **Step 7: Commit**

```bash
git add addons/custom_appointments/models/appointment_feedback.py \
        addons/custom_appointments/models/__init__.py \
        addons/custom_appointments/security/ir.model.access.csv \
        addons/custom_appointments/tests/test_feedback.py
git commit -m "feat: add custom.appointment.feedback model"
```

---

## Task 3: Add feedback configuration fields to settings

**Files:**
- Modify: `addons/custom_appointments/models/appointment_settings.py`
- Test: `addons/custom_appointments/tests/test_feedback.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_feedback.py`:
```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run the per-task test command.
Expected: ERROR — `'custom.appointment.settings' object has no attribute 'enable_feedback_requests'`.

- [ ] **Step 3: Add the fields**

In `addons/custom_appointments/models/appointment_settings.py`, insert the following just before the `@api.model` `get_settings` method (after the `followup_sms_template` field, around line 66):
```python
    # ==================== CUSTOMER FEEDBACK ====================

    enable_feedback_requests = fields.Boolean(
        string='Collect Customer Feedback', default=False,
        help='Enable requesting feedback from customers after their appointment is completed')

    feedback_channel = fields.Selection([
        ('sms', 'SMS Only'),
        ('email', 'Email Only'),
        ('both', 'Both SMS and Email'),
    ], string='Feedback Channel', default='both', required=True)

    feedback_first_delay_minutes = fields.Integer(
        string='First Request After (Minutes)', default=5,
        help='Minutes after appointment completion before the first feedback request is sent')
    feedback_repeat_interval_minutes = fields.Integer(
        string='Repeat Every (Minutes)', default=1440,
        help='Minutes between repeated feedback requests (1440 = 1 day)')
    feedback_max_requests = fields.Integer(
        string='Maximum Requests', default=3,
        help='Maximum number of feedback requests to send per appointment')

    # Which fields to ask
    feedback_ask_staff_rating = fields.Boolean(string='Ask Staff Rating', default=True)
    feedback_ask_service_rating = fields.Boolean(string='Ask Service Rating', default=True)
    feedback_ask_recommend = fields.Boolean(string='Ask Recommend Score (NPS)', default=True)
    feedback_ask_cleanliness = fields.Boolean(string='Ask Cleanliness Rating', default=True)
    feedback_ask_comfort = fields.Boolean(string='Ask Comfort Rating', default=True)
    feedback_ask_value = fields.Boolean(string='Ask Value Rating', default=True)
    feedback_ask_comments = fields.Boolean(string='Ask Comments', default=True)

    # Request messages
    feedback_request_email_subject = fields.Char(
        string='Feedback Email Subject',
        default="How was your visit? We'd love your feedback")
    feedback_request_email_template = fields.Text(string='Feedback Email Template')
    feedback_request_sms_template = fields.Text(
        string='Feedback SMS Template',
        default='Hi {customer_name}! How was your {service_name}? Share quick feedback: {feedback_link}')

    # Promo reward
    feedback_reward_enabled = fields.Boolean(
        string='Reward Feedback with Promo', default=False,
        help='Generate a unique promo code for customers who submit feedback')
    feedback_reward_discount_type = fields.Selection([
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
        ('free_booking', 'Free Booking Fee'),
    ], string='Reward Discount Type', default='percentage')
    feedback_reward_discount_value = fields.Float(string='Reward Discount Value', default=10.0)
    feedback_reward_applies_to = fields.Selection([
        ('booking_fee', 'Booking Fee Only'),
        ('full_price', 'Full Service Price'),
        ('both', 'Both (Booking Fee + Balance)'),
    ], string='Reward Applies To', default='full_price')
    feedback_reward_max_discount = fields.Float(
        string='Reward Maximum Discount', default=0.0,
        help='Cap on discount amount for percentage rewards. 0 = no cap')
    feedback_reward_validity_days = fields.Integer(string='Reward Valid For (Days)', default=30)
    feedback_reward_code_prefix = fields.Char(string='Reward Code Prefix', default='LASH-')
    feedback_reward_email_template = fields.Text(string='Reward Email Template')
    feedback_reward_sms_template = fields.Text(
        string='Reward SMS Template',
        default='Thank you for your feedback! Enjoy {discount} off your next visit. '
                'Use code {promo_code} (valid until {valid_to}). Book: {booking_link}')
```

- [ ] **Step 4: Run to verify it passes**

Run the per-task test command.
Expected: `0 failed, 0 error(s)`; `test_feedback_settings_defaults` passes.

- [ ] **Step 5: Commit**

```bash
git add addons/custom_appointments/models/appointment_settings.py addons/custom_appointments/tests/test_feedback.py
git commit -m "feat: add feedback configuration fields to settings"
```

---

## Task 4: Backfill feedback records for completed appointments

**Files:**
- Modify: `addons/custom_appointments/models/appointment_feedback.py`
- Test: `addons/custom_appointments/tests/test_feedback.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_feedback.py`:
```python
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
```

- [ ] **Step 2: Run to verify it fails**

Run the per-task test command.
Expected: ERROR — `cron_send_feedback_requests` does not exist.

- [ ] **Step 3: Implement cron entrypoint + backfill + create helper**

In `addons/custom_appointments/models/appointment_feedback.py`, add these methods to the `AppointmentFeedback` class (after `create`):
```python
    @api.model
    def _create_for_appointment(self, appointment):
        """Create a pending feedback record copying appointment data."""
        return self.create({
            'appointment_id': appointment.id,
            'partner_id': appointment.partner_id.id,
            'customer_name': appointment.customer_name,
            'customer_email': appointment.customer_email,
            'customer_phone': appointment.customer_phone,
            'staff_member_id': appointment.staff_member_id.id,
            'service_id': appointment.service_id.id,
            'branch_id': appointment.branch_id.id,
        })

    @api.model
    def _backfill_feedback_records(self):
        """Create pending feedback records for completed appointments missing one."""
        Appointment = self.env['custom.appointment']
        completed = Appointment.search([
            ('state', '=', 'completed'),
            ('completed_date', '!=', False),
        ])
        if not completed:
            return
        existing = self.search([('appointment_id', 'in', completed.ids)])
        existing_appt_ids = set(existing.mapped('appointment_id').ids)
        for appt in completed:
            if appt.id not in existing_appt_ids:
                self._create_for_appointment(appt)

    @api.model
    def cron_send_feedback_requests(self):
        """Cron entrypoint: backfill records, then send any due feedback requests."""
        settings = self.env['custom.appointment.settings'].get_settings()
        if not settings.enable_feedback_requests:
            return
        self._backfill_feedback_records()
        self._send_due_requests(settings)
```

- [ ] **Step 4: Add a temporary no-op `_send_due_requests`**

Still in the class, add (it is fully implemented in Task 5):
```python
    @api.model
    def _send_due_requests(self, settings):
        """Send feedback requests that are due. Implemented in Task 5."""
        return
```

- [ ] **Step 5: Run to verify it passes**

Run the per-task test command.
Expected: `0 failed, 0 error(s)`; the three backfill tests pass.

- [ ] **Step 6: Commit**

```bash
git add addons/custom_appointments/models/appointment_feedback.py addons/custom_appointments/tests/test_feedback.py
git commit -m "feat: backfill feedback records for completed appointments"
```

---

## Task 5: Send due feedback requests (timing + stop conditions)

**Files:**
- Modify: `addons/custom_appointments/models/appointment_feedback.py`
- Create: `addons/custom_appointments/templates/email/feedback_request.html`
- Test: `addons/custom_appointments/tests/test_feedback.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_feedback.py`:
```python
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
        before = self.env['sms.sms'].search_count([('number', '=', 'alice@test.com')])
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
```

- [ ] **Step 2: Run to verify it fails**

Run the per-task test command.
Expected: FAIL — `request_count` stays 0 (no-op `_send_due_requests`).

- [ ] **Step 3: Create the request email template**

Create `addons/custom_appointments/templates/email/feedback_request.html`:
```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
    <h2 style="color: #c2185b;">How was your visit, {customer_name}?</h2>
    <p>Thank you for choosing {company_name}. We'd love to hear about your
       <strong>{service_name}</strong> with {staff_name}.</p>
    <p>It only takes a minute:</p>
    <p style="text-align: center; margin: 30px 0;">
        <a href="{feedback_link}"
           style="background-color: #c2185b; color: #fff; padding: 12px 28px;
                  text-decoration: none; border-radius: 4px; font-weight: bold;">
            Leave Feedback
        </a>
    </p>
    <p style="font-size: 12px; color: #888;">If the button doesn't work, paste this link into your browser:<br/>{feedback_link}</p>
</div>
```

- [ ] **Step 4: Implement `_send_due_requests`, `_send_request`, and link helper**

In `addons/custom_appointments/models/appointment_feedback.py`, replace the temporary `_send_due_requests` no-op with:
```python
    def _get_feedback_link(self):
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        return f"{base_url}/appointments/feedback/{self.access_token}"

    @api.model
    def _send_due_requests(self, settings):
        now = fields.Datetime.now()
        first_delay = timedelta(minutes=settings.feedback_first_delay_minutes or 0)
        repeat = timedelta(minutes=settings.feedback_repeat_interval_minutes or 0)
        pending = self.search([('state', '=', 'pending')])
        for fb in pending:
            if fb.appointment_id.state == 'cancelled':
                continue
            if fb.request_count >= settings.feedback_max_requests:
                fb.state = 'expired'
                continue
            if fb.request_count == 0:
                anchor = fb.appointment_id.completed_date
                if not anchor:
                    continue
                due = anchor + first_delay
            else:
                if not fb.last_request_date:
                    continue
                due = fb.last_request_date + repeat
            if now >= due:
                fb._send_request(settings)

    def _send_request(self, settings):
        self.ensure_one()
        link = self._get_feedback_link()
        company = self.env.company

        if settings.feedback_channel in ('email', 'both') and self.customer_email:
            try:
                template = self.appointment_id._load_email_template('feedback_request')
                body_html = template.format(
                    customer_name=self.customer_name or 'there',
                    company_name=company.name,
                    service_name=self.service_id.name or '',
                    staff_name=self.staff_member_id.name or '',
                    feedback_link=link,
                )
                email_from = (self.branch_id.email or company.email or 'noreply@localhost')
                self.env['mail.mail'].sudo().create({
                    'subject': settings.feedback_request_email_subject or 'We value your feedback',
                    'body_html': body_html,
                    'email_to': self.customer_email,
                    'email_from': email_from,
                }).send()
            except Exception as e:
                _logger.error('Feedback: failed to send request email for %s: %s', self.id, str(e))

        if settings.feedback_channel in ('sms', 'both') and self.customer_phone:
            tmpl = settings.feedback_request_sms_template or (
                'Hi {customer_name}! How was your {service_name}? Share feedback: {feedback_link}')
            sms_body = tmpl.format(
                customer_name=self.customer_name or 'there',
                service_name=self.service_id.name or '',
                staff_name=self.staff_member_id.name or '',
                branch_name=self.branch_id.name or '',
                feedback_link=link,
            )
            self.appointment_id._send_sms_notification(self.customer_phone, sms_body)

        self.write({
            'request_count': self.request_count + 1,
            'last_request_date': fields.Datetime.now(),
        })
```

- [ ] **Step 5: Run to verify it passes**

Run the per-task test command.
Expected: `0 failed, 0 error(s)`; all four new tests pass.

- [ ] **Step 6: Commit**

```bash
git add addons/custom_appointments/models/appointment_feedback.py \
        addons/custom_appointments/templates/email/feedback_request.html \
        addons/custom_appointments/tests/test_feedback.py
git commit -m "feat: send due feedback requests via email/sms"
```

---

## Task 6: Submit feedback + generate promo reward

**Files:**
- Modify: `addons/custom_appointments/models/appointment_feedback.py`
- Create: `addons/custom_appointments/templates/email/feedback_reward.html`
- Test: `addons/custom_appointments/tests/test_feedback.py`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_feedback.py`:
```python
    def test_submit_saves_answers_and_rewards(self):
        self.settings.write({
            'enable_feedback_requests': True,
            'feedback_reward_enabled': True,
            'feedback_reward_discount_type': 'percentage',
            'feedback_reward_discount_value': 15.0,
            'feedback_reward_validity_days': 30,
            'feedback_reward_code_prefix': 'LASH-',
        })
        appt = self._make_appointment()
        appt.action_complete()
        fb = self.env['custom.appointment.feedback']._create_for_appointment(appt)
        promo = fb.submit_feedback({
            'staff_rating': 5,
            'service_rating': 4,
            'recommend_score': '9',
            'comments': 'Loved it!',
        })
        self.assertEqual(fb.state, 'submitted')
        self.assertTrue(fb.submitted_date)
        self.assertEqual(fb.staff_rating, 5)
        self.assertEqual(fb.recommend_score, '9')
        self.assertEqual(fb.comments, 'Loved it!')
        self.assertTrue(promo)
        self.assertEqual(fb.reward_promo_id, promo)
        self.assertTrue(promo.code.startswith('LASH-'))
        self.assertEqual(promo.discount_type, 'percentage')
        self.assertEqual(promo.discount_value, 15.0)
        self.assertEqual(promo.max_uses, 1)
        self.assertEqual(promo.max_uses_per_customer, 1)
        self.assertEqual(promo.assigned_partner_id, appt.partner_id)

    def test_submit_no_reward_when_disabled(self):
        self.settings.write({'feedback_reward_enabled': False})
        appt = self._make_appointment()
        appt.action_complete()
        fb = self.env['custom.appointment.feedback']._create_for_appointment(appt)
        promo = fb.submit_feedback({'staff_rating': 5})
        self.assertEqual(fb.state, 'submitted')
        self.assertFalse(promo)
        self.assertFalse(fb.reward_promo_id)

    def test_submit_is_idempotent(self):
        self.settings.write({'feedback_reward_enabled': True})
        appt = self._make_appointment()
        appt.action_complete()
        fb = self.env['custom.appointment.feedback']._create_for_appointment(appt)
        promo1 = fb.submit_feedback({'staff_rating': 5})
        promo2 = fb.submit_feedback({'staff_rating': 1})
        self.assertEqual(promo1, promo2)
        self.assertEqual(fb.staff_rating, 5)  # second submit ignored
```

- [ ] **Step 2: Run to verify it fails**

Run the per-task test command.
Expected: ERROR — `submit_feedback` does not exist.

- [ ] **Step 3: Create the reward email template**

Create `addons/custom_appointments/templates/email/feedback_reward.html`:
```html
<div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
    <h2 style="color: #c2185b;">Thank you, {customer_name}!</h2>
    <p>We appreciate your feedback. As a thank-you, here's a reward for your next visit:</p>
    <p style="text-align: center; margin: 24px 0;">
        <span style="display: inline-block; border: 2px dashed #c2185b; padding: 14px 28px;
                     font-size: 22px; font-weight: bold; letter-spacing: 2px; color: #c2185b;">
            {promo_code}
        </span>
    </p>
    <p style="text-align: center;">{discount} off &middot; valid until {valid_to}</p>
    <p style="text-align: center; margin-top: 24px;">
        <a href="{booking_link}"
           style="background-color: #c2185b; color: #fff; padding: 12px 28px;
                  text-decoration: none; border-radius: 4px; font-weight: bold;">
            Book Now
        </a>
    </p>
</div>
```

- [ ] **Step 4: Implement `submit_feedback`, `_generate_reward_promo`, `_send_reward_notification`**

In `addons/custom_appointments/models/appointment_feedback.py`, add to the class:
```python
    ANSWER_FIELDS = [
        'staff_rating', 'service_rating', 'recommend_score',
        'cleanliness_rating', 'comfort_rating', 'value_rating', 'comments',
    ]

    def submit_feedback(self, values):
        """Save answers, mark submitted, generate reward promo. Idempotent."""
        self.ensure_one()
        if self.state == 'submitted':
            return self.reward_promo_id
        to_write = {k: values[k] for k in self.ANSWER_FIELDS if k in values}
        to_write['state'] = 'submitted'
        to_write['submitted_date'] = fields.Datetime.now()
        self.write(to_write)
        settings = self.env['custom.appointment.settings'].sudo().get_settings()
        if settings.feedback_reward_enabled and not self.reward_promo_id:
            self._generate_reward_promo(settings)
        return self.reward_promo_id

    def _reward_discount_label(self, settings):
        if settings.feedback_reward_discount_type == 'percentage':
            return f"{settings.feedback_reward_discount_value:g}%"
        if settings.feedback_reward_discount_type == 'free_booking':
            return "a free booking fee"
        currency = self.env.company.currency_id
        return f"{currency.symbol}{settings.feedback_reward_discount_value:g}"

    def _generate_reward_promo(self, settings):
        self.ensure_one()
        Promo = self.env['custom.appointment.promo'].sudo()
        code = (settings.feedback_reward_code_prefix or '') + Promo.generate_unique_code()
        valid_to = fields.Date.today() + timedelta(days=settings.feedback_reward_validity_days or 0)
        promo = Promo.create({
            'name': f"Feedback reward - {self.customer_name or 'Customer'}",
            'code': code,
            'discount_type': settings.feedback_reward_discount_type,
            'discount_value': settings.feedback_reward_discount_value,
            'applies_to': settings.feedback_reward_applies_to,
            'maximum_discount': settings.feedback_reward_max_discount,
            'valid_from': fields.Date.today(),
            'valid_to': valid_to,
            'max_uses': 1,
            'max_uses_per_customer': 1,
            'assigned_partner_id': self.partner_id.id if self.partner_id else False,
            'active': True,
        })
        self.reward_promo_id = promo.id
        self._send_reward_notification(settings, promo)
        return promo

    def _send_reward_notification(self, settings, promo):
        self.ensure_one()
        company = self.env.company
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')
        booking_link = f"{base_url}/appointments"
        discount = self._reward_discount_label(settings)
        valid_to = promo.valid_to.strftime('%B %d, %Y') if promo.valid_to else ''

        if settings.feedback_channel in ('email', 'both') and self.customer_email:
            try:
                template = self.appointment_id._load_email_template('feedback_reward')
                body_html = template.format(
                    customer_name=self.customer_name or 'there',
                    promo_code=promo.code,
                    discount=discount,
                    valid_to=valid_to,
                    booking_link=booking_link,
                )
                email_from = (self.branch_id.email or company.email or 'noreply@localhost')
                self.env['mail.mail'].sudo().create({
                    'subject': 'Your feedback reward is here!',
                    'body_html': body_html,
                    'email_to': self.customer_email,
                    'email_from': email_from,
                }).send()
            except Exception as e:
                _logger.error('Feedback: failed to send reward email for %s: %s', self.id, str(e))

        if settings.feedback_channel in ('sms', 'both') and self.customer_phone:
            tmpl = settings.feedback_reward_sms_template or (
                'Thank you! Use code {promo_code} for {discount} off (valid until {valid_to}). {booking_link}')
            sms_body = tmpl.format(
                customer_name=self.customer_name or 'there',
                promo_code=promo.code,
                discount=discount,
                valid_to=valid_to,
                booking_link=booking_link,
            )
            self.appointment_id._send_sms_notification(self.customer_phone, sms_body)
```

- [ ] **Step 5: Run to verify it passes**

Run the per-task test command.
Expected: `0 failed, 0 error(s)`; all three submit tests pass.

- [ ] **Step 6: Commit**

```bash
git add addons/custom_appointments/models/appointment_feedback.py \
        addons/custom_appointments/templates/email/feedback_reward.html \
        addons/custom_appointments/tests/test_feedback.py
git commit -m "feat: submit feedback and generate unique promo reward"
```

---

## Task 7: Register the feedback cron

**Files:**
- Modify: `addons/custom_appointments/data/cron_jobs.xml`

- [ ] **Step 1: Add the cron record**

In `addons/custom_appointments/data/cron_jobs.xml`, before the closing `</odoo>`, add:
```xml
    <!-- Scheduled Action for Feedback Requests (after appointment completion) -->
    <record id="feedback_request_cron" model="ir.cron">
        <field name="name">Send Feedback Requests</field>
        <field name="model_id" ref="model_custom_appointment_feedback"/>
        <field name="state">code</field>
        <field name="code">model.cron_send_feedback_requests()</field>
        <field name="interval_number">15</field>
        <field name="interval_type">minutes</field>
        <field name="active">True</field>
        <field name="user_id" ref="base.user_root"/>
    </record>
```

- [ ] **Step 2: Update the module and confirm the cron loads**

Run:
```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo --config=/etc/odoo/odoo-local.conf \
  -d feedback_test --without-demo=all \
  -u custom_appointments --stop-after-init --no-http
```
Expected: completes with no XML/parse errors and `Modules loaded`.

- [ ] **Step 3: Verify the cron record exists**

Run:
```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo shell --config=/etc/odoo/odoo-local.conf -d feedback_test --no-http <<'PY'
cron = env.ref('custom_appointments.feedback_request_cron')
print(cron.name, cron.interval_number, cron.interval_type, cron.active)
PY
```
Expected: prints `Send Feedback Requests 15 minutes True`.

- [ ] **Step 4: Commit**

```bash
git add addons/custom_appointments/data/cron_jobs.xml
git commit -m "feat: add feedback request cron (every 15 min)"
```

---

## Task 8: Public feedback controller route

**Files:**
- Modify: `addons/custom_appointments/controllers/main.py`

- [ ] **Step 1: Add the route**

In `addons/custom_appointments/controllers/main.py`, add this method to the `AppointmentController` class (e.g. after `terms_page`, near line 605):
```python
    @http.route('/appointments/feedback/<string:token>', type='http', auth='public',
                website=True, methods=['GET', 'POST'])
    def appointment_feedback(self, token, **kwargs):
        """Public tokenized feedback page (GET shows form, POST submits)."""
        feedback = request.env['custom.appointment.feedback'].sudo().search(
            [('access_token', '=', token)], limit=1)
        if not feedback:
            return request.render('custom_appointments.feedback_invalid_page', {})

        settings = request.env['custom.appointment.settings'].sudo().get_settings()

        if request.httprequest.method == 'POST' and feedback.state != 'submitted':
            values = {}
            for field in ['staff_rating', 'service_rating', 'cleanliness_rating',
                          'comfort_rating', 'value_rating']:
                raw = kwargs.get(field)
                if raw:
                    try:
                        values[field] = int(raw)
                    except (ValueError, TypeError):
                        pass
            if kwargs.get('recommend_score'):
                values['recommend_score'] = kwargs.get('recommend_score')
            if kwargs.get('comments'):
                values['comments'] = kwargs.get('comments').strip()
            feedback.submit_feedback(values)

        if feedback.state == 'submitted':
            return request.render('custom_appointments.feedback_thankyou_page', {
                'feedback': feedback,
                'promo': feedback.reward_promo_id,
            })

        return request.render('custom_appointments.feedback_form_page', {
            'feedback': feedback,
            'settings': settings,
        })
```

- [ ] **Step 2: Update the module (templates added in Task 9; this step just confirms the controller imports cleanly)**

Run:
```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo --config=/etc/odoo/odoo-local.conf \
  -d feedback_test --without-demo=all \
  -u custom_appointments --stop-after-init --no-http
```
Expected: `Modules loaded` with no Python import errors. (Hitting the URL is verified in Task 9 once templates exist.)

- [ ] **Step 3: Commit**

```bash
git add addons/custom_appointments/controllers/main.py
git commit -m "feat: add public feedback controller route"
```

---

## Task 9: Public feedback website templates

**Files:**
- Create: `addons/custom_appointments/views/feedback_website_templates.xml`
- Modify: `addons/custom_appointments/__manifest__.py`

- [ ] **Step 1: Create the templates**

Create `addons/custom_appointments/views/feedback_website_templates.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Feedback form page -->
    <template id="feedback_form_page" name="Appointment Feedback Form">
        <t t-call="website.layout">
            <div class="container my-5" style="max-width: 640px;">
                <h2 class="mb-1">Share your feedback</h2>
                <p class="text-muted">
                    <t t-esc="feedback.service_id.name"/> with <t t-esc="feedback.staff_member_id.name"/>
                </p>
                <form method="post" t-attf-action="/appointments/feedback/#{feedback.access_token}" class="mt-4">
                    <input type="hidden" name="csrf_token" t-att-value="request.csrf_token()"/>

                    <div t-if="settings.feedback_ask_staff_rating" class="mb-4">
                        <label class="form-label fw-bold">How would you rate your technician?</label>
                        <div>
                            <t t-foreach="[1,2,3,4,5]" t-as="n">
                                <label class="me-3">
                                    <input type="radio" name="staff_rating" t-att-value="n"/>
                                    <span t-esc="n"/>
                                </label>
                            </t>
                        </div>
                    </div>

                    <div t-if="settings.feedback_ask_service_rating" class="mb-4">
                        <label class="form-label fw-bold">How would you rate the service?</label>
                        <div>
                            <t t-foreach="[1,2,3,4,5]" t-as="n">
                                <label class="me-3">
                                    <input type="radio" name="service_rating" t-att-value="n"/>
                                    <span t-esc="n"/>
                                </label>
                            </t>
                        </div>
                    </div>

                    <div t-if="settings.feedback_ask_recommend" class="mb-4">
                        <label class="form-label fw-bold">How likely are you to recommend us? (0-10)</label>
                        <div>
                            <t t-foreach="[0,1,2,3,4,5,6,7,8,9,10]" t-as="n">
                                <label class="me-2">
                                    <input type="radio" name="recommend_score" t-att-value="n"/>
                                    <span t-esc="n"/>
                                </label>
                            </t>
                        </div>
                    </div>

                    <div t-if="settings.feedback_ask_cleanliness" class="mb-4">
                        <label class="form-label fw-bold">Cleanliness</label>
                        <div>
                            <t t-foreach="[1,2,3,4,5]" t-as="n">
                                <label class="me-3">
                                    <input type="radio" name="cleanliness_rating" t-att-value="n"/>
                                    <span t-esc="n"/>
                                </label>
                            </t>
                        </div>
                    </div>

                    <div t-if="settings.feedback_ask_comfort" class="mb-4">
                        <label class="form-label fw-bold">Comfort during your service</label>
                        <div>
                            <t t-foreach="[1,2,3,4,5]" t-as="n">
                                <label class="me-3">
                                    <input type="radio" name="comfort_rating" t-att-value="n"/>
                                    <span t-esc="n"/>
                                </label>
                            </t>
                        </div>
                    </div>

                    <div t-if="settings.feedback_ask_value" class="mb-4">
                        <label class="form-label fw-bold">Value for money</label>
                        <div>
                            <t t-foreach="[1,2,3,4,5]" t-as="n">
                                <label class="me-3">
                                    <input type="radio" name="value_rating" t-att-value="n"/>
                                    <span t-esc="n"/>
                                </label>
                            </t>
                        </div>
                    </div>

                    <div t-if="settings.feedback_ask_comments" class="mb-4">
                        <label class="form-label fw-bold">Any comments?</label>
                        <textarea name="comments" class="form-control" rows="4"
                                  placeholder="Tell us about your experience..."/>
                    </div>

                    <button type="submit" class="btn btn-primary btn-lg">Submit Feedback</button>
                </form>
            </div>
        </t>
    </template>

    <!-- Thank-you page -->
    <template id="feedback_thankyou_page" name="Appointment Feedback Thank You">
        <t t-call="website.layout">
            <div class="container my-5 text-center" style="max-width: 640px;">
                <h2 class="mb-3">Thank you for your feedback!</h2>
                <p class="lead">We truly appreciate you taking the time.</p>
                <div t-if="promo" class="card mx-auto mt-4" style="max-width: 420px;">
                    <div class="card-body">
                        <p class="mb-2">Here's a little thank-you for your next visit:</p>
                        <h3 class="text-primary" style="letter-spacing: 2px;">
                            <t t-esc="promo.code"/>
                        </h3>
                        <p class="text-muted mb-3">
                            Valid until <t t-esc="promo.valid_to" t-options='{"widget": "date"}'/>
                        </p>
                        <a href="/appointments" class="btn btn-primary">Book Your Next Visit</a>
                    </div>
                </div>
            </div>
        </t>
    </template>

    <!-- Invalid / expired link page -->
    <template id="feedback_invalid_page" name="Appointment Feedback Invalid">
        <t t-call="website.layout">
            <div class="container my-5 text-center" style="max-width: 640px;">
                <h2 class="mb-3">Link not found</h2>
                <p class="text-muted">This feedback link is invalid or has expired.</p>
                <a href="/appointments" class="btn btn-primary mt-3">Go to Booking</a>
            </div>
        </t>
    </template>
</odoo>
```

- [ ] **Step 2: Register the file in the manifest**

In `addons/custom_appointments/__manifest__.py`, in the `data` list, add after `'views/website_templates.xml',` (line 41):
```python
        'views/feedback_website_templates.xml',
```

- [ ] **Step 3: Update the module**

Run:
```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo --config=/etc/odoo/odoo-local.conf \
  -d feedback_test --without-demo=all \
  -u custom_appointments --stop-after-init --no-http
```
Expected: `Modules loaded` with no QWeb/XML parse errors.

- [ ] **Step 4: Manually verify the page renders**

Run (creates a feedback record and prints its public URL token via odoo shell):
```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo shell --config=/etc/odoo/odoo-local.conf -d feedback_test --no-http <<'PY'
appt = env['custom.appointment'].search([], limit=1)
if appt:
    fb = env['custom.appointment.feedback']._create_for_appointment(appt)
    env.cr.commit()
    print('TOKEN', fb.access_token)
PY
```
Then start the server (`docker compose -f docker-compose-local.yml up -d odoo` if not running on `feedback_test`) OR confirm via production routing. Expected: visiting `/appointments/feedback/<TOKEN>` shows the form; submitting redirects to the thank-you page. (If serving only `LashesByShazz` over HTTP, this manual check can be performed there after the production update in Task 12.)

- [ ] **Step 5: Commit**

```bash
git add addons/custom_appointments/views/feedback_website_templates.xml \
        addons/custom_appointments/__manifest__.py
git commit -m "feat: add public feedback form, thank-you, and invalid templates"
```

---

## Task 10: Reorganize the settings form into tabs + Feedback tab

**Files:**
- Modify: `addons/custom_appointments/views/appointment_settings_views.xml`

- [ ] **Step 1: Replace the settings form view**

In `addons/custom_appointments/views/appointment_settings_views.xml`, replace the entire `appointment_settings_form_view` record (lines 4-63) with:
```xml
    <record id="appointment_settings_form_view" model="ir.ui.view">
        <field name="name">custom.appointment.settings.form</field>
        <field name="model">custom.appointment.settings</field>
        <field name="arch" type="xml">
            <form string="Communication Settings" create="false" delete="false">
                <sheet>
                    <div class="oe_title">
                        <h1>Communication Settings</h1>
                        <p class="text-muted">Configure follow-up and feedback messages sent to customers after their appointments</p>
                    </div>

                    <notebook>
                        <page string="Follow-up Messages" name="followup">
                            <group>
                                <group string="Enable Follow-up Messages">
                                    <field name="send_followup_messages" widget="boolean_toggle"/>
                                </group>
                            </group>
                            <div invisible="not send_followup_messages">
                                <group>
                                    <group string="Communication Channel">
                                        <field name="followup_channel" widget="radio"/>
                                    </group>
                                </group>
                                <group>
                                    <group string="Timing">
                                        <field name="followup_start_days"/>
                                        <field name="followup_repeat_interval"/>
                                    </group>
                                    <group string="Follow-up Limits">
                                        <field name="max_followup_count" invisible="followup_until_rebooked"/>
                                        <field name="followup_until_rebooked"/>
                                    </group>
                                </group>
                                <group string="Email Settings">
                                    <field name="followup_email_subject" placeholder="We Miss You! Book Your Next Session"/>
                                    <field name="followup_email_template" placeholder="Custom email body (uses HTML template if left blank)"/>
                                </group>
                                <group string="SMS Settings">
                                    <field name="followup_sms_template" placeholder="Hi {customer_name}! Ready for your next {service_name}? Book now: {booking_link}"/>
                                </group>
                                <div class="alert alert-info" role="alert">
                                    <strong>Available Placeholders:</strong><br/>
                                    <code>{customer_name}</code> - Customer's name<br/>
                                    <code>{service_name}</code> - Name of the service they had<br/>
                                    <code>{branch_name}</code> - Branch name<br/>
                                    <code>{booking_link}</code> - Link to booking page
                                </div>
                            </div>
                        </page>

                        <page string="Customer Feedback" name="feedback">
                            <group>
                                <group string="Collect Customer Feedback">
                                    <field name="enable_feedback_requests" widget="boolean_toggle"/>
                                </group>
                            </group>
                            <div invisible="not enable_feedback_requests">
                                <group>
                                    <group string="Channel">
                                        <field name="feedback_channel" widget="radio"/>
                                    </group>
                                    <group string="Timing">
                                        <field name="feedback_first_delay_minutes"/>
                                        <field name="feedback_repeat_interval_minutes"/>
                                        <field name="feedback_max_requests"/>
                                    </group>
                                </group>
                                <group string="Which Questions to Ask">
                                    <field name="feedback_ask_staff_rating"/>
                                    <field name="feedback_ask_service_rating"/>
                                    <field name="feedback_ask_recommend"/>
                                    <field name="feedback_ask_cleanliness"/>
                                    <field name="feedback_ask_comfort"/>
                                    <field name="feedback_ask_value"/>
                                    <field name="feedback_ask_comments"/>
                                </group>
                                <group string="Request Messages">
                                    <field name="feedback_request_email_subject"/>
                                    <field name="feedback_request_sms_template"
                                           placeholder="Hi {customer_name}! How was your {service_name}? Share feedback: {feedback_link}"/>
                                </group>
                                <group string="Feedback Reward">
                                    <field name="feedback_reward_enabled" widget="boolean_toggle"/>
                                </group>
                                <group invisible="not feedback_reward_enabled">
                                    <group string="Discount">
                                        <field name="feedback_reward_discount_type"/>
                                        <field name="feedback_reward_discount_value"
                                               invisible="feedback_reward_discount_type == 'free_booking'"/>
                                        <field name="feedback_reward_applies_to"/>
                                        <field name="feedback_reward_max_discount"
                                               invisible="feedback_reward_discount_type != 'percentage'"/>
                                    </group>
                                    <group string="Code">
                                        <field name="feedback_reward_validity_days"/>
                                        <field name="feedback_reward_code_prefix"/>
                                    </group>
                                </group>
                                <group invisible="not feedback_reward_enabled" string="Reward SMS">
                                    <field name="feedback_reward_sms_template"
                                           placeholder="Thank you! Use code {promo_code} for {discount} off..."/>
                                </group>
                                <div class="alert alert-info" role="alert">
                                    <strong>Feedback placeholders:</strong>
                                    <code>{customer_name}</code>, <code>{service_name}</code>,
                                    <code>{staff_name}</code>, <code>{branch_name}</code>,
                                    <code>{feedback_link}</code><br/>
                                    <strong>Reward placeholders:</strong>
                                    <code>{promo_code}</code>, <code>{discount}</code>,
                                    <code>{valid_to}</code>, <code>{booking_link}</code>
                                </div>
                            </div>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>
```

- [ ] **Step 2: Update the module and verify the view parses**

Run:
```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo --config=/etc/odoo/odoo-local.conf \
  -d feedback_test --without-demo=all \
  -u custom_appointments --stop-after-init --no-http
```
Expected: `Modules loaded` with no view validation errors (a bad field name here would raise during load).

- [ ] **Step 3: Commit**

```bash
git add addons/custom_appointments/views/appointment_settings_views.xml
git commit -m "feat: add Customer Feedback tab to Communication Settings"
```

---

## Task 11: Feedback admin views, menu, and appointment smart button

**Files:**
- Create: `addons/custom_appointments/views/appointment_feedback_views.xml`
- Modify: `addons/custom_appointments/models/appointment.py`
- Modify: `addons/custom_appointments/views/appointment_views.xml` (button box around lines 64-68)
- Modify: `addons/custom_appointments/__manifest__.py`

- [ ] **Step 1: Add the appointment-side glue (One2many, count, action)**

In `addons/custom_appointments/models/appointment.py`, add these fields after `completed_date` (added in Task 1):
```python
    feedback_ids = fields.One2many('custom.appointment.feedback', 'appointment_id', string='Feedback')
    feedback_count = fields.Integer(string='Feedback Count', compute='_compute_feedback_count')
```
Add this compute near the other compute methods (e.g. after `_compute_payment_count`, around line 127):
```python
    @api.depends('feedback_ids')
    def _compute_feedback_count(self):
        for appointment in self:
            appointment.feedback_count = len(appointment.feedback_ids)
```
Add this action method near `action_view_payment` (around line 480):
```python
    def action_view_feedback(self):
        self.ensure_one()
        return {
            'name': 'Feedback',
            'type': 'ir.actions.act_window',
            'res_model': 'custom.appointment.feedback',
            'view_mode': 'form,list',
            'domain': [('appointment_id', '=', self.id)],
            'context': {'default_appointment_id': self.id},
        }
```

- [ ] **Step 2: Add the smart button**

In `addons/custom_appointments/views/appointment_views.xml`, inside the `<div class="oe_button_box" name="button_box">` (after the `action_view_invoice` button block ending near line 70), add:
```xml
                        <button name="action_view_feedback" type="object" class="oe_stat_button" icon="fa-comments" invisible="feedback_count == 0">
                            <field name="feedback_count" widget="statinfo" string="Feedback"/>
                        </button>
```

- [ ] **Step 3: Create the feedback admin views + menu**

Create `addons/custom_appointments/views/appointment_feedback_views.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="feedback_search_view" model="ir.ui.view">
        <field name="name">custom.appointment.feedback.search</field>
        <field name="model">custom.appointment.feedback</field>
        <field name="arch" type="xml">
            <search>
                <field name="customer_name"/>
                <field name="staff_member_id"/>
                <field name="service_id"/>
                <field name="branch_id"/>
                <filter name="submitted" string="Submitted" domain="[('state', '=', 'submitted')]"/>
                <filter name="pending" string="Pending" domain="[('state', '=', 'pending')]"/>
                <group expand="0" string="Group By">
                    <filter name="group_customer" string="Customer" context="{'group_by': 'partner_id'}"/>
                    <filter name="group_staff" string="Staff Member" context="{'group_by': 'staff_member_id'}"/>
                    <filter name="group_service" string="Service" context="{'group_by': 'service_id'}"/>
                    <filter name="group_branch" string="Branch" context="{'group_by': 'branch_id'}"/>
                    <filter name="group_state" string="Status" context="{'group_by': 'state'}"/>
                </group>
            </search>
        </field>
    </record>

    <record id="feedback_list_view" model="ir.ui.view">
        <field name="name">custom.appointment.feedback.list</field>
        <field name="model">custom.appointment.feedback</field>
        <field name="arch" type="xml">
            <list create="false">
                <field name="submitted_date"/>
                <field name="customer_name"/>
                <field name="staff_member_id"/>
                <field name="service_id"/>
                <field name="branch_id"/>
                <field name="staff_rating"/>
                <field name="service_rating"/>
                <field name="recommend_score"/>
                <field name="reward_promo_id"/>
                <field name="state"/>
            </list>
        </field>
    </record>

    <record id="feedback_form_view" model="ir.ui.view">
        <field name="name">custom.appointment.feedback.form</field>
        <field name="model">custom.appointment.feedback</field>
        <field name="arch" type="xml">
            <form string="Feedback" create="false">
                <sheet>
                    <group>
                        <group string="Customer">
                            <field name="customer_name"/>
                            <field name="customer_email"/>
                            <field name="customer_phone"/>
                            <field name="appointment_id"/>
                        </group>
                        <group string="Context">
                            <field name="staff_member_id"/>
                            <field name="service_id"/>
                            <field name="branch_id"/>
                            <field name="state"/>
                            <field name="submitted_date"/>
                            <field name="reward_promo_id"/>
                        </group>
                    </group>
                    <group string="Ratings">
                        <field name="staff_rating"/>
                        <field name="service_rating"/>
                        <field name="recommend_score"/>
                        <field name="cleanliness_rating"/>
                        <field name="comfort_rating"/>
                        <field name="value_rating"/>
                    </group>
                    <group string="Comments">
                        <field name="comments" nolabel="1"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <record id="feedback_action" model="ir.actions.act_window">
        <field name="name">Feedback</field>
        <field name="res_model">custom.appointment.feedback</field>
        <field name="view_mode">list,form</field>
        <field name="search_view_id" ref="feedback_search_view"/>
        <field name="context">{'search_default_submitted': 1}</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">No feedback yet</p>
        </field>
    </record>

    <menuitem id="feedback_menu"
              name="Feedback"
              parent="appointments_main_menu"
              action="feedback_action"
              sequence="40"/>
</odoo>
```

- [ ] **Step 4: Register the file in the manifest**

In `addons/custom_appointments/__manifest__.py`, in the `data` list, add after `'views/customer_views.xml',` (line 40):
```python
        'views/appointment_feedback_views.xml',
```

- [ ] **Step 5: Update the module and run the test suite (regression)**

Run the per-task test command.
Expected: `Modules loaded` with no view errors and `0 failed, 0 error(s)`.

- [ ] **Step 6: Commit**

```bash
git add addons/custom_appointments/views/appointment_feedback_views.xml \
        addons/custom_appointments/models/appointment.py \
        addons/custom_appointments/views/appointment_views.xml \
        addons/custom_appointments/__manifest__.py
git commit -m "feat: add feedback admin views, menu, and appointment smart button"
```

---

## Task 12: Full clean-install regression + production update

**Files:** none (verification + deploy)

- [ ] **Step 1: Clean install on a fresh DB to catch ordering/dependency issues**

Run:
```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo --config=/etc/odoo/odoo-local.conf \
  -d feedback_fresh --without-demo=all \
  -i custom_appointments --test-enable \
  --test-tags /custom_appointments \
  --stop-after-init --no-http --log-level=test
```
Expected: module installs from scratch and all feedback tests report `0 failed, 0 error(s)`.

- [ ] **Step 2: Update the production database**

> Confirm with the user before running against production `LashesByShazz`.

Run:
```bash
docker compose -f docker-compose-local.yml exec -T odoo \
  odoo --config=/etc/odoo/odoo-local.conf \
  -d LashesByShazz -u custom_appointments --stop-after-init --no-http
```
Expected: `Modules loaded`, no errors. New fields/menu/cron now present.

- [ ] **Step 3: Restart the running server**

Run:
```bash
docker compose -f docker-compose-local.yml restart odoo
```
Expected: container restarts and serves normally.

- [ ] **Step 4: Manual smoke check in production**

- In Odoo backend: Appointments → Configuration → Communication Settings → **Customer Feedback** tab. Toggle on, set fields, save.
- Mark a test appointment **Completed**; after the configured delay the cron sends the request (or trigger the cron manually from Settings → Technical → Scheduled Actions → "Send Feedback Requests" → Run Manually).
- Open the feedback link, submit, confirm the thank-you page shows a promo code and the customer receives it.
- Appointments → **Feedback** menu shows the submission; group by Staff Member / Customer works.

- [ ] **Step 5: Final commit (if any doc/notes updates) and push the branch**

```bash
git add -A
git commit -m "chore: appointment feedback feature complete" --allow-empty
git push -u origin feature/appointment-feedback
```

---

## Self-Review Notes

- **Spec coverage:** model fields (Task 2), `completed_date` (Task 1), settings/tab (Tasks 3, 10), minute-based cron + backfill + stop conditions (Tasks 4, 5, 7), public tokenized page + promo-on-submit (Tasks 6, 8, 9), admin views/menu/grouping + smart button (Task 11), security/manifest/templates (Tasks 2, 5, 6, 9, 11) — all covered.
- **NPS storage:** `recommend_score` is a `Selection` of `'0'`–`'10'` strings (`range(0, 11)` → 11 values) so a true 0 is distinguishable from unanswered (`False`); tests and controller treat it as a string.
- **Method/name consistency:** `cron_send_feedback_requests`, `_backfill_feedback_records`, `_send_due_requests`, `_send_request`, `_create_for_appointment`, `submit_feedback`, `_generate_reward_promo`, `_send_reward_notification`, `_get_feedback_link`, `action_view_feedback`, `feedback_count`/`feedback_ids` are used consistently across tasks.
- **Reused existing APIs:** `custom.appointment._send_sms_notification`, `custom.appointment._load_email_template`, `custom.appointment.promo.generate_unique_code`, `custom.appointment.settings.get_settings` — all verified to exist in the current code.
