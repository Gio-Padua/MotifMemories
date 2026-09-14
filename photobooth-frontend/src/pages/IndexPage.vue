<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { refThrottled, useIntervalFn, watchDebounced } from '@vueuse/core'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import CountdownTimer from '@/components/CountdownTimer.vue'
import KioskCaptureHud from '@/components/kiosk/KioskCaptureHud.vue'
import KioskIdleFlow from '@/components/kiosk/KioskIdleFlow.vue'
import KioskOperatorDialog from '@/components/kiosk/KioskOperatorDialog.vue'
import KioskPaymentPanel from '@/components/kiosk/KioskPaymentPanel.vue'
import { resolveKioskPresets, type ResolvedKioskFramePreset } from '@/components/kiosk/kiosk-presets'
import MediaItemApprovalViewer from '@/components/MediaItemApprovalViewer.vue'
import PreviewStream from '@/components/PreviewStream.vue'
import type { components } from '@/dto/api'
import { useConfigurationStore } from '@/stores/configuration-store'
import { useMainStore } from '@/stores/main-store'
import { useStateStore } from '@/stores/state-store'
import type { TriggerSchema } from '@/types/trigger-schema'
import { _fetch, remoteProcedureCall } from '@/util/fetch_api.js'
import type { Size2D } from '@/util/streamRenderer.ts'

const { t } = useI18n()
const mainStore = useMainStore()
const stateStore = useStateStore()
const configurationStore = useConfigurationStore()
const router = useRouter()
const btnAdminClickCounter = shallowRef(0)
const starting = shallowRef(false)
const startError = shallowRef<string | null>(null)
const operatorOpen = shallowRef(false)
let startWatchdog: number | undefined

const kioskPresets = computed(() => (configurationStore.isLoaded ? resolveKioskPresets(configurationStore.configuration.actions.collage) : []))
const entitled = computed(() => {
  const session = mainStore.kioskState?.session
  if (!session || session.state !== 'paid') return false
  return session.mode === 'test'
    ? Boolean(mainStore.kioskTestGrant && mainStore.kioskState?.readiness.camera)
    : Boolean(mainStore.kioskState?.readiness.ready)
})

async function refreshKioskStatus() {
  const headers = mainStore.kioskTestGrant ? { 'X-Kiosk-Test-Grant': mainStore.kioskTestGrant } : undefined
  const response = await _fetch('/api/kiosk/status', { headers })
  if (response.ok) mainStore.kioskState = await response.json()
  const session = mainStore.kioskState?.session
  if (session?.state === 'presenting' && session.printable_result_id && (session.mode === 'paid' || mainStore.kioskTestGrant)) {
    await router.replace({ name: 'itempresenter', params: { id: session.printable_result_id } })
  }
}

watch(
  () => mainStore.kioskTestGrant,
  () => refreshKioskStatus(),
  { immediate: true }
)
useIntervalFn(refreshKioskStatus, 1000)

watchDebounced(
  btnAdminClickCounter,
  () => {
    if (btnAdminClickCounter.value >= 5) operatorOpen.value = true
    btnAdminClickCounter.value = 0
  },
  { debounce: 500 }
)

watch(
  () => stateStore.target,
  target => {
    if (target !== 'counting') return
    window.clearTimeout(startWatchdog)
    starting.value = false
    startError.value = null
  }
)

const showPreview = computed(() => {
  const enabled = configurationStore.configuration.uisettings.enable_livestream_when_active
  const kioskCapture = mainStore.lastAction?.action === 'actions/collage' && sessionStorage.getItem('kioskLastActionName')
  return ((enabled || kioskCapture) && (stateStore.isStateCountdown || stateStore.isStateCapture)) || stateStore.isStateRecording
})

const showPreviewThrottled = refThrottled(showPreview, 500)

const fixedSize = computed((): Size2D | null => {
  const captureDefinition = stateStore.jobmodel.captures_definition
  return captureDefinition ? { width: captureDefinition.width, height: captureDefinition.height } : null
})

const frameOverlay = computed((): components['schemas']['UiFrameOverlay'] | null => {
  return stateStore.isStateCountdown && stateStore.jobmodel.frame_overlay ? stateStore.jobmodel.frame_overlay : null
})

function onBtnAdminClick() {
  btnAdminClickCounter.value++
}

