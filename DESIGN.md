---
name: SGUM-UCI
description: Sistema de Gestión Universitaria de Mantenimiento — plano de la UCI
colors:
  ink: "#0b4a7f"
  ink-deep: "#083a66"
  ink-press: "#062d50"
  text: "#0b2a44"
  text-2: "#33536b"
  text-3: "#46667f"
  on-ink: "#ffffff"
  sheet: "#f3f6f9"
  panel: "#f9fbfd"
  paper: "#ffffff"
  hover: "#e4eef6"
  selected: "#d7e8f5"
  grid: "#c9d3dc"
  grid-strong: "#9db3c6"
  line-control: "#5d7d97"
  cyan: "#2a94d4"
  focus: "#1a7fbd"
  warn-bg: "#fdf1d0"
  warn-fg: "#5a3c00"
  warn-line: "#8a5a00"
  ok-bg: "#e2f3e8"
  ok-fg: "#0f5a30"
  ok-line: "#17643a"
  danger-bg: "#fbe4e5"
  danger-fg: "#8f161d"
  danger-line: "#a61d24"
  info-bg: "#dcebf7"
  info-fg: "#0a4470"
  info-line: "#0b4a7f"
  neutral-bg: "#eaeff4"
  neutral-fg: "#33536b"
  neutral-line: "#6a8aa4"
  danger: "#a61d24"
  danger-deep: "#8f161d"
  danger-press: "#741015"
  ok: "#17643a"
  ok-deep: "#0f5a30"
  backdrop: "rgba(11, 42, 68, 0.5)"
  scrim: "rgba(243, 246, 249, 0.72)"
typography:
  display:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "var(--sg-fs-3xl)"
    fontWeight: 700
    lineHeight: var(--sg-lh-tight)
    letterSpacing: normal
  headline:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "var(--sg-fs-xl)"
    fontWeight: 600
    lineHeight: var(--sg-lh-tight)
    letterSpacing: normal
  title:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "var(--sg-fs-lg)"
    fontWeight: 600
    lineHeight: var(--sg-lh-snug)
    letterSpacing: normal
  body:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "var(--sg-fs-md)"
    fontWeight: 400
    lineHeight: var(--sg-lh-body)
    letterSpacing: normal
  label:
    fontFamily: "Segoe UI, system-ui, -apple-system, Noto Sans, Liberation Sans, Helvetica Neue, Arial, sans-serif"
    fontSize: "var(--sg-fs-2xs)"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.08em"
  mono:
    fontFamily: "ui-monospace, Cascadia Mono, Consolas, SFMono-Regular, DejaVu Sans Mono, Liberation Mono, monospace"
    fontSize: "var(--sg-fs-sm)"
    fontWeight: 400
    lineHeight: var(--sg-lh-body)
    letterSpacing: normal
rounded:
  none: "0"
spacing:
  s-0: "0"
  s-1: "4px"
  s-2: "8px"
  s-3: "12px"
  s-4: "16px"
  s-5: "24px"
  s-6: "32px"
  s-7: "48px"
  s-8: "64px"
