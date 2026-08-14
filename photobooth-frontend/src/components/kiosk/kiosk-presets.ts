export type KioskLayout = 'twin' | 'grid' | 'hero' | 'scrapbook' | 'six' | 'eight'

export type KioskFramePreset = {
  id: string
  actionName: string
  title: string
  layout: KioskLayout
  accent: 'blush' | 'butter' | 'mint' | 'lavender'
  preview: string
  captureCount: number
}

export type ResolvedKioskFramePreset = KioskFramePreset & { actionIndex: number }

type CollageAction = {
  name: string
  trigger: { ui_trigger: { show_button: boolean } }
  processing: { merge_definition: { predefined_image?: string | null; capture_index?: number | null }[] }
}

export const KIOSK_FRAME_PRESETS: readonly KioskFramePreset[] = [
  {
    id: 'four-strip-twin',
    actionName: 'kiosk-fourcut-stack',
    title: 'Four Strip ×2',
    layout: 'twin',
    accent: 'blush',
    preview: '/kiosk/previews/four-strip-twin.png',
    captureCount: 4,
  },
  {
    id: 'butter-grid',
    actionName: 'kiosk-fourcut-grid',
    title: 'Butter Grid',
    layout: 'grid',
    accent: 'butter',
    preview: '/kiosk/previews/butter-grid.png',
    captureCount: 4,
  },
  {
    id: 'mint-editorial',
    actionName: 'kiosk-fourcut-hero',
    title: 'Mint Editorial',
    layout: 'hero',
    accent: 'mint',
    preview: '/kiosk/previews/mint-editorial.png',
    captureCount: 4,
  },
  {
    id: 'lavender-scrapbook',
    actionName: 'kiosk-fourcut-scrapbook',
    title: 'Lavender Scrapbook',
    layout: 'scrapbook',
    accent: 'lavender',
    preview: '/kiosk/previews/lavender-scrapbook.png',
    captureCount: 4,
  },
  {
    id: 'mint-six-grid',
    actionName: 'kiosk-sixcut-grid',
    title: 'Six Moments',
    layout: 'six',
    accent: 'mint',
    preview: '/kiosk/previews/mint-six-grid.png',
    captureCount: 6,
  },
  {
    id: 'lavender-eight-grid',
    actionName: 'kiosk-eightcut-grid',
    title: 'Eight Story',
    layout: 'eight',
    accent: 'lavender',
    preview: '/kiosk/previews/lavender-eight-grid.png',
    captureCount: 8,
  },
]

export function resolveKioskPresets(actions: readonly CollageAction[]): ResolvedKioskFramePreset[] {
  return KIOSK_FRAME_PRESETS.flatMap(preset => {
    const actionIndex = actions.findIndex(action => action.name === preset.actionName)
    const action = actions[actionIndex]
    const placements = action?.processing.merge_definition.filter(item => !item.predefined_image) ?? []
    const indexedCaptures = placements.flatMap(item => (Number.isInteger(item.capture_index) ? [item.capture_index as number] : []))
    const captures = indexedCaptures.length === placements.length && indexedCaptures.length ? Math.max(...indexedCaptures) + 1 : placements.length

    return action?.trigger.ui_trigger.show_button && captures === preset.captureCount ? [{ ...preset, actionIndex }] : []
  })
}
