# Motif Moments

## Product intent

Motif Moments is an offline-first, touch-friendly paid kiosk built on Photobooth-App. Its guest promise is **“Make it a motif. Keep the memory.”** It preserves the existing Vue, Quasar, Pinia, SSE, camera, collage, gallery, and printing pipeline while providing an original Korean self-photo-studio experience.

The product is a single-terminal booth with curated 4-, 6-, and 8-photo layouts and one included print. Completed kiosk collages upload to a public Supabase bucket for direct QR download and are deleted after seven days. Accounts, a frame editor, optical cash authentication, and 360 video remain separate products.

## Users and journey

- **Guest:** inserts cash, selects one frame, takes uninterrupted photos, reviews the finished collage, then prints or scans a QR code.
- **Operator:** commissions, tests, and recovers camera, printer, sharing, payment, and storage through the existing administration.

`Insert configured price (₱200 default) → choose frame → confirm frame → take 4, 6, or 8 photos → review (Keep / Retake) → choose look → print/QR/done`

Review means the completed collage, never individual captures.

## Locked behavior

- Primary display: 1920×1080 landscape; fallback: 1280×720.
- Six curated collage actions resolve by stable backend action name, never numeric index.
- Every result uses a 1200×1800 portrait canvas and approximately 4:3 landscape photo windows.
- Every kiosk capture shows `10…2`, plays one complete 2.4-second smile cue, holds its final frame for 0.3 seconds, and only then opens the shutter. There is no per-photo approval or individual gallery entry.
- The attract screen accepts ₱50, ₱100, and ₱200 notes toward a configurable session price (`kiosk.price_php`, ₱200 by default). Partial credit expires after 90 seconds; overpayment receives no change.
- Payment entitlement is stored in SQLite and survives reloads/restarts. Failed capture starts do not consume it.
- One complete retake and one print are included. Keep these photos permanently closes retake. Filters follow Keep; only the confirmed final JPEG is printable and published.
- Looks: Original, Soft, Warm, and Mono. One look applies to all photo windows; frame artwork, text, and background keep their colors. Sources and previews remain local.
- Paid operation requires camera, printer, 2 GiB free disk, public customer-result storage, a changed admin password, and qualified payment hardware.
- The hidden five-tap operator dialog issues a memory-only four-hour test grant. Test mode requires the camera but bypasses payment, printer, and cloud readiness.
- Guest delivery includes one print and a QR code that points directly to a forced-download Supabase public URL; no customer website is required.
- Kiosk result IDs, local files, and public cloud objects are retained for seven days. Public URLs do not expire before cleanup.
- Frame selection resets after 45 seconds. Review closes after 30 seconds without automatically keeping or uploading the result. Filter selection confirms the selected look after 30 seconds of inactivity (Original by default), warning in the last 10 seconds. Delivery closes after 30 idle seconds; active rendering, printing, and QR polling pause the timer.
- Missing kiosk actions show `Operator code: KIOSK-C06`.

## Curated frames

| Backend action | Guest title | Captures | Layout |
|---|---|---:|---|
| `kiosk-fourcut-stack` | Four Strip ×2 | 4 | Two matching 2×6 strips |
| `kiosk-fourcut-grid` | Butter Grid | 4 | 2×2 grid |
| `kiosk-fourcut-hero` | Mint Editorial | 4 | One hero and three small windows |
| `kiosk-fourcut-scrapbook` | Lavender Scrapbook | 4 | Four rotated windows |
| `kiosk-sixcut-grid` | Six Moments | 6 | 2×3 grid |
| `kiosk-eightcut-grid` | Eight Story | 8 | 2×4 grid |

## Deployment boundaries

- The TB74 production driver is blocked until the purchased Philippine model, firmware, interface, harness, pulse map, and inhibit polarity are electrically qualified. `payment_enabled=false` is the shipping default and remains required until the TB74, changed admin password, camera, printer, disk, and cloud checks are all healthy.
- A banknote vision model may be advisory only and can never grant credit.
- Supabase uses the public `photobooth-testloc` bucket and server-side rclone S3 credentials. Only kept, filter-finalized paid/test kiosk JPEGs upload; ordinary gallery media, rejected sets, previews, and source captures remain local. Customer accounts, Supabase Auth, BetterAuth, custom domains, refunds/change, vouchers, and optical cash authentication are not included.
