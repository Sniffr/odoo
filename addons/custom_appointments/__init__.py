from . import models
from . import controllers
from . import wizard


def _backfill_appointment_source(env):
    """Set existing appointments with no source to the seeded Online source."""
    online = env.ref(
        'custom_appointments.appointment_source_online',
        raise_if_not_found=False)
    if not online:
        return
    env['custom.appointment'].search(
        [('source_id', '=', False)]).write({'source_id': online.id})
