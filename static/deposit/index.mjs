import {
  createApp,
  ref,
} from "https://unpkg.com/vue@3/dist/vue.esm-browser.js";
const html = String.raw;
createApp({
  setup() {
    const cardFields = ref(null);
    const amount = ref(null);
    const nuvei_data = ref(null);
    const user_data = ref(null);
    /**
     * @description Parse data from text content of element with id `element_id`
     * @param {string} element_id
     * @returns {string | null}
     */
    function parseDataFromElement(element_id) {
      const element = document.querySelector(`#${element_id}`);
      if (element !== null) {
        const content = element.textContent;
        const data = JSON.parse(content.replaceAll("'", '"'));
        return data;
      }
      return null;
    }
    return {
      cardFields,
      amount,
      nuvei_data,
      user_data,
      parseDataFromElement,
    };
  },
  mounted() {
    this.nuvei_data = this.parseDataFromElement("nuvei_data");
    this.amount = this.parseDataFromElement("amount");
    this.user_data = this.parseDataFromElement("user_data");

    if (SafeCharge !== undefined && this.cardFields !== null) {
      const sfc = SafeCharge({
        env: "int", // Nuvei API environment - 'int' (integration) or 'prod' (production - default if omitted)
        merchantId: this.nuvei_data.merchantId, // your Merchant ID provided by Nuvei
        merchantSiteId: this.nuvei_data.siteId, // your Merchant site ID provided by Nuvei
      });

      //Instantiate Nuvei Fields
      const ScFields = sfc.fields({
        fonts: [
          { cssUrl: "https://fonts.googleapis.com/css?family=Roboto" }, // include your custom fonts
        ],
      });

      // set state field style/ check Nuvei Fields for details.
      const style = {
        /* state styles */
      };

      // Instantiate Nuvei Fields
      const scard = ScFields.create("card", { style: style });

      // attach the Nuvei fields to the vue placeholder
      scard.attach(this.cardFields);

      // document
      //   .querySelector("#submit-payout-button")
      //   .addEventListener("click", (event) => {
      //     event.preventDefault();
      //     sfc.createPayment(
      //       {
      //         sessionToken: "{{ sessionToken|escapejs }}",
      //         clientUniqueId: "{{ transactionId|escapejs }}",
      //         paymentOption: scard,
      //         billingAddress: {
      //           email: "{{ email|first|escapejs }}",
      //           country: "{{ country|escapejs }}".slice(0, 2),
      //         },
      //       },
      //       function (res) {
      //         console.log(res);
      //       }
      //     );
      //   });
    }
  },
  template: html`
    <form action="/charge" method="post" id="payment-form">
      <div>
        <label for="amount">Deposit Amount</label>
        <input type="number" disabled name="amount" :value="amount" />
        <label for="card-field-placeholder"> Credit or debit card </label>
        <div
          id="card-field-placeholder"
          class="some initial css-classes"
          ref="cardFields"
        ></div>
        <div id="scard-errors" role="alert"></div>
      </div>
    </form>
    <button id="submit-payout-button">Submit Payment</button>
  `,
}).mount("#deposit-app");
