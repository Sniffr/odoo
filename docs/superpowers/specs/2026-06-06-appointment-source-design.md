# Appointment Source Tracking — Design

**Date:** 2026-06-06
**Module:** `custom_appointments`
**Status:** Approved

## Problem

Appointments are booked through two paths — the public online booking flow and
manual creation by staff in the backend — but the system does not record *how*
each appointment originated. The salon wants to categorize each appointment by
its source (e.g. booked Online vs. taken over the phone as a Call-in), see the
source on the appointment, group appointments by source, and let staff add their
own source options over time. Existing historical appointments should be
categorized as **Online** by default.

## Goals

- Record the source of every appointment.
- Online bookings (public flow) are automatically tagged **Online**.
- Backend/manual bookings default to **Online** and staff can change the source.
- Staff can add, rename, reorder, and archive source options from the backend UI
  without a code change.
- Existing appointments are backfilled to **Online** on upgrade.
- Appointments can be grouped/filtered by source.

## Non-Goals (YAGNI)

- Per-source colors or icons.
- Any analytics dashboard or pivot/report beyond a group-by in the list view.
- Auto-detecting finer-grained sources (campaign, referrer, etc.).

## Design

### 1. New model: `custom.appointment.source`

A small admin-manageable lookup model, mirroring the existing
`custom.branch` / `company.service` patterns.

| Field      | Type    | Notes                                            |
|------------|---------|--------------------------------------------------|
| `name`     | Char    | required                                         |
| `sequence` | Integer | default 10; controls ordering (`_order = 'sequence, name'`) |
| `active`   | Boolean | default True; archive instead of delete          |

Seeded records via data XML, **`noupdate="1"`** so admin renames/edits persist
across module upgrades:

- `appointment_source_online` — "Online" (sequence 1)
- `appointment_source_call_in` — "Call-in" (sequence 2)
- `appointment_source_walk_in` — "Walk-in" (sequence 3)

Security: read/write/create/unlink for the internal appointments user group
(same group used by other config models); add a row to `ir.model.access.csv`.

### 2. `source_id` on `custom.appointment`

```python
source_id = fields.Many2one(
    'custom.appointment.source', string='Source',
    ondelete='restrict',
    default=lambda self: self.env.ref(
        'custom_appointments.appointment_source_online',
        raise_if_not_found=False))
```

- `ondelete='restrict'` prevents deleting a source that is in use (archive
  instead).
- Shown on the appointment form (near branch/service) and as a column in the
  list view.
- Added to the appointment **search view** as a filterable field and a
  **group-by** option.

### 3. Online bookings auto-tagged

In `controllers/main.py`, where the public booking creates the appointment
(`appointment_vals`, ~line 331), explicitly set:

```python
'source_id': request.env.ref(
    'custom_appointments.appointment_source_online').id,
```

This guarantees online bookings are always **Online** regardless of the model
default (defensive against future default changes).

### 4. Backfill existing appointments

A `post_init_hook` (registered in `__manifest__.py`) sets `source_id` to the
**Online** source for every existing appointment where `source_id IS NULL`:

```python
def _backfill_appointment_source(env):
    online = env.ref('custom_appointments.appointment_source_online',
                     raise_if_not_found=False)
    if not online:
        return
    env['custom.appointment'].search([('source_id', '=', False)]).write(
        {'source_id': online.id})
```

Runs once on install/upgrade; idempotent (only touches NULL rows).

### 5. Menu

New menu item **Appointments → Configuration → Sources** opening a list/form
action for `custom.appointment.source`, placed alongside the other
configuration menus.

## Testing

`TransactionCase` tests in `custom_appointments/tests/`:

1. The three sources are seeded; `appointment_source_online` exists.
2. A new backend appointment defaults to **Online**.
3. An appointment created with an explicit source (Call-in) keeps that source.
4. The online controller booking path results in `source_id == Online`.
5. The backfill hook sets `source_id = Online` for an appointment whose source
   was cleared to NULL.
6. `read_group` by `source_id` returns appointments bucketed by source.

## Files Touched

- `models/appointment_source.py` (new)
- `models/__init__.py` (import new model)
- `models/appointment.py` (add `source_id`)
- `controllers/main.py` (set source on online booking)
- `data/appointment_source_data.xml` (new — seed records)
- `security/ir.model.access.csv` (access row)
- `views/appointment_source_views.xml` (new — list/form/action/menu)
- `views/appointment_views.xml` (form + list + search: add `source_id`)
- `__init__.py` / `__manifest__.py` (post_init_hook registration + data/views)
- `tests/` (new test module)
