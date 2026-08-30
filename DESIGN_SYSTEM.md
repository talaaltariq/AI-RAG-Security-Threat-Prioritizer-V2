# Neo-Electric Slate & Obsidian: The "GoodBoard" Design System Specification

> **Version**: 1.0.0  
> **Aesthetic Archetype**: Neo-Sleek Modern SaaS / High-Contrast Obsidian & Electric Lime  
> **Primary Persona**: High-velocity B2B SaaS, Analytics Dashboards, Fintech, Executive Command Centers  
> **Core Visual Contrast**: Solid Obsidian Black Sidebar + Crisp Frosted Ice Canvas + Vibrant Electric Lime (`#D4F638`) & Cyber Teal (`#36C6AF`) Accents

---

## 1. Executive Summary & Design Philosophy

The **GoodBoard Design System** is an ultra-modern, high-contrast visual framework that pairs deep obsidian black foundational containers with an airy, ultra-clean light dashboard canvas, punctuated by hyper-vibrant **Electric Lime (Chartreuse)** and **Cyber Teal (Seafoam Mint)** accents.

### Core Tenets

1. **High-Contrast Hybrid Layout**: 
   - A deep, solid obsidian navigation sidebar (`#0C0E12`) anchors the interface on the left, establishing visual authority.
   - The main workspace lives on an ultra-soft cool-white/ice canvas (`#F4F7FC`), creating zero cognitive fatigue and maximum readability.
2. **Electric Energy Accents**:
   - Electric Lime (`#D8FA42` / `#DCF838`) is used for primary active states, key data series, and high-priority callout cards.
   - Cyber Teal (`#36C6AF`) provides complementary balance for secondary metrics, volume bars, and map heatmaps.
3. **Inverted Obsidian Hero Stat Cards**:
   - Instead of standard white cards everywhere, primary KPI summary cards are rendered in sleek jet black (`#0B0D11`), immediately drawing the eye to critical numbers before transitioning into lighter analytical charts.
4. **Soft Pill Radii & Curved Geometry**:
   - Generous container curves (`20px` to `24px` border-radius) combined with continuous pill buttons (`rounded-full` / `9999px`) create a friendly, tactile, and highly modern aesthetic.
5. **Data Visualization as First-Class Citizen**:
   - Clean, borderless charts with smooth cubic-bezier bezier curves, stacked dual-tone vertical bars, capsule-shaped progress meters, and sleek dark floating tooltips (`#0B0D11`).

---

## 2. Design Tokens Reference

### 2.1 Complete Color Palette

```css
:root {
  /* ==========================================================================
     1. BRAND ACCENTS (ELECTRIC ENERGIZERS)
     ========================================================================== */
  --color-electric-lime: #D8FA42;       /* Primary active pills, primary data line */
  --color-electric-lime-hover: #C5E82F; /* Hover state for electric lime */
  --color-electric-lime-light: #F4FDC6; /* Subtle lime background tint */
  --color-electric-lime-surface: #DCF838; /* Bold callout card background (Buyer Satisfaction) */
  
  --color-cyber-teal: #36C6AF;          /* Secondary accent, volume metrics, line 2 */
  --color-cyber-teal-hover: #2EB39E;    /* Hover state for cyber teal */
  --color-cyber-teal-light: #D5F6F0;    /* Muted teal background */
  --color-cyber-teal-pill: #A7EDE0;     /* Soft badge background */

  /* ==========================================================================
     2. OBSIDIAN & DARK NEUTRALS (SIDEBAR & HERO CARDS)
     ========================================================================== */
  --color-obsidian-900: #0C0E12;        /* Sidebar background, primary brand shell */
  --color-obsidian-800: #12141A;        /* KPI Hero Cards, Black Tooltips */
  --color-obsidian-700: #1D2129;        /* Hover state for dark elements */
  --color-obsidian-pill: #000000;       /* Percentage badges, CTA button */
  
  /* ==========================================================================
     3. LIGHT CANVAS & ELEVATED SURFACES
     ========================================================================== */
  --color-canvas-bg: #F4F7FC;           /* Main dashboard background canvas */
  --color-surface-card: #FFFFFF;        /* Elevated white cards */
  --color-surface-input: #FFFFFF;       /* Search bar and input surfaces */
  --color-surface-hover: #F8FAFD;       /* Hover state on white rows/cards */
  
  /* ==========================================================================
     4. TYPOGRAPHY & TEXT COLORS
     ========================================================================== */
  --color-text-primary: #12141A;        /* Headings, main numbers, primary labels */
  --color-text-secondary: #7E8695;      /* Subtitles, table headers, inactive dates */
  --color-text-muted: #A3ABB9;          /* Axis labels, placeholders, breadcrumbs */
  --color-text-white: #FFFFFF;          /* Text on dark sidebar and obsidian cards */
  --color-text-dark-on-lime: #0C0E12;   /* Text on lime pills and active items */
  --color-text-sidebar-muted: #8E95A5;  /* Inactive navigation link text */

  /* ==========================================================================
     5. BORDERS & DIVIDERS
     ========================================================================== */
  --color-border-subtle: #EDF2F7;       /* Table row dividers, search input borders */
  --color-border-card: rgba(0, 0, 0, 0.04); /* Subtle boundary for light cards */
  --color-border-dark: rgba(255, 255, 255, 0.08); /* Divider on obsidian surfaces */

  /* ==========================================================================
     6. DATA VISUALIZATION COLOR MAP
     ========================================================================== */
  --chart-series-lime: #D8FA42;         /* "Repeat Buyer", "Services", "MacBook Air" */
  --chart-series-teal: #36C6AF;         /* "New Buyer", "Volume", "Satisfied" */
  --chart-series-black: #12141A;        /* "Unsatisfied" bar */
  --chart-gridline: #EFF3F8;            /* Chart horizontal gridlines */
  --chart-tooltip-bg: #0C0E12;          /* Hover tooltip bubble */
  --chart-tooltip-text: #FFFFFF;        /* Tooltip text */
}
```

