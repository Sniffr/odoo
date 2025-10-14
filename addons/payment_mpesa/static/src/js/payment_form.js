odoo.define('payment_mpesa.payment_form', function (require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var ajax = require('web.ajax');

    var _t = core._t;

    publicWidget.registry.MpesaPaymentForm = publicWidget.Widget.extend({
        selector: '.mpesa_payment_container',
        events: {
            'click #mpesa_pay_button': '_onClickPay',
        },

        _onClickPay: function (ev) {
            ev.preventDefault();
            var $button = $(ev.currentTarget);
            var phoneNumber = $('#mpesa_phone').val().trim();
            var txId = parseInt($button.data('tx-id'));

            if (!phoneNumber) {
                this._showMessage('error', _t('Please enter your phone number'));
                return;
            }

            $button.prop('disabled', true);
            $('#mpesa_loading').show();
            this._hideMessage();

            ajax.jsonRpc('/payment/mpesa/initiate', 'call', {
                tx_id: txId,
                phone_number: phoneNumber,
            }).then(function (data) {
                if (data.success) {
                    this._showMessage('success', data.message || _t('Payment initiated successfully'));
                    setTimeout(function () {
                        window.location.reload();
                    }, 3000);
                } else {
                    this._showMessage('error', data.error || _t('Payment failed'));
                    $button.prop('disabled', false);
                    $('#mpesa_loading').hide();
                }
            }.bind(this)).guardedCatch(function (error) {
                this._showMessage('error', _t('An error occurred. Please try again.'));
                $button.prop('disabled', false);
                $('#mpesa_loading').hide();
            }.bind(this));
        },

        _showMessage: function (type, message) {
            var $msg = $('#mpesa_message');
            $msg.removeClass('alert-success alert-danger alert-info');
            $msg.addClass(type === 'success' ? 'alert-success' : 'alert-danger');
            $msg.text(message);
            $msg.show();
        },

        _hideMessage: function () {
            $('#mpesa_message').hide();
        },
    });

    return publicWidget.registry.MpesaPaymentForm;
});
