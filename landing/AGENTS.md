<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# Motif Moments landing page

## Scope and source of truth

- This is the public discovery site, built with Next.js App Router, TypeScript, React, Tailwind v4, and pnpm. Read the installed Next.js guides for the APIs you change.
- Read `../PRODUCT.md` for product facts and `../DESIGN.md` for brand rules. Kiosk Vue/Quasar architecture and payment/display rules do not apply to this site. Do not change the kiosk applications while working here.
- Primary CTA: **Explore the frames**. Do not invent a price, address, hours, contacts, booking service, testimonials, launch status, or registered trademark claim.
- English copy. Actual six frames, one print, one full retake before printing, direct QR downloads retained seven days. This site neither captures nor processes customer photos.

## Approved visual direction

- **From pose to print**: loose photographs assemble into a real frame, then become a keepsake as visitors scroll. Persuade mode; composition selected by the user (surface seed `0f2aff48`).
- Paper `#F7F3EB`, Ink `#171717`, Blush `#F4B8C2`, Butter `#F4D77A`, Mint `#BFD8C2`, Lavender `#C8BCE8`, White `#FFFDFA`. Local Inter variable font. Pastels are surfaces, not body text.
- Editorial spacing, large crisp typography, simple sticker geometry, real sample imagery. Controls use 12–16px radii and minimum 56px targets. Preserve native scrolling and visible focus.
- Root `DESIGN.md` belongs to the kiosk; record website-specific decisions in `landing/DESIGN.md`.

## Assets and components

- `lib/frames.mjs` mirrors exact kiosk frame placement geometry; reuse it for composition, controls, and animation. Keep Four Strip ×2's duplicated capture mapping.
- Eight AI-generated originals and their provenance are under `assets/`; only optimized delivery images belong in `public/images/`. Never imply illustrative subjects are customers. Use built-in Imagegen for new photography.
- `pnpm assets` builds the six exact 1200×1800 sample collages, responsive textures, hero, local font, and social image using Sharp. Originals are local and outside public routes.
- Server-render content. Keep interaction in small client boundaries; one dynamically imported Fiber v9 canvas. No CMS, customer backend, smooth-scroll library, autoplay video, external fonts, or extra animation framework.

## Performance and resilience

- First view is complete HTML plus one dimensioned, eager, high-priority hero. Use accurate `next/image` sizes; lazy-load remaining imagery.
- Defer 3D until the hero is loaded and the story is near the viewport; initialize during idle time with a bounded fallback. Keep the poster until the first successful frame.
- Mobile hero ≤200KB, initial transfer before 3D ≤700KB, deferred runtime plus first-scene textures ≤1.5MB compressed. Measure production output rather than guessing from source sizes.
- Skip WebGL on screens up to 700px and use the selected optimized collage preview. Above 700px, cap pixel ratio at 1.5 and texture long edges at 1536px. No real-time shadow maps or postprocessing. Load selected textures on demand.
- Use refs for scroll progress and imperative Three.js objects. Render on demand, stop when idle/offscreen/hidden, and dispose resources/listeners on teardown.
- Reduced motion, Save-Data, failed textures, and WebGL failure/context loss retain usable static previews. HTML content and frame thumbnails work without JavaScript.

## Verification

- Run `pnpm check`, `pnpm lint`, `pnpm typecheck`, and `pnpm build`.
- Inspect production at 1440px, 768px, 390px, 320px, and 200% zoom. Verify keyboard operation, frame selection, reverse scroll, all CTAs, reduced motion, no JavaScript, and WebGL failure.
- Run three cold Lighthouse mobile audits and report median lab results: performance ≥90, accessibility ≥95, LCP ≤2.5s, CLS ≤0.1, TBT ≤200ms. Also check transferred bytes and idle rendering.
- Complete a bounded visual review. Record actual results and remaining limits in `VALIDATION.md`. Deployment is a separate task.
