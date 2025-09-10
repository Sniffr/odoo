/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { MpesaPayPopup } from "@eagle_payments/js/MpesaPayPopup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { makeAwaitable } from "@point_of_sale/app/store/make_awaitable_dialog";

patch(PaymentScreen.prototype, {
  //@Override
  setup() {
    super.setup();
    this.pos = usePos();
    this.orm = useService("orm");
    this.dialog = useService("dialog");
    this.busService = this.env.services.bus_service;
    this.channel = "mpesa_payment_channel";
    this.busService.addChannel(this.channel);
    this.busService.subscribe(this.channel, this.onMessage.bind(this));
    console.log("payment screen oveeridden");
    console.log(this.pos.get_order());
  },

  callValidatePaymentOnPopUp() {
    //select button with id validatePayment
    let validateButton = document.getElementById("validate_payment");
    if (validateButton) validateButton.click();
  },

  callValidateTillPaymentOnPopUp() {
    //select button with id validatePayment
    let validateButton = document.getElementById("validate_till_payment");
    if (validateButton) validateButton.click();
  },

  async validateMpesaPayment(item) {
    try {
      let txn_id = item.data.transaction_id;
      const res = await this.orm.call("mpesa.transaction", "action_validate_payment", [txn_id], {});
      console.log("response of payment validation by js Bus");
      console.log(res);
      this.callValidatePaymentOnPopUp();
    } catch (e) {
      console.log("*********error***************");
      console.error(e);
    }
  },

  async validateMpesaTillPayment(item) {
    try {
      let amount = item.data.amount;
      const res = await this.orm.call("mpesa.transaction", "action_validate_till_payment", [amount], {});

      console.log("response of till payment validation by js Bus");
      console.log(res);

      this.callValidateTillPaymentOnPopUp();
    } catch (e) {
      console.log("*********error***************");
      console.error(e);
    }
  },

  async onMessage(payload) {
    console.log("Mpesa Payment Response received in js....");
    console.log(payload.data);

    if (payload.data.type === "till" || payload.data.type === "bill") {
      await this.validateMpesaTillPayment(payload);
    } else {
      await this.validateMpesaPayment(payload);
    }
  },


  async createTemporaryOrder(paymentRef) {
    const res = await this.orm.call("pesapal.transaction", "createTemporaryOrder", [this.pos.get_order().cashier.id, paymentRef], {});
    console.log("createTemporaryOrder response is");
    console.log(res);
  },

  //@override
  async validateOrder(isForceValidate) {
    // Console log payment methods to see available attributes
    this.pos.get_order().payment_ids.forEach((paymentLine, index) => {
      console.log(`Payment Line ${index}:`, paymentLine);
      console.log(`Payment Line keys ${index}:`, Object.keys(paymentLine));

      if (paymentLine.payment_method) {
        console.log(`Payment Method ${index}:`, paymentLine.payment_method);
        console.log(`Payment Method attributes ${index}:`, Object.keys(paymentLine.payment_method));
      } else {
        console.log(`Payment Method ${index}: undefined`);
        // Check if payment method is stored elsewhere
        console.log(`Looking for payment method in other properties...`);
        if (paymentLine.payment_method_id) {
          console.log(`payment_method_id found:`, paymentLine.payment_method_id);
          console.log(`payment_method_id type:`, typeof paymentLine.payment_method_id);
          console.log(`payment_method_id keys:`, Object.keys(paymentLine.payment_method_id));

          // The payment_method_id is actually the payment method object itself
          const paymentMethod = paymentLine.payment_method_id;
          if (paymentMethod) {
            console.log(`Payment Method object from ID:`, paymentMethod);
            console.log(`Payment Method attributes from ID:`, Object.keys(paymentMethod));
          }
        }
      }
    });

    let mpesaPay = this.pos.get_order().payment_ids.some((paymentLine) => {
      // First try direct payment_method object
      if (paymentLine.payment_method?.is_Mpesa) {
        return true;
      }
      // The payment_method_id is actually the payment method object itself
      if (paymentLine.payment_method_id?.is_Mpesa) {
        return true;
      }
      return false;
    });

    let isTillPayment = this.pos.get_order().payment_ids.some((paymentLine) => {
      // First try direct payment_method object
      if (paymentLine.payment_method?.isTillPayment) {
        return true;
      }
      // The payment_method_id is actually the payment method object itself
      if (paymentLine.payment_method_id?.isTillPayment) {
        return true;
      }
      return false;
    });

    let totalAmount = this.paymentLines.reduce((sum, line) => sum + line.amount, 0);

    console.log("mpesaPay:", mpesaPay);
    console.log("isTillPayment:", isTillPayment);
    console.log("totalAmount:", totalAmount);

    if (mpesaPay || isTillPayment) {
      console.log("M-PESA or Till payment detected, checking order validity...");
      if (await this._isOrderValid(isForceValidate)) {
        console.log("Order is valid, opening MpesaPayPopup...");
        localStorage.removeItem("transaction_id");

        try {
          console.log("About to call makeAwaitable with:", {
            dialog: this.dialog,
            component: MpesaPayPopup,
            props: {
              info: totalAmount,
              keepBehind: true,
              isTillPayment: isTillPayment,
            },
          });

          const response = await makeAwaitable(this.dialog, MpesaPayPopup, {
            info: totalAmount,
            keepBehind: true,
            isTillPayment: isTillPayment,
          });
          console.log("Popup response:", response);
        } catch (error) {
          console.error("Error opening popup:", error);
          console.error("Error stack:", error.stack);
        }

        let userAction = localStorage.getItem("payment_status");
        console.log("User action from localStorage:", userAction);
        if (userAction === "0" || userAction === "1") {
          await super.validateOrder(...arguments);
          localStorage.removeItem("payment_status");
          localStorage.removeItem("transaction_id");
        }
      } else {
        console.log("Order is not valid, skipping popup");
      }
    } else {
      console.log("No M-PESA or Till payment detected, using standard validation");
      await super.validateOrder(...arguments);
    }
  },
});
