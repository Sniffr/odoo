# Customer Feedback for Appointments — Design Spec

**Date:** 2026-06-05
**Module:** `custom_appointments` (Odoo 18, db `lashesByshazz`)
**Status:** Approved design, pending implementation plan

## Goal

After an appointment is marked **completed**, prompt the customer (starting a few
minutes later) to leave feedback about the staff, the service, and how likely they
are to recommend the salon, plus a few lash-salon-specific items. Feedback collection
is admin-configurable (on/off, which fields, timing, repeat cadence). When a customer
submits feedback they receive a unique single-use promo code as a thank-you reward,
reusing the existing promo-code system.

## Scope / constraints

- Reuse existing patterns: the follow-up reminder system, the `custom.appointment.promo`
  model, `_send_sms_notification`, `_load_email_template`, timezone helpers,
  `generate_unique_code`.
- Curated, fixed set of feedback fields for now (each individually toggleable). A fully
  dynamic field builder is explicitly **out of scope** for this iteration but the data
  model should not block adding it later.
- Promo reward issues a **unique code per customer** (not a shared code).
- Timing is **minute-based**, driven by a cron running every ~15 minutes (to honor the
  "5 minutes after completion" requirement).
- Feedback config lives on the existing **Communication Settings** page as a new tab,
  with its **own** master toggle independent of the follow-up toggle.

## 1. New model: `custom.appointment.feedback`

One record per appointment, created in state `pending` when the appointment is marked
completed (and feedback collection is enabled).

**Identity / tracking fields**

| Field | Type | Notes |
|---|---|---|
| `appointment_id` | M2O `custom.appointment` | required, unique, `ondelete='cascade'` |
| `partner_id` | M2O `res.partner` | copied from appointment |
| `customer_name` | Char | copied |
| `customer_email` | Char | copied |
| `customer_phone` | Char | copied |
| `staff_member_id` | M2O `custom.staff.member` | copied (denormalized for reporting) |
| `service_id` | M2O `company.service` | copied |
| `branch_id` | M2O `custom.branch` | copied |
| `access_token` | Char | `secrets.token_urlsafe`, indexes the public link |
| `state` | Selection | `pending` / `submitted` / `expired` |
| `request_count` | Integer | number of feedback requests sent |
| `last_request_date` | Datetime | when the last request was sent |
| `submitted_date` | Datetime | when the customer submitted |

**Answer fields** (curated set; all nullable, rendered only when enabled in settings).
The 1–5 ratings are stored as `Integer` where `0` means unanswered (0 is not a valid
star value). `recommend_score` is stored as a `Selection` of `'0'`–`'10'` so that a true
NPS score of 0 is distinguishable from "unanswered" (`False`/null). Ratings render as
stars / a numeric scale in the public form and as plain numbers in admin views.

| Field | Type | Range |
|---|---|---|
| `staff_rating` | Integer | 1–5 (0 = unanswered) |
| `service_rating` | Integer | 1–5 (0 = unanswered) |
| `recommend_score` | Selection `'0'`–`'10'` | 0–10 (NPS); null = unanswered |
| `cleanliness_rating` | Integer | 1–5 (0 = unanswered) |
| `comfort_rating` | Integer | 1–5 (0 = unanswered) |
| `value_rating` | Integer | 1–5 (0 = unanswered) |
| `comments` | Text | free text |

**Reward link**

| Field | Type | Notes |
|---|---|---|
| `reward_promo_id` | M2O `custom.appointment.promo` | the unique code generated on submit |

### Supporting change to `custom.appointment`

- Add `completed_date` (Datetime), set whenever state transitions to `completed`
  (in `action_complete()` **and** in `write()` when state becomes `completed`). This is
  the anchor for the "minutes after completion" timer.
- Add a smart button / link to view the related feedback record from the appointment form.

## 2. Settings — extend `custom.appointment.settings`

The existing singleton gains new fields and the form is reorganized into a notebook with
two tabs.

- **Tab "Follow-up Messages"** — existing fields, unchanged, gated by the existing
  `send_followup_messages` toggle.
- **Tab "Customer Feedback"** — gated by a new `enable_feedback_requests` toggle
  (independent of the follow-up toggle).

New fields on the settings model:

**Request behavior**
- `feedback_channel` — Selection `sms` / `email` / `both` (default `both`)
- `feedback_first_delay_minutes` — Integer (default 5)
- `feedback_repeat_interval_minutes` — Integer (default 1440)
- `feedback_max_requests` — Integer (default 3)

