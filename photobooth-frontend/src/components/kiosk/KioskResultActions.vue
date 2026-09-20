<script setup lang="ts">
import { computed, onBeforeUnmount, shallowRef, watch } from 'vue'
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
  stage: 'review' | 'delivery'
  busy: boolean
  error: string | null
  mediaId: string
  printActionIndex: number | null
  qrEnabled: boolean
  qrTextAbove: string
  qrTextBelow: string
  qrLinkCodes: boolean
  retakeAction: TriggerSchema | null
}>()
const emit = defineEmits<{ keep: []; busy: [value: boolean] }>()

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
  Boolean(
    props.stage === 'delivery' &&
    props.printActionIndex !== null &&
    session.value?.prints_remaining &&
    session.value.printable_result_id === props.mediaId
  )
)
const canRetake = computed(() =>
  Boolean(props.stage === 'review' && props.retakeAction && session.value?.retakes_remaining && session.value.prints_remaining)
)
let qrController: AbortController | null = null
watch(
  () => printing.value || retaking.value || qrLoading.value,
  value => emit('busy', value)
)
onBeforeUnmount(() => {
  qrController?.abort()
  emit('busy', false)
})

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
  if (!open) {
    qrController?.abort()
    qrLoading.value = false
    return
  }
  if (!open || qrUrls.value.length || qrLoading.value) return
  qrLoading.value = true
  qrError.value = null
  qrController?.abort()
  const controller = new AbortController()
  qrController = controller
  const deadline = Date.now() + 60_000
  const timeout = window.setTimeout(() => controller.abort(), 60_000)

  try {
    while (Date.now() < deadline && !controller.signal.aborted) {
      const response = await _fetch(`/api/kiosk/results/${props.mediaId}/download`, { signal: controller.signal })
      const result = await response.json()
      if (response.ok && Array.isArray(result.urls) && result.urls.length) {
        qrUrls.value = result.urls
        return
      }
      if (response.status !== 202) throw new Error(result.error || `${response.status} ${response.statusText}`)
      await new Promise<void>((resolve, reject) => {
        const abort = () => {
          window.clearTimeout(timer)
          reject(new DOMException('Cancelled', 'AbortError'))
        }
        const timer = window.setTimeout(() => {
          controller.signal.removeEventListener('abort', abort)
          resolve()
        }, 2000)
        controller.signal.addEventListener('abort', abort, { once: true })
      })
    }
    throw new Error('Upload timed out')
  } catch {
    if (!controller.signal.aborted || (qrOpen.value && Date.now() >= deadline)) qrError.value = t('kiosk.result.qrError')
  } finally {
    window.clearTimeout(timeout)
    if (qrController === controller) qrLoading.value = false
  }
}

async function retryQr() {
  if (qrLoading.value) return
  try {
    const response = await _fetch(`/api/kiosk/results/${props.mediaId}/download/retry`, { method: 'POST', headers: kioskHeaders() })
    if (!response.ok) throw new Error('retry failed')
    await loadQr(true)
  } catch {
    qrError.value = t('kiosk.result.qrError')
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
  try {
    const response = await _fetch('/api/kiosk/session/done', { method: 'POST', headers: kioskHeaders() })
    if (!response.ok) {
      printError.value = t('kiosk.filters.keepError')
      return
    }
    sessionStorage.removeItem('kioskLastActionName')
    mainStore.lastAction = null
    router.push('/')
  } catch {
    printError.value = t('kiosk.filters.keepError')
  }
}
</script>

<template>
  <Card class="kiosk-result-card tw:w-full tw:max-w-xl tw:border-0">
    <CardHeader class="tw:pb-5">
      <CardTitle class="tw:text-[clamp(2.5rem,4.5vw,5.25rem)] tw:leading-[0.94] tw:tracking-[-0.04em]">{{ t('kiosk.result.title') }}</CardTitle>
      <CardDescription class="tw:max-w-[32ch] tw:text-lg tw:leading-relaxed">{{
        t(stage === 'review' ? 'kiosk.filters.reviewDescription' : 'kiosk.result.description')
      }}</CardDescription>
    </CardHeader>

    <CardContent class="tw:grid tw:grid-cols-2 tw:gap-4">
      <Button v-if="stage === 'review'" size="lg" class="tw:col-span-2 tw:min-h-16" :disabled="busy || retaking" @click="emit('keep')">{{
        t('kiosk.filters.keep')
      }}</Button>
      <Button v-if="canPrint || printQueued" size="lg" class="tw:min-h-16 tw:text-base" :disabled="printing || printQueued" @click="printOne">
        <LoaderCircle v-if="printing" data-icon="inline-start" class="tw:animate-spin" aria-hidden="true" />
        <Check v-else-if="printQueued" data-icon="inline-start" aria-hidden="true" />
        <Printer v-else data-icon="inline-start" aria-hidden="true" />
        {{ printQueued ? t('kiosk.result.printQueued') : t('kiosk.result.print') }}
      </Button>

      <Button v-if="stage === 'delivery' && qrEnabled" variant="secondary" size="lg" class="tw:min-h-16 tw:text-base" @click="loadQr(true)">
        <QrCode data-icon="inline-start" aria-hidden="true" />
        {{ t('kiosk.result.qr') }}
      </Button>

      <Button v-if="canRetake" variant="outline" size="lg" class="tw:min-h-16 tw:text-base" :disabled="busy" @click="retakeOpen = true">
        <RefreshCcw data-icon="inline-start" aria-hidden="true" />
        {{ t('kiosk.result.retake') }}
      </Button>

      <Button variant="outline" size="lg" class="tw:min-h-16 tw:text-base" :disabled="busy || printing || retaking" @click="done">
        <X data-icon="inline-start" aria-hidden="true" />
        {{ t('kiosk.result.done') }}
      </Button>
    </CardContent>

    <CardFooter v-if="printError || error" class="tw:text-destructive" role="status">{{ printError || error }}</CardFooter>
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
      <Button v-if="qrError" variant="secondary" size="lg" class="tw:min-h-14" @click="retryQr">{{ t('kiosk.retry') }}</Button>
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

@media (max-width: 1000px) and (min-height: 800px) {
  .kiosk-result-card {
    max-width: none;
  }
  .kiosk-result-card :deep([data-slot='card-header']) {
    padding-block: 0.25rem 0.75rem;
  }
  .kiosk-result-card :deep([data-slot='card-title']) {
    font-size: clamp(2rem, 5vw, 3rem);
  }
  .kiosk-result-card :deep([data-slot='card-description']) {
    max-width: none;
    font-size: 1rem;
    line-height: 1.45;
  }
}
</style>
