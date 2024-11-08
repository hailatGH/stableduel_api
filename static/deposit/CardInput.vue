<template>
  <div class="input-wrapper" :class="{ 'input-wide': wide }">
    <div class="input">
      <slot />
    </div>
    <Transition name="fade">
      <div class="input-error" v-if="error !== undefined">
        <p>{{ error.message }}</p>
      </div>
    </Transition>
  </div>
</template>
<script setup>
  const props = defineProps({
    error: Object,
    wide: {
      type: Boolean,
      default: false
    },

  })
</script>

<style scoped>
  .input-wrapper {
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    align-items: stretch;
    gap: 1rem;
  }

  .input {
    min-width: 90px;
    background-color: #192136;
    border-radius: calc(var(--input-height) / 2);
    height: var(--input-height);
    padding: calc(var(--input-padding) / 2) var(--input-padding);
  }

  .input-wide {
    grid-column: span 2;
  }

  .input>div {
    width: 100%;
  }

  .input-error>p {
    padding-left: 1rem;
    margin: 0;
    color: hsl(0, 80%, 40%);
    text-transform: capitalize;
    font-size: var(--fs-400);
    font-weight: var(--fw-400);
  }
</style>