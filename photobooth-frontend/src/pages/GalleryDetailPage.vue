<template>
  <q-layout view="hhh Lpr ffr">
    <div v-if="currentMediaitem" class="fixed-full">
      <template v-if="itemPresenterMode">
        <main class="kiosk-shell kiosk-result">
          <div class="kiosk-result-print">
            <img
              v-if="filterPreview && stage === 'filters'"
              :src="filterPreview"
              :alt="$t('kiosk.filters.previewAlt')"
              class="tw:block tw:h-full tw:w-full tw:object-contain"
            />
            <MediaItemPreviewViewer v-else :item="currentMediaitem" style="user-select: none" />
          </div>
          <section class="kiosk-result-panel">
            <ol class="kiosk-stage-indicator" :aria-label="$t('kiosk.filters.progressLabel')">
              <li
                v-for="(label, index) in kioskStageLabels"
                :key="label"
                :data-state="index + 1 === kioskStageStep ? 'current' : index + 1 < kioskStageStep ? 'complete' : 'upcoming'"
                :aria-current="index + 1 === kioskStageStep ? 'step' : undefined"
              >
                <span aria-hidden="true" />{{ label }}
              </li>
            </ol>
            <KioskFilterPicker
              v-if="stage === 'filters'"
              :options="kioskFilters"
              :loading="filtersLoading"
              :busy="kioskBusy"
              :error="kioskError"
              @select="selectFilter"
              @confirm="finalizeFilter"
            />
            <section v-else-if="stage === 'rendering'" role="status" class="kiosk-rendering">
              <h1 class="tw:text-4xl">{{ $t('kiosk.filters.preparing') }}</h1>
              <q-spinner size="64px" />
            </section>
            <KioskResultActions
              v-else
              :key="currentMediaitem.id"
              :stage="stage"
              :busy="kioskBusy"
              :error="kioskError"
              :media-id="currentMediaitem.id"
              :print-action-index="printActionIndex"
              :qr-enabled="qrEnabled"
              :qr-text-above="configurationStore.configuration.uisettings.qrcode_text_above"
              :qr-text-below="configurationStore.configuration.uisettings.qrcode_text_below"
              :qr-link-codes="configurationStore.configuration.uisettings.qrcode_link_codes"
              :retake-action="retakeAction"
              @keep="keepPhotos"
              @busy="deliveryBusy = $event"
            />
          </section>
          <RouteAfterTimeout
            v-if="!kioskBusy && !deliveryBusy && stage !== 'rendering' && !(stage === 'filters' && kioskError)"
            :key="stage"
            :timeout-ms="stage === 'filters' ? 30000 : configurationStore.configuration.uisettings.AUTOCLOSE_NEW_ITEM_ARRIVED * 1000"
            :warning-time-ms="10000"
            :warning-message="$t(stage === 'filters' ? 'kiosk.filters.timeoutWarning' : 'kiosk.result.timeoutWarning')"
            @on-timeout="onKioskTimeout"
          />
        </main>
      </template>

      <template v-else>
        <q-header class="bg-primary text-white">
          <HeaderProcessing v-if="displayIndeterminateProgressbar" />
        </q-header>

        <q-dialog v-if="showFilter" v-model="openFilterDialog">
          <q-card style="min-width: 550px; min-height: 400px; max-width: 90vw; max-height: 90vh" flat>
            <q-card-section class="row items-center q-pb-none">
              <q-space />
              <div class="text-h6">{{ $t('Choose your filter') }}</div>
              <q-space />
              <q-btn icon="sym_o_close" flat round v-close-popup />
            </q-card-section>
            <q-card-section>
              <FilterCards
                v-if="openFilterDialog"
                :id="currentMediaitem.id"
                :available-filter="available_filter"
                @trigger-apply-filter="doApplyFilter"
              />
            </q-card-section>
          </q-card>
        </q-dialog>

        <q-page-container class="q-pa-none galleryimagedetail full-height">
          <q-page class="full-height">
            <PageCarouselView
              :mediaitem-id="currentMediaitem.id"
              :sliced-images="mediacollectionStore.collection"
              @trigger-changed-item="onCarouselTransition"
            />

            <q-page-sticky v-if="configurationStore.configuration.uisettings.gallery_show_qrcode" position="top-right" class="q-ma-lg">
              <PageQrCode
                :urls="qrShareUrls"
                :text-above="configurationStore.configuration.uisettings.qrcode_text_above"
                :text-below="configurationStore.configuration.uisettings.qrcode_text_below"
                :link-qr-codes="configurationStore.configuration.uisettings.qrcode_link_codes"
              />
            </q-page-sticky>

            <PageToolbar
              :item="currentMediaitem"
              :show-filter="configurationStore.configuration.uisettings.gallery_show_filter"
              :enable-filter="filterEnabled(currentMediaitem.media_type)"
              :show-share="
                configurationStore.configuration.uisettings.gallery_show_shareprint && configurationStore.configuration.share.sharing_enabled
              "
              :share-buttons="shareButtons"
              :show-delete="configurationStore.configuration.uisettings.gallery_show_delete"
              :show-download="configurationStore.configuration.uisettings.gallery_show_download"
              :image_number="currentMediaitemNumber"
              :images_total="mediacollectionStore.collection_number_of_items"
              :last-action-trigger-button="null"
              @trigger-toggle-display-filter="openFilterDialog = !openFilterDialog"
              @trigger-delete-mediaitem="doDeleteItem"
              @trigger-share-action="doShareAction"
              @trigger-action="invokeAction"
            ></PageToolbar>

            <q-dialog v-model="showDialogShareActionWithParameters">
              <PageShareParameters
                :parameters="configurationStore.configuration.share.actions[shareActionWithParametersConfigIndex].processing.parameters"
                :parameters_dialog_caption="
                  configurationStore.configuration.share.actions[shareActionWithParametersConfigIndex].processing.parameters_dialog_caption
                "
                :parameters_dialog_action_icon="
                  configurationStore.configuration.share.actions[shareActionWithParametersConfigIndex].processing.parameters_dialog_action_icon
                "
                :parameters_dialog_action_label="
                  configurationStore.configuration.share.actions[shareActionWithParametersConfigIndex].processing.parameters_dialog_action_label
                "
                :config_index="shareActionWithParametersConfigIndex"
                @trigger-share-action-with-parameters="doShareActionWithParameters"
              >
              </PageShareParameters>
            </q-dialog>
          </q-page>
        </q-page-container>
      </template>
    </div>
    <div v-else>
      <!-- usually not visible but if page is called with wrong id or the page was not closed after an item is deleted -->
      <ItemNotAvailableError />
    </div>
  </q-layout>
