import assert from 'node:assert/strict'
import test from 'node:test'

import { countdownState } from './countdown-timing.ts'

test('runs 10 through 2, then the full animated and static cue', () => {
  assert.deepEqual(countdownState(0, 10, 2.4, 0.3, 0.5), { phase: 'countdown', number: 10, total: 11.7 })
  assert.equal(countdownState(8.99, 10, 2.4, 0.3, 0.5).number, 2)
  assert.equal(countdownState(9, 10, 2.4, 0.3, 0.5).phase, 'animated-cue')
  assert.equal(countdownState(11.399, 10, 2.4, 0.3, 0.5).phase, 'animated-cue')
  assert.equal(countdownState(11.4, 10, 2.4, 0.3, 0.5).phase, 'static-cue')
  assert.equal(countdownState(11.699, 10, 2.4, 0.3, 0.5).phase, 'static-cue')
  assert.equal(countdownState(11.7, 10, 2.4, 0.3, 0.5).phase, 'done')
})
