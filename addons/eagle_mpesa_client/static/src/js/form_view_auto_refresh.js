odoo.define('eagle_payroll_client.FormViewAutoRefresh', function (require) {
    "use strict";

    const FormController = require('web.FormController');
    const core = require('web.core');

    const FormControllerAutoRefresh = FormController.extend({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);

            const recordId = params.model.get(this.handle).res_id;
            this.channel = `form_view_refresh_${recordId}`;

            // Subscribe to bus notifications
            core.bus.on(this.channel, this, this._onNotificationReceived);
        },

        _onNotificationReceived: function (message) {
            if (message.type === 'refresh') {
                this.reload();  // Reload the form view to reflect changes
            }
        },

        destroy: function () {
            core.bus.off(this.channel, this, this._onNotificationReceived);
            this._super.apply(this, arguments);
        },
    });

    return FormControllerAutoRefresh;
});
