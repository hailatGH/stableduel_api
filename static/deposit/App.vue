<template>
  <div class="deposit">
    <h1>Complete your deposit order</h1>
    <!-- <div class="form-group amount">
      <label for="amount">Deposit Amount</label>
      <input type="number" :value="amount" disabled>
    </div> -->
    <div class="amount-wrapper">
      <h2>Deposit Amount</h2>
      <p class="amount">{{ amountText }}</p>
    </div>

    <hr>
    <CardInputs />
  </div>
</template>

<script setup>
  import { onMounted, ref, computed } from 'vue'
  import { parseDataFromElement } from './utils.mjs';

  import CardInputs from './CardInputs.vue';
  const amount = ref(null);
  onMounted(() => {
    amount.value = parseDataFromElement('amount')
  })

  const amountText = computed(() => {
    const amountValue = amount.value !== null ? amount.value : 0
    const formatter = new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' })
    return formatter.format(amountValue)
  })

</script>

<style scoped>
  h1 {
    font-size: var(--fs-xl);
    font-weight: var(--fw-xl);
  }

  h2 {
    font-weight: var(--fw-600);
    font-size: var(--fs-600);
  }

  hr {
    border: none;
    height: 4px;
    color: #eee;
    background-color: #eee;
    margin-block: 1rem;
  }

  .deposit {
    width: 100%;
    max-width: 90vw;

    @media (min-width: 1024px) {
      max-width: 1024px;
    }

    margin: 2rem auto 1rem;
  }


  .amount-wrapper {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: start;
    gap: 1rem;
    margin-block: 1rem;
  }

  .amount-wrapper>h2,
  .amount-wrapper>p {
    margin: 0;
  }

  .amount {
    color: var(--primary);
    font-weight: var(--fw-600);
    font-size: var(--fs-xl);
  }
</style>