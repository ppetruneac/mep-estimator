/** @type {import('tailwindcss').Config} */
// Include dark-tremor palette so Tremor Card/Table dark:bg-dark-tremor-* work.

const tremorColors = [
  "slate",
  "gray",
  "zinc",
  "neutral",
  "stone",
  "red",
  "orange",
  "amber",
  "yellow",
  "lime",
  "green",
  "emerald",
  "teal",
  "cyan",
  "sky",
  "blue",
  "indigo",
  "violet",
  "purple",
  "fuchsia",
  "pink",
  "rose",
];
const shades = [
  "50",
  "100",
  "200",
  "300",
  "400",
  "500",
  "600",
  "700",
  "800",
  "900",
  "950",
];
const colorPattern = `(?:${tremorColors.join("|")})`;
const shadePattern = `(?:${shades.join("|")})`;

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@tremor/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    transparent: "transparent",
    current: "currentColor",
    extend: {
      colors: {
        tremor: {
          brand: {
            faint: "#eff6ff",
            muted: "#bfdbfe",
            subtle: "#60a5fa",
            DEFAULT: "#3b82f6",
            emphasis: "#1d4ed8",
            inverted: "#ffffff",
          },
          background: {
            muted: "#f9fafb",
            subtle: "#f3f4f6",
            DEFAULT: "#ffffff",
            emphasis: "#374151",
          },
          border: {
            DEFAULT: "#e5e7eb",
          },
          ring: {
            DEFAULT: "#e5e7eb",
          },
          content: {
            subtle: "#9ca3af",
            DEFAULT: "#6b7280",
            emphasis: "#374151",
            strong: "#111827",
            inverted: "#ffffff",
          },
        },
        "dark-tremor": {
          brand: {
            faint: "#1e1b4b",
            muted: "#312e81",
            subtle: "#4338ca",
            DEFAULT: "#6366f1",
            emphasis: "#818cf8",
            inverted: "#030712",
          },
          background: {
            muted: "#030712",
            subtle: "#111827",
            DEFAULT: "#111827",
            emphasis: "#e5e7eb",
          },
          border: {
            DEFAULT: "#1f2937",
          },
          ring: {
            DEFAULT: "#1f2937",
          },
          content: {
            subtle: "#6b7280",
            DEFAULT: "#9ca3af",
            emphasis: "#d1d5db",
            strong: "#f9fafb",
            inverted: "#030712",
          },
        },
      },
    },
  },
  darkMode: "class",
  safelist: [
    {
      pattern: new RegExp(
        `^(bg|text|border|ring|stroke|fill)-${colorPattern}-${shadePattern}$`
      ),
      variants: ["hover", "data-[selected]", "dark"],
    },
  ],
  plugins: [],
};
