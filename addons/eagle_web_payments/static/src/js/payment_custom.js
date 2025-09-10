(function () {
    // some code here
  
    let currentUrl = window.location.href;
    console.log("Current URL: " + currentUrl);
  
  
    function getElementReference(id) {
      return document.getElementById(id);
    }
  
    function displayBlock(id) {
      if (document.getElementById(id)) {
        document.getElementById(id).style.display = "block";
      }
    }
  
  
    function displayNone(id) {
      if (document.getElementById(id)) {
        document.getElementById(id).style.display = "none";
      }
    }
  
    function getValue(id) {
      if (document.getElementById(id)) {
        return document.getElementById(id).value;
      } else {
        return false;
      }
    }
  
    function setValue(id, value) {
      if (document.getElementById(id)) {
        document.getElementById(id).textContent = value;
      }
    }
  
    const AIRTELREGEX = /^(070|075|074|020)/;
    const MTNREGEX = /^(077|078|076|039|031)/;
  
    const cleanNo = (_number) => {
      displayNone("invalidNum");
  
      let cleanedNumber = _number.replace(/\D/g, "");
      let formattedNumber;
      if (cleanedNumber.length === 9) {
        formattedNumber = "0" + cleanedNumber;
      } else {
        formattedNumber = cleanedNumber;
      }
      return formattedNumber;
    };
  
  
    const verifyNo = (_provider, _number) => {
      console.log(_number, _provider);
      let errorp =
        _provider === "eagle_mtn"
          ? "invalidMtnNum"
          : _provider === "eagle_airtel"
            ? "invalidAirtelNum"
            : "invalidMpesaNum";
  
  
      if (_number.length === 0) {
        displayBlock(errorp);
        setValue(errorp, "Phone Number Cannot be empty!");
        return false;
      }
  
  
  
      _number = cleanNo(_number);
      let regex =
        _provider === "eagle_mtn"
          ? MTNREGEX
          : _provider === "eagle_airtel"
            ? AIRTELREGEX
            : null;
      if (regex) {
        if (!regex.test(_number)) {
          displayBlock(errorp);
          setValue(errorp, `Invalid ${_provider.toUpperCase()} Phone Number!`);
          return false;
        }
      }
  
      if (_number.length !== 10) {
        displayBlock(errorp);
        setValue(errorp, "Invalid Phone Number!");
        return false;
      }
  
      displayNone(errorp);
  
      return true;
    };
  
    function setErrorInput(element) {
      if (getElementReference(element)) {
        getElementReference(element).style.border = "1px solid red";
      }
    }
    function setValidInput(element) {
      if (getElementReference(element)) {
        getElementReference(element).style.border = "1px solid #bec8d0";
      }
    }
  
  
    function getElementReferenceByName(_name) {
      return document.getElementsByName(_name)[0];
    }
    var paymentRadioButtons = document.querySelectorAll(
      'input[name="o_payment_radio"]'
    );
  
    console.log(paymentRadioButtons)
    const eagleBtn = getElementReference("o_eagle_submit_button");
    let paymentMethod;
    if (paymentRadioButtons) {
      paymentRadioButtons.forEach(function (radioButton) {
        radioButton.addEventListener("change", function (event) {
          if (this.checked) {
            console.log("checked")
            eagleBtn.classList.remove("disabled");

            displayNone("invalidMtnNum");
            displayNone("invalidAirtelNum");
            displayNone("invalidMpesaNum"); // Add this line - it was missing!

            let dataProviderCode = radioButton.getAttribute("data-provider-code");
            let dataPaymentMethodCode = radioButton.getAttribute(
              "data-payment-method-code"
            );
            paymentMethod = dataPaymentMethodCode;

            let _btn = getElementReferenceByName("o_payment_submit_button");

            //Replace Button from here incase of airtel & mtn
            console.log(dataProviderCode)
            if (dataProviderCode === "eagle") {
              if (_btn) {
                _btn.style.visibility = "hidden";
              }
              displayNone("odoo_payment_btn");
              displayBlock("o_eagle_submit_button");
            } else {
              displayNone("o_eagle_submit_button");
              displayBlock("odoo_payment_btn")
              console.log("reaches here", getElementReference("odoo_payment_btn"))
              getElementReference("odoo_payment_btn").style.visibility = "visible";
            }
          } else {



  
            console.log("*********",eagleBtn,_btn)
            if (eagleBtn) {
              eagleBtn.classList.remove("disabled");
  
            }
            if (_btn) {
              _btn.style.visibility = "visible";
              displayNone("o_eagle_submit_button");
            }
            return;
          }
        });
      });
    }
  
  
  
  
  
  
    if (eagleBtn) {
      eagleBtn.addEventListener("click", async function (event) {
        //check total
  
        let _phoneNo =
          paymentMethod === "eagle_mtn"
            ? getValue("mtn_phone")
            : paymentMethod === "eagle_airtel"
              ? getValue("airtel_phone")
              : getValue("mpesa_phone");
  
        let _result = verifyNo(paymentMethod, _phoneNo);
  
        if (_result) {
          // let _submitForm = getElementReference('')
          displayBlock("o_eagle_submit_button");
          let _submitBtn = getElementReferenceByName("o_payment_submit_button");
          if (_submitBtn) {
            displayNone("o_eagle_submit_button");
            displayBlock("o_eagle_submit_loader");
  
            console.log("on submiting")
            _submitBtn.click();
          }
        }
      });
    }
  
  })();