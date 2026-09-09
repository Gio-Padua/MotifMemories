# Motif Moments

A responsive self-photo booth discovery page. The first view is static HTML and an optimized image; one Three.js canvas progressively adds the native-scroll photo story. No kiosk service, database, or external asset host is required.

## Run

```sh
pnpm install
pnpm dev
```

Production preview:

```sh
pnpm build
pnpm start
```

Open http://localhost:3000. Set `SITE_URL` to the real HTTPS origin before a deployment build so social metadata uses the correct domain. The local default is `http://localhost:3000`. Business location, price, hours, and contact details remain intentionally unpublished.

## Checks

```sh
pnpm check
pnpm lint
pnpm typecheck
pnpm build
```

`scripts/browser-check.mjs` runs headless Edge checks with Playwright. `scripts/audit.mjs` performs three cold mobile Lighthouse runs against the production server. These are optional review tools, not production dependencies. Install Playwright and Lighthouse in a separate tooling directory and set `PLAYWRIGHT_MODULE` and `LIGHTHOUSE_MODULE` to their module URLs, or make the packages available to Node. Reports and screenshots are saved in `.impeccable/review/`.

## Local assets

- `assets/originals/`: eight generated source photographs; not exposed by the site.
- `assets/manifest.json`: generation provenance and prompts.
- `lib/frames.mjs`: exact kiosk layout placements, including duplicated strip captures.
- `public/images/`: optimized portraits, completed collages, thumbnails, textures, and hero.
- `assets/fonts/inter-latin.woff2`: English subset of the existing Inter variable font; variable weights are preserved. Original OFL license is served alongside the font.

Run `pnpm assets` to regenerate delivery images using Sharp and the existing sibling kiosk overlays. No image-generation API call is needed for this step. To regenerate the font subset, install build-only `fonttools[woff]` and run `python scripts/subset-font.py`, then `pnpm assets`. Extend the subset when adding new language characters.

See `AGENTS.md` for project constraints, `DESIGN.md` for the implemented website design, and `VALIDATION.md` for measured results.
