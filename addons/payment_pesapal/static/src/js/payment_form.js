/** @odoo-module **/

import paymentForm from '@payment/js/payment_form';

paymentForm.include({
    /**
     * Prepare PesaPal-specific payment values
     */
    _prepareInlineForm(provider, paymentOptionId, flow) {
        if (provider !== 'pesapal') {
            return this._super(...arguments);
        }
        return {};
    },
});