---

### 2.2 Typography Scale

The design system utilizes **Plus Jakarta Sans**, **Outfit**, or **Inter** as the primary font family with heavy emphasis on high-contrast weight pairing (`800/700` bold with `500/400` medium/regular).

```css
:root {
  --font-family-sans: "Plus Jakarta Sans", "Outfit", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --font-family-mono: "JetBrains Mono", "SF Mono", monospace;

  /* Font Sizes & Line Heights */
  --text-xs: 0.6875rem;   /* 11px */   --leading-xs: 0.875rem; /* 14px */
  --text-sm: 0.8125rem;   /* 13px */   --leading-sm: 1.125rem; /* 18px */
  --text-base: 0.9375rem; /* 15px */   --leading-base: 1.375rem; /* 22px */
  --text-md: 1.0625rem;   /* 17px */   --leading-md: 1.5rem;   /* 24px */
  --text-lg: 1.25rem;     /* 20px */   --leading-lg: 1.75rem;  /* 28px */
  --text-xl: 1.5rem;      /* 24px */   --leading-xl: 2rem;     /* 32px */
  --text-2xl: 1.875rem;   /* 30px */   --leading-2xl: 2.25rem; /* 36px */
  --text-3xl: 2.25rem;    /* 36px */   --leading-3xl: 2.75rem; /* 44px */

  /* Font Weights */
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --font-weight-extrabold: 800;

  /* Letter Spacing */
  --tracking-tight: -0.025em;
  --tracking-normal: 0em;
  --tracking-wide: 0.03em;
}
```

---

### 2.3 Spatial Scale & Radii

```css
:root {
  /* Spacing Scale (8pt System with 4pt half-steps) */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-5: 1.25rem;   /* 20px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-10: 2.5rem;   /* 40px */
  --space-12: 3rem;     /* 48px */

  /* Border Radii */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 20px;
  --radius-2xl: 24px;   /* Standard Card Radius */
  --radius-3xl: 32px;   /* Major Container Radius */
  --radius-full: 9999px; /* Pill Buttons, Search Bar, Progress Bars */

  /* Elevation & Shadows */
  --shadow-card: 0 4px 20px -2px rgba(18, 38, 63, 0.03), 0 2px 6px -1px rgba(18, 38, 63, 0.02);
  --shadow-card-hover: 0 12px 32px -4px rgba(18, 38, 63, 0.08), 0 4px 12px -2px rgba(18, 38, 63, 0.04);
  --shadow-pill: 0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow-tooltip: 0 8px 24px rgba(12, 14, 18, 0.25);
  --shadow-lime-glow: 0 4px 16px rgba(216, 250, 66, 0.35);
}
```

---

## 3. Tailwind CSS Configuration (v3 & v4 Compatible)

```javascript
// tailwind.config.js
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        lime: {
          DEFAULT: '#D8FA42',
          surface: '#DCF838',
          hover: '#C5E82F',
          light: '#F4FDC6',
        },
        teal: {
          DEFAULT: '#36C6AF',
          hover: '#2EB39E',
          pill: '#A7EDE0',
          light: '#D5F6F0',
        },
        obsidian: {
          900: '#0C0E12',
          800: '#12141A',
          700: '#1D2129',
          600: '#2A2E39',
        },
        canvas: '#F4F7FC',
        card: '#FFFFFF',
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', 'Outfit', 'Inter', 'sans-serif'],
      },
      borderRadius: {
        '2xl': '20px',
        '3xl': '24px',
        '4xl': '32px',
      },
      boxShadow: {
        'soft-card': '0 4px 20px -2px rgba(18, 38, 63, 0.03)',
        'soft-hover': '0 12px 32px -4px rgba(18, 38, 63, 0.08)',
        'lime-glow': '0 4px 16px rgba(216, 250, 66, 0.35)',
      }
    },
  },
  plugins: [],
}
```

---

## 4. Component Blueprints & Architecture

### 4.1 Shell Layout (Sidebar + Topbar + Content Grid)

