---
name: Stark Holographic HUD
colors:
  surface: '#0e131f'
  surface-dim: '#0e131f'
  surface-bright: '#343946'
  surface-container-lowest: '#090e19'
  surface-container-low: '#171b27'
  surface-container: '#1b1f2b'
  surface-container-high: '#252a36'
  surface-container-highest: '#303541'
  on-surface: '#dee2f3'
  on-surface-variant: '#b9cacb'
  inverse-surface: '#dee2f3'
  inverse-on-surface: '#2c303d'
  outline: '#849495'
  outline-variant: '#3b494b'
  surface-tint: '#00dbe9'
  primary: '#dbfcff'
  on-primary: '#00363a'
  primary-container: '#00f0ff'
  on-primary-container: '#006970'
  inverse-primary: '#006970'
  secondary: '#dcb8ff'
  on-secondary: '#480081'
  secondary-container: '#7701d0'
  on-secondary-container: '#dcb7ff'
  tertiary: '#daffde'
  on-tertiary: '#003919'
  tertiary-container: '#00f985'
  on-tertiary-container: '#006d37'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#7df4ff'
  primary-fixed-dim: '#00dbe9'
  on-primary-fixed: '#002022'
  on-primary-fixed-variant: '#004f54'
  secondary-fixed: '#efdbff'
  secondary-fixed-dim: '#dcb8ff'
  on-secondary-fixed: '#2c0051'
  on-secondary-fixed-variant: '#6700b5'
  tertiary-fixed: '#60ff99'
  tertiary-fixed-dim: '#00e479'
  on-tertiary-fixed: '#00210c'
  on-tertiary-fixed-variant: '#005228'
  background: '#0e131f'
  on-background: '#dee2f3'
  surface-variant: '#303541'
typography:
  headline-xl:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: 0.08em
  headline-xl-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: 0.06em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 36px
    fontWeight: '600'
    lineHeight: 44px
    letterSpacing: 0.06em
  headline-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: 0.05em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: 0.04em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0.01em
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0.01em
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
    letterSpacing: 0.02em
  label-telemetry:
    fontFamily: JetBrains Mono
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.12em
  label-code-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.1em
  label-micro:
    fontFamily: JetBrains Mono
    fontSize: 9px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.18em
spacing:
  gutter: 1.5rem
  gutter-mobile: 0.75rem
  margin: 2rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system channels an advanced artificial intelligence heads-up display (HUD) inspired by Stark Industries telemetry terminals. The interface communicates computational supremacy, split-second tactical clarity, and ambient spatial immersion. It is engineered for engineers, tactical operators, and telemetry analysts commanding autonomous systems or multi-threaded AI pipelines.

### Design Style: Tactical Holographic Glassmorphism & High-Tech Brutalism
- **Atmospheric Void:** Deep obsidian canvas layers act as non-reflective space, allowing holographic projections to cast optical resonance without background clutter.
- **Micro-Structured Visual Syntax:** Thin precision linework, hairline calibration markers, technical crosshairs, and fractional coordinates ground the interface in absolute accuracy.
- **Luminous Radiance:** Critical interactions emit light rather than traditional paper-derived drop shadows. Components look projected rather than printed.

## Colors

The palette simulates photonic emissions against an unlit optic lens. All interactions rely on an active emitter hierarchy:

- **Primary (`#00f0ff` - Arc Cyan):** Default state of nominal intelligence, operational telemetry, standard actions, and structural bounding rings.
- **Secondary (`#8a2be2` - Pulse Violet):** Neural computation, deep algorithmic analysis, AI synthesis pipelines, and encrypted logic threads.
- **Tertiary (`#00ff88` - Kinetic Matrix Emerald):** Verified states, nominal integrity, completed sync cycles, and environmental bio-monitors.
- **Accent Alert (`#ff003c` - Crimson Override):** System threats, thermal spikes, hardware warnings, and manual kill-switch controls.
- **Neutral Core (`#050914` - Void Obsidian):** The light-absorbent vacuum base that establishes dynamic contrast ratios exceeding 15:1 for projected neon tokens.

### Dynamic States & Color Bleed
Avoid opaque fills on primary surfaces. Utilize alpha tiers of `#00f0ff` (e.g., `rgba(0, 240, 255, 0.04)` to `rgba(0, 240, 255, 0.12)`) to convey physical volume without blocking underlying micro-grid telemetry.

## Typography

The type hierarchy unites geometric computational display with precise engineering data:

