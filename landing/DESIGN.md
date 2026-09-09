---
name: Motif Moments landing page
description: Make it a motif. Keep the memory.
colors:
  paper: "#f7f3eb"
  ink: "#171717"
  blush: "#f4b8c2"
  butter: "#f4d77a"
  mint: "#bfd8c2"
  lavender: "#c8bce8"
  white: "#fffdfa"
  muted: "#605b53"
  line: "#d8d2c8"
  accent-word: "#655770"
  scene-disc: "#e9e1ef"
typography:
  display:
    fontFamily: "Inter, sans-serif"
    fontSize: "clamp(64px, 6.65vw, 96px)"
    fontWeight: 600
    lineHeight: 0.98
    letterSpacing: "-0.04em"
  headline:
    fontFamily: "Inter, sans-serif"
    fontSize: "clamp(38px, 4.3vw, 62px)"
    fontWeight: 550
    lineHeight: 1.06
    letterSpacing: "-0.04em"
  title:
    fontFamily: "Inter, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "16px"
    lineHeight: 1.75
rounded:
  control: "12px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    rounded: "{rounded.control}"
    padding: "16px 25px"
  button-primary-hover:
    backgroundColor: "#39342e"
---

# Design System: Motif Moments Landing

## Overview

**Creative North Star: "From pose to print"**

The landing page carries the established warm paper, pastel, and Inter identity into an editorial introduction to the booth. Large conversational headlines, illustrative studio portraits, loose printed-photo arrangements, and small flower stickers make the finished keepsake tangible. The hero stays static; the scroll story supplies the page's principal motion.

This document describes only `landing/`. Root `PRODUCT.md` and `DESIGN.md` remain authoritative for product behavior and the Vue/Quasar kiosk. The landing is a separate Next.js surface: it neither starts sessions nor controls payment, capture, printing, SSE, or entitlement state.

## Colors

Ink supplies the wordmark, headings, controls, and focus outlines against Paper. Muted carries supporting copy; Line separates sections and unselected frame choices; White suggests photographic paper. Blush underlines the hero and fills the closing invitation. Butter fills the phrase band and numbered journey markers. The subdued purple Accent Word marks selected headline phrases, while Scene Disc supplies a quiet stage for the print.

Frame choice backgrounds preserve the kiosk mapping: Blush for Four Strip ×2, Butter for Butter Grid, Mint for Mint Editorial and Six Moments, Lavender for Lavender Scrapbook and Eight Story. Pastels are surfaces with dark text, not body-copy colors.

## Typography

Inter is loaded locally through `next/font/local` with `display: swap` and a sans-serif fallback. The WOFF2 is subset to this page's English glyphs (37,428 bytes); revisit the subset when adding languages or new characters.

The frontmatter records desktop display, headline, title, and body roles. The wordmark is restrained (22px, weight 650). Supporting paragraphs generally use 14px; story paragraphs have a maximum width of 43ch. Frame names use compact weight-550 labels, with photo counts beneath. Small image captions disclose illustrative samples rather than carrying essential instructions.

At 700px and below, the hero becomes `clamp(55px, 13.8vw, 88px)` with line-height 1 and fewer forced line breaks. Story headlines become 39px; journey and keepsake titles become 15px, with 13px descriptions. Do not introduce a second display family.

## Layout

The page runs from header and static hero through the Butter phrase band, three-part scroll story, three occasion portraits, FAQ, Blush closing invitation, and footer. All primary calls to action link to the frame section. Header links also reach the experience and FAQ.

The desktop container caps at 1320px with 56px side gutters. The hero uses a `.95fr / 1.25fr` split; its image is the dominant companion to the headline. The story uses equal columns with a 9% gap: the left visual sticks while experience, frame choice, and keepsake copy pass on the right. Each story step has an 88svh minimum height. The visual is at most 680px or 86svh tall, with a 450px minimum. The frame choices form two columns; the occasions form three. FAQ uses a split heading and disclosure list. Major section padding is approximately 60–130px.