```
+-----------------------------------------------------------------------------------------------+
| SIDEBAR (Obsidian #0C0E12)  | TOPBAR (White Canvas #F4F7FC)                                   |
|                             | [ 🔍 Tap here to search...   v ]     [🔔] [💬] [👤 James McGill]|
| [Logo] GoodBoard            +-----------------------------------------------------------------+
|                             | MAIN DASHBOARD CONTENT GRID (3 Columns / Multi-row)             |
| (•) Dashboard (Lime Pill)   | +------------------------------------+ +----------------------+ |
|  •  Leaderboard             | | Today's Sales [Export ↥]          | | Volume Service Level | |
|  •  Order                   | | +--------+ +--------+ +--------+   | | [Bar Chart: Teal/    | |
|  •  Sales Report            | | | $1k    | | 350    | | 345    |   | |  Lime Stacked]       | |
|  •  Settings                | | | Total  | | Orders | | Buyers |   | |                      | |
|  •  Sign Out                | | | [+20%] | | [+10%] | | [+40%] |   | | Vol: 1,135  Svc: 635 | |
|                             | | +--------+ +--------+ +--------+   | +----------------------+ |
| +-------------------------+ | +------------------------------------+                          |
| | PROMO WIDGET (Lime Card)| | +----------------------+ +------------------------------------+ |
| |  GO+  [3D Squiggle]     | | | Buyer Satisfaction   | | Today's Sales (Multi-line Chart)   | |
| |  Get all features...    | | | (Lime Card + Watermk)| | [Teal Line + Lime Line]            | |
| |  [Go Pro now ↥]         | | | [Teal/Black Bars]    | |   Hover: [ 250 Buyer ] (Black Pill)| |
| +-------------------------+ | +----------------------+ +------------------------------------+ |
|                             | +------------------------------------+ +----------------------+ |
|                             | | Top Products Table                 | | Volume Service Level | |
|                             | | 01 MacBook Air       [====] [70%]  | | (Global Map View)    | |
|                             | | 02 USB-C Adapter     [=== ] [58%]  | | [World Vector Dots + | |
|                             | | 03 Mac Pro Feet      [=   ] [18%]  | |  Teal Highlight]     | |
|                             | +------------------------------------+ +----------------------+ |
+-----------------------------------------------------------------------------------------------+
```

---

### 4.2 Sidebar Navigation Component

#### Key Specifications:
- **Background**: Solid `#0C0E12`.
- **Width**: `240px` fixed desktop width.
- **Logo**: Crisp bold typography with geometric circles (`GoodBoard`), text color `#FFFFFF`, `20px` bold.
- **Active Nav Item**: Full pill container (`border-radius: 9999px`), background `var(--color-electric-lime)` (`#D8FA42`), text color `#000000` (extra bold), with solid black glyph icon.
- **Inactive Nav Items**: Transparent background, text color `#8E95A5`, clean 1.5px monoline vector icons, hover transitions to `#FFFFFF` with slight background shift `rgba(255, 255, 255, 0.05)`.
- **Sign Out Action**: Placed at bottom of standard nav links with distinct exit icon.

```html
<aside class="sidebar">
  <div class="sidebar-brand">
    <span class="brand-text">GoodBoard</span>
  </div>

  <nav class="sidebar-nav">
    <a href="#" class="nav-item active">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="currentColor"><!-- Dashboard Grid Icon --></svg>
      <span>Dashboard</span>
    </a>
    <a href="#" class="nav-item">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><!-- Bar Chart Icon --></svg>
      <span>Leaderboard</span>
    </a>
    <a href="#" class="nav-item">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><!-- Cart Icon --></svg>
      <span>Order</span>
    </a>
    <a href="#" class="nav-item">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><!-- Analytics Spark Icon --></svg>
      <span>Sales Report</span>
    </a>
    <a href="#" class="nav-item">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><!-- Gear Icon --></svg>
      <span>Settings</span>
    </a>
    <a href="#" class="nav-item sign-out">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor"><!-- Exit Icon --></svg>
      <span>Sign Out</span>
    </a>
  </nav>

  <!-- Floating Upgrade Card -->
  <div class="upgrade-card">
    <div class="upgrade-header">
      <span class="upgrade-title">GO<span class="plus">+</span></span>
      <div class="upgrade-art">
        <svg class="squiggle" viewBox="0 0 100 100"><!-- 3D Smooth Tube Squiggle --></svg>
      </div>
    </div>
    <p class="upgrade-sub">Get all features on GoodBoard</p>
    <button class="upgrade-btn">
      <span>Go Pro now</span>
      <svg class="btn-arrow" viewBox="0 0 16 16"><!-- Upward Arrow --></svg>
    </button>
  </div>
</aside>
```

---

### 4.3 Inverted Obsidian KPI Metric Cards

These cards create the distinct signature look of the GoodBoard UI: dark obsidian backgrounds contrasting against the bright white card container.

#### Visual Hierarchy:
1. **Top Row**: Circular icon badge (`40px x 40px`, white background `#FFFFFF` with black vector glyph) on the left + subtle diagonal top-right link arrow (`↗`) on the right.
2. **Center Metric**: Ultra-bold stat counter (`$1k`, `350`, `345`) in crisp white (`#FFFFFF`, `28px` bold) + subtitle (`Total Sales`, `Total Order`, `New Buyers`) in muted gray (`#8D95A5`, `13px`).
3. **Bottom Pill**: Full width or inline rounded badge (`border-radius: 9999px`), background `var(--color-electric-lime)` or `var(--color-cyber-teal-pill)`, text `+20% from last month` in deep obsidian bold text.

```html
<div class="kpi-card obsidian">
  <div class="kpi-top">
    <div class="kpi-icon-bubble">
      <svg class="kpi-icon" viewBox="0 0 24 24"><!-- Rocket / Shapes / User-Plus Icon --></svg>
    </div>
    <button class="kpi-arrow-btn" aria-label="View details">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M7 17L17 7M17 7H7M17 7V17" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>
  </div>

  <div class="kpi-content">
    <div class="kpi-value">$1k</div>
    <div class="kpi-label">Total Sales</div>
  </div>

  <div class="kpi-badge lime-pill">
    <span>+20% from last month</span>
  </div>
</div>
```

