# Appointment Source Tracking Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the source of every appointment (Online / Call-in / Walk-in / staff-added), auto-tagging online bookings, defaulting everything else to Online, and backfilling existing appointments.

**Architecture:** Add an admin-manageable `custom.appointment.source` lookup model seeded with three records. Add a `source_id` Many2one on `custom.appointment` defaulting to the seeded "Online" record. The public booking controller sets the source explicitly to Online. A `post_init_hook` backfills existing appointments to Online. Views expose the field and a group-by; a Configuration submenu manages the source list.

**Tech Stack:** Odoo 18, Python, QWeb/XML views, PostgreSQL. All commands run inside the Docker container.

---

## Conventions

**Module path:** `addons/custom_appointments/`

**Running the test suite** (throwaway DB named `test_source`; first run installs, later runs update):

```bash
# First run (install):
docker compose -f docker-compose-local.yml exec -T odoo odoo \
  --config=/etc/odoo/odoo-local.conf -d test_source --without-demo=all \
  -i custom_appointments --test-enable --test-tags /custom_appointments \
  --stop-after-init --no-http --log-level=test

# Subsequent runs (update):
docker compose -f docker-compose-local.yml exec -T odoo odoo \
  --config=/etc/odoo/odoo-local.conf -d test_source --without-demo=all \
  -u custom_appointments --test-enable --test-tags /custom_appointments \
  --stop-after-init --no-http --log-level=test
```

**Success:** log shows `odoo.tests.stats: custom_appointments: N tests` and NO `FAIL:` or `ERROR:` lines.

**Note on schema changes:** When you add a new Python field or new model, you MUST run with `-u`/`-i` (not just rerun) so Odoo applies the schema migration before the test sees it. The commands above already do this.

---

## File Structure

- `models/appointment_source.py` (new) — the `custom.appointment.source` model.
- `models/__init__.py` (modify) — import the new model.
- `models/appointment.py` (modify) — add `source_id` field.
- `__init__.py` (module root, modify) — define `post_init_hook` backfill function.
- `__manifest__.py` (modify) — register data file, view file, and `post_init_hook`.
- `data/appointment_source_data.xml` (new) — seed Online / Call-in / Walk-in.
- `security/ir.model.access.csv` (modify) — access rows for the new model.
- `views/appointment_source_views.xml` (new) — list/form/action + Sources menu.
- `views/appointment_views.xml` (modify) — add `source_id` to form, list, search + group-by.
- `controllers/main.py` (modify) — set `source_id` on the online booking.
- `tests/test_appointment_source.py` (new) — test module.
- `tests/__init__.py` (modify) — import the new test module.

---

## Task 1: Create the `custom.appointment.source` model

**Files:**
- Create: `addons/custom_appointments/models/appointment_source.py`
- Modify: `addons/custom_appointments/models/__init__.py`
- Modify: `addons/custom_appointments/security/ir.model.access.csv`

- [ ] **Step 1: Create the model file**

Create `addons/custom_appointments/models/appointment_source.py`:

```python
from odoo import models, fields


class AppointmentSource(models.Model):
    _name = 'custom.appointment.source'
    _description = 'Appointment Source'
    _order = 'sequence, name'

    name = fields.Char(string='Source', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
```

- [ ] **Step 2: Register the model import**

In `addons/custom_appointments/models/__init__.py`, add after the last import
(`from . import appointment_feedback`):

```python
from . import appointment_source
```

- [ ] **Step 3: Add security access rows**

In `addons/custom_appointments/security/ir.model.access.csv`, append two lines at
the end (internal users full access; public read-only, matching the other lookup
models like `custom.branch`):

```csv
access_custom_appointment_source_user,custom.appointment.source.user,model_custom_appointment_source,base.group_user,1,1,1,1
access_custom_appointment_source_public,custom.appointment.source.public,model_custom_appointment_source,base.group_public,1,0,0,0
```

- [ ] **Step 4: Verify it loads (install)**

