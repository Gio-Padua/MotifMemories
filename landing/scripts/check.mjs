import assert from 'node:assert/strict';
import { frames, storyStage } from '../lib/frames.mjs';

assert.equal(frames.length, 6);
assert.equal(new Set(frames.map(f => f.id)).size, 6);
assert.deepEqual(frames.map(f => f.count), [4, 4, 4, 4, 6, 8]);
for (const frame of frames) {
  assert.equal(new Set(frame.placements.map(p => p[5])).size, frame.count);
  for (const [x, y, w, h, , capture] of frame.placements) {
    assert.ok(x >= 0 && y >= 0 && x + w <= 1200 && y + h <= 1800);
    assert.equal(w / h, 4 / 3);
    assert.ok(capture >= 0 && capture < frame.count);
  }
}
assert.deepEqual(frames[0].placements.map(p => p[5]), [0, 0, 1, 1, 2, 2, 3, 3]);
assert.deepEqual(storyStage(-1), { assemble: 0, keep: 0 });
assert.deepEqual(storyStage(0.45), { assemble: 1, keep: 0 });
assert.deepEqual(storyStage(0.65), { assemble: 1, keep: 0 });
assert.deepEqual(storyStage(2), { assemble: 1, keep: 1 });
assert.ok(storyStage(0.8).keep > storyStage(0.7).keep);
console.log('Six frame layouts, twin capture mapping, and reversible story boundaries pass.');