</template>

<script setup lang="ts">
import type { TriggerSchema } from '@/types/trigger-schema'
import { useMainStore } from '@/stores/main-store'
import { useConfigurationStore } from '@/stores/configuration-store'
import { useMediacollectionStore } from '@/stores/mediacollection-store'
import { computed, onBeforeMount, onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { default as PageShareParameters } from '@/components/mediaviewer/PageShareParameters.vue'
import { default as PageToolbar } from '@/components/mediaviewer/PageToolbar.vue'
import { default as HeaderProcessing } from '@/components/mediaviewer/HeaderProcessing.vue'
import { default as FilterCards } from '@/components/mediaviewer/FilterCards.vue'
import { default as PageQrCode } from '@/components/mediaviewer/PageQrCode.vue'
import { default as PageCarouselView } from '@/components/mediaviewer/PageCarouselView.vue'
import ItemNotAvailableError from '@/components/ItemNotAvailableError.vue'
import { useRouter, useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { type ShareSchema } from '@/components/ShareTriggerButtons.vue'
import { remoteProcedureCall, _fetch } from '@/util/fetch_api.js'
import { watchDebounced } from '@vueuse/core'
import { default as MediaItemPreviewViewer } from '@/components/MediaItemPreviewViewer.vue'
import KioskResultActions from '@/components/kiosk/KioskResultActions.vue'
import KioskFilterPicker, { type KioskFilterOption } from '@/components/kiosk/KioskFilterPicker.vue'
import { resolveKioskPresets } from '@/components/kiosk/kiosk-presets'
import RouteAfterTimeout from '@/components/RouteAfterTimeout.vue'
import { useI18n } from 'vue-i18n'

const $q = useQuasar()
const { t } = useI18n()
const route = useRoute('mediaviewer')
const router = useRouter()
const mainStore = useMainStore()
const configurationStore = useConfigurationStore()
const mediacollectionStore = useMediacollectionStore()
const selectedMediaitemId = shallowRef<string | null>(null)
const openFilterDialog = shallowRef(false)
const displayIndeterminateProgressbar = shallowRef(false)
const showDialogShareActionWithParameters = shallowRef(false)
const shareActionWithParametersConfigIndex = shallowRef(0)
const available_filter = ref([])
const qrShareUrls = ref([])
const kioskBusy = ref(false)
const deliveryBusy = ref(false)
const kioskError = ref<string | null>(null)
const kioskFilters = ref<KioskFilterOption[]>([])
const filtersLoading = shallowRef(false)
const selectedFilter = ref('original')
const filterPreview = ref<string | null>(null)
const currentMediaitem = computed(() => mediacollectionStore.collection.find(item => item.id === selectedMediaitemId.value) ?? null)
const stage = computed(() => {
  const session = mainStore.kioskState?.session
  return session && session.printable_result_id === currentMediaitem.value?.id ? session.presentation_stage : 'review'
})
const kioskStageStep = computed(() => (stage.value === 'review' ? 1 : stage.value === 'delivery' ? 3 : 2))
const kioskStageLabels = computed(() => [t('kiosk.filters.steps.review'), t('kiosk.filters.steps.look'), t('kiosk.filters.steps.save')])
let statusTimer: ReturnType<typeof setInterval> | undefined
let statusPending = false
const props = defineProps<{
  startTimer: boolean
  itemPresenterMode?: boolean
}>()

onBeforeMount(() => {
  selectedMediaitemId.value = route.params.id as string
  if (!props.itemPresenterMode) getAvailableFilter()
  else {
    refreshKioskStatus()
    statusTimer = setInterval(refreshKioskStatus, 2000)
  }
})
onBeforeUnmount(() => clearInterval(statusTimer))

function kioskHeaders() {
  return mainStore.kioskTestGrant ? { 'X-Kiosk-Test-Grant': mainStore.kioskTestGrant } : {}
}

async function refreshKioskStatus() {
  if (statusPending) return
  statusPending = true
  try {
    const response = await _fetch('/api/kiosk/status', { headers: kioskHeaders() })
    if (response.ok) mainStore.kioskState = await response.json()
  } catch {
    /* SSE/polling reconnects on the next tick. */
  } finally {
    statusPending = false
  }
}

watch(
  stage,
  async value => {
    if (!props.itemPresenterMode || value !== 'filters' || !currentMediaitem.value) return
    filtersLoading.value = true
    kioskFilters.value = []
    try {
      const response = await _fetch(`/api/kiosk/results/${currentMediaitem.value.id}/filters`)
      if (!response.ok) throw new Error('preview unavailable')
      kioskFilters.value = await response.json()
    } catch {
      kioskFilters.value = [{ id: 'original', label: 'Original', preview_url: `/media/preview/${currentMediaitem.value.id}` }]
    } finally {
      filtersLoading.value = false
    }
  },
  { immediate: true }
)

function selectFilter(filter: string, preview: string | null) {
  selectedFilter.value = filter
  filterPreview.value = preview
}

async function keepPhotos() {
  if (kioskBusy.value || !currentMediaitem.value) return
  kioskBusy.value = true
  kioskError.value = null
  try {
    const response = await _fetch(`/api/kiosk/results/${currentMediaitem.value.id}/keep`, { method: 'POST', headers: kioskHeaders() })
    if (!response.ok) throw new Error('keep failed')
    mainStore.kioskState = await response.json()
  } catch {
    kioskError.value = t('kiosk.filters.keepError')
  } finally {
    kioskBusy.value = false
  }
}

async function finalizeFilter(filter: string) {
  if (kioskBusy.value || !currentMediaitem.value) return
  kioskBusy.value = true
  kioskError.value = null
  try {
    const response = await _fetch(`/api/kiosk/results/${currentMediaitem.value.id}/finalize`, {
      method: 'POST',
      headers: { ...kioskHeaders(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ filter }),
    })
    if (!response.ok) throw new Error('render failed')
    const result = await response.json()
    mediacollectionStore.updateMediaitem({ ...currentMediaitem.value, revision: result.revision })
  } catch {
    kioskError.value = t('kiosk.filters.renderError')
  } finally {
    await refreshKioskStatus()
    kioskBusy.value = false
  }
}

async function onKioskTimeout() {
  if (stage.value === 'filters') await finalizeFilter(selectedFilter.value)
  else await finishKioskSession()
}
watch(route, to => {
  selectedMediaitemId.value = to.params.id as string
})
const onCarouselTransition = (newMediaitemId: string | number) => {
  selectedMediaitemId.value = newMediaitemId as string
}

const printActionIndex = computed(() => {
  if (!configurationStore.configuration.share.sharing_enabled) return null
  const index = configurationStore.configuration.share.actions.findIndex(action => {
    const label = `${action.name} ${action.trigger.ui_trigger.title} ${action.trigger.ui_trigger.icon}`
    return (
      action.handles_images_only && action.trigger.ui_trigger.show_button && !action.processing.ask_user_for_parameter_input && /print/i.test(label)
    )
  })
  return index < 0 ? null : index
})

const qrEnabled = computed(
  () => configurationStore.configuration.share.sharing_enabled && configurationStore.configuration.uisettings.gallery_show_qrcode
)

const retakeAction = computed<TriggerSchema | null>(() => {
  const actionName = sessionStorage.getItem('kioskLastActionName')
  const preset = resolveKioskPresets(configurationStore.configuration.actions.collage).find(item => item.actionName === actionName)
  if (preset) {
    return {
      action: 'actions/collage',
      config_index: preset.actionIndex,
      show_button: true,
      title: preset.title,
      icon: 'photo_camera',
      use_custom_color: false,
      custom_color: '#171717',
    }
  }

  return mainStore.lastAction
})

async function finishKioskSession() {
  try {
    const response = await _fetch('/api/kiosk/session/done', { method: 'POST', headers: kioskHeaders() })
    if (!response.ok) throw new Error('Could not close session')
    sessionStorage.removeItem('kioskLastActionName')
    mainStore.lastAction = null
    await router.push({ path: '/' })
  } catch {
    kioskError.value = t('kiosk.filters.keepError')
  }
}

watchDebounced(
  selectedMediaitemId,
  async () => {
    if (props.itemPresenterMode || selectedMediaitemId.value === null) return

    try {
      const response = await _fetch(`/api/share/download/${selectedMediaitemId.value}`)
      if (!response.ok) {
        throw `Error: ${response.status} ${response.statusText}`
      }
      qrShareUrls.value = await response.json()
      console.log(qrShareUrls.value)
    } catch (error) {
      console.warn(error)
    }
  },

  { debounce: 600 }
)

const currentMediaitemNumber = computed(() => {
  return mediacollectionStore.collection.findIndex(mediaitem => mediaitem.id == selectedMediaitemId.value) + 1
})
const showFilter = computed(() => {
  if (!currentMediaitem.value) return false
  return configurationStore.configuration.uisettings.gallery_show_filter && filterEnabled(currentMediaitem.value.media_type)
})
const shareButtons = computed(() => {
  const result: ShareSchema[] = []

  const share_config = configurationStore.configuration.share.actions
  share_config.forEach((action, index: number) => {
    const trigger: ShareSchema = {
      config_index: index,
      handles_images_only: action.handles_images_only,
      show_button: action.trigger.ui_trigger.show_button,
      title: action.trigger.ui_trigger.title,
      icon: action.trigger.ui_trigger.icon,
    }

    result.push(trigger)
  })

  return result
})
const getMediaitemById = (id: string) => {
  return mediacollectionStore.collection.find(mediaitem => mediaitem.id == id)
}

const filterEnabled = (media_type: string) => {
  return ['image'].includes(media_type)
}

const getAvailableFilter = async () => {
  try {
    const response = await _fetch('/api/filter/')

    available_filter.value = await response.json()
    console.log(available_filter.value)
  } catch (error) {
    console.warn(error)
  }
}
const doApplyFilter = (id: string, filter: string) => {
  // close filter dialog
  openFilterDialog.value = false

  displayIndeterminateProgressbar.value = true
  fetch(`/api/filter/${id}?filter=${filter}`, { method: 'PATCH' })
    .then(response => {
      if (!response.ok) {
        throw new Error('Server returned ' + response.status)
      }

      displayIndeterminateProgressbar.value = false
    })
    .catch(err => {
      console.error(err)
      displayIndeterminateProgressbar.value = false
    })
}
const doDeleteItem = (id: string) => {
  selectedMediaitemId.value = null
  mediacollectionStore.deleteItem(id)
  router.back()
}
const doShareAction = (config_index: number) => {
  console.log('doShareAction', selectedMediaitemId.value, config_index)

  const askUserForInput = configurationStore.configuration.share.actions[config_index].processing.ask_user_for_parameter_input
  if (askUserForInput) {
    // advanced share, user input is requested, so show a dialog for the config_index that was already chosen by button click
    shareActionWithParametersConfigIndex.value = config_index
    showDialogShareActionWithParameters.value = true
  } else {
    // there are no parameters from user required here -> go on and use default values without further questions
    remoteProcedureCall(`/api/share/actions/${selectedMediaitemId.value}/${config_index}`, 'POST')
  }
}
const doShareActionWithParameters = async (config_index: number, input_data: unknown) => {
  console.warn(selectedMediaitemId.value, config_index, input_data)
  console.log(JSON.stringify(input_data))
  try {
    const response = await _fetch(`/api/share/actions/${selectedMediaitemId.value}/${config_index}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input_data),
    })
    console.log(response)
    if (!response.ok) {
      throw new Error(`Network error:${response.status} ${response.statusText}}`)
    }
  } catch (error) {
    console.error(error)
    const msg = error instanceof Error ? error.message : String(error)
    $q.notify({
      message: msg,
      caption: 'Request Error!',
      color: 'negative',
    })
  }
}
const invokeAction = (trigger: TriggerSchema) => {
  remoteProcedureCall(`/api/${trigger.action}/${trigger.config_index}`)
}
</script>

<style scoped>
.kiosk-result {
  display: grid;
  width: 100%;
  height: 100dvh;
  grid-template-columns: minmax(0, 1.15fr) minmax(390px, 0.85fr);
  align-items: center;
  gap: clamp(2rem, 5vw, 7rem);
  overflow: hidden;
  padding: clamp(2rem, 5vh, 5rem) clamp(2rem, 6vw, 7rem);
  background-image: radial-gradient(circle at 20% 30%, rgb(23 23 23 / 2.5%) 0 0.7px, transparent 0.9px);
  background-size: 10px 10px;
}

.kiosk-result-print {
  width: min(100%, 58.67dvh, 720px);
  aspect-ratio: 2 / 3;
  margin-inline: auto;
  padding: clamp(0.75rem, 1.5vw, 1.4rem);
  overflow: hidden;
  rotate: -1deg;
  border-radius: var(--kiosk-panel-radius);
  background: var(--kiosk-white);
  box-shadow: var(--kiosk-panel-shadow);
}

.kiosk-result-panel {
  display: flex;
  width: 100%;
  min-width: 0;
  max-width: 36rem;
  flex-direction: column;
  gap: 1.25rem;
}

.kiosk-stage-indicator {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.5rem;
  margin: 0;
  padding: 0;
  color: color-mix(in srgb, var(--kiosk-ink) 55%, var(--kiosk-paper));
  font-size: 0.875rem;
  font-weight: 600;
  list-style: none;
}

.kiosk-stage-indicator li {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 0.5rem;
}

.kiosk-stage-indicator span {
  width: 0.75rem;
  height: 0.75rem;
  flex: 0 0 auto;
  border: 2px solid currentcolor;
  border-radius: 999px;
}

.kiosk-stage-indicator li[data-state='current'] {
  color: var(--kiosk-ink);
}

.kiosk-stage-indicator li[data-state='current'] span {
  background: var(--kiosk-butter);
}

.kiosk-stage-indicator li[data-state='complete'] span {
  background: var(--kiosk-ink);
}

.kiosk-rendering {
  display: flex;
  min-height: 18rem;
  flex-direction: column;
  justify-content: center;
  gap: 1rem;
}

@media (max-width: 1100px), (max-height: 760px) {
  .kiosk-result {
    grid-template-columns: minmax(0, 1fr) minmax(360px, 0.8fr);
    gap: 2rem;
    padding: 2rem 3rem;
  }
}

@media (max-width: 1000px) and (min-height: 800px) {
  .kiosk-result {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: minmax(0, 0.9fr) minmax(0, 1.1fr);
    gap: 1rem;
    padding: 1.25rem 2rem;
  }
  .kiosk-result-print {
    width: min(100%, 28.67dvh, 320px);
  }
  .kiosk-result-panel {
    max-width: none;
    gap: 0.625rem;
  }
  .kiosk-stage-indicator {
    max-width: 32rem;
  }
}

@media (max-width: 849px), (max-width: 1000px) and (max-height: 799px) {
  .kiosk-result {
    height: auto;
    min-height: 100dvh;
    grid-template-columns: minmax(0, 1fr);
    overflow-y: auto;
    padding: 1.5rem;
  }
  .kiosk-result-print {
    width: min(70vw, 360px);
  }
  .kiosk-result-panel {
    max-width: none;
  }
}
</style>