Run the **install** command from Conventions. Expected: install completes,
`custom_appointments: 0 tests` (no tests yet), no `ERROR:`.

- [ ] **Step 5: Commit**

```bash
git add addons/custom_appointments/models/appointment_source.py \
        addons/custom_appointments/models/__init__.py \
        addons/custom_appointments/security/ir.model.access.csv
git commit -m "feat: add custom.appointment.source model"
```

---

## Task 2: Seed the source records (Online / Call-in / Walk-in)

**Files:**
- Create: `addons/custom_appointments/data/appointment_source_data.xml`
- Modify: `addons/custom_appointments/__manifest__.py`
- Create: `addons/custom_appointments/tests/test_appointment_source.py`
- Modify: `addons/custom_appointments/tests/__init__.py`

- [ ] **Step 1: Write the failing test**

Create `addons/custom_appointments/tests/test_appointment_source.py`:

```python
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
```

- [ ] **Step 2: Register the test module**

In `addons/custom_appointments/tests/__init__.py`, add:

```python
from . import test_appointment_source
```

- [ ] **Step 3: Run the test to verify it fails**

Run the **update** command from Conventions. Expected: FAIL — the
`env.ref('custom_appointments.appointment_source_online')` raises
`ValueError: External ID not found` because the seed data does not exist yet.

- [ ] **Step 4: Create the seed data file**

Create `addons/custom_appointments/data/appointment_source_data.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <data noupdate="1">
        <record id="appointment_source_online" model="custom.appointment.source">
            <field name="name">Online</field>
            <field name="sequence">1</field>
        </record>
        <record id="appointment_source_call_in" model="custom.appointment.source">
            <field name="name">Call-in</field>
            <field name="sequence">2</field>
        </record>
        <record id="appointment_source_walk_in" model="custom.appointment.source">
            <field name="name">Walk-in</field>
            <field name="sequence">3</field>
        </record>
    </data>
</odoo>
```

`noupdate="1"` ensures admin renames/edits survive future module upgrades.

- [ ] **Step 5: Register the data file in the manifest**

In `addons/custom_appointments/__manifest__.py`, in the `'data'` list, add this
line immediately after `'security/ir.model.access.csv',`:

```python
        'data/appointment_source_data.xml',
```

- [ ] **Step 6: Run the test to verify it passes**

Run the **update** command. Expected: `custom_appointments: 1 tests`, no `FAIL:`/`ERROR:`.

- [ ] **Step 7: Commit**

```bash
git add addons/custom_appointments/data/appointment_source_data.xml \
        addons/custom_appointments/__manifest__.py \
        addons/custom_appointments/tests/test_appointment_source.py \
        addons/custom_appointments/tests/__init__.py
git commit -m "feat: seed appointment source records + test"
```

---

## Task 3: Add `source_id` to appointments, defaulting to Online

**Files:**
- Modify: `addons/custom_appointments/models/appointment.py`
- Modify: `addons/custom_appointments/tests/test_appointment_source.py`

- [ ] **Step 1: Write the failing tests**

In `addons/custom_appointments/tests/test_appointment_source.py`, add these
methods to the `TestAppointmentSource` class:

```python
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
        self._make_appointment(source_id=call_in.id)   # Call-in
        groups = self.env['custom.appointment'].read_group(
            [], fields=['source_id'], groupby=['source_id'])
        counts = {g['source_id'][1]: g['__count'] for g in groups if g['source_id']}
        self.assertEqual(counts.get('Online'), 1)
        self.assertEqual(counts.get('Call-in'), 1)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run the **update** command. Expected: FAIL — `source_id` is not a field on
`custom.appointment` yet (`Invalid field 'source_id'`).

- [ ] **Step 3: Add the field**

In `addons/custom_appointments/models/appointment.py`, add this field directly
after the `branch_id` field definition (around line 28):

```python
    source_id = fields.Many2one(
        'custom.appointment.source', string='Source',
        ondelete='restrict',
        default=lambda self: self.env.ref(
            'custom_appointments.appointment_source_online',
            raise_if_not_found=False))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run the **update** command. Expected: `custom_appointments: 4 tests`, no `FAIL:`/`ERROR:`.

