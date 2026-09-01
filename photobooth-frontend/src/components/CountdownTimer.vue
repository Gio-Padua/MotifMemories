<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, shallowRef } from 'vue'

import { countdownState } from './countdown-timing'

interface Props {
  duration: number
  captureCueDuration?: number
  captureCueSafety?: number
  messageDuration?: number
  messageText?: string
}

const props = withDefaults(defineProps<Props>(), {
  captureCueDuration: 0,
  captureCueSafety: 0,
  messageDuration: 0.5,
  messageText: 'Smile!',
})

let intervalTimerId: number | undefined
let startedAt = 0
const elapsed = shallowRef(0)
const cueInstanceKey = Date.now()
const state = computed(() => countdownState(elapsed.value, props.duration, props.captureCueDuration, props.captureCueSafety, props.messageDuration))
const showBox = computed(() => state.value.phase !== 'done')
const showCountdown = computed(() => state.value.phase === 'countdown')
const showAnimatedCue = computed(() => state.value.phase === 'animated-cue')
const showStaticCue = computed(() => state.value.phase === 'static-cue')
const showLegacyMessage = computed(() => state.value.phase === 'legacy-message')
const progressValue = computed(() => Math.max(props.duration - elapsed.value, 0))

onMounted(() => {
  const preload = new Image()
  preload.src = '/kiosk/animated-smile.webp'
  startedAt = performance.now()
  intervalTimerId = window.setInterval(() => {
    elapsed.value = (performance.now() - startedAt) / 1000
    if (state.value.phase === 'done') clearInterval(intervalTimerId)
  }, 25)
})

onBeforeUnmount(() => clearInterval(intervalTimerId))
</script>

<template>
  <div v-show="showBox" id="countdown-timer-container" class="flex flex-center" style="width: 70vw; height: 70vh">
    <div v-if="showAnimatedCue || showStaticCue" id="countdown-timer-message" role="img" :aria-label="messageText">
      <img v-if="showAnimatedCue" :key="cueInstanceKey" class="animated-smile" src="/kiosk/animated-smile.webp" alt="" aria-hidden="true" />
      <img v-else class="static-smile" src="/kiosk/animated-smile-final.png" alt="" aria-hidden="true" />
      <img class="reduced-motion-smile" src="/kiosk/animated-smile-final.png" alt="" aria-hidden="true" />
    </div>
    <div v-else-if="showLegacyMessage" id="countdown-timer-message" role="img" :aria-label="messageText">
      {{ messageText }}
    </div>
    <div v-else style="height: 100%">
      <q-circular-progress
        id="countdown-circular-progress"
        v-show="showCountdown"
        show-value
        style="width: 100%; height: 100%; color: var(--kiosk-butter)"
        :value="progressValue"
        :min="0"
        :max="duration"
        reverse
        animation-speed="100"
        font-size="0.5em"
        size="70vh"
        class="countdown-progress"
        :thickness="0.16"
      >
        {{ state.number }}
      </q-circular-progress>
    </div>
  </div>
</template>

<style scoped>
#countdown-timer-container {
  pointer-events: none;
  user-select: none;
}

#countdown-timer-message {
  position: absolute;
  display: grid;
  place-items: center;
  color: var(--kiosk-butter);
  font-size: clamp(7rem, 16vw, 13rem);
  font-weight: 800;
}

#countdown-timer-message img {
  grid-area: 1 / 1;
  width: clamp(8rem, 18vw, 14rem);
  height: clamp(8rem, 18vw, 14rem);
}

.reduced-motion-smile {
  display: none;
}

.countdown-progress {
  font-weight: 800;
  opacity: 0.95;
  text-shadow: 0 2px 8px rgb(23 23 23 / 70%);
}

@media (prefers-reduced-motion: reduce) {
  .animated-smile,
  .static-smile {
    display: none;
  }

  .reduced-motion-smile {
    display: block;
  }
}
</style>
