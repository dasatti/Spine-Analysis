<script setup>
</script>

<template>
  <router-view />
</template>

<style>
:root {
  --bg-base: #0a0a0a;
  --text-primary: #ffffff;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'Inter', sans-serif;
  background: var(--bg-base);
  color: var(--text-primary);
  min-height: 100vh;
}
</style>