- [ ] **Step 5: Commit**

```bash
git add addons/custom_appointments/models/appointment.py \
        addons/custom_appointments/tests/test_appointment_source.py
git commit -m "feat: add source_id to appointments, default Online"
```

---

## Task 4: Tag online bookings as Online in the controller

**Files:**
- Modify: `addons/custom_appointments/controllers/main.py`

- [ ] **Step 1: Set the source on the online booking vals**

In `addons/custom_appointments/controllers/main.py`, locate the
`appointment_vals = { ... }` dict in the booking submission handler (around line
331–356). Add this entry inside the dict, immediately after the
`'branch_id': staff.branch_id.id,` line:

```python
                'source_id': request.env.ref(
                    'custom_appointments.appointment_source_online').id,
```

This guarantees public bookings are always Online, independent of the model
default. (Behavior is already covered by `test_new_appointment_defaults_to_online`
since the controller value matches the default; this change makes the intent
explicit and future-proof.)

- [ ] **Step 2: Run the full suite to confirm nothing broke**

Run the **update** command. Expected: `custom_appointments: 4 tests`, no `FAIL:`/`ERROR:`.

- [ ] **Step 3: Commit**

```bash
git add addons/custom_appointments/controllers/main.py
git commit -m "feat: tag online bookings with Online source"
```

---

## Task 5: Backfill existing appointments via post_init_hook

**Files:**
- Modify: `addons/custom_appointments/__init__.py`
- Modify: `addons/custom_appointments/__manifest__.py`
- Modify: `addons/custom_appointments/tests/test_appointment_source.py`

- [ ] **Step 1: Write the failing test**

In `addons/custom_appointments/tests/test_appointment_source.py`, add this method
to the `TestAppointmentSource` class:

```python
    def test_backfill_sets_online_for_null_source(self):
        from odoo.addons.custom_appointments import _backfill_appointment_source
        online = self.env.ref('custom_appointments.appointment_source_online')
        appt = self._make_appointment()
        appt.source_id = False
        self.assertFalse(appt.source_id)
        _backfill_appointment_source(self.env)
        self.assertEqual(appt.source_id, online)
```

- [ ] **Step 2: Run the test to verify it fails**

Run the **update** command. Expected: FAIL — `ImportError` /
`cannot import name '_backfill_appointment_source'` because the function does not
exist yet.

- [ ] **Step 3: Define the backfill function**

In `addons/custom_appointments/__init__.py` (the module root file), add at the end:

```python


def _backfill_appointment_source(env):
    """Set existing appointments with no source to the seeded Online source."""
    online = env.ref(
        'custom_appointments.appointment_source_online',
        raise_if_not_found=False)
    if not online:
        return
    env['custom.appointment'].search(
        [('source_id', '=', False)]).write({'source_id': online.id})
```

- [ ] **Step 4: Register the hook in the manifest**

In `addons/custom_appointments/__manifest__.py`, add this top-level key (e.g.
right after the `'license': 'LGPL-3',` line, inside the dict):

```python
    'post_init_hook': '_backfill_appointment_source',
```

- [ ] **Step 5: Run the test to verify it passes**

Run the **update** command. Expected: `custom_appointments: 5 tests`, no `FAIL:`/`ERROR:`.

- [ ] **Step 6: Commit**

```bash
git add addons/custom_appointments/__init__.py \
        addons/custom_appointments/__manifest__.py \
        addons/custom_appointments/tests/test_appointment_source.py
git commit -m "feat: backfill existing appointments to Online source"
```

---

## Task 6: Views — Sources management menu + expose source on appointments

**Files:**
- Create: `addons/custom_appointments/views/appointment_source_views.xml`
- Modify: `addons/custom_appointments/__manifest__.py`
- Modify: `addons/custom_appointments/views/appointment_views.xml`

This task is view XML (no unit test). Verification is that the module updates
cleanly (views parse and load) and the existing test suite still passes.

