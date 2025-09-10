/** @odoo-module */

import paymentForm from "@payment/js/payment_form";

paymentForm.include({
  /**
   * Redirect the customer by submitting the redirect form included in the processing values.
   * @override method from payment.payment_form_mixin
   * @private
   * @param {string} providerCode - The code of the selected payment option's provider.
   * @param {number} paymentOptionId - The id of the selected payment option.
   * @param {string} paymentMethodCode - The code of the selected payment method, if any.
   * @param {object} processingValues - The processing values of the transaction.
   * @return {void}
   */
  _processRedirectFlow(
    providerCode,
    paymentOptionId,
    paymentMethodCode,
    processingValues
  ) {
    // Create and configure the form element with the content rendered by the server.

    const div = document.createElement("div");
    div.innerHTML = processingValues["redirect_form_html"];
    let redirectForm;


    console.log(processingValues)

    if (processingValues.provider_code !== "eagle") {
      return this._super.apply(this, arguments);
    }

    if (processingValues.provider_code === "custom") {
      redirectForm = document.getElementById("bank_payment_form");
      let orderReference = document.getElementsByName("reference")[0];
      orderReference.value = processingValues.reference;
    }

    else if (processingValues.provider_code === "eagle") {
      redirectForm = document.getElementById("o_payment_form");
      console.log(redirectForm, processingValues)
      redirectForm.setAttribute("action", "/payment/eagle/process");
      redirectForm.setAttribute("method", "POST");

      let input = document.createElement("input");
      input.type = "hidden";
      input.name = "reference";
      input.value = processingValues.reference;
      redirectForm.appendChild(input);

    }

    redirectForm.setAttribute("id", "o_payment_redirect_form");
    redirectForm.setAttribute("target", "_top"); // Ensures redirections when in an iframe.

    // Submit 
    document.body.appendChild(redirectForm);
    redirectForm.submit();
  },
});
