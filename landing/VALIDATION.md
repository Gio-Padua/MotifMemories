# Landing page validation

Verified 10 September 2026 against a local **production build**.

## Production checks

| Check | Result |
| --- | --- |
| `pnpm check` | Pass: six layouts, capture counts, twin-strip duplication, placement bounds, reversible story-stage boundaries |
| `pnpm lint` | Pass |
| `pnpm typecheck` | Pass |
| `pnpm build` | Pass: statically prerendered home page |
| Visual finish review | **Pass — no material visual, accessibility, or product-truth findings** |
| Impeccable mechanical detector | Advisory token-ramp findings only; no blocking findings |

## Cold mobile Lighthouse results

Lighthouse 13.4.1, headless Microsoft Edge, default mobile simulated throttling. Each run starts a fresh browser. These are local lab measurements, not real-user field data or deployed-host measurements.

| Metric | Run 1 | Run 2 | Run 3 | Median | Target |
| --- | ---: | ---: | ---: | ---: | ---: |
| Performance | 98 | 98 | 98 | **98** | ≥90 |
| Accessibility | 100 | 100 | 100 | **100** | ≥95 |
| Best practices | 100 | 100 | 100 | **100** | — |
| SEO | 100 | 100 | 100 | **100** | — |
| LCP | 2.437 s | 2.426 s | 2.425 s | **2.426 s** | ≤2.5 s |
| CLS | 0 | 0 | 0 | **0** | ≤0.1 |
| Total blocking time | 20.5 ms | 40 ms | 20 ms | **20.5 ms** | ≤200 ms |
| Total initial transfer | 247,054 B | 247,054 B | 247,054 B | **247 KB** | ≤700 KB |

The original full-font implementation scored 88 with approximately 555 KB transferred and 3.98 s LCP. Subsetting the existing Inter font from approximately 346 KB to **37,428 bytes** removed the largest initial download. Explicit hero sizing eliminated an intermittent image layout shift.

## Image and 3D budgets

- Mobile hero source: **26,994 B**; desktop source: **67,250 B**. Actual responsive hero requests are further sized by Next.js.
- First-scene additional transfer observed on desktop: **483,400 B**, including other assets entering the viewport. It remains below the 1.5 MB deferred budget. Mobile skips the 3D runtime.
- No canvas or 3D enhancement initializes on the initial unscrolled load at 1440, 768, 390, or 320 px.
- No additional WebGL draw calls during the measured 800 ms desktop idle window after settling.
- No long tasks over 50 ms were observed during the tested forward/reverse scroll sequence. This is a bounded headless lab check, not a guarantee for every physical device.

## Browser scenarios

- No horizontal overflow at 1440×1000, 768×1024, 390×844, or 320×740; no overflow at 200% CSS zoom.
- All six choices update the selected frame. Desktop uses the single deferred canvas; mobile uses a static optimized preview and keeps the story in normal flow.
- Forward and reverse scrolling work; native scrolling remains available.
- Reduced motion, Save-Data, unavailable WebGL, failed texture loading, and WebGL context loss preserve the static poster.
- Without JavaScript, content, frame thumbnails, anchor navigation, and native FAQs remain available; the interactive-preview limitation is explained.
- Keyboard skip link, radio selection with arrow keys, and FAQ expansion with Space are checked.
- No uncaught application errors in the normal desktop/mobile flows.
- Full desktop, tablet, mobile, frame-explorer, and social-image layouts were visually inspected. The finished desktop collage retains every portrait after forward and reverse scrolling, and the mobile story no longer sticks to half the screen. Generated imagery is labeled illustrative; business details are not invented.

## Reproduce and handoff

Use the production server, then run `scripts/browser-check.mjs` with Playwright and `scripts/audit.mjs` with Playwright/Lighthouse as described in `README.md`. Raw reports and screenshots live locally in `.impeccable/review/` and are ignored by Git.

The website is not deployed. Set `SITE_URL` to the real HTTPS origin before deployment, then remeasure on the actual host/network. No live kiosk, real customer photos, booking, payment, or business-contact service is connected to this landing page. Original kiosk applications and root product/design documents were not modified.
