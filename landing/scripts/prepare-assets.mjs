import sharp from 'sharp';
import { mkdir, copyFile, readFile, writeFile, stat } from 'node:fs/promises';
import { resolve } from 'node:path';
import { frames } from '../lib/frames.mjs';

const root = resolve(import.meta.dirname, '..');
const out = resolve(root, 'public/images');
await mkdir(out, { recursive: true });
await mkdir(resolve(root, 'public/fonts'), { recursive: true });
await copyFile(resolve(root, 'assets/fonts/inter-latin.woff2'), resolve(root, 'public/fonts/inter-variable.woff2'));
await copyFile(resolve(root, '../photobooth-frontend/src/css/fonts/Inter-4.0/LICENSE.txt'), resolve(root, 'public/fonts/OFL.txt'));
const portraits = [];
for (let i = 1; i <= 8; i++) {
  const input = resolve(root, `assets/originals/portrait-${i}.png`);
  portraits.push(await sharp(input).resize(1040, 780, { fit: 'cover' }).png().toBuffer());
  await sharp(input).resize(640, 480, { fit: 'cover' }).webp({ quality: 76 }).toFile(resolve(out, `portrait-${i}.webp`));
}
for (const frame of frames) {
  const photos = [];
  for (const [x, y, width, height, angle, capture] of frame.placements) {
    const image = await sharp(portraits[capture]).resize(width, height).rotate(-angle, { background: '#00000000' }).png().toBuffer({ resolveWithObject: true });
    photos.push({ input: image.data, left: Math.round(x - (image.info.width - width) / 2), top: Math.round(y - (image.info.height - height) / 2) });
  }
  const overlay = await readFile(resolve(root, `../photobooth-frontend/public/kiosk/frames/${frame.id}.png`));
  const collage = await sharp({ create: { width: 1200, height: 1800, channels: 4, background: '#F7F3EB' } }).composite([...photos, { input: overlay }]).png().toBuffer();
  await sharp(collage).webp({ quality: 85 }).toFile(resolve(out, `${frame.id}.webp`));
  for (const [name, height] of [['mobile', 1024], ['desktop', 1536], ['thumb', 240]]) {
    await sharp(collage).resize({ height }).webp({ quality: name === 'thumb' ? 65 : 76 }).toFile(resolve(out, `${frame.id}-${name}.webp`));
  }
}
// The hero is one delivered image, instead of multiple eager image requests.
const large = await sharp(portraits[0]).resize(650, 490).extend({ top: 20, left: 20, right: 20, bottom: 100, background: '#FFFDFA' }).rotate(-7, { background: '#00000000' }).png().toBuffer();
const strip = await sharp(resolve(out, 'four-strip-twin.webp')).extract({ left: 0, top: 0, width: 600, height: 1800 }).resize({ height: 840 }).rotate(12, { background: '#00000000' }).png().toBuffer();
const card = await sharp(resolve(out, 'mint-editorial.webp')).resize({ height: 600 }).rotate(15, { background: '#00000000' }).png().toBuffer();
const hero = await sharp({ create: { width: 1200, height: 1100, channels: 4, background: '#F7F3EB' } }).composite([{ input: card, left: 570, top: 40 }, { input: large, left: 20, top: 280 }, { input: strip, left: 730, top: 150 }]).png().toBuffer();
await sharp(hero).resize(1200).webp({ quality: 82 }).toFile(resolve(out, 'hero.webp'));
await sharp(hero).resize(700).webp({ quality: 76 }).toFile(resolve(out, 'hero-mobile.webp'));
const svg = await readFile(resolve(root, 'assets/social-type.svg'));
await sharp(svg).composite([{ input: await sharp(hero).resize(520, 477).png().toBuffer(), left: 680, top: 120 }]).jpeg({ quality: 85 }).toFile(resolve(root, 'app/opengraph-image.jpg'));
const budgets = {};
for (const file of ['hero.webp', 'hero-mobile.webp', 'four-strip-twin-mobile.webp', 'four-strip-twin-desktop.webp']) budgets[file] = (await stat(resolve(out, file))).size;
await writeFile(resolve(root, 'assets/sizes.json'), JSON.stringify(budgets, null, 2) + '\n');
console.log(budgets);