components:
  btn-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-ink}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
    fontWeight: 600
    fontSize: "15px"
    minHeight: "44px"
    borderWidth: "1.5px"
    borderColor: "{colors.ink}"
  btn-primary-hover:
    backgroundColor: "{colors.ink-deep}"
    textColor: "{colors.on-ink}"
    borderColor: "{colors.ink-deep}"
  btn-secondary:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
    fontWeight: 600
    fontSize: "15px"
    minHeight: "44px"
    borderWidth: "1.5px"
    borderColor: "{colors.ink}"
  btn-danger:
    backgroundColor: "{colors.danger}"
    textColor: "{colors.on-ink}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
    fontWeight: 600
    fontSize: "15px"
    minHeight: "44px"
    borderWidth: "1.5px"
    borderColor: "{colors.danger}"
  btn-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
    fontWeight: 600
    fontSize: "15px"
    minHeight: "44px"
    borderWidth: "1.5px"
    borderColor: "transparent"
  btn-loading:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
    fontWeight: 600
    fontSize: "15px"
    minHeight: "44px"
    borderWidth: "1.5px"
    borderColor: "{colors.ink}"
  input-field:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.text}"
    rounded: "{rounded.none}"
    padding: "8px 12px"
    fontSize: "15px"
    minHeight: "44px"
    borderWidth: "1px"
    borderColor: "{colors.line-control}"
    focusBorderColor: "{colors.ink}"
    focusShadowColor: "rgba(26, 127, 189, 0.35)"
  badge-state:
    backgroundColor: "{colors.warn-bg}"
    textColor: "{colors.warn-fg}"
    rounded: "{rounded.none}"
    borderWidth: "1px"
    borderColor: "{colors.warn-line}"
    fontSize: "12px"
    fontWeight: 600
    height: "24px"
    padding: "0 8px 0 4px"
  badge-state-process:
    backgroundColor: "{colors.info-bg}"
    textColor: "{colors.info-fg}"
    rounded: "{rounded.none}"
    borderWidth: "1px"
    borderColor: "{colors.info-line}"
    fontSize: "12px"
    fontWeight: 600
    height: "24px"
    padding: "0 8px 0 4px"
  badge-state-resolved:
    backgroundColor: "{colors.ok-bg}"
    textColor: "{colors.ok-fg}"
    rounded: "{rounded.none}"
    borderWidth: "1px"
    borderColor: "{colors.ok-line}"
    fontSize: "12px"
    fontWeight: 600
    height: "24px"
    padding: "0 8px 0 4px"
  table-row:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.text}"
    borderColor: "{colors.grid}"
    hoverBackgroundColor: "{colors.hover}"
    selectedBackgroundColor: "{colors.selected}"
  modal:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.text}"
    rounded: "{rounded.none}"
    borderWidth: "2px"
    borderColor: "{colors.ink}"
    shadow: "none"
  toast:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.text}"
    rounded: "{rounded.none}"
    borderWidth: "1.5px"
    borderColor: "{colors.ink}"
    shadow: "{shadows.pop}"
  navbar:
    backgroundColor: "{colors.paper}"
    borderColor: "{colors.ink}"
    borderWidth: "2px"
  sheet:
    backgroundColor: "{colors.paper}"
    borderColor: "{colors.ink}"
    borderWidth: "1.5px"
    borderRadius: "{rounded.none}"
---

# Design System: SGUM-UCI

## Overview

**Creative North Star: "The Architect's Draft"**

SGUM-UCI is a sheet of architectural blueprint — a clean, ordered, methodical workspace where every element earns its place and nothing is decorative for its own sake. The interface evokes the precision of a drafting table: ink lines on white paper, a fine grid underlying everything, right angles everywhere. This is an institutional maintenance dispatch system for the Universidad de las Ciencias Informáticas, designed for an administrator who spends a full workday scanning, prioritizing, and assigning — speed and clarity are not luxuries, they are the job description.

The system is institutional yet approachable. Spanish formal of a university governs every label, button, message, and error. The voice addresses users as "usted," with verbs that name the action ("Asignar técnico," "Registre la incidencia"). Components feel tactile and confident — buttons respond like physical switches, fields have clear boundaries, every interaction yields a visible result. The flat, shadowless aesthetic reinforces trust: nothing is hidden behind decorative effects, everything is legible at a glance.

**Key Characteristics:**
- Blueprint precision: zero border-radius, strict 8px module grid, fine grid lines
- Institutional Spanish with "usted" throughout, never casual language
- Flat by default: shadows appear only as functional responses to state
- One primary action per screen; the rest recede
- SVG icon system, no external dependencies, purely local

## Colors

The palette is a blueprint: deep navy ink on a warm white sheet, with a fine cyan accent reserved exclusively for registration marks and active-state indicators. Every color serves a function — no color is decorative for its own sake.

