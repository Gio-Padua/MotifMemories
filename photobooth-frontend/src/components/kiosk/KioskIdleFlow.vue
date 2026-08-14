<script setup lang="ts">
import { onBeforeUnmount, shallowRef, watch } from 'vue'
import { ArrowLeft, Camera, LoaderCircle, Settings } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import type { ResolvedKioskFramePreset } from './kiosk-presets'

const props = defineProps<{
  presets: ResolvedKioskFramePreset[]
  busy: boolean
  startError: string | null
  adminEnabled: boolean
  adminInvisible: boolean
  showGallery: boolean
  startInFrames?: boolean
}>()

const emit = defineEmits<{
  start: [preset: ResolvedKioskFramePreset]
  adminTap: []
  gallery: []
}>()

const { t } = useI18n()
const stage = shallowRef<'attract' | 'frames'>(props.startInFrames ? 'frames' : 'attract')
const selected = shallowRef<ResolvedKioskFramePreset | null>(null)
const dialogOpen = shallowRef(false)
let inactivityTimer: number | undefined

const accentClasses = {
  blush: 'tw:bg-[var(--kiosk-blush)]',
  butter: 'tw:bg-[var(--kiosk-butter)]',
  mint: 'tw:bg-[var(--kiosk-mint)]',
  lavender: 'tw:bg-[var(--kiosk-lavender)]',
} as const

function resetToAttract() {
  window.clearTimeout(inactivityTimer)
  dialogOpen.value = false
  selected.value = null
  stage.value = props.startInFrames ? 'frames' : 'attract'
}

function armInactivityReset() {
  if (stage.value === 'attract') return
  window.clearTimeout(inactivityTimer)
  inactivityTimer = window.setTimeout(resetToAttract, 45_000)
}

function showFrames() {
  stage.value = 'frames'
  armInactivityReset()
}

function choosePreset(preset: ResolvedKioskFramePreset) {
  selected.value = preset
  dialogOpen.value = true
  armInactivityReset()
}

function closeDialog() {
  if (props.busy) return
  dialogOpen.value = false
  selected.value = null
  armInactivityReset()
}

function start() {
  if (!selected.value || props.busy) return
  emit('start', selected.value)
  armInactivityReset()
}

watch(dialogOpen, open => {
  if (!open && !props.busy) selected.value = null
})

onBeforeUnmount(() => window.clearTimeout(inactivityTimer))
</script>

