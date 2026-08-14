<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { Check, LoaderCircle, Printer, QrCode, RefreshCcw, X } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import PageQrCode from '@/components/mediaviewer/PageQrCode.vue'
import { useMainStore } from '@/stores/main-store'
import type { TriggerSchema } from '@/types/trigger-schema'
import { _fetch } from '@/util/fetch_api.js'

const props = defineProps<{
  mediaId: string
  printActionIndex: number | null
  qrEnabled: boolean
  qrTextAbove: string
  qrTextBelow: string
  qrLinkCodes: boolean
  retakeAction: TriggerSchema | null
}>()

const { t } = useI18n()
const router = useRouter()
const mainStore = useMainStore()
const printing = shallowRef(false)
const printQueued = shallowRef(false)
const printError = shallowRef<string | null>(null)
const qrOpen = shallowRef(false)
const qrLoading = shallowRef(false)
const qrError = shallowRef<string | null>(null)
const qrUrls = shallowRef<string[]>([])
const retakeOpen = shallowRef(false)
const retaking = shallowRef(false)
const retakeError = shallowRef<string | null>(null)
const session = computed(() => mainStore.kioskState?.session)
const canPrint = computed(() =>
  Boolean(props.printActionIndex !== null && session.value?.prints_remaining && session.value.printable_result_id === props.mediaId)
)
const canRetake = computed(() => Boolean(props.retakeAction && session.value?.retakes_remaining && session.value.prints_remaining))

function kioskHeaders() {
  return mainStore.kioskTestGrant ? { 'X-Kiosk-Test-Grant': mainStore.kioskTestGrant } : undefined
}

async function printOne() {
  if (props.printActionIndex === null || printing.value || printQueued.value) return
  printing.value = true
  printError.value = null

  try {
    const response = await _fetch(`/api/kiosk/results/${props.mediaId}/print?action_index=${props.printActionIndex}`, {
      method: 'POST',
      headers: kioskHeaders(),
    })
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
    printQueued.value = true
  } catch {
    printError.value = t('kiosk.result.printError')
  } finally {
    printing.value = false
  }
}

async function loadQr(open: boolean) {
  qrOpen.value = open
  if (!open || qrUrls.value.length || qrLoading.value) return
  qrLoading.value = true
  qrError.value = null

  try {
    for (let attempt = 0; attempt < 15; attempt++) {
      const response = await _fetch(`/api/kiosk/results/${props.mediaId}/download`)
      const result = await response.json()
      if (response.ok && Array.isArray(result.urls) && result.urls.length) {
        qrUrls.value = result.urls
        return
      }
      if (response.status !== 202) throw new Error(result.error || `${response.status} ${response.statusText}`)
      await new Promise(resolve => window.setTimeout(resolve, Number(response.headers.get('Retry-After') || 2) * 1000))
    }
    throw new Error('Upload timed out')
  } catch {
    qrError.value = t('kiosk.result.qrError')
  } finally {
    qrLoading.value = false
  }
}

async function retake() {
  if (!props.retakeAction || retaking.value) return
  retaking.value = true
  retakeError.value = null

  try {
    const response = await _fetch(`/api/${props.retakeAction.action}/${props.retakeAction.config_index}`, { headers: kioskHeaders() })
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)
    retakeOpen.value = false
    await router.push('/')
  } catch {
    retakeError.value = t('kiosk.result.retakeError')
  } finally {
    retaking.value = false
  }
}

async function done() {
  await _fetch('/api/kiosk/session/done', { method: 'POST', headers: kioskHeaders() })
  sessionStorage.removeItem('kioskLastActionName')
  mainStore.lastAction = null
  router.push('/')
}
</script>