- **Display & Section Headers (`Space Grotesk`):** Engineered uppercase styling, wide tracking, and sharp geometric cuts project structural authority across top-level tactical matrices.
- **General Interface & Narrative (`Inter`):** Clean, neutral glyph forms that prevent eye strain when parsing complex readouts, instructions, or synthetic logs.
- **Data Readouts, Telemetry, & Coordinate Trackers (`JetBrains Mono`):** Fixed-width monospaced rhythm ensures fluctuating numeric telemetry, spatial coordinates, and hex codes align without jitter. Set all telemetry labels to uppercase with expanded letter-spacing (`0.1em` to `0.18em`).

## Layout & Spacing

The spatial grid operates on an 8-column layout for tablets and a 12-column layout for large tactical displays, switching to a 4-column flow on mobile. Layout surfaces emulate flight-deck avionics:

- **Viewport Canvas:** Pinned telemetry headers and docked diagnostic sidebars frame an uninhibited dynamic operational center.
- **Reflow Architecture:** On desktop, widgets snap into modular telemetry docks with 24px gutters. On mobile viewports, secondary diagnostics tuck into collapsable drawer trays, maintaining single-column focal priority.
- **Rhythm Rules:** Internal component paddings rely on dense `space-xs` and `space-sm` increments to preserve high information density, while module separation uses `space-lg` and `space-xl` to prevent sensory overload.

## Elevation & Depth

Depth is defined by optical illumination, luminescence levels, and frosted chromatic glass rather than opaque elevation drops:

- **Level 0 (Void Ground):** Pure obsidian (`#020408`) with a faint vector dot matrix (`rgba(0, 240, 255, 0.03)` spaced at 32px intervals).
- **Level 1 (Docked Containers):** Translucent backdrop panels with `background: rgba(5, 12, 26, 0.65)`, `backdrop-filter: blur(16px)`, and hairline borders (`border: 1px solid rgba(0, 240, 255, 0.15)`).
- **Level 2 (Active Holograms / Hover Focus):** Luminance flares up. Borders intensify to `rgba(0, 240, 255, 0.5)` with an ambient outer glow (`box-shadow: 0 0 20px rgba(0, 240, 255, 0.2), inset 0 0 15px rgba(0, 240, 255, 0.05)`).
- **Level 3 (Modal Overlays / Critical Alerts):** Edge glows shift towards alert palettes (`#ff003c` or `#00f0ff`) with high-intensity chromatic dispersion (`box-shadow: 0 0 35px rgba(255, 0, 60, 0.35)`), commanding direct tactical focus.

## Shapes

The interface embraces a razor-sharp, angular architectural aesthetic:

- **Zero-Radius Primitives:** All structural viewports, inputs, panels, and trigger nodes utilize a sharp edge (`0px` border-radius) or high-tech 45-degree chamfered corners (`clip-path: polygon(...)`).
- **Bracket Framing:** Major diagnostic containers use structural corner ticks: L-shaped framing accents anchored on the top-left and bottom-right edges to emulate holographic targeting reticles.

## Components

### Buttons & Tactical Triggers
- **Primary Action:** Sharp-cornered bounding box with semi-transparent cyan background (`rgba(0, 240, 255, 0.08)`), 1px solid cyan border, and uppercase `JetBrains Mono` label. On hover, background shifts to solid cyan `#00f0ff` with void-black text, casting a 12px outer glow.
- **Destructive / Override Trigger:** Outlined in Crimson Alert `#ff003c`, animated diagonal warning scanlines in the background layer at 15% opacity.

### Glassmorphic HUD Panels & Cards
- Built with frosted glass layers and technical corner reticles. Every card contains a top telemetry metadata bar (`// SYS.MOD_01 // SEC_LEVEL: 4`) in `label-micro` typography.

### Form Inputs & Telemetry Fields
- Monospaced inputs with an integrated terminal prompt icon (`> `). Ghost underline or minimal hairline border (`rgba(0, 240, 255, 0.25)`). Focus states introduce a vertical scanning pulse cursor and cyan bottom-edge illumination.

### Checkboxes & Segmented Toggles
- Square checkboxes styled as crosshair markers. When checked, a centered glowing diamond or electric cross ticks active with instant transitions. Toggles act as binary linear sliders with digital `0 / 1` indicators.

### Telemetry Gauges & Micro-Widgets
- **Circular Arc Monos:** Circular SVG radial progress rings mapping AI inference speeds, power distribution, and thermal readings. Rings utilize segmented dashed strokes (`stroke-dasharray`) with gradient luminous heads.
- **Coordinate Crosshairs:** Miniature vector crosshairs placed at grid intersections to reinforce Stark holographic display spatial calibration.