### Primary
- **Blueprint Ink** (#0b4a7f): The dominant visual force — text, headings, primary action buttons, strong borders, and the active tab indicator. This is the color that defines the system's identity. Hover darkens to ink-deep (#083a66), active press to ink-press (#062d50).
- **Ink Deep** (#083a66): Hover state for primary elements.
- **Ink Press** (#062d50): Active/pressed state for primary elements.

### Secondary
- **Ink Text** (#0b2a44): Body text and values — 13.5:1 contrast on the sheet. This is the highest-contrast reading color.
- **Secondary Text** (#33536b): Secondary labels, metadata, and supporting text — 7.5:1 contrast.
- **Tertiary Text** (#46667f): Labels, help text, and placeholder text — 5.6:1 contrast, the minimum for small labels.

### Tertiary
- **Cyan** (#2a94d4): **Only** registration marks and active-state indicators. Never used as text color, button fill, or background. This is the color of the cross marks at the corners of the blueprint sheet.
- **Focus Ring** (#1a7fbd): Keyboard focus indicator — 2px outline with 35% opacity.

### Neutral
- **Sheet** (#f3f6f9): Application background — the blueprint paper itself, with a faint 32px grid pattern.
- **Panel** (#f9fbfd): Second layer — navigation bars, table headers, footer panels, card-like containers.
- **Paper** (#ffffff): Work cells — table rows, form fields, modals.
- **Hover** (#e4eef6): Row or element under the pointer.
- **Selected** (#d7e8f5): Selected row or activated element.
- **Grid** (#c9d3dc): Fine divisions and borders — decorative and structural lines.
- **Grid Strong** (#9db3c6): Marked grid lines — table headers, section dividers.
- **Line Control** (#5d7d97): Loose control borders — 4:1 contrast for input borders.

### Named Rules
**The One Ink Rule.** The primary ink (#0b4a7f) is the sole source of visual authority. One primary action per screen wears ink; everything else defers to paper, hover, or secondary states. The cyan (#2a94d4) is reserved exclusively for registration marks and active-state indicators — it never appears as text, button fill, or background.

## Typography

**Display Font:** Segoe UI with system-ui fallback — a clean, institutional sans-serif optimized for screen reading at body size. No remote fonts; everything is served locally within the intranet.

**Body Font:** Same family — Segoe UI → system-ui → Noto Sans → Liberation Sans → Helvetica Neue → Arial → sans-serif. The mono stack (ui-monospace → Cascadia Mono → Consolas) is reserved for data only.

**Character:** The type pairing is functional and institutional — no display face drama, no expressive serifs. Weight and size carry hierarchy; the typeface itself disappears into the workflow.

### Hierarchy
- **Display** (700, 25px/1.15): Page headings (h1) — the title of the current work surface.
- **Headline** (600, 19px/1.15): Section headings (h2) — grouping labels within a sheet.
- **Title** (600, 17px/1.35): Card titles, modal headers, panel heads (h3).
- **Body** (400, 15px/1.5): All prose, instructions, and readable text. Measure capped at 68ch.
- **Label** (600, 11px/1.2, letter-spacing 0.08em): Field labels, table headers — uppercase with tracking, marking them as metadata rather than prose.
- **Mono** (400, 13px/1.5): Numeric data, dates, codes, reference numbers — tabular figures, monospaced for alignment.

### Named Rules
**The Label Rule.** Field labels are always uppercase, 11px, semi-bold, with 0.08em tracking. They mark territory, not content — never mixed with body text weight or size.

**The Data Rule.** Dates, quantities, codes, and reference numbers live in monospace with tabular numerals. Names, locations, and descriptions live in the regular face. Never let monospace touch a button, label, or casual sentence.

## Layout

The layout is a blueprint sheet — a constrained working area with a fine grid visible beneath it. The application wraps content in a `.sg-sheet` container: `min(100% - 40px, 1440px)` wide with 20px gutters on each side, centered on the page. On screens below 576px, the sheet fills the width without margins or borders.

The system operates on a strict 8px module grid (with 4px half-steps): spacing values are 4, 8, 12, 16, 24, 32, 48, 64px. The navigation bar is 64px tall. Touch targets and controls are minimum 44px. Forms use 12-column grids of cajetín cells (`.sg-field`), each cell sharing borders with its neighbors like a spreadsheet — creating a seamless, dense surface for data entry.

Density is the priority: the administrator sees more information per screen, not less. Tables are dense by default (`--sg-fs-sm` for `--dense` variant), headers are sticky, and rows hover and select with clear tonal feedback. The layout is not decorative — it is a working surface designed for scanning and decision-making.

## Elevation & Depth

**The system is flat by default.** Surfaces are flat at rest. There is no ambient shadow, no decorative elevation, no layered depth. The design system uses tonal layering instead — lighter backgrounds (`--sg-sheet` → `--sg-panel` → `--sg-paper`) indicate layer hierarchy, and borders (`--sg-line`, `--sg-line-strong`, `--sg-frame`) separate elements.

The only shadow in the system is `--sg-shadow-pop` (`0 6px 16px -6px rgba(11, 42, 68, 0.28)`), which appears exclusively on dropdown menus and toasts — elements that genuinely float above the content plane. Modals have `box-shadow: none`; they are defined by a 2px solid ink border instead.

### Named Rules
**The Flat-By-Default Rule.** Surfaces are flat at rest. Shadows appear only as a functional response to state: dropdowns pop up, toasts float, and the sole shadow (`--sg-shadow-pop`) marks those transitions. Nothing else carries a shadow.

**The Border-As-Structure Rule.** Where a flat world needs separation, it uses borders — 1px grid lines, 1.5px cajetín borders, 2px frame borders for modals and the navbar. Depth is a property of borders and tonal contrast, not of shadow.

## Shapes

The form language is right angles — everything is rectangular with 0px border-radius. This is deliberate and consistent: buttons, inputs, cards, modals, badges, alerts, and toasts all share the same zero-radius philosophy. The only circle in the system is the radio button's inner dot.

Borders define hierarchy: 1px for standard divisions (`--sg-grid`), 1.5px for cajetín cells (`--sg-line-strong`), and 2px for the navbar frame and modal borders (`--sg-frame`). The system is not soft — it is architectural, built from lines and right angles like a blueprint.

## Components

### Buttons
- **Shape:** 0px radius — perfectly square corners, defined by a 1.5px border.
- **Primary:** Ink background (`#0b4a7f`) with white text. The sole primary action per screen. Padding: 8px 16px, minimum height 44px. Hover darkens to ink-deep, active presses to ink-press.
- **Secondary:** Paper background with ink border and ink text. Used for alternative actions and standard Bootstrap-style buttons. Hover shows ink text on hover background.
- **Danger:** Danger background (`#a61d24`) with white text. Only for destructive actions. Hover darkens.
- **Ghost:** Transparent background with ink text, no visible border. For low-hierarchy actions. Hover shows hover background.
- **Loading:** Shows a progress bar animation on the bottom edge (3px, `sg-slide` keyframe) while preserving the variant's colors.
- **States:** `:hover` (color shift), `:focus-visible` (2px cyan ring, 2px offset), `:active` (press color), `disabled` (muted text, not-allowed cursor), `.is-loading` (progress bar).

### Fields / Cajetín
- **Style:** Paper background, 1px solid `--sg-line-control` border, 0px radius, 44px minimum height. Focus shows 2px ink border with focus ring. Invalid state shows 2px danger border on a danger-tinted background.
- **Label:** 11px semi-bold, uppercase, 0.08em tracking, `--sg-text-3` color.
- **Control font:** 17px (`--sg-fs-lg`) inside cajetín cells, regular weight.
- **Hint:** 13px `--sg-text-3` text below the control.
- **Error message:** 13px bold, `--sg-danger-fg` color, inside the cajetín cell.

### Badges (State and Priority)
- **Style:** Inline-flex, 24px height, 1px solid border, 0px radius. Each state has its own background, foreground, and border color with a pattern mark (not just color):
  - **Pending** (`--pendiente`): Warn tones with diagonal stripe pattern mark.
  - **In Progress** (`--proceso`): Info tones with half-bar pattern mark.
  - **Resolved** (`--resuelto`): OK tones with solid bar mark.
- **Priority** (`--alta`, `--media`, `--baja`): Three vertical bars of varying height (5px, 8px, 12px) with border treatment.

### Tables
- **Container:** `.sg-table-wrap` with scrollable overflow and sticky header. Maximum height calculated from viewport minus navbar and margins.
- **Header:** 12px semi-bold uppercase with tracking, `--sg-panel` background, 1.5px strong ink border bottom. Sticky at top.
- **Rows:** 15px body font, 1px `--sg-grid` border bottom. Hover shows `--sg-hover` background, selected shows `--sg-selected`.
- **Number column:** Monospace, tabular numerals, 13px, right-aligned, 3.75rem wide.
- **Data column:** Monospace, tabular numerals, 13px — for dates, codes, quantities.
- **Mobile:** `sg-table--stack` transforms rows into labeled grid items with `data-label` attributes.

### Modal
- **Shape:** 0px radius, 2px solid ink border (`--sg-frame`). No shadow — the border defines the modal's presence.
- **Header:** `--sg-panel` background, 1.5px ink border bottom, 19px bold title.
- **Footer:** `--sg-panel` background, 1px grid border top, buttons right-aligned.
- **Backdrop:** `#0b2a44` at 0.55 opacity.
- **Animation:** Slides down from -0.75rem on show (200ms ease).
- **Confirm variant:** Max-width 30rem, with a lead section showing a danger icon and explanatory text.

### Toast
- **Style:** Paper background, 1.5px ink border, 0px radius, `--sg-shadow-pop`. Fixed position bottom-right, 24rem max width, stacked vertically.
- **Animation:** Slides in from 8px below with fade (200ms ease). Leaves with fade + 6px translate.
- **States:** `--danger`, `--warn`, `--ok`, `--info` variants each carry their own background/foreground/border colors.

### Navigation
- **Style:** Sticky top, `--sg-paper` background, 2px solid ink bottom border (`--sg-frame`). 64px height.
- **Brand:** Ink color, with logo mark and "SGUM-UCI" name (19px bold). On wide screens, a small tagline appears below the name.
- **Links:** 15px semi-bold, `--sg-text-2` color. Active tab shows ink background and a 3px cyan bottom border (the registration mark).
- **User menu:** Shows role name (Administrador, Técnico, Almacenero, Solicitante) and chevron. On wide screens (≥1200px) shows name and role.
- **Notification count:** 18px circular badge with `--sg-danger` background, white text.
- **Mobile:** Hamburger menu collapses nav items vertically. Below 992px, user and notifications are always visible in the collapsed menu.

### Sheets and Panels
- **Sheet** (`.sg-sheet`): The primary page container. Paper background, 1.5px solid ink border, with registration marks (cyan cross SVGs) at each corner. Max-width 1440px, min(100% - 40px) wide, centered with 24px top/bottom margin.
- **Section** (`.sg-section`): Padding 24px, 1px grid border top — for grouping within a sheet.
- **Panel** (`.sg-panel`): Paper background, 1px solid grid-strong border — for grouping within sections. Header with 17px bold title, body with 16px padding.
- **Page Head** (`.sg-page-head`): Grid layout with title (25px bold ink), description, count, and action buttons. Bottom 1.5px ink border.

## Do's and Don'ts

### Do
- **Do** use the 8px module grid for all spacing — every margin, padding, and gap is a multiple of 4px (half-step) or 8px (full module).
- **Do** use ink (#0b4a7f) as the sole primary action color, and cyan (#2a94d4) only for registration marks and active indicators.
- **Do** mark state badges with text AND pattern, never color alone. A pending badge shows "Pendiente" with a diagonal stripe; a resolved badge shows "Resuelto" with a solid bar.
- **Do** use `sg-table--stack` with `data-label` attributes for mobile table rendering.
- **Do** include `aria-label` on icon-only buttons (`.sg-btn--icon`), and name action buttons with their verb ("Asignar técnico," "Retirar material").
- **Do** use monospace (`--sg-font-mono`) only for numeric data, dates, codes, and reference numbers.

### Don't
- **Don't** use border-radius on any component — buttons, inputs, badges, modals, toasts, alerts, and cards are all 0px. The right angle is the design system's signature.
- **Don't** use color as the sole carrier of meaning for state or priority. Always pair color with text and pattern.
- **Don't** use `--sg-cyan` as text color, button fill, or background. It is reserved for registration marks and active-state indicators only.
- **Don't** use decorative shadows. The only acceptable shadow is `--sg-shadow-pop` on dropdowns and toasts. A zero-offset colored halo is decoration, not depth.
- **Don't** use gradient text, glass effects, or blur as decoration. Emphasis comes from weight or size.
- **Don't** use cards as page structure (icon + heading + text). The sheet is the container; use `sg-section` or `sg-panel` for grouping — never nested cards.
- **Don't** place a kicker or eyebrow above a heading. The heading carries its own weight. Delete the label and let the heading speak.
- **Don't** number sections (01, 02, 03) unless the sequence itself carries information the reader needs.
- **Don't** load anything from the internet — CDNs, Google Fonts, Font Awesome, Bootstrap Icons, or emoji as icons. Everything is local SVG, local Bootstrap, local fonts.
- **Don't** use `alert()` or `confirm()` browser dialogs — use `modal_confirm.html` for destructive confirmations.
- **Don't** edit `static/vendor/` or `static/sgum/` from within a page task. If the system is missing something, request it from the foundation team.
- **Don't** duplicate the Django messages loop — `master.html` already paints messages once. Never include `{% for message in messages %}` in a page template.