<template>
  <Card class="kiosk-result-card tw:w-full tw:max-w-xl tw:border-0">
    <CardHeader class="tw:pb-5">
      <CardTitle class="tw:text-[clamp(2.5rem,4.5vw,5.25rem)] tw:leading-[0.94] tw:tracking-[-0.04em]">{{ t('kiosk.result.title') }}</CardTitle>
      <CardDescription class="tw:max-w-[32ch] tw:text-lg tw:leading-relaxed">{{ t('kiosk.result.description') }}</CardDescription>
    </CardHeader>

    <CardContent class="tw:grid tw:grid-cols-2 tw:gap-4">
      <Button v-if="canPrint" size="lg" class="tw:min-h-16 tw:text-base" :disabled="printing || printQueued" @click="printOne">
        <LoaderCircle v-if="printing" data-icon="inline-start" class="tw:animate-spin" aria-hidden="true" />
        <Check v-else-if="printQueued" data-icon="inline-start" aria-hidden="true" />
        <Printer v-else data-icon="inline-start" aria-hidden="true" />
        {{ printQueued ? t('kiosk.result.printQueued') : t('kiosk.result.print') }}
      </Button>

      <Button v-if="qrEnabled" variant="secondary" size="lg" class="tw:min-h-16 tw:text-base" @click="loadQr(true)">
        <QrCode data-icon="inline-start" aria-hidden="true" />
        {{ t('kiosk.result.qr') }}
      </Button>

      <Button v-if="canRetake" variant="outline" size="lg" class="tw:min-h-16 tw:text-base" @click="retakeOpen = true">
        <RefreshCcw data-icon="inline-start" aria-hidden="true" />
        {{ t('kiosk.result.retake') }}
      </Button>

      <Button variant="outline" size="lg" class="tw:min-h-16 tw:text-base" @click="done">
        <X data-icon="inline-start" aria-hidden="true" />
        {{ t('kiosk.result.done') }}
      </Button>
    </CardContent>

    <CardFooter v-if="printError" class="tw:text-destructive" role="status">{{ printError }}</CardFooter>
  </Card>

  <Dialog :open="qrOpen" @update:open="loadQr">
    <DialogContent class="tw:max-w-md">
      <DialogHeader>
        <DialogTitle class="tw:text-3xl tw:tracking-[-0.025em]">{{ t('kiosk.result.qrTitle') }}</DialogTitle>
        <DialogDescription>{{ t('kiosk.result.qrDescription') }}</DialogDescription>
      </DialogHeader>
      <div class="tw:grid tw:min-h-72 tw:place-items-center">
        <LoaderCircle v-if="qrLoading" class="tw:size-12 tw:animate-spin" aria-hidden="true" />
        <p v-else-if="qrError" class="tw:text-center tw:text-destructive" role="status">{{ qrError }}</p>
        <PageQrCode v-else :urls="qrUrls" :text-above="qrTextAbove" :text-below="qrTextBelow" :link-qr-codes="qrLinkCodes" />
      </div>
    </DialogContent>
  </Dialog>

  <Dialog v-model:open="retakeOpen">
    <DialogContent class="tw:max-w-lg" :show-close-button="!retaking">
      <DialogHeader>
        <DialogTitle class="tw:text-3xl tw:tracking-[-0.025em]">{{ t('kiosk.result.retakeTitle') }}</DialogTitle>
        <DialogDescription>{{ t('kiosk.result.retakeDescription') }}</DialogDescription>
      </DialogHeader>
      <p v-if="retakeError" class="tw:text-destructive" role="status">{{ retakeError }}</p>
      <DialogFooter class="tw:gap-3 tw:sm:gap-3">
        <Button variant="outline" size="lg" class="tw:min-h-14" :disabled="retaking" @click="retakeOpen = false">{{ t('kiosk.cancel') }}</Button>
        <Button size="lg" class="tw:min-h-14" :disabled="retaking" @click="retake">
          <LoaderCircle v-if="retaking" data-icon="inline-start" class="tw:animate-spin" aria-hidden="true" />
          {{ t('kiosk.result.retakeConfirm') }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

<style scoped>
.kiosk-result-card {
  background: transparent;
  box-shadow: none;
}
</style>