- [ ] **Step 1: Create the Sources views + menu**

Create `addons/custom_appointments/views/appointment_source_views.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Source List View -->
    <record id="appointment_source_list_view" model="ir.ui.view">
        <field name="name">custom.appointment.source.list</field>
        <field name="model">custom.appointment.source</field>
        <field name="arch" type="xml">
            <list editable="bottom">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="active" widget="boolean_toggle"/>
            </list>
        </field>
    </record>

    <!-- Source Form View -->
    <record id="appointment_source_form_view" model="ir.ui.view">
        <field name="name">custom.appointment.source.form</field>
        <field name="model">custom.appointment.source</field>
        <field name="arch" type="xml">
            <form>
                <sheet>
                    <group>
                        <field name="name"/>
                        <field name="sequence"/>
                        <field name="active"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Source Action -->
    <record id="appointment_source_action" model="ir.actions.act_window">
        <field name="name">Appointment Sources</field>
        <field name="res_model">custom.appointment.source</field>
        <field name="view_mode">list,form</field>
        <field name="help" type="html">
            <p class="o_view_nocontent_smiling_face">
                Add your first appointment source!
            </p>
            <p>
                Sources describe how an appointment was booked (Online, Call-in, Walk-in, ...).
            </p>
        </field>
    </record>

    <!-- Sources Menu (under Configuration) -->
    <menuitem id="appointment_sources_menu"
              name="Sources"
              parent="menu_appointments_configuration"
              action="appointment_source_action"
              sequence="20"/>
</odoo>
```

- [ ] **Step 2: Register the view file in the manifest**

In `addons/custom_appointments/__manifest__.py`, in the `'data'` list, add this
line immediately after `'views/appointment_settings_views.xml',` (so the
`menu_appointments_configuration` parent menu is defined before this file
references it):

```python
        'views/appointment_source_views.xml',
```

- [ ] **Step 3: Add `source_id` to the appointment search view**

In `addons/custom_appointments/views/appointment_views.xml`, inside the
`<search>` of `appointment_search_view`:

(a) After `<field name="branch_id"/>` (around line 13), add:

```xml
                <field name="source_id"/>
```

(b) Inside the `<group ... string="Group By">`, after
`<filter string="Branch" name="group_by_branch" .../>` (around line 22), add:

```xml
                    <filter string="Source" name="group_by_source" context="{'group_by': 'source_id'}"/>
```

- [ ] **Step 4: Add `source_id` to the appointment list view**

In `appointment_list_view`, after `<field name="branch_id"/>` (around line 39), add:

```xml
                <field name="source_id" optional="show"/>
```

- [ ] **Step 5: Add `source_id` to the appointment form view**

In `appointment_form_view`, inside the `<group string="Appointment Details">`,
after `<field name="branch_id"/>` (around line 84), add:

```xml
                            <field name="source_id"/>
```

- [ ] **Step 6: Run the full suite to confirm views load and tests pass**

Run the **update** command. Expected: module updates without view-parse errors,
`custom_appointments: 5 tests`, no `FAIL:`/`ERROR:`.

- [ ] **Step 7: Commit**

```bash
git add addons/custom_appointments/views/appointment_source_views.xml \
        addons/custom_appointments/__manifest__.py \
        addons/custom_appointments/views/appointment_views.xml
git commit -m "feat: source management menu and source_id on appointment views"
```

---

## Final Verification

- [ ] **Run the full suite one last time** (update command). Confirm
  `custom_appointments: 5 tests` with no `FAIL:`/`ERROR:`.
- [ ] **Manual smoke (optional, local LashesByShazz DB):** update the module on
  the real local DB, open an appointment form → confirm the **Source** field
  shows **Online**; open **Appointments → Configuration → Sources** → confirm the
  three records; group the appointments list by **Source**; confirm existing
  appointments are bucketed under **Online** (backfill worked).
- [ ] **Clean install check:** install the module on a fresh DB to confirm the
  post_init_hook and seed data load cleanly from scratch.
```
