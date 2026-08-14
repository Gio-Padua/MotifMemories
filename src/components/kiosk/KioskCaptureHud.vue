<script setup lang="ts">
import { computed } from 'vue'
import { LoaderCircle } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

const props = defineProps<{
  capturesTaken: number
  totalCaptures: number
  processing: boolean
}>()

const { t } = useI18n()
const photoNumber = computed(() => Math.min(props.capturesTaken + 1, props.totalCaptures))
const progress = computed(() => (props.capturesTaken / props.totalCaptures) * 100)
</script>

<template>
  <div class="kiosk-shell tw:pointer-events-none tw:absolute tw:inset-0 tw:z-10 tw:bg-transparent">
    <div
      v-if="processing"
      class="tw:grid tw:h-full tw:place-items-center tw:bg-[color-mix(in_srgb,var(--kiosk-paper)_90%,transparent)] tw:p-8 tw:text-center"
    >
      <div>
        <LoaderCircle class="tw:mx-auto tw:size-16 tw:animate-spin" aria-hidden="true" />
        <h1 class="tw:mt-7 tw:text-[clamp(2.5rem,5vw,5rem)] tw:font-semibold tw:tracking-[-0.035em]">{{ t('kiosk.capture.processing') }}</h1>
        <p class="tw:mt-3 tw:text-xl tw:text-muted-foreground">{{ t('kiosk.capture.processingDescription') }}</p>
      </div>
    </div>

    <div
      v-else
      class="tw:absolute tw:left-1/2 tw:top-7 tw:w-[min(640px,calc(100%-3rem))] tw:-translate-x-1/2 tw:rounded-2xl tw:bg-[color-mix(in_srgb,var(--kiosk-paper)_92%,transparent)] tw:px-7 tw:py-5 tw:shadow-[0_12px_34px_rgba(23,23,23,0.18)] tw:backdrop-blur-sm"
    >
      <div class="tw:mb-3 tw:flex tw:items-center tw:justify-between tw:gap-5">
        <h1 class="tw:text-2xl tw:font-semibold tw:tracking-[-0.025em]">
          {{ t('kiosk.capture.progress', { current: photoNumber, total: totalCaptures }) }}
        </h1>
        <Badge variant="secondary">{{ t('kiosk.capture.stayReady') }}</Badge>
      </div>
      <Progress :model-value="progress" class="tw:h-3" />
    </div>
  </div>
</template>