**Which fields to ask** (Booleans, default `True`)
- `feedback_ask_staff_rating`, `feedback_ask_service_rating`, `feedback_ask_recommend`,
  `feedback_ask_cleanliness`, `feedback_ask_comfort`, `feedback_ask_value`,
  `feedback_ask_comments`

**Request messages**
- `feedback_request_email_subject` (Char)
- `feedback_request_email_template` (Text)
- `feedback_request_sms_template` (Text)
- Placeholders: `{customer_name}`, `{service_name}`, `{staff_name}`, `{branch_name}`,
  `{feedback_link}`

**Promo reward sub-section** (gated by `feedback_reward_enabled` Boolean)
- `feedback_reward_discount_type` — Selection `percentage` / `fixed` / `free_booking`
- `feedback_reward_discount_value` — Float
- `feedback_reward_applies_to` — Selection `booking_fee` / `full_price` / `both`
  (default `full_price`)
- `feedback_reward_max_discount` — Float (0 = no cap)
- `feedback_reward_validity_days` — Integer (default 30)
- `feedback_reward_code_prefix` — Char (default `LASH-`)
- `feedback_reward_email_template` (Text), `feedback_reward_sms_template` (Text)
- Reward placeholders include `{promo_code}`, `{discount}`, `{valid_to}` in addition to
  the common ones.

## 3. Lifecycle & cron

**New cron "Send Feedback Requests"**, interval 15 minutes, calling
`custom.appointment.feedback.cron_send_feedback_requests()`:

1. If `enable_feedback_requests` is off → return.
2. **Backfill:** find appointments with `state = completed`, `completed_date` set, and no
   feedback record yet → create `pending` feedback records (copying customer / staff /
   service / branch and generating the access token). This catches completions done via
   direct edits, not just `action_complete()`.
3. **Send due requests** over `pending` records:
   - due = `completed_date + first_delay` when `request_count == 0`,
     else `last_request_date + repeat_interval`
   - if `request_count >= feedback_max_requests` → set `state = expired`, skip
   - if `now >= due` → send request via configured channel (email/SMS with tokenized
     link), increment `request_count`, set `last_request_date = now`
4. **Stop conditions:** record `submitted`, `request_count` reached max (→ `expired`), or
   the appointment was cancelled.

All datetime comparisons use `fields.Datetime.now()` (UTC), consistent with the module.

## 4. Public feedback page + promo reward

**Controller routes** (`custom_appointments/controllers/main.py`):

- `GET /appointments/feedback/<token>` — look up feedback by `access_token`. If already
  `submitted`, render a "thank you / already submitted" page. Otherwise render the form
  showing only the enabled fields.
- `POST /appointments/feedback/<token>` — validate token, require at least one field
  answered, save answers, set `state = submitted` and `submitted_date`, which stops
  further requests. Then, if `feedback_reward_enabled`:
  1. Create a `custom.appointment.promo`:
     - `code = feedback_reward_code_prefix + generate_unique_code()`
     - discount type / value / `applies_to` / `maximum_discount` from settings
     - `valid_from = today`, `valid_to = today + feedback_reward_validity_days`
     - `max_uses = 1`, `max_uses_per_customer = 1`
     - `assigned_partner_id = partner_id`
     - `name = "Feedback reward - {customer_name}"`
  2. Link `reward_promo_id`.
  3. Send the code to the customer via the configured channel.
  4. Redirect to a thank-you page displaying the promo code.

Token-based access means no login is required and links are not guessable by appointment
ID.

## 5. Admin feedback views (Appointments module)

- New **Feedback** top-level menu in the appointments app.
- **List view:** customer, staff, service, branch, ratings, NPS, submitted date, reward
  code, state — sortable.
- **Search / group-by:** customer, staff member, service, branch, state, recommend score
  (so feedback can be organized "by customers etc.").
- **Form view:** read-only display of all answers, link to the appointment and reward
  promo.
- Smart button on the appointment form to open its feedback record.

## 6. Templates, security, files

- New email templates: `templates/email/feedback_request.html`,
  `templates/email/feedback_reward.html`.
- New website templates for the feedback form and thank-you / already-submitted pages
  (new file or appended to `website_templates.xml`).
- `security/ir.model.access.csv`: access rules for `custom.appointment.feedback`
  (admin manage; controller uses `sudo()` for public submission).
- New cron entry in `data/cron_jobs.xml`.
- `__manifest__.py` data list updated for any new view/template files.

## Out of scope (future)

- Dynamic / admin-built custom feedback questions of arbitrary types.
- Per-field "required" configuration (all enabled fields optional for now; submit
  requires at least one answer).
- Aggregated dashboards / NPS analytics beyond list grouping.
