// @ts-expect-error Node provides this built-in at test runtime; app typecheck intentionally excludes this file.
import assert from 'node:assert/strict'
// @ts-expect-error Node provides this built-in at test runtime; app typecheck intentionally excludes this file.
import test from 'node:test'
import { KIOSK_FRAME_PRESETS, resolveKioskPresets } from './kiosk-presets.ts'

const action = (name: string, captures: number, visible = true, captureIndexes?: number[]) => ({
  name,
  trigger: { ui_trigger: { show_button: visible } },
  processing: {
    merge_definition: captureIndexes
      ? captureIndexes.map(capture_index => ({ predefined_image: null, capture_index }))
      : Array.from({ length: captures }, () => ({ predefined_image: null })),
  },
})

test('resolves variable capture counts and duplicated strip placements after reordering', () => {
  const reordered = [...KIOSK_FRAME_PRESETS]
    .reverse()
    .map(preset => action(preset.actionName, preset.captureCount, true, preset.layout === 'twin' ? [0, 0, 1, 1, 2, 2, 3, 3] : undefined))
  const resolved = resolveKioskPresets(reordered)

  assert.deepEqual(
    resolved.map(preset => preset.actionIndex),
    [5, 4, 3, 2, 1, 0]
  )
  assert.equal(new Set(resolved.map(preset => preset.id)).size, 6)
  assert.equal(new Set(resolved.map(preset => preset.actionIndex)).size, 6)
})

test('omits missing, hidden, predefined-only, and wrong-capture-count actions', () => {
  const [stack, grid, hero] = KIOSK_FRAME_PRESETS
  const resolved = resolveKioskPresets([
    action(stack.actionName, 4, false),
    action(grid.actionName, 3),
    {
      ...action(hero.actionName, 4),
      processing: { merge_definition: Array.from({ length: 4 }, () => ({ predefined_image: 'frame.png' })) },
    },
  ])

  assert.deepEqual(resolved, [])
})
