<template>
  <q-card class="connection-card q-pa-md" flat role="status" aria-live="polite">
    <q-card-section class="row items-center no-wrap q-pa-sm">
      <q-spinner class="connection-spinner" size="2em" />
      <span class="q-ml-md text-weight-medium">{{ $t('MSG_CONNECTING_TO_BACKEND') }}</span>
    </q-card-section>

    <q-card-actions align="right">
      <q-btn v-close-popup class="connection-reload" :label="$t('BTN_LABEL_RELOAD_PAGE')" unelevated @click="reloadPage" />
    </q-card-actions>
  </q-card>
</template>

<script setup lang="ts">
const reloadPage = () => {
  window.location.reload()
}
</script>

<style scoped>
.connection-card {
  max-width: min(34rem, calc(100vw - 2rem));
  border-radius: var(--kiosk-panel-radius);
  color: var(--kiosk-ink);
  background: var(--kiosk-paper);
  box-shadow: var(--kiosk-panel-shadow);
}

.connection-spinner {
  color: var(--kiosk-danger);
}

.connection-reload {
  min-height: 56px;
  color: var(--kiosk-ink);
  background: var(--kiosk-butter);
}
</style>