At 1100px and below, gutters become 32px, the story gap becomes 6%, and frame choices become one column. At 700px and below, gutters become 20px, hero and content sections stack, and only the header's frame link remains visible. The story visual becomes a sticky paper-backed panel above the copy (43svh, constrained to 240–390px); story steps lose viewport minimum heights. Frame choices return to two columns and use 44svh scroll margins to remain reachable beneath the preview. Occasion portraits stack; the footer wraps. At 1700px and above, the hero has an 860px minimum height.

## Elevation & Depth

Printed pieces supply depth; navigation and copy remain flat. Occasion prints use the shared shadow (`5px 16px 32px #35271918`) and small alternating rotations. The static story print uses a drop shadow (`5px 15px 12px #35271920`) and a −7° tilt. A small soft shadow lifts the round hero sticker. Fine rules and photographic margins define other boundaries.

One transparent orthographic canvas turns separated portrait pieces into the selected print, then gently tilts the keepsake. Native scroll progress drives assembly over the first 45% of the story and the final pose over its last 35%. Fine-pointer movement adds a small tilt; touch remains vertical native scrolling. There is no separate canvas per frame or scroll interception.

## Shapes

Primary links styled as buttons and frame choices share the control radius. Buttons have a 58px minimum height; header and footer links have 56px targets. Frame choices are generous rectangular labels with a thumbnail, title, count, and selected dot. Printed portraits keep square edges. Circles, flower silhouettes, small crop corners, and the four-square wordmark mark provide restrained decoration.

## Components

- **Hero:** an eager, high-priority responsive WebP collage and static decoration. The imagery uses eight AI-generated sample portraits across the landing assets, with visible sample disclosure. Supporting occasion images use `next/image` dimensions and responsive sizes.
- **Frame explorer:** a native radio fieldset with a screen-reader legend, six actual frame thumbnails, checked pastel surfaces, keyboard focus outlines, and a polite live description. Selection updates both the poster and scene. Four Strip ×2 repeats four captures in two matching strips; Butter Grid, Mint Editorial, and Lavender Scrapbook use four captures; Six Moments uses six; Eight Story uses eight. `lib/frames.mjs` retains the kiosk's 1200×1800 placement geometry without a runtime kiosk dependency.
- **Scroll preview:** a responsive static poster stays available while the dynamically imported scene initializes or fails. Loading waits until the hero completes, the visitor has scrolled at least 40px, the story is near the viewport, and idle time is available. Reduced motion and Save-Data keep the poster. Texture errors, render errors, and WebGL context loss restore it. The canvas is decorative and hidden from assistive technology; frame names and descriptions remain in HTML.
- **Canvas budget:** demand rendering, visibility/intersection checks, mobile DPR 1 and desktop DPR 1.5, low-power renderer preference, one selected frame texture, and explicit geometry/material/texture disposal. The poster is hidden only after a scene frame paints. Preserve these mechanisms when changing the story.
- **Primary action:** dark rounded anchor with an arrow, a slight upward hover movement, and a 180ms transition. All focusable elements receive visible Ink outlines. The skip link appears on focus; decorative SVGs are hidden from assistive technology.
- **Keepsake explanation:** three icon-and-copy rows describe the included print, account-free QR download within seven days, and one complete retake before printing. They explain the booth rather than offering online checkout or downloads.
- **FAQ:** five native `details`/`summary` disclosures cover session flow, inclusions, retakes, downloads, and posing. The plus becomes a minus when open; each summary has a 76px minimum height. Native semantics retain keyboard operation without custom accordion state.
- **Reduced motion:** disables smooth scrolling, transitions, and animations, and disables the 3D enhancement. A `noscript` message explains the frame preview's JavaScript requirement while the thumbnails remain available.

## Do's and Don'ts

- **Do** preserve the static first viewport and the single progressive scroll scene.
- **Do** keep AI sample disclosure, exact kiosk frame layouts, native radio/disclosure semantics, visible focus, and a useful poster fallback.
- **Do** keep imagery and fonts local; update glyph coverage when copy expands.
- **Don't** add unconfirmed prices, opening hours, addresses, booking availability, testimonials, or contact details.
- **Don't** turn landing selections into kiosk state or change the root capture, payment, gallery, sharing, or printing architecture.
- **Don't** present performance scores without a fresh measurement of the delivered build. The completed third-party finish review found no material issues; that review is not a performance score.