<template>
  <section
    class="kiosk-shell tw:relative tw:h-dvh tw:min-h-[640px] tw:w-full tw:overflow-hidden"
    @pointerdown="armInactivityReset"
    @keydown="armInactivityReset"
  >
    <div class="kiosk-paper-texture tw:pointer-events-none tw:absolute tw:inset-0" aria-hidden="true" />

    <button
      v-if="adminEnabled"
      type="button"
      :aria-label="t('kiosk.admin')"
      :class="
        cn(
          'kiosk-admin-button tw:absolute tw:right-5 tw:top-5 tw:z-10 tw:grid tw:size-14 tw:place-items-center tw:rounded-full',
          adminInvisible && 'tw:opacity-0'
        )
      "
      @click.stop="emit('adminTap')"
    >
      <Settings aria-hidden="true" />
    </button>

    <div v-if="presets.length === 0" class="tw:grid tw:h-full tw:place-items-center tw:p-8 tw:text-center">
      <div class="tw:max-w-xl">
        <Camera class="tw:mx-auto tw:mb-7 tw:size-16" aria-hidden="true" />
        <h1 class="tw:text-5xl tw:font-semibold tw:tracking-[-0.03em]">{{ t('kiosk.setupRequired.title') }}</h1>
        <p class="tw:mt-5 tw:text-xl tw:text-muted-foreground">{{ t('kiosk.setupRequired.description') }}</p>
        <Badge variant="outline" class="tw:mt-7 tw:px-4 tw:py-2 tw:text-base">{{ t('kiosk.setupRequired.code') }}</Badge>
      </div>
    </div>

    <div
      v-else-if="stage === 'attract'"
      class="tw:grid tw:h-full tw:grid-cols-[minmax(0,1fr)_minmax(360px,0.72fr)] tw:items-center tw:gap-[clamp(2rem,6vw,8rem)] tw:px-[clamp(3rem,8vw,10rem)] tw:py-[clamp(2rem,6vh,5rem)]"
    >
      <div class="tw:max-w-4xl">
        <div class="tw:mb-8 tw:flex tw:items-center tw:gap-4" aria-hidden="true">
          <span class="tw:h-3 tw:w-24 tw:bg-[var(--kiosk-blush)]" />
          <span class="tw:h-3 tw:w-14 tw:bg-[var(--kiosk-butter)]" />
          <span class="tw:h-3 tw:w-8 tw:bg-[var(--kiosk-mint)]" />
        </div>
        <h1 class="tw:max-w-[12ch] tw:text-[clamp(4rem,7.4vw,6rem)] tw:font-semibold tw:leading-[0.9] tw:tracking-[-0.04em]">
          {{ t('kiosk.brand.name') }}
        </h1>
        <p class="tw:mt-7 tw:max-w-[34ch] tw:text-[clamp(1.2rem,1.8vw,2rem)] tw:leading-relaxed tw:text-muted-foreground">
          {{ t('kiosk.brand.tagline') }}
        </p>
        <div class="tw:mt-10 tw:flex tw:flex-wrap tw:gap-4">
          <Button size="lg" class="tw:min-h-16 tw:min-w-64 tw:px-9 tw:text-xl" @click="showFrames">
            <Camera data-icon="inline-start" aria-hidden="true" />
            {{ t('kiosk.attract.action') }}
          </Button>
          <Button v-if="showGallery" variant="outline" size="lg" class="tw:min-h-16 tw:px-8 tw:text-lg" @click="emit('gallery')">
            {{ t('kiosk.attract.gallery') }}
          </Button>
        </div>
      </div>

      <div
        class="kiosk-attract-print tw:relative tw:mx-auto tw:w-[min(34vw,410px)] tw:rotate-[2deg] tw:bg-card tw:p-4 tw:shadow-[14px_18px_40px_rgba(23,23,23,0.18)]"
        aria-hidden="true"
      >
        <img :src="presets[0].preview" alt="" class="tw:block tw:h-auto tw:w-full" />
        <span class="tw:absolute tw:-left-8 tw:top-16 tw:h-14 tw:w-28 tw:-rotate-12 tw:bg-[color-mix(in_srgb,var(--kiosk-butter)_76%,transparent)]" />
        <span class="tw:absolute tw:-bottom-5 tw:right-7 tw:size-14 tw:rounded-full tw:bg-[var(--kiosk-mint)]" />
      </div>
    </div>

    <div v-else class="tw:flex tw:h-full tw:flex-col tw:px-[clamp(2rem,5vw,6rem)] tw:py-[clamp(1.5rem,4vh,3.5rem)]">
      <header class="tw:flex tw:items-end tw:justify-between tw:gap-8">
        <div>
          <h1 class="tw:text-[clamp(2.6rem,4vw,5rem)] tw:font-semibold tw:leading-none tw:tracking-[-0.035em]">{{ t('kiosk.frames.title') }}</h1>
          <p class="tw:mt-3 tw:text-[clamp(1rem,1.4vw,1.45rem)] tw:text-muted-foreground">{{ t('kiosk.frames.description') }}</p>
        </div>
        <div class="tw:flex tw:items-center tw:gap-6">
          <span class="tw:text-xl tw:font-semibold tw:tracking-[-0.025em]">{{ t('kiosk.brand.name') }}</span>
          <Button variant="outline" size="lg" class="tw:min-h-14 tw:px-6" @click="resetToAttract">
            <ArrowLeft data-icon="inline-start" aria-hidden="true" />
            {{ t('kiosk.back') }}
          </Button>
        </div>
      </header>

      <div class="tw:mt-[clamp(1.25rem,3vh,2.5rem)] tw:grid tw:min-h-0 tw:flex-1 tw:grid-cols-3 tw:grid-rows-2 tw:gap-[clamp(0.75rem,1.5vw,1.5rem)]">
        <button v-for="preset in presets" :key="preset.id" type="button" class="tw:min-h-0 tw:text-left" @click="choosePreset(preset)">
          <Card
            class="kiosk-frame-card tw:h-full tw:gap-1 tw:overflow-hidden tw:py-0 tw:transition-[transform,box-shadow] tw:duration-200 tw:hover:-translate-y-1 tw:hover:shadow-[0_18px_44px_rgba(23,23,23,0.16)]"
          >
            <CardHeader class="tw:flex-row tw:items-center tw:justify-between tw:gap-4 tw:px-5 tw:pb-1 tw:pt-4">
              <CardTitle class="tw:text-xl tw:tracking-[-0.02em]">{{ preset.title }}</CardTitle>
              <span :class="cn('tw:size-5 tw:rounded-full', accentClasses[preset.accent])" aria-hidden="true" />
            </CardHeader>
            <CardContent class="tw:grid tw:min-h-0 tw:flex-1 tw:place-items-center tw:px-5 tw:pb-1">
              <img
                :src="preset.preview"
                alt=""
                class="tw:mx-auto tw:block tw:h-full tw:max-h-[30vh] tw:w-auto tw:object-contain tw:max-[1400px]:h-[120px] tw:max-[1400px]:max-h-[120px]"
              />
            </CardContent>
            <CardFooter class="tw:px-5 tw:pb-3 tw:pt-1">
              <Badge variant="secondary">{{ t(`kiosk.layouts.${preset.layout}`) }}</Badge>
            </CardFooter>
          </Card>
        </button>
      </div>
    </div>

    <Dialog v-model:open="dialogOpen">
      <DialogContent class="tw:max-w-xl" :show-close-button="!busy">
        <DialogHeader>
          <DialogTitle class="tw:text-3xl tw:tracking-[-0.025em]">
            {{
              busy
                ? t('kiosk.confirm.starting')
                : startError
                  ? t('kiosk.confirm.failed')
                  : t('kiosk.confirm.title', { title: selected?.title, count: selected?.captureCount })
            }}
          </DialogTitle>
          <DialogDescription class="tw:text-base">
            {{ busy ? t('kiosk.confirm.startingDescription') : startError || t('kiosk.confirm.description') }}
          </DialogDescription>
        </DialogHeader>
        <img v-if="selected" :src="selected.preview" alt="" class="tw:mx-auto tw:max-h-[42vh] tw:w-auto tw:max-w-full" />
        <DialogFooter class="tw:gap-3 tw:sm:gap-3">
          <Button variant="outline" size="lg" class="tw:min-h-14" :disabled="busy" @click="closeDialog">{{ t('kiosk.back') }}</Button>
          <Button size="lg" class="tw:min-h-14" :disabled="busy" @click="start">
            <LoaderCircle v-if="busy" data-icon="inline-start" class="tw:animate-spin" aria-hidden="true" />
            {{ startError ? t('kiosk.retry') : t('kiosk.confirm.action') }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </section>
</template>

<style scoped>
.kiosk-paper-texture {
  opacity: 0.2;
  background-image: radial-gradient(circle at 20% 30%, rgb(23 23 23 / 9%) 0 0.6px, transparent 0.8px);
  background-size: 9px 9px;
  mix-blend-mode: multiply;
}

.kiosk-admin-button {
  color: var(--kiosk-ink);
  background: transparent;
}

.kiosk-frame-card {
  display: flex;
  flex-direction: column;
  border: 0;
  box-shadow: 0 8px 26px rgb(23 23 23 / 10%);
}

@media (max-height: 760px) {
  .kiosk-attract-print {
    width: min(28vw, 300px);
  }
}
</style>
