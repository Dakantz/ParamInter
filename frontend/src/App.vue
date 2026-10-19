<template>
  <main>
    <RouterView />
    <footer class="disclaimer">
      Research use only. Not a medical device.
      <a href="https://github.com/Dakantz/ParamInter/blob/main/DISCLAIMER.md" target="_blank" rel="noopener">Disclaimer</a>
    </footer>
  </main>
</template>

<script setup lang="ts">

</script>
<style>
.disclaimer {
  color: rgb(137, 137, 137);
  font-size: 0.7rem;
  margin: 10px 20px;
}

.disclaimer a {
  color: inherit;
}
</style>
