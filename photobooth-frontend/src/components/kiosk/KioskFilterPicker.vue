<script setup lang="ts">
import { computed, ref, shallowRef, watch } from 'vue'
import { ToggleGroupItem, ToggleGroupRoot } from 'reka-ui'
import { Check, LoaderCircle } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { Button } from '@/components/ui/button'

export type KioskFilterOption = { id: string; label: string; preview_url: string }
const props = defineProps<{ options: KioskFilterOption[]; loading: boolean; busy: boolean; error: string | null }>()
const emit = defineEmits<{ select: [filter: string, preview: string | null]; confirm: [filter: string] }>()
const { t } = useI18n()
const selected = shallowRef('original')
const visibleCount = shallowRef(2)
const settled = ref<Record<string, boolean>>({})
const failed = ref<Record<string, boolean>>({})
const choice = computed(() => props.options.find(option => option.id === selected.value))
const originalReady = computed(() => Boolean(settled.value.original && !failed.value.original))

watch(
  [selected, settled],
  () => {
    emit('select', selected.value, choice.value && settled.value[selected.value] && !failed.value[selected.value] ? choice.value.preview_url : null)
  },
  { deep: true, immediate: true }
)

function loaded(id: string, success: boolean) {
  if (settled.value[id]) return
  settled.value[id] = true
  failed.value[id] = !success
  visibleCount.value++
  if (!success && selected.value === id) selected.value = 'original'
}

function choose(value: unknown) {
  if (typeof value === 'string' && value) selected.value = value
}
</script>

<template>
  <section class="kiosk-filter-picker" aria-labelledby="filter-title" :aria-busy="loading || busy">
    <h1 id="filter-title">{{ t('kiosk.filters.title') }}</h1>
    <p>{{ t('kiosk.filters.description') }}</p>
    <div v-if="loading && options.length === 0" class="kiosk-filter-loading" role="status">
      <LoaderCircle class="tw:size-9 tw:animate-spin" aria-hidden="true" />
      <span>{{ t('kiosk.filters.loading') }}</span>
    </div>
    <ToggleGroupRoot
      v-else
      type="single"
      :model-value="selected"
      class="kiosk-filter-options"
      :disabled="loading || busy"
      aria-labelledby="filter-title"
      @update:model-value="choose"
    >
      <ToggleGroupItem
        v-for="(option, index) in options"
        :key="option.id"
        :value="option.id"
        class="kiosk-filter-option"
        :disabled="loading || busy || (option.id !== 'original' && (!settled[option.id] || failed[option.id]))"
      >
        <span class="kiosk-filter-thumbnail">
          <img
            v-if="index < visibleCount && !failed[option.id]"
            :src="option.preview_url"
            alt=""
            width="100"
            height="150"
            @load="loaded(option.id, true)"
            @error="loaded(option.id, false)"
          />
          <span v-if="failed[option.id]">{{ t('kiosk.filters.previewUnavailable') }}</span>
          <LoaderCircle v-else-if="!settled[option.id]" class="tw:size-6 tw:animate-spin" aria-hidden="true" />
        </span>
        <span class="kiosk-filter-label"
          >{{ t(`kiosk.filters.looks.${option.id}`) }}<Check v-if="selected === option.id" class="tw:size-5" aria-hidden="true"
        /></span>
      </ToggleGroupItem>
    </ToggleGroupRoot>
    <p v-if="error" role="alert" class="tw:text-destructive">{{ error }}</p>
    <div class="tw:flex tw:gap-3">
      <Button size="lg" class="tw:min-h-14 tw:flex-1" :disabled="loading || busy || !originalReady" @click="emit('confirm', selected)">
        <LoaderCircle v-if="busy" data-icon="inline-start" class="tw:animate-spin" aria-hidden="true" />
        {{ t(error ? 'kiosk.retry' : 'kiosk.filters.confirm') }}
      </Button>
      <Button v-if="error" variant="outline" size="lg" class="tw:min-h-14" :disabled="busy" @click="emit('confirm', 'original')">{{
        t('kiosk.filters.useOriginal')
      }}</Button>
    </div>
  </section>
</template>

<style scoped>
.kiosk-filter-picker {
  display: flex;
  flex-direction: column;
  min-width: 0;
  gap: 0.875rem;
  max-width: 34rem;
}
.kiosk-filter-picker h1 {
  margin: 0;
  font-size: clamp(2.25rem, 3.5vw, 4rem);
  line-height: 1.05;
  letter-spacing: -0.03em;
}
.kiosk-filter-picker p {
  margin: 0;
  font-size: 1rem;
  line-height: 1.5;
}
.kiosk-filter-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}
.kiosk-filter-loading {
  display: grid;
  min-height: 18rem;
  place-items: center;
  align-content: center;
  gap: 0.75rem;
  border-radius: var(--kiosk-panel-radius);
  background: var(--kiosk-white);
}
.kiosk-filter-option {
  display: flex;
  min-width: 0;
  min-height: 8.5rem;
  flex-direction: row;
  align-items: center;
  gap: 0.75rem;
  padding: 0.625rem;
  border: 2px solid transparent;
  border-radius: 12px;
  background: var(--kiosk-white);
  color: var(--kiosk-ink);
  cursor: pointer;
  transition:
    background-color 180ms ease-out,
    border-color 180ms ease-out;
}
.kiosk-filter-option[data-state='on'] {
  background: var(--kiosk-butter);
  border-color: var(--kiosk-ink);
}
.kiosk-filter-option:disabled {
  cursor: default;
  opacity: 0.65;
}
.kiosk-filter-thumbnail {
  display: grid;
  width: clamp(72px, 6.5vw, 92px);
  height: clamp(108px, 9.75vw, 138px);
  flex: 0 0 auto;
  overflow: hidden;
  border-radius: 8px;
  background: var(--kiosk-paper);
  place-items: center;
}
.kiosk-filter-thumbnail > * {
  grid-area: 1 / 1;
}
.kiosk-filter-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}
.kiosk-filter-label {
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  min-height: 1.5rem;
}
@media (max-width: 1000px) {
  .kiosk-filter-picker {
    max-width: none;
    gap: 0.625rem;
  }
  .kiosk-filter-picker h1 {
    font-size: clamp(2rem, 5vw, 2.75rem);
  }
  .kiosk-filter-option {
    min-height: 6.75rem;
    padding: 0.5rem;
  }
  .kiosk-filter-thumbnail {
    width: 60px;
    height: 90px;
  }
  .kiosk-filter-loading {
    min-height: 12rem;
  }
}
@media (prefers-reduced-motion: reduce) {
  .kiosk-filter-option {
    transition: none;
  }
}
</style>
