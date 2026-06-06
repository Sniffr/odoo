import logging

from . import models
from . import controllers
from . import wizard

_logger = logging.getLogger(__name__)


def _backfill_appointment_source(env):
    """Set existing appointments with no source to the seeded Online source."""
    online = env.ref(
        'custom_appointments.appointment_source_online',
        raise_if_not_found=False)
    if not online:
        return
    appointments = env['custom.appointment'].search([('source_id', '=', False)])
    if appointments:
        appointments.write({'source_id': online.id})
        _logger.info(
            '_backfill_appointment_source: set Online source on %d appointment(s)',
            len(appointments))