```css
.kpi-card.obsidian {
  background-color: #0C0E12;
  border-radius: 20px;
  padding: 20px 18px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 180px;
  color: #FFFFFF;
  position: relative;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.2s ease;
}

.kpi-card.obsidian:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px -4px rgba(0, 0, 0, 0.3);
}

.kpi-icon-bubble {
  width: 44px;
  height: 44px;
  background: #FFFFFF;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0C0E12;
}

.kpi-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: #FFFFFF;
  letter-spacing: -0.03em;
  line-height: 1.1;
}

.kpi-label {
  font-size: 0.8125rem;
  color: #8E95A5;
  font-weight: 500;
  margin-top: 4px;
}

.kpi-badge.lime-pill {
  background-color: #D8FA42;
  color: #0C0E12;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 14px;
  width: fit-content;
}
```

---

### 4.4 Buyer Satisfaction Accent Card (Lime Callout)

A dedicated, eye-catching card featuring full Electric Lime background styling with abstract circular wave line-art watermark in the top right.

#### Specs:
- **Background**: Solid `#DCF838` (Electric Lime).
- **Watermark**: Concentric circular vector stroke arcs `rgba(0, 0, 0, 0.08)` in top-right corner.
- **Card Title**: `Buyer Satisfaction` (`18px` Bold `#0C0E12`).
- **Bar Elements**:
  - Satisfied Bars: Solid Teal `#36C6AF`.
  - Unsatisfied Bars: Solid Obsidian `#0C0E12`.
  - Radius on Bars: `4px` top rounded (`border-top-left-radius: 4px`, `border-top-right-radius: 4px`).
- **Legend**: Inline dot/square indicators `■ Satisfied` (Teal), `■ Unsatisfied` (Obsidian).

---

### 4.5 Smooth Spline Curve Chart & Floating Interactive Tooltip

#### Visual Construction:
- **Grid Lines**: Horizontal dashed or ultra-soft solid lines `#EFF3F8` at intervals `0, 100, 200, 300, 400`.
- **Curves**:
  - Series 1 (Repeat Buyer): Electric Lime curve `#D8FA42`, stroke width `3px`, smooth cubic bezier interpolations (`curveCatmullRom` or `curveMonotoneX`).
  - Series 2 (New Buyer): Cyber Teal curve `#36C6AF`, stroke width `3px`.
- **Interactive Tooltip Pointer**:
  - Target Node: Glowing cyan/teal inner dot surrounded by a semi-transparent ring.
  - Tooltip Bubble: Solid obsidian `#0C0E12` pill badge with rounded corner caret arrow pointing to the node.
  - Typography: Pure white text `"250 Buyer"`, `12px` bold.

```css
.chart-tooltip-bubble {
  background: #0C0E12;
  color: #FFFFFF;
  font-size: 0.8125rem;
  font-weight: 700;
  padding: 8px 16px;
  border-radius: 9999px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
  position: absolute;
  transform: translate(-50%, -130%);
  white-space: nowrap;
  pointer-events: none;
  z-index: 20;
}

.chart-tooltip-bubble::after {
  content: '';
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 8px;
  height: 8px;
  background: #0C0E12;
}
```

---

### 4.6 Dual-Tone Stacked Bar Chart ("Volume Service Level")

#### Specs:
- **Structure**: Vertical rectangular pill bars with stacked sections.
- **Top Segment**: Cyber Teal `#36C6AF` (Volume).
- **Bottom Segment**: Electric Lime `#D8FA42` (Services).
- **Segment Transitions**: Seamless flush alignment with pill radius on outer ends (`6px` rounded corners).
- **Bottom Legend / Aggregate Stat Row**:
  - Left Stat: `■ Volume` (Teal square) -> `1,135` bold value.
  - Right Stat: `■ Services` (Lime square) -> `635` bold value.

---

### 4.7 Top Products Table with Dual-Color Progress Bars

#### Specs:
- **Layout**: Clean tabular list with zero harsh vertical borders.
- **Column Headers**: `#`, `Name`, `Popularity`, `Sales` in soft slate `#7E8695`, `12px` medium.
- **Item Row Index**: `#01, #02, #03, #04` in light gray mono/sans `#8E95A5`.
- **Product Name**: Semi-bold `#12141A`, `14px`.
- **Progress Track**: Background `#F0F4FA`, height `8px`, `border-radius: 9999px`.
- **Progress Fill**:
  - Alternate between Electric Lime (`#D8FA42`) and Cyber Teal (`#36C6AF`).
  - Fill indicator is smoothly rounded on both ends.
- **Sales Percentage Badge**: Solid obsidian capsule (`#0C0E12`), text `#FFFFFF` (`70%`, `58%`, `18%`, `7%`), `11px` bold.

```html
<div class="product-row">
  <span class="product-index">01</span>
  <span class="product-name">MacBook Air</span>
  <div class="progress-container">
    <div class="progress-track">
      <div class="progress-fill lime" style="width: 70%;"></div>
    </div>
  </div>
  <div class="sales-pill">70%</div>
</div>
```

---

### 4.8 Global Geographic Sales Map

#### Specs:
- **Map Style**: Minimalist vector dot or polygonal world silhouette in soft slate-gray `#E5EAF2`.
- **Active Sales Regions**: North America, parts of Africa, Europe, Australia highlighted in Cyber Teal `#36C6AF`.
- **Legend**: Bottom left `■ Sales Area` (Teal indicator + slate text).

---

## 5. Omnibar Search & Header Controls

#### Specs:
- **Search Pill**:
  - Background: Pure white `#FFFFFF`.
  - Shape: Continuous pill `border-radius: 9999px`.
  - Border: Subtle `1px solid #EDF2F7`.
  - Icon: Monoline Search Glyph (`🔍`).
  - Placeholder: `"Tap here to search..."` in `#A3ABB9`.
  - Right Adornment: Subtle chevron down `v` or shortcut badge `⌘K`.
