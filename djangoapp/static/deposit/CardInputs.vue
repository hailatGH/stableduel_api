<template>
  <form action="post" @submit.prevent="submitCard">
    <div class="card-fields">
      <p class="card-field-label"> Credit or debit card </p>
      <div class="card-fields-wrapper" ref="cardFields">
        <CardInput wide :error="errors.get('cardInput')">
          <div id="cardInput"></div>
        </CardInput>
        <CardInput :error="errors.get('expiryInput')">
          <div class="input" id="expiryInput"></div>
        </CardInput>
        <CardInput :error="errors.get('cvcInput')">
          <div class="input" id="cvcInput"></div>
        </CardInput>
        <button type="submit" class="submit-button" :disabled="!isFormComplete || loading">
          <Spinner v-if="loading" />
          <span v-else>Submit</span>
        </button>
      </div>
      <Transition name="fade">
        <div class="scard-message" v-if="sfc_response !== null"
          :class="{ error: sfc_response.result !== 'APPROVED', success: sfc_response.result === 'APPROVED' }">
          <p>{{ sfc_response.description }}</p>
        </div>
      </Transition>
    </div>
  </form>
</template>

<script setup type="module">
  import { onMounted, ref, unref, shallowRef, computed } from 'vue'
  import { parseDataFromElement } from './utils.mjs';
  import CardInput from './CardInput.vue';
  import Spinner from './Spinner.vue';

  const cardFields = ref(null);
  const nuvei_data = ref(null);
  const user_data = ref(null);
  const errors = ref(new Map())
  const sfc = shallowRef(null)
  const scard = shallowRef(null)
  const sfc_response = ref(null)
  const fieldStates = ref(new Map())
  const loading = ref(false)

  const isFormComplete = computed(() => {
    if (fieldStates.value.size === 0) {
      // No events have been fired, assume incomplete
      return false
    }

    if (Array.from(fieldStates.value.values()).every(field => field.complete)) {
      // All fields are complete
      return true
    }
  })


  function handleFieldChange(fieldName) {
    return function (event) {
      if (sfc_response.value !== null) {
        sfc_response.value = null
      }
      fieldStates.value.set(fieldName, { complete: event.complete })
      if (event.complete) {
        errors.value.delete(fieldName)
      } else if (event.error) {
        const message = event.error.message.replaceAll("_", " ");
        const { id } = event.error;
        errors.value.set(fieldName, { id, message })
      }
    }
  }

  function submitCard() {
    const { sessionToken, transactionId: clientUniqueId } = unref(nuvei_data)
    const { fullName, email, country } = unref(user_data)
    loading.value = true
    sfc.value.createPayment({
      sessionToken,
      clientUniqueId,
      paymentOption: scard.value,
      cardHolderName: fullName,
      billingAddress: {
        email,
        country: country.slice(0, 2)
      }
    }, function (res) {
      console.dir(res)
      const { result, errorDescription } = res
      const description = errorDescription != undefined ? errorDescription.replaceAll("_", " ") : result === "APPROVED" ? "Deposit Complete!" : "Oops! Unknown error"
      sfc_response.value = { result, description }
      loading.value = false
    })
  }

  const styles = {
    base: {
      fontWeight: '500', // --fw-500
      fontSize: '2.5rem', // --fs-500
      backgroundColor: "#192136",
      color: '#E3F0FF',
      '::placeholder': {
        color: '#95AAC1'
      }
    },
    valid: {
      color: "#1ebb57" // --primary
    }
  };

  onMounted(() => {
    // Parse data from html injected by django templating
    nuvei_data.value = parseDataFromElement('nuvei_data')
    amount.value = parseDataFromElement('amount')
    user_data.value = parseDataFromElement('user_data')
    if (SafeCharge !== undefined && cardFields.value !== null) {
      const { merchantId, siteId: merchantSiteId } = unref(nuvei_data)
      sfc.value = SafeCharge({
        env: 'int',
        merchantId,
        merchantSiteId
      })
      const ScFields = sfc.value.fields({});
      scard.value = ScFields.create('ccNumber', {
        style: styles,
      })
      scard.value.attach(cardFields.value.querySelector("#cardInput"))
      scard.value.on("change", handleFieldChange("cardInput"))
      const expiryInput = ScFields.create('ccExpiration', {
        style: styles,
      })
      expiryInput.attach(cardFields.value.querySelector("#expiryInput"))
      expiryInput.on("change", handleFieldChange("expiryInput"))

      const cvcInput = ScFields.create('ccCvc', {
        style: styles,
      })
      cvcInput.attach(cardFields.value.querySelector("#cvcInput"))
      cvcInput.on("change", handleFieldChange("cvcInput"))

    }
  })
</script>
<style scoped>
  .card-fields {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    align-items: start;
  }

  .card-fields-wrapper {
    width: 100%;
    display: grid;
    gap: 2rem;
    grid-template-columns: 1fr 1fr;
  }

  .card-field-label {
    font-size: var(--fs-600);
    font-weight: var(--fw-600);
  }

  .submit-button {
    grid-column: span 2;
    border-radius: calc(var(--input-height) / 2);
    height: var(--input-height);
    padding: calc(var(--input-padding) / 2) var(--input-padding);
    background-color: #16AE4C;
    color: #000;
    font-size: var(--fs-500);
    font-weight: var(--fw-500);
  }

  .submit-button:disabled {
    background-color: hsl(144, 25%, 71%);
    color: slategray;
  }

  .scard-message {
    border-radius: 1rem;
    min-height: 2rem;
    padding: 4px 1rem;
    width: 100%;
  }

  .scard-message>p {
    margin: 0;
  }

  .scard-message.success {
    color: hsl(118, 80%, 40%);
    border: 1px solid hsl(118, 50%, 35%);
  }

  .scard-message.error {
    color: hsl(0, 80%, 40%);
    border: 1px solid hsl(0, 50%, 35%);
  }
</style>