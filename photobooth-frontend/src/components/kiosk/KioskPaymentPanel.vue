<script setup lang="ts">
import { computed } from 'vue'
import { Banknote, Camera, CircleAlert, Cloud, HardDrive, KeyRound, Printer, Settings } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import type { KioskState } from '@/stores/main-store'

const props = defineProps<{ state: KioskState | null }>()
const emit = defineEmits<{ operatorTap: []; operatorOpen: [] }>()
const { t } = useI18n()

const credit = computed(() => props.state?.session?.credit ?? 0)
const price = computed(() => props.state?.price ?? 200)
const progress = computed(() => Math.min((credit.value / price.value) * 100, 100))
const partial = computed(() => props.state?.session?.state === 'collecting')
const paidButPaused = computed(() => props.state?.session?.state === 'paid' && props.state.session.mode === 'paid')
const unavailable = computed(() => !props.state?.payment_enabled || !props.state?.readiness.ready)
const checks = computed(() => [
  { key: 'camera', icon: Camera, ok: props.state?.readiness.camera },
  { key: 'printer', icon: Printer, ok: props.state?.readiness.printer },
  { key: 'disk', icon: HardDrive, ok: props.state?.readiness.disk },
  { key: 'cloud', icon: Cloud, ok: props.state?.readiness.cloud },
  { key: 'payment_hardware', icon: Banknote, ok: props.state?.readiness.payment_hardware },
  { key: 'password_changed', icon: KeyRound, ok: props.state?.readiness.password_changed },
])
</script>

<template>
  <section
    class="kiosk-shell tw:relative tw:grid tw:h-dvh tw:min-h-[640px] tw:grid-cols-[minmax(0,1.15fr)_minmax(380px,0.85fr)] tw:items-center tw:overflow-hidden tw:px-[clamp(3rem,8vw,10rem)] tw:py-[clamp(2rem,7vh,6rem)]"
  >
    <div class="kiosk-paper-texture tw:pointer-events-none tw:absolute tw:inset-0" aria-hidden="true" />
    <button
      class="tw:absolute tw:right-5 tw:top-5 tw:z-10 tw:grid tw:size-14 tw:place-items-center tw:rounded-full tw:opacity-0 focus:tw:opacity-100"
      type="button"
      :aria-label="t('kiosk.admin')"
      @click="emit('operatorTap')"
    >
      <Settings aria-hidden="true" />
    </button>

    <div class="tw:relative tw:max-w-4xl">
      <div class="tw:mb-8 tw:flex tw:items-center tw:gap-5">
        <img src="/icons/mm-logo-sm.webp" alt="" class="tw:size-16 tw:shrink-0 tw:object-contain" aria-hidden="true" />
        <div>
          <p class="tw:text-3xl tw:font-semibold tw:tracking-[-0.03em]">{{ t('kiosk.brand.name') }}</p>
          <p class="tw:text-lg tw:text-muted-foreground">{{ t('kiosk.brand.tagline') }}</p>
        </div>
      </div>
      <div class="tw:mb-8 tw:flex tw:gap-4" aria-hidden="true">
        <span class="tw:h-3 tw:w-24 tw:bg-[var(--kiosk-blush)]" /><span class="tw:h-3 tw:w-14 tw:bg-[var(--kiosk-butter)]" /><span
          class="tw:h-3 tw:w-8 tw:bg-[var(--kiosk-mint)]"
        />
      </div>
      <h1 class="tw:max-w-[11ch] tw:text-[clamp(4rem,7vw,6rem)] tw:font-semibold tw:leading-[0.9] tw:tracking-[-0.04em]">{{
        unavailable ? t('kiosk.payment.lockedTitle') : t('kiosk.payment.title', { amount: price })
      }}</h1>
      <p class="tw:mt-7 tw:max-w-[38ch] tw:text-[clamp(1.2rem,1.8vw,2rem)] tw:leading-relaxed tw:text-muted-foreground">{{
        unavailable ? t('kiosk.payment.lockedDescription') : t('kiosk.payment.description')
      }}</p>
      <p v-if="!unavailable" class="tw:mt-5 tw:text-lg tw:font-semibold">{{ t('kiosk.payment.noChange') }}</p>
      <div v-if="!unavailable" class="tw:mt-8 tw:flex tw:flex-wrap tw:gap-3">
        <Badge v-for="bill in state?.denominations ?? []" :key="bill" variant="outline" class="tw:px-5 tw:py-3 tw:text-lg">₱{{ bill }}</Badge>
      </div>
    </div>

    <div
      class="kiosk-payment-card tw:relative tw:justify-self-end tw:w-full tw:max-w-[520px] tw:rounded-2xl tw:bg-card tw:p-[clamp(2rem,4vw,4rem)] tw:shadow-[12px_20px_46px_rgba(23,23,23,0.16)]"
    >
      <template v-if="unavailable">
        <CircleAlert class="tw:mb-7 tw:size-14" aria-hidden="true" />
        <h2 class="tw:text-[clamp(2.2rem,4vw,4.4rem)] tw:font-semibold tw:leading-none tw:tracking-[-0.035em]">{{
          t('kiosk.payment.setupTitle')
        }}</h2>
        <p class="tw:mt-5 tw:text-xl tw:leading-relaxed tw:text-muted-foreground">{{ t('kiosk.payment.setupDescription') }}</p>
        <div class="tw:mt-8 tw:grid tw:grid-cols-2 tw:gap-3">
          <div v-for="check in checks" :key="check.key" class="tw:flex tw:min-h-14 tw:items-center tw:gap-3 tw:text-base">
            <component :is="check.icon" class="tw:size-5" aria-hidden="true" />
            <span>{{ t(`kiosk.operator.checks.${check.key}`) }}: {{ t(`kiosk.operator.status.${check.ok ? 'ready' : 'notReady'}`) }}</span>
          </div>
        </div>
        <p v-if="partial" class="tw:mt-5 tw:text-base tw:font-semibold" role="status">
          {{ t('kiosk.payment.pausedCredit', { amount: credit, seconds: state?.session?.seconds_remaining ?? 0 }) }}
        </p>
        <p v-else-if="paidButPaused" class="tw:mt-5 tw:text-base tw:font-semibold" role="status">
          {{ t('kiosk.payment.paidCreditSafe', { amount: credit }) }}
        </p>
        <Button size="lg" class="tw:mt-9 tw:min-h-16 tw:w-full tw:text-lg" @click="emit('operatorOpen')">{{
          t('kiosk.payment.operatorAction')
        }}</Button>
      </template>
      <template v-else>
        <p class="tw:text-xl tw:text-muted-foreground">{{ partial ? t('kiosk.payment.remaining') : t('kiosk.payment.price') }}</p>
        <p class="tw:mt-3 tw:text-[clamp(5rem,8vw,8rem)] tw:font-semibold tw:leading-none tw:tracking-[-0.04em]"
          >₱{{ partial ? state?.session?.remaining_balance : price }}</p
        >
        <Progress :model-value="progress" class="tw:mt-9 tw:h-4" />
        <div class="tw:mt-6 tw:flex tw:items-baseline tw:justify-between tw:gap-6">
          <span class="tw:text-lg">{{ t('kiosk.payment.inserted', { amount: credit }) }}</span>
          <span v-if="state?.session?.seconds_remaining" class="tw:text-lg tw:font-semibold tw:tabular-nums">{{
            t('kiosk.payment.expires', { seconds: state.session.seconds_remaining })
          }}</span>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
@media (max-height: 760px) {
  .kiosk-payment-card {
    padding: 1rem;
  }
}
</style>
