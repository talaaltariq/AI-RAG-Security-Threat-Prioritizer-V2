import type { Config } from "tailwindcss";

/**
 * ThreatIQ — Tailwind configuration
 * Design tokens strictly follow DESIGN_SYSTEM.md
 * ("Neo-Electric Slate & Obsidian / GoodBoard" design system v1.0.0)
 */
const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        /* ------------------------------------------------------------------
         * DESIGN_SYSTEM.md — 2.1 Complete Color Palette
         * ------------------------------------------------------------------ */
        // 1. Brand accents (Electric Energizers)
        lime: {
          DEFAULT: "#D7FF3F", // --color-electric-lime
          hover: "#C7F02B", // --color-electric-lime-hover
          light: "#F5FDE1", // --color-electric-lime-light
          surface: "#D7FF3F", // --color-electric-lime-surface
        },
        teal: {
          DEFAULT: "#36C6AF", // --color-cyber-teal
          hover: "#2EB39E", // --color-cyber-teal-hover
          light: "#D5F6F0", // --color-cyber-teal-light
          pill: "#A7EDE0", // --color-cyber-teal-pill
        },
        // 2. Obsidian & dark neutrals (sidebar & hero cards)
        obsidian: {
          900: "#0D0D10", // sidebar background, primary brand shell
          800: "#141418", // KPI hero cards, black tooltips
          700: "#1D2129", // hover state for dark elements
          600: "#2A2E39",
          pill: "#000000", // percentage badges, CTA button
        },
        // 3. Light canvas & elevated surfaces
        canvas: "#F6F7F9", // main dashboard background canvas
        surface: {
          card: "#FFFFFF",
          input: "#FFFFFF",
          hover: "#F8FAFD",
        },
        // 4. Typography & text colors
        content: {
          primary: "#0D0D10", // headings, main numbers
          secondary: "#7E8695", // subtitles, table headers
          muted: "#8A8F98", // axis labels, placeholders
          white: "#FFFFFF", // text on dark surfaces
          "on-lime": "#0D0D10", // text on lime pills / active items
          "sidebar-muted": "#8E95A5", // inactive navigation link text
        },
        // 5. Borders & dividers
        outline: {
          subtle: "#EDF2F7", // table row dividers, input borders
          card: "rgba(0, 0, 0, 0.04)", // subtle boundary for light cards
          dark: "rgba(255, 255, 255, 0.08)", // divider on obsidian surfaces
        },
        // 6. Data visualization color map
        chart: {
          lime: "#D7FF3F", // series 1
          teal: "#36C6AF", // series 2
          black: "#0D0D10", // series 3
          gridline: "#EFF3F8", // horizontal gridlines
          "tooltip-bg": "#0D0D10", // hover tooltip bubble
          "tooltip-text": "#FFFFFF", // tooltip text
          // shadcn chart tokens (mapped onto the DS palette)
          1: "hsl(var(--chart-1))",
          2: "hsl(var(--chart-2))",
          3: "hsl(var(--chart-3))",
          4: "hsl(var(--chart-4))",
          5: "hsl(var(--chart-5))",
        },

        /* ------------------------------------------------------------------
         * shadcn/ui semantic tokens (values defined in globals.css and
         * aligned with the DESIGN_SYSTEM.md palette)
         * ------------------------------------------------------------------ */
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: "hsl(var(--destructive))",
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        sidebar: {
          DEFAULT: "hsl(var(--sidebar))",
          foreground: "hsl(var(--sidebar-foreground))",
          primary: "hsl(var(--sidebar-primary))",
          "primary-foreground": "hsl(var(--sidebar-primary-foreground))",
          accent: "hsl(var(--sidebar-accent))",
          "accent-foreground": "hsl(var(--sidebar-accent-foreground))",
          border: "hsl(var(--sidebar-border))",
          ring: "hsl(var(--sidebar-ring))",
        },
      },
      fontFamily: {
        // DESIGN_SYSTEM.md — 2.2: Inter as primary sans, JetBrains Mono as mono
        sans: ["var(--font-sans)", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "SF Mono", "monospace"],
      },
      fontWeight: {
        regular: "400",
        medium: "500",
        semibold: "600",
        bold: "700",
        extrabold: "800",
      },
      letterSpacing: {
        tightest: "-0.03em", // hero numbers
        tight: "-0.025em",
        normal: "0em",
        wide: "0.03em",
      },
      borderRadius: {
        // DESIGN_SYSTEM.md — 2.3 Spatial Scale & Radii
        sm: "8px",
        md: "12px",
        lg: "16px",
        xl: "20px", // KPI inner cards
        "2xl": "24px", // standard dashboard card radius
        "3xl": "32px", // major container radius
        full: "9999px", // pill buttons, search bar, progress bars
      },
      boxShadow: {
        // DESIGN_SYSTEM.md — 2.3 Elevation & Shadows
        card: "0 4px 20px -2px rgba(18, 38, 63, 0.03), 0 2px 6px -1px rgba(18, 38, 63, 0.02)",
        "card-hover":
          "0 12px 32px -4px rgba(18, 38, 63, 0.08), 0 4px 12px -2px rgba(18, 38, 63, 0.04)",
        pill: "0 2px 8px rgba(0, 0, 0, 0.06)",
        tooltip: "0 8px 24px rgba(12, 14, 18, 0.25)",
        "lime-glow": "0 4px 16px rgba(216, 250, 66, 0.35)",
      },
      transitionTimingFunction: {
        // DESIGN_SYSTEM.md — 6. Micro-Interactions
        spring: "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      transitionDuration: {
        fast: "150ms",
        normal: "250ms",
      },
      keyframes: {
        "progress-fill": {
          from: { width: "0%" },
          to: { width: "var(--target-width)" },
        },
      },
      animation: {
        "progress-fill": "progress-fill 1s cubic-bezier(0.16, 1, 0.3, 1) forwards",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};
export default config;
