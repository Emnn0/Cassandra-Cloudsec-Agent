import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      colors: {
        bg:       "#060D17",
        surface:  "#0D1B2E",
        surface2: "#132238",
        border:   "#1E3A5F",
        accent:   "#00D4FF",
        crimson:  "#EF2B2D",
        navy:     "#0F172A",
      },
      boxShadow: {
        glow:     "0 0 20px rgba(0, 212, 255, 0.12)",
        "glow-red":"0 0 20px rgba(239, 43, 45, 0.15)",
      },
    },
  },
  plugins: [],
};

export default config;