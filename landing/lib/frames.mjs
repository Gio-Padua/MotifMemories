// Placement coordinates match the kiosk's install-kiosk-presets.py; no runtime kiosk dependency.
const grid = (xs, ys) => ys.flatMap((y, row) => xs.map((x, col) => [x, y, 520, 390, 0, row * xs.length + col]));
export const frames = [
  { id: 'four-strip-twin', title: 'Four Strip ×2', count: 4, color: '#F4B8C2', description: 'One for you. One for your person.', placements: [50, 445, 840, 1235].flatMap((y, i) => [40, 640].map(x => [x, y, 520, 390, 0, i])) },
  { id: 'butter-grid', title: 'Butter Grid', count: 4, color: '#F4D77A', description: 'Four little moments, perfectly together.', placements: grid([60, 620], [260, 700]) },
  { id: 'mint-editorial', title: 'Mint Editorial', count: 4, color: '#BFD8C2', description: 'A main-character moment. And the outtakes.', placements: [[80, 80, 1040, 780, 0, 0], ...[80, 440, 800].map((x, i) => [x, 910, 320, 240, 0, i + 1])] },
  { id: 'lavender-scrapbook', title: 'Lavender Scrapbook', count: 4, color: '#C8BCE8', description: 'A little less perfect. A little more you.', placements: [[70, 140, 500, 375, -4, 0], [620, 190, 500, 375, 3, 1], [100, 620, 500, 375, 4, 2], [630, 690, 500, 375, -3, 3]] },
  { id: 'mint-six-grid', title: 'Six Moments', count: 6, color: '#BFD8C2', description: 'More room for every side of you.', placements: grid([60, 620], [90, 520, 950]) },
  { id: 'lavender-eight-grid', title: 'Eight Story', count: 8, color: '#C8BCE8', description: 'For the moments that need a whole story.', placements: grid([60, 620], [45, 445, 845, 1245]) },
];

export const clamp = (value, min = 0, max = 1) => Math.min(max, Math.max(min, value));
export function storyStage(progress) {
  const p = clamp(progress);
  return { assemble: clamp(p / 0.45), keep: clamp((p - 0.65) / 0.35) };
}
