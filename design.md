# Apple-Inspired Design System Specification

## Overview
This document specifies the Apple-inspired design system for the **Istanbul University Alumni Management & Tracking System (İÜ Mezun Takip Sistemi)**. It provides a clean, modern, and accessible design language characterized by content-focused hierarchy, generous whitespace, refined typography, and purposeful micro-interactions.

---

## 1. Color Palette

The color system is inspired by Apple's Human Interface Guidelines (HIG) and web design principles. All colors are defined as CSS custom properties.

| Token Name | CSS Custom Property | HEX Value | Usage & Meaning |
| :--- | :--- | :--- | :--- |
| **Apple Blue** | `--apple-blue`, `--color-apple-blue` | `#0071e3` | Primary brand color, main call-to-actions, focus rings, primary highlights |
| **Link Blue** | `--link-blue`, `--color-link-blue` | `#0066cc` | Hyperlinks, button active/hover states |
| **Signal Blue** | `--signal-blue`, `--color-signal-blue` | `#2997ff` | Bright accents, dark mode / high-contrast highlights, live indicators |
| **Carbon** | `--carbon`, `--color-carbon` | `#1d1d1f` | Primary typography, deep surfaces, high-contrast headings |
| **Frost** | `--frost`, `--color-frost` | `#f5f5f7` | Global page background, subtle secondary card surfaces |
| **Ice** | `--ice`, `--color-ice` | `#f4f8fb` | Badge backgrounds, subtle table row hover highlights |
| **Smoke** | `--smoke`, `--color-smoke` | `#333333` | Subheadings, prominent secondary text |
| **Graphite** | `--graphite`, `--color-graphite` | `#474747` | Body copy, default metadata text |
| **Ash** | `--ash`, `--color-ash` | `#707070` | Secondary labels, form hints, timestamps |
| **Mist** | `--mist`, `--color-mist` | `#858585` | Placeholders, disabled states, subtle borders |
| **Pebble** | `--pebble`, `--color-pebble` | `#e2e2e5` | Structural hairline dividers, subtle card and input borders |

### Semantic Role Mappings
- **Page Background:** `--color-frost` (`#f5f5f7`)
- **Surface / Card Background:** `#ffffff` (Elevated cards and modal containers)
- **Primary Text:** `--color-carbon` (`#1d1d1f`)
- **Muted Text:** `--color-graphite` (`#474747`)
- **Border / Hairline:** `--color-pebble` (`#e2e2e5`)
- **Interactive Primary:** `--color-apple-blue` (`#0071e3`)
- **Interactive Hover:** `--color-link-blue` (`#0066cc`)

---

## 2. Typography

The typographic scale uses Apple's native San Francisco fonts with comprehensive system fallbacks.

### Font Families
- **Headings & Display:** `SF Pro Display`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `"Helvetica Neue"`, `sans-serif`
- **Body & UI Text:** `SF Pro Text`, `-apple-system`, `BlinkMacSystemFont`, `"Segoe UI"`, `Roboto`, `"Helvetica Neue"`, `sans-serif`
- **Monospace & Code:** `SFMono-Regular`, `ui-monospace`, `Menlo`, `Monaco`, `Consolas`, `monospace`

### Typography Scale
| Style | Size | Weight | Line Height | Tracking | Usage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Large Title** | `2.125rem` (34px) | 700 / Bold | 1.18 | `-0.022em` | Hero titles, primary landing banners |
| **Title 1** | `1.75rem` (28px) | 700 / Bold | 1.21 | `-0.019em` | Page headers, main section titles |
| **Title 2** | `1.375rem` (22px) | 600 / Semi-Bold | 1.27 | `-0.016em` | Card headers, subsection titles |
| **Title 3** | `1.25rem` (20px) | 600 / Semi-Bold | 1.30 | `-0.014em` | Modal titles, feature headlines |
| **Headline** | `1.0625rem` (17px) | 600 / Semi-Bold | 1.41 | `-0.011em` | List item titles, table headers |
| **Body** | `1.0625rem` (17px) | 400 / Regular | 1.47 | `-0.011em` | Default reading text, paragraphs |
| **Callout** | `1.00rem` (16px) | 400 / Regular | 1.45 | `-0.009em` | Expanded hints, blockquotes |
| **Subhead** | `0.9375rem` (15px) | 400 / Regular | 1.42 | `-0.006em` | Subtitles, user roles, descriptions |
| **Footnote** | `0.8125rem` (13px) | 400 / Regular | 1.38 | `0.000em` | Metadata, timestamps, helper text |
| **Caption 1** | `0.75rem` (12px) | 400 / Regular | 1.33 | `0.004em` | Badges, tags, breadcrumbs |
| **Caption 2** | `0.6875rem` (11px) | 500 / Medium | 1.30 | `0.007em` | Legal text, micro-labels |

