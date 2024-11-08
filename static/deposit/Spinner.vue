<template>
  <div class="lds-dual-ring"></div>
</template>
<style scoped>
  .lds-dual-ring {
    display: inline-block;
    width: 1rem;
    height: 1rem;
  }

  .lds-dual-ring:after {
    content: " ";
    display: block;
    width: 12.8px;
    height: 12.8px;
    margin: auto;
    border-radius: 50%;
    border: 2px solid #16AE4C;
    border-color: #16AE4C transparent #16AE4C transparent;
    animation: lds-dual-ring 1.2s linear infinite;
  }

  @keyframes lds-dual-ring {
    0% {
      transform: rotate(0deg);
    }

    100% {
      transform: rotate(360deg);
    }
  }
</style>