- **Notification & Chat Cluster**:
  - Circular buttons (`40px x 40px`, `#FFFFFF`, soft shadow).
  - Status dot: Electric Lime or Coral Red on top-right badge.
- **User Profile Pill**:
  - Circular avatar (`38px`) with illustrated character / avatar photo.
  - User name: `"James McGill"` (`14px` bold `#12141A`).
  - User role: `"Sales Manager"` (`11px` regular `#7E8695`).
  - Chevron dropdown icon.

---

## 6. Micro-Interactions & Animation Standards

```css
/* Smooth interaction variables */
:root {
  --ease-spring: cubic-bezier(0.16, 1, 0.3, 1);
  --duration-fast: 150ms;
  --duration-normal: 250ms;
}

/* Card Hover Elevation */
.dashboard-card {
  transition: transform var(--duration-normal) var(--ease-spring),
              box-shadow var(--duration-normal) var(--ease-spring);
}

.dashboard-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card-hover);
}

/* Button & Pill Press Feedback */
.btn-pill, .upgrade-btn, .kpi-arrow-btn {
  transition: transform var(--duration-fast) ease, background-color var(--duration-fast) ease;
}

.btn-pill:active, .upgrade-btn:active {
  transform: scale(0.97);
}

/* Progress Bar Initial Load Animation */
@keyframes progressFill {
  from { width: 0%; }
  to { width: var(--target-width); }
}

.progress-fill {
  animation: progressFill 1s var(--ease-spring) forwards;
}
```

---

## 7. AI System Prompt Directive (For Autonomous Generation)

> **Copy and paste this directive directly into Claude, Gemini, ChatGPT, Cursor Rules, or any AI coding tool to generate pixel-perfect GoodBoard-themed UIs.**

```markdown
# Role & Aesthetic Directive: GoodBoard Neo-Electric Design System

When designing or writing frontend code for this application, strictly adhere to the "GoodBoard" Neo-Electric Design System:

1. COLOR PALETTE:
   - Sidebar Background: Solid Obsidian Black `#0C0E12`
   - Main Canvas Background: Soft Ice Pearl `#F4F7FC`
   - Primary Cards: Pure White `#FFFFFF` with 24px rounded corners (`rounded-3xl`)
   - Inverted Hero KPI Cards: Jet Black `#0C0E12` / `#12141A` with pure white text and Electric Lime status pills
   - Electric Lime (Primary Accent): `#D8FA42` / `#DCF838` (Active nav pill, repeat buyer curve, progress fill)
   - Cyber Teal (Secondary Accent): `#36C6AF` (New buyer curve, volume bars, satisfied metric)
   - Badge & Capsule Background: Solid Black `#000000` with white text for percentage pills (`70%`, `58%`)

2. TYPOGRAPHY & WEIGHTS:
   - Font Family: 'Plus Jakarta Sans', 'Outfit', or 'Inter'
   - Hero Numbers: Extra-bold 800 with tight tracking (-0.03em)
   - Card Titles: Bold 700 with deep neutral #12141A
   - Subtitles & Labels: Medium 500 in muted slate #7E8695

3. GEOMETRY & RADII:
   - Main Dashboard Cards: `border-radius: 24px` (`rounded-3xl`)
   - KPI Inner Cards: `border-radius: 20px` (`rounded-2xl`)
   - Search Bars, Buttons, Status Badges, Tooltips: Full pill `border-radius: 9999px` (`rounded-full`)
   - Avoid sharp rectangular borders or harsh 1px black borders on cards.

4. COMPONENT SIGNATURES:
   - Sidebar: Include brand logo "GoodBoard", active nav link in an Electric Lime pill with black text/icon, and a bottom "GO+" upgrade promo card in Electric Lime with a 3D tube squiggle and black "Go Pro now" pill CTA.
   - Header: Omnibar search pill with search icon, notification/message icons, and user avatar with name/role subtitles.
   - Data Visualizations: Use dual-tone Lime and Teal curves with a floating black tooltip (`#0C0E12` pill with arrow) on active data points.
   - Table: Clean borderless list with multi-color capsule progress bars and black percentage pills.
