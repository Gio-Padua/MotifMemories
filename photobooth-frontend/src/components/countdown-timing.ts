export type CountdownPhase = 'countdown' | 'animated-cue' | 'static-cue' | 'legacy-message' | 'done'

export function countdownState(
  elapsed: number,
  duration: number,
  cueDuration: number,
  cueSafety: number,
  legacyMessageDuration: number
): { phase: CountdownPhase; number: number | null; total: number } {
  if (cueDuration > 0) {
    const numericDuration = Math.max(duration - 1, 0)
    const total = Number((numericDuration + cueDuration + cueSafety).toFixed(3))
    if (elapsed < numericDuration) return { phase: 'countdown', number: Math.ceil(duration - elapsed), total }
    if (elapsed < numericDuration + cueDuration) return { phase: 'animated-cue', number: null, total }
    if (elapsed < total) return { phase: 'static-cue', number: null, total }
    return { phase: 'done', number: null, total }
  }

  if (elapsed >= duration) return { phase: 'done', number: null, total: duration }
  if (duration - elapsed <= legacyMessageDuration) return { phase: 'legacy-message', number: null, total: duration }
  return { phase: 'countdown', number: Math.ceil(duration - elapsed), total: duration }
}
