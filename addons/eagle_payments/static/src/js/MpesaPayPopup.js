/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

export class MpesaPayPopup extends Component {
  static template = "eagle_payments.MpesaPayPopup";
  static components = { Dialog };
  static props = {
    info: { type: Number },
    keepBehind: { type: Boolean, optional: true },
    isTillPayment: { type: Boolean, optional: true },
    getPayload: Function,
    close: Function,
  };

  // NB: payment_status --> 0: failed and  1: success

  setup() {
    console.log("MpesaPayPopup setup called with props:", this.props);
    this.pos = usePos();
    this.dialog = useService("dialog");
    this.orm = useService("orm");
    this.state = useState({
      totalAmount: this.props.info,
    });
    console.log("MpesaPayPopup setup completed");
  }

  //=========================Make payment Function===================
  async makePayment() {
    console.log("makePayment called");
    console.log("pos:", this.pos);
    console.log("pos.get_order():", this.pos.get_order());
    console.log("pos.get_order().cashier:", this.pos.get_order()?.cashier);
    console.log("pos.config:", this.pos.config);

    let phone = document.getElementById("phone").value;
    let amount = document.getElementById("amount").value;
    if (!phone || !amount) {
      return (document.getElementById("success_message").innerHTML =
        "<div style='background-color: #ffd0d0;color: red; padding: 20px;margin-top: 10px;'> Please Fill in all required fields! </div> ");
    }

    // Safely get cashier and config IDs
    const order = this.pos.get_order();
    const cashierId = order?.cashier?.id || null;
    const configId = this.pos.config?.id || null;

    console.log("cashierId:", cashierId);
    console.log("configId:", configId);
    this.orm.call("mpesa.transaction", "action_make_payment", [phone, parseFloat(amount), cashierId, configId], {}).then(async function (result) {
      if (result.transaction_id) {
        //save txn-id to local storage
        localStorage.setItem("transaction_id", result.transaction_id);
        document.getElementById("success_message").innerHTML =
          "<div style='background-color: #aafaaa;color: green; padding: 20px;margin-top: 10px;'> Please Enter the PIN on your phone to Proceed </div> ";

        document.getElementById("makePay").style.display = "none";
        // document.getElementById("validatePay").style.display = "block";
        document.getElementById("createOrder").style.display = "block";
      } else {
        return (document.getElementById("success_message").innerHTML =
          "<div style='background-color: #ffd0d0;color: red; padding: 20px;margin-top: 10px;'> Something Went Wrong, Try Again! </div> ");
      }
    });
  }
  //=========================Make payment Function End===================

  async validatePayment() {
    var successDiv = document.getElementById("success_message");
    let transaction_id = localStorage.getItem("transaction_id");
    const result = await this.orm.call("mpesa.transaction", "action_validate_payment", [transaction_id], {});

    if (result.status == "TIP") {
      successDiv.innerHTML =
        "<div style='background-color:#fffec5;color: #b39100; font-weight:800; padding: 20px;margin-top: 10px;'> STATUS: Transaction In Progress(TIP)</div> ";
      successDiv.style.display = "block";
    } else if (result.status == "TS") {
      localStorage.setItem("payment_status", "1");
      const payload = { payment: true, status: "success", type: "stk" };
      this.props.getPayload(payload);
      this.props.close({ confirmed: true, payload });
    } else {
      successDiv.innerHTML =
        "<div style='background-color:#fffec5;color: red; font-weight:800; padding: 20px;margin-top: 10px;'> STATUS: Transaction Failed(TF)</div> ";
      successDiv.style.display = "block";
    }
  }

  async validateTillPayment() {
    var successDiv = document.getElementById("success_message");
    const result = await this.orm.call("mpesa.transaction", "action_validate_till_payment", [this.state.totalAmount], {});

    if (result.status == "TIP") {
      successDiv.innerHTML =
        "<div style='background-color:#fffec5;color: #b39100; font-weight:800; padding: 20px;margin-top: 10px;'> STATUS: Transaction In Progress(TIP)</div> ";
      successDiv.style.display = "block";
    } else if (result.status == "TS") {
      localStorage.setItem("payment_status", "1");
      const payload = { payment: true, status: "success", type: "till" };
      this.props.getPayload(payload);
      this.props.close({ confirmed: true, payload });
    } else {
      successDiv.innerHTML =
        "<div style='background-color:#fffec5;color: red; font-weight:800; padding: 20px;margin-top: 10px;'> STATUS: Transaction Failed(TF)</div> ";
      successDiv.style.display = "block";
    }
  }

  async createOrder() {
    console.log("Creating An Order***************************************");
    localStorage.setItem("payment_status", "0");
    this.pos.get_order().partner;

    // Pass payload using getPayload like CreditNoteReasonPopUp does
    const payload = { payment: false, status: "created" };
    this.props.getPayload(payload);
    this.props.close({ confirmed: true, payload });
  }
  //@override
  async cancel() {
    if (this.canCancel() && localStorage.getItem("transaction_id")) {
      const confirmed = await ask(this.dialog, {
        title: _t("Confirm to Proceed"),
        body: _t("The Transaction Will be Marked as Failed?"),
      });

      if (confirmed) {
        this.props.close({ confirmed: false, payload: null });
      }
    } else {
      this.props.close({ confirmed: false, payload: null });
    }
  }

  canCancel() {
    return true;
  }
  closePos() {
    this.props.close();
  }
}