```

---

## 8. Standalone Complete Implementation Template (HTML/CSS)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GoodBoard — Executive Sales Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Plus Jakarta Sans', sans-serif;
      background-color: #F4F7FC;
      color: #12141A;
      display: flex;
      min-height: 100vh;
      overflow-x: hidden;
    }

    /* ==========================================================================
       SIDEBAR
       ========================================================================== */
    .sidebar {
      width: 250px;
      background-color: #0C0E12;
      color: #FFFFFF;
      padding: 32px 20px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      flex-shrink: 0;
    }

    .brand-logo {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.03em;
      color: #FFFFFF;
      margin-bottom: 36px;
      padding-left: 12px;
    }

    .nav-list {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .nav-link {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 12px 18px;
      border-radius: 9999px;
      color: #8E95A5;
      text-decoration: none;
      font-size: 14px;
      font-weight: 600;
      transition: all 0.2s ease;
    }

    .nav-link:hover {
      color: #FFFFFF;
      background-color: rgba(255, 255, 255, 0.05);
    }

    .nav-link.active {
      background-color: #D8FA42;
      color: #0C0E12;
      font-weight: 700;
    }

    .nav-link.sign-out {
      margin-top: 24px;
      color: #D8FA42;
    }

    /* Upgrade Promo Card */
    .promo-card {
      background-color: #DCF838;
      border-radius: 24px;
      padding: 24px 18px;
      color: #0C0E12;
      margin-top: auto;
      position: relative;
      overflow: hidden;
    }

    .promo-badge {
      font-size: 20px;
      font-weight: 800;
      letter-spacing: -0.02em;
    }

    .promo-desc {
      font-size: 12px;
      font-weight: 600;
      margin: 16px 0 14px 0;
      line-height: 1.4;
    }

    .promo-btn {
      width: 100%;
      background-color: #0C0E12;
      color: #FFFFFF;
      border: none;
      border-radius: 9999px;
      padding: 10px 16px;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      transition: transform 0.15s ease;
    }

    .promo-btn:hover {
      transform: scale(1.02);
    }

    /* ==========================================================================
       MAIN CONTENT WRAPPER
       ========================================================================== */
    .main-wrapper {
      flex: 1;
      display: flex;
      flex-direction: column;
      padding: 24px 36px 36px 36px;
      gap: 24px;
      max-width: 1440px;
      margin: 0 auto;
      width: 100%;
    }

    /* ==========================================================================
       TOPBAR
       ========================================================================== */
    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 20px;
    }

    .search-pill {
      background-color: #FFFFFF;
      border-radius: 9999px;
      padding: 12px 24px;
      display: flex;
      align-items: center;
      gap: 12px;
      width: 380px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    }

    .search-pill input {
      border: none;
      outline: none;
      font-family: inherit;
      font-size: 13px;
      color: #12141A;
      width: 100%;
    }

    .search-pill input::placeholder {
      color: #A3ABB9;
    }

    .topbar-actions {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .icon-btn {
      width: 42px;
      height: 42px;
      border-radius: 50%;
      background-color: #FFFFFF;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      color: #12141A;
      cursor: pointer;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
    }

    .user-profile {
      display: flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      margin-left: 8px;
    }

    .user-avatar {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #FFE3D1;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
    }

    .user-meta .user-name {
      font-size: 14px;
      font-weight: 700;
      color: #12141A;
    }

    .user-meta .user-role {
      font-size: 11px;
      font-weight: 500;
      color: #7E8695;
    }

    /* ==========================================================================
       DASHBOARD GRID SYSTEM
       ========================================================================== */
    .dashboard-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
    }

    .card {
      background-color: #FFFFFF;
      border-radius: 24px;
      padding: 24px;
      box-shadow: 0 4px 20px -2px rgba(18, 38, 63, 0.03);
    }

    .card-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 20px;
    }

    .card-title {
      font-size: 16px;
      font-weight: 700;
      color: #12141A;
    }

    .card-subtitle {
      font-size: 12px;
      font-weight: 500;
      color: #7E8695;
      margin-top: 2px;
    }

    .export-btn {
      background: #FFFFFF;
      border: 1px solid #E2E8F0;
      border-radius: 9999px;
      padding: 6px 14px;
      font-size: 12px;
      font-weight: 700;
      color: #12141A;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
    }

    /* Today's Sales 3 KPI Cards */
    .kpi-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
    }

    .kpi-card {
      background-color: #0C0E12;
      border-radius: 20px;
      padding: 18px;
      color: #FFFFFF;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }

    .kpi-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
    }

    .kpi-icon-wrap {
      width: 40px;
      height: 40px;
      border-radius: 50%;
      background: #FFFFFF;
      color: #0C0E12;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
    }

    .kpi-value {
      font-size: 26px;
      font-weight: 800;
      letter-spacing: -0.03em;
      line-height: 1;
    }

    .kpi-label {
      font-size: 12px;
      color: #8E95A5;
      margin-top: 4px;
      font-weight: 500;
    }

    .kpi-trend {
      background-color: #D8FA42;
      color: #0C0E12;
      font-size: 11px;
      font-weight: 700;
      padding: 6px 12px;
      border-radius: 9999px;
      margin-top: 14px;
      width: fit-content;
    }

    /* Buyer Satisfaction Lime Card */
    .satisfaction-card {
      background-color: #DCF838;
      border-radius: 24px;
      padding: 24px;
      position: relative;
    }

    /* Products Table */
    .product-table {
      width: 100%;
      border-collapse: collapse;
    }

    .product-table th {
      text-align: left;
      font-size: 12px;
      color: #7E8695;
      font-weight: 500;
      padding-bottom: 14px;
    }

    .product-table td {
      padding: 12px 0;
      font-size: 13px;
      font-weight: 600;
      border-top: 1px solid #F4F7FC;
    }

    .progress-bar-wrap {
      background-color: #F0F4FA;
      height: 8px;
      border-radius: 9999px;
      width: 100%;
      overflow: hidden;
    }

    .progress-bar-fill {
      height: 100%;
      border-radius: 9999px;
    }

    .fill-lime { background-color: #D8FA42; }
    .fill-teal { background-color: #36C6AF; }

    .sales-badge {
      background-color: #0C0E12;
      color: #FFFFFF;
      font-size: 11px;
      font-weight: 700;
      padding: 4px 10px;
      border-radius: 9999px;
      display: inline-block;
    }
  </style>
</head>
<body>

  <!-- Sidebar -->
  <aside class="sidebar">
    <div>
      <div class="brand-logo">GoodBoard</div>
      <ul class="nav-list">
        <li><a href="#" class="nav-link active"><span>📊</span> Dashboard</a></li>
        <li><a href="#" class="nav-link"><span>📈</span> Leaderboard</a></li>
        <li><a href="#" class="nav-link"><span>🛒</span> Order</a></li>
        <li><a href="#" class="nav-link"><span>📑</span> Sales Report</a></li>
        <li><a href="#" class="nav-link"><span>⚙️</span> Settings</a></li>
        <li><a href="#" class="nav-link sign-out"><span>🚪</span> Sign Out</a></li>
      </ul>
    </div>

    <!-- Promo Widget -->
    <div class="promo-card">
      <div class="promo-badge">GO+</div>
      <div class="promo-desc">Get all features on GoodBoard</div>
      <button class="promo-btn">Go Pro now ↥</button>
    </div>
  </aside>

  <!-- Main Container -->
  <main class="main-wrapper">
    
    <!-- Topbar -->
    <header class="topbar">
      <div class="search-pill">
        <span>🔍</span>
        <input type="text" placeholder="Tap here to search...">
        <span style="color: #A3ABB9; font-size: 11px;">▼</span>
      </div>

      <div class="topbar-actions">
        <button class="icon-btn">🔔</button>
        <button class="icon-btn">💬</button>
        <div class="user-profile">
          <div class="user-avatar">👨‍💼</div>
          <div class="user-meta">
            <div class="user-name">James McGill</div>
            <div class="user-role">Sales Manager</div>
          </div>
          <span style="color: #A3ABB9; font-size: 11px; margin-left: 4px;">▼</span>
        </div>
      </div>
    </header>

    <!-- Grid Row 1 -->
    <div class="dashboard-grid">
      
      <!-- Today's Sales Card -->
      <section class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">Today's Sales</h2>
            <p class="card-subtitle">Sales Summary</p>
          </div>
          <button class="export-btn">Export ↥</button>
        </div>

        <div class="kpi-row">
          <!-- Metric 1 -->
          <div class="kpi-card">
            <div class="kpi-header">
              <div class="kpi-icon-wrap">🚀</div>
              <span>↗</span>
            </div>
            <div>
              <div class="kpi-value">$1k</div>
              <div class="kpi-label">Total Sales</div>
            </div>
            <div class="kpi-trend">+20% from last month</div>
          </div>

          <!-- Metric 2 -->
          <div class="kpi-card">
            <div class="kpi-header">
              <div class="kpi-icon-wrap">📦</div>
              <span>↗</span>
            </div>
            <div>
              <div class="kpi-value">350</div>
              <div class="kpi-label">Total Order</div>
            </div>
            <div class="kpi-trend">+10% from last month</div>
          </div>

          <!-- Metric 3 -->
          <div class="kpi-card">
            <div class="kpi-header">
              <div class="kpi-icon-wrap">👤</div>
              <span>↗</span>
            </div>
            <div>
              <div class="kpi-value">345</div>
              <div class="kpi-label">New Buyers</div>
            </div>
            <div class="kpi-trend">+40% from last month</div>
          </div>
        </div>
      </section>

      <!-- Volume Service Level -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">Volume Service Level</h2>
        </div>
        <!-- Dual Stacked Bars Simulation -->
        <div style="display: flex; justify-content: space-around; align-items: flex-end; height: 130px; margin-top: 10px;">
          <div style="width: 14px; height: 110px; background: #36C6AF; border-radius: 4px; position: relative;">
            <div style="position: absolute; bottom: 0; width: 100%; height: 50px; background: #D8FA42; border-radius: 0 0 4px 4px;"></div>
          </div>
          <div style="width: 14px; height: 130px; background: #36C6AF; border-radius: 4px; position: relative;">
            <div style="position: absolute; bottom: 0; width: 100%; height: 75px; background: #D8FA42; border-radius: 0 0 4px 4px;"></div>
          </div>
          <div style="width: 14px; height: 95px; background: #36C6AF; border-radius: 4px; position: relative;">
            <div style="position: absolute; bottom: 0; width: 100%; height: 60px; background: #D8FA42; border-radius: 0 0 4px 4px;"></div>
          </div>
          <div style="width: 14px; height: 105px; background: #36C6AF; border-radius: 4px; position: relative;">
            <div style="position: absolute; bottom: 0; width: 100%; height: 45px; background: #D8FA42; border-radius: 0 0 4px 4px;"></div>
          </div>
          <div style="width: 14px; height: 80px; background: #36C6AF; border-radius: 4px; position: relative;">
            <div style="position: absolute; bottom: 0; width: 100%; height: 40px; background: #D8FA42; border-radius: 0 0 4px 4px;"></div>
          </div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 20px; font-size: 11px; color: #7E8695;">
          <div><span style="color: #36C6AF;">■</span> Volume <b>1,135</b></div>
          <div><span style="color: #D8FA42;">■</span> Services <b>635</b></div>
        </div>
      </section>
    </div>

    <!-- Grid Row 2 -->
    <div class="dashboard-grid">
      <!-- Buyer Satisfaction -->
      <section class="satisfaction-card">
        <h2 class="card-title">Buyer Satisfaction</h2>
        <div style="display: flex; justify-content: space-around; align-items: flex-end; height: 130px; margin-top: 15px;">
          <div style="width: 10px; height: 80px; background: #36C6AF; border-radius: 2px;"></div>
          <div style="width: 10px; height: 40px; background: #0C0E12; border-radius: 2px;"></div>
          <div style="width: 10px; height: 60px; background: #36C6AF; border-radius: 2px;"></div>
          <div style="width: 10px; height: 75px; background: #0C0E12; border-radius: 2px;"></div>
          <div style="width: 10px; height: 65px; background: #36C6AF; border-radius: 2px;"></div>
          <div style="width: 10px; height: 45px; background: #0C0E12; border-radius: 2px;"></div>
          <div style="width: 10px; height: 95px; background: #36C6AF; border-radius: 2px;"></div>
          <div style="width: 10px; height: 80px; background: #0C0E12; border-radius: 2px;"></div>
        </div>
        <div style="display: flex; gap: 14px; margin-top: 16px; font-size: 11px; font-weight: 600;">
          <div><span style="color: #36C6AF;">■</span> Satisfied</div>
          <div><span style="color: #0C0E12;">■</span> Unsatisfied</div>
        </div>
      </section>

      <!-- Multi-Line Chart (Today's Sales) -->
      <section class="card" style="position: relative;">
        <div class="card-header">
          <h2 class="card-title">Today's Sales</h2>
        </div>
        
        <!-- Interactive Tooltip Mockup -->
        <div style="position: absolute; top: 75px; right: 230px; background: #0C0E12; color: #FFFFFF; font-size: 11px; font-weight: 700; padding: 6px 12px; border-radius: 9999px;">
          250 Buyer
        </div>

        <!-- SVG Line Curves -->
        <svg viewBox="0 0 500 130" style="width: 100%; height: 130px; overflow: visible;">
          <line x1="0" y1="30" x2="500" y2="30" stroke="#EFF3F8" stroke-width="1" stroke-dasharray="3"/>
          <line x1="0" y1="70" x2="500" y2="70" stroke="#EFF3F8" stroke-width="1" stroke-dasharray="3"/>
          <line x1="0" y1="110" x2="500" y2="110" stroke="#EFF3F8" stroke-width="1" stroke-dasharray="3"/>
          
          <!-- Teal Curve -->
          <path d="M0,110 Q80,20 180,50 T320,50 T500,60" fill="none" stroke="#36C6AF" stroke-width="3" stroke-linecap="round"/>
          <!-- Lime Curve -->
          <path d="M0,90 Q80,40 180,30 T320,40 T500,60" fill="none" stroke="#D8FA42" stroke-width="3" stroke-linecap="round"/>
          
          <!-- Node Dot -->
          <circle cx="265" cy="48" r="4" fill="#36C6AF" stroke="#FFFFFF" stroke-width="2"/>
        </svg>

        <div style="display: flex; justify-content: space-between; font-size: 10px; color: #A3ABB9; margin-top: 10px;">
          <span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span><span>June</span><span>July</span><span>Aug</span><span>Sept</span><span>Oct</span><span>Nov</span><span>Dec</span>
        </div>
      </section>
    </div>

    <!-- Grid Row 3 -->
    <div class="dashboard-grid">
      <!-- Top Products Table -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">Top Products</h2>
        </div>
        <table class="product-table">
          <thead>
            <tr>
              <th style="width: 8%;">#</th>
              <th style="width: 42%;">Name</th>
              <th style="width: 35%;">Popularity</th>
              <th style="width: 15%; text-align: right;">Sales</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style="color: #7E8695;">01</td>
              <td>MacBook Air</td>
              <td>
                <div class="progress-bar-wrap">
                  <div class="progress-bar-fill fill-lime" style="width: 70%;"></div>
                </div>
              </td>
              <td style="text-align: right;"><span class="sales-badge">70%</span></td>
            </tr>
            <tr>
              <td style="color: #7E8695;">02</td>
              <td>USB-C VGA Multiport Adapter</td>
              <td>
                <div class="progress-bar-wrap">
                  <div class="progress-bar-fill fill-teal" style="width: 58%;"></div>
                </div>
              </td>
              <td style="text-align: right;"><span class="sales-badge">58%</span></td>
            </tr>
            <tr>
              <td style="color: #7E8695;">03</td>
              <td>Mac Pro Feet Kit</td>
              <td>
                <div class="progress-bar-wrap">
                  <div class="progress-bar-fill fill-lime" style="width: 18%;"></div>
                </div>
              </td>
              <td style="text-align: right;"><span class="sales-badge">18%</span></td>
            </tr>
            <tr>
              <td style="color: #7E8695;">04</td>
              <td>Apple 30-pin to USB Cable</td>
              <td>
                <div class="progress-bar-wrap">
                  <div class="progress-bar-fill fill-teal" style="width: 7%;"></div>
                </div>
              </td>
              <td style="text-align: right;"><span class="sales-badge">7%</span></td>
            </tr>
          </tbody>
        </table>
      </section>

      <!-- Global Map Area -->
      <section class="card">
        <div class="card-header">
          <h2 class="card-title">Volume Service Level</h2>
        </div>
        <div style="display: flex; align-items: center; justify-content: center; height: 140px; color: #7E8695; font-size: 13px;">
          <!-- SVG Minimal Map Graphic -->
          <svg viewBox="0 0 300 150" style="width: 100%; height: 100%; opacity: 0.85;">
            <circle cx="80" cy="50" r="18" fill="#E5EAF2"/>
            <circle cx="100" cy="65" r="14" fill="#36C6AF"/>
            <circle cx="160" cy="60" r="22" fill="#E5EAF2"/>
            <circle cx="170" cy="80" r="18" fill="#36C6AF"/>
            <circle cx="230" cy="95" r="14" fill="#36C6AF"/>
            <circle cx="210" cy="50" r="16" fill="#E5EAF2"/>
          </svg>
        </div>
        <div style="font-size: 11px; color: #7E8695; margin-top: 8px;">
          <span style="color: #36C6AF;">■</span> Sales Area
        </div>
      </section>
    </div>

  </main>

</body>
</html>
```
