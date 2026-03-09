import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'IBM Plex Mono'", "monospace"],
        sans: ["'DM Sans'", "sans-serif"],
      },
      colors: {
        bg: "#080b0f",
        surface: "#0e1318",
        border: "#1e2830",
        muted: "#3a4a56",
        text: "#c8d4dc",
        bright: "#e8f0f5",
        green: "#00e87a",
        amber: "#ffb700",
        orange: "#ff7322",
        red: "#ff2d4e",
        blue: "#00b4ff",
      },
    },
  },
  plugins: [],
};
export default config;