async function invokeKioskAction(preset: ResolvedKioskFramePreset) {
  if (starting.value || !stateStore.isStateIdle) return
  starting.value = true
  startError.value = null

  try {
    const headers = mainStore.kioskTestGrant ? { 'X-Kiosk-Test-Grant': mainStore.kioskTestGrant } : undefined
    const response = await _fetch(`/api/actions/collage/${preset.actionIndex}`, { headers })
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`)

    const trigger: TriggerSchema = {
      action: 'actions/collage',
      config_index: preset.actionIndex,
      show_button: true,
      title: preset.title,
      icon: 'photo_camera',
      use_custom_color: false,
      custom_color: '#171717',
    }
    mainStore.lastAction = trigger
    sessionStorage.setItem('kioskLastActionName', preset.actionName)

    window.clearTimeout(startWatchdog)
    startWatchdog = window.setTimeout(() => {
      if (stateStore.target === 'counting') return
      starting.value = false
      startError.value = t('kiosk.errors.startTimeout')
    }, 10_000)
  } catch {
    starting.value = false
    startError.value = t('kiosk.errors.startFailed')
  }
}

function stopRecordingVideo() {
  remoteProcedureCall('/api/processing/next')
}
</script>

<template>
  <q-page id="index-page" class="q-pa-none full-height tw:overflow-hidden">
    <KioskIdleFlow
      v-if="stateStore.isStateIdle && entitled"
      :presets="kioskPresets"
      :busy="starting"
      :start-error="startError"
      :admin-enabled="configurationStore.configuration.uisettings.show_admin_on_frontpage"
      :admin-invisible="configurationStore.configuration.uisettings.admin_button_invisible"
      :show-gallery="configurationStore.configuration.uisettings.show_gallery_on_frontpage"
      start-in-frames
      @start="invokeKioskAction"
      @admin-tap="onBtnAdminClick"
      @gallery="router.push('/gallery')"
    />
    <KioskPaymentPanel
      v-else-if="stateStore.isStateIdle"
      :state="mainStore.kioskState"
      @operator-tap="onBtnAdminClick"
      @operator-open="operatorOpen = true"
    />
    <KioskOperatorDialog v-model:open="operatorOpen" :state="mainStore.kioskState" @test-started="refreshKioskStatus" />

    <PreviewStream
      v-if="showPreviewThrottled"
      :index_device="configurationStore.configuration.cameras.index_backend_video"
      :frame-overlay="frameOverlay"
      :fixed-size="fixedSize"
      :enable-blurred-background-stream="configurationStore.configuration.uisettings.livestream_blurredbackground"
      :enable-mirror-effect-stream="configurationStore.configuration.uisettings.livestream_mirror_effect"
      :blurredbackground-high-framerate="configurationStore.configuration.uisettings.livestream_blurredbackground_high_framerate"
    />

    <KioskCaptureHud
      v-if="stateStore.isStateCountdown || stateStore.isStateCapture || stateStore.isStateProcessing"
      :captures-taken="stateStore.jobmodel.number_captures_taken"
      :total-captures="stateStore.jobmodel.total_captures_to_take || 4"
      :processing="stateStore.isStateProcessing"
    />

    <div
      v-if="stateStore.isStateCountdown"
      id="frontpage-countdown"
      class="full-height full-width column justify-center content-center tw:absolute tw:inset-0 tw:z-20"
    >
      <CountdownTimer
        :duration="stateStore.jobmodel.duration"
        :capture-cue-duration="stateStore.jobmodel.capture_cue_duration"
        :capture-cue-safety="stateStore.jobmodel.capture_cue_safety"
        :message-duration="configurationStore.configuration.uisettings.TAKEPIC_MSG_TIME"
        :message-text="configurationStore.configuration.uisettings.TAKEPIC_MSG_TEXT"
      />
    </div>

    <MediaItemApprovalViewer
      v-if="stateStore.isStateApproval && stateStore.jobmodel.approval_id"
      :approval_id="stateStore.jobmodel.approval_id"
      :number_captures_taken="stateStore.jobmodel.number_captures_taken"
      :total_captures_to_take="stateStore.jobmodel.total_captures_to_take"
    />

    <q-page-sticky v-if="stateStore.isStateRecording" id="frontpage-indicator-recording" position="top-right" :offset="[25, 25]" align="center">
      <q-spinner-puff color="red" size="12em" thickness="20" />
    </q-page-sticky>
    <q-page-sticky v-if="stateStore.isStateRecording" id="frontpage-indicator-stop-recording" position="bottom" :offset="[0, 25]" align="center">
      <q-btn stack rounded no-caps color="negative" class="action-button glass-effect" @click="stopRecordingVideo">
        <q-icon name="sym_o_stop_circle" />
        <div>{{ $t('Stop recording') }}</div>
      </q-btn>
    </q-page-sticky>
  </q-page>
</template>
