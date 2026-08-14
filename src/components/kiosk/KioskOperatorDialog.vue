<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { Check, LoaderCircle, Settings, ShieldAlert, X } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { useMainStore, type KioskState } from '@/stores/main-store'
import { authStateChange } from '@/util/auth.js'
import { _fetch } from '@/util/fetch_api.js'

const props = defineProps<{ open: boolean; state: KioskState | null }>()
const emit = defineEmits<{ 'update:open': [value: boolean]; testStarted: [] }>()
const { t } = useI18n()
const router = useRouter()
const mainStore = useMainStore()
const password = shallowRef('')
const busy = shallowRef(false)
const error = shallowRef<string | null>(null)

const checks = computed(() => props.state?.readiness ?? null)

watch(
  () => props.open,
  open => {
    if (!open) {
      password.value = ''
      error.value = null
    }
  }
)

async function adminToken() {
  const body = new FormData()
  body.append('username', 'admin')
  body.append('password', password.value)
  const response = await fetch('/api/admin/auth/token', { method: 'POST', body })
  if (!response.ok) throw new Error(response.status === 429 ? t('kiosk.operator.locked') : t('kiosk.operator.badPassword'))
  return response.json() as Promise<{ access_token: string; token_type: string }>
}

async function startTest() {
  if (busy.value) return
  busy.value = true
  error.value = null
  try {
    const token = await adminToken()
    const response = await fetch('/api/admin/kiosk/test-grant', { method: 'POST', headers: { Authorization: `Bearer ${token.access_token}` } })
    if (!response.ok) throw new Error(t('kiosk.operator.startFailed'))
    mainStore.kioskTestGrant = (await response.json()).grant
    emit('testStarted')
    emit('update:open', false)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : t('kiosk.operator.startFailed')
  } finally {
    busy.value = false
  }
}

async function voidSession() {
  if (busy.value) return
  busy.value = true
  error.value = null
  try {
    const token = await adminToken()
    const response = await fetch('/api/admin/kiosk/session/void', { method: 'POST', headers: { Authorization: `Bearer ${token.access_token}` } })
    if (!response.ok) throw new Error(t('kiosk.operator.voidFailed'))
    mainStore.kioskTestGrant = null
    emit('update:open', false)
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : t('kiosk.operator.voidFailed')
  } finally {
    busy.value = false
  }
}

async function openAdmin() {
  if (busy.value) return
  busy.value = true
  error.value = null
  try {
    const token = await adminToken()
    authStateChange(token)
    emit('update:open', false)
    await router.push('/admin')
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : t('kiosk.operator.badPassword')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="tw:max-w-2xl" :show-close-button="!busy">
      <DialogHeader>
        <DialogTitle class="tw:text-4xl tw:tracking-[-0.03em]">{{ t('kiosk.operator.title') }}</DialogTitle>
        <DialogDescription class="tw:text-base">{{ t('kiosk.operator.description') }}</DialogDescription>
      </DialogHeader>

      <div class="tw:grid tw:grid-cols-2 tw:gap-3">
        <div
          v-for="key in ['camera', 'printer', 'disk', 'cloud', 'payment_hardware', 'password_changed'] as const"
          :key="key"
          class="tw:flex tw:min-h-12 tw:items-center tw:gap-3"
        >
          <Check v-if="checks?.[key]" class="tw:size-5" aria-hidden="true" />
          <X v-else class="tw:size-5" aria-hidden="true" />
          <span>{{ t(`kiosk.operator.checks.${key}`) }}: {{ t(`kiosk.operator.status.${checks?.[key] ? 'ready' : 'notReady'}`) }}</span>
        </div>
      </div>

      <label class="tw:mt-3 tw:flex tw:flex-col tw:gap-2 tw:text-base tw:font-medium">
        {{ t('kiosk.operator.password') }}
        <input
          v-model="password"
          type="password"
          autocomplete="current-password"
          class="tw:min-h-14 tw:rounded-xl tw:border tw:border-input tw:bg-background tw:px-4 tw:text-lg tw:outline-none focus:tw:ring-2 focus:tw:ring-ring"
          @keydown.enter="startTest"
        />
      </label>
      <p class="tw:flex tw:items-center tw:gap-2 tw:text-sm tw:text-muted-foreground"
        ><ShieldAlert class="tw:size-5" aria-hidden="true" />{{ t('kiosk.operator.defaultWarning') }}</p
      >
      <p v-if="error" class="tw:text-destructive" role="alert">{{ error }}</p>

      <DialogFooter class="tw:flex-wrap tw:gap-3 tw:sm:justify-stretch">
        <Button size="lg" class="tw:min-h-14 tw:flex-1" :disabled="busy || !password" @click="startTest">
          <LoaderCircle v-if="busy" data-icon="inline-start" class="tw:animate-spin" aria-hidden="true" />
          <Settings v-else data-icon="inline-start" aria-hidden="true" />
          {{ t('kiosk.operator.startTest') }}
        </Button>
        <Button variant="outline" size="lg" class="tw:min-h-14 tw:flex-1" :disabled="busy || !password" @click="voidSession">{{
          t('kiosk.operator.void')
        }}</Button>
        <Button variant="outline" size="lg" class="tw:min-h-14 tw:flex-1" :disabled="busy || !password" @click="openAdmin">{{
          t('kiosk.operator.openAdmin')
        }}</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