---

## 3. Spacing System (4px Grid)

All layout margins, paddings, and component dimensions adhere to a strict 4px grid:

| Token | Value | Standard Usage |
| :--- | :--- | :--- |
| `--space-1` | `4px` | Fine-grain alignment, micro-gaps, icon margins |
| `--space-2` | `8px` | Badge padding, compact button padding, item gaps |
| `--space-3` | `12px` | Input vertical padding, standard element gap |
| `--space-4` | `16px` | Standard component padding, list gaps, input horizontal padding |
| `--space-5` | `20px` | Medium padding, section sub-gaps |
| `--space-6` | `24px` | Standard card internal padding, grid column gaps |
| `--space-7` | `28px` | Button horizontal padding (large), expanded card padding |
| `--space-8` | `32px` | Section header margins, spacious card padding |
| `--space-10` | `40px` | Section padding (mobile), feature blocks |
| `--space-12` | `48px` | Container margins, prominent section spacing |
| `--space-16` | `64px` | Large section padding, hero top/bottom padding |
| `--space-20` | `80px` | Major page section vertical separation |

---

## 4. Corner Radii & Geometry

- **Cards, Images, and Form Inputs:** `8px` (`--radius-card: 8px`, `--radius-input: 8px`, `--radius-image: 8px`).
- **Buttons and Badges / Tags:** Pill shape (`border-radius: 9999px` / `--radius-pill: 9999px`).

---

## 5. UI Component Guidelines

### Cards
- **Background:** `#ffffff`
- **Border:** `1px solid #e2e2e5` (`--pebble`)
- **Border Radius:** `8px`
- **Padding:** `24px` to `32px`
- **Shadow:** Subtle Apple elevation: `0 2px 8px rgba(0, 0, 0, 0.04)` on resting; `0 8px 24px rgba(0, 0, 0, 0.08)` on hover.

### Buttons
- **Shape:** Pill (`border-radius: 9999px`)
- **Primary Button:**
  - Background: `#0071e3` (Apple Blue)
  - Color: `#ffffff`
  - Hover: `#0066cc` (Link Blue) with subtle smooth transition
- **Secondary / Outline Button:**
  - Background: `#ffffff` or `rgba(255, 255, 255, 0.8)`
  - Border: `1px solid #e2e2e5` (`--pebble`)
  - Color: `#1d1d1f` (`--carbon`) or `#0071e3` (`--apple-blue`)
  - Hover: Background `#f5f5f7` (`--frost`)
- **Text Button / Inline Action:**
  - Color: `#0066cc` (Link Blue)
  - Hover: `#0071e3`, underline

### Form Inputs
- **Border Radius:** `8px`
- **Border:** `1px solid #e2e2e5` (`--pebble`)
- **Background:** `#ffffff`
- **Padding:** `12px 16px`
- **Focus State:** `border-color: #0071e3; box-shadow: 0 0 0 3px rgba(0, 113, 227, 0.2); outline: none;`

### Navigation Bar
- **Frosted Glass Blur:** `background-color: rgba(245, 245, 247, 0.8);`
- **Backdrop Filter:** `-webkit-backdrop-filter: saturate(180%) blur(20px); backdrop-filter: saturate(180%) blur(20px);`
- **Border Bottom:** `1px solid #e2e2e5;`

---

## 6. Accessibility & Contrast

- Text contrast ratios exceed WCAG AA standards (4.5:1 for normal text, 3:1 for large text).
- Primary text on Frost (`#1d1d1f` on `#f5f5f7`) has a contrast ratio of ~**15.2:1**.
- Apple Blue (`#0071e3`) with white text (`#ffffff`) provides a contrast ratio of ~**4.6:1**.
- Link Blue (`#0066cc`) on white background provides a contrast ratio of ~**5.5:1**.
