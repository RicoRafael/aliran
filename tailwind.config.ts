import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        panel: "var(--panel)",
        panel2: "var(--panel-2)",
        edge: "var(--edge)",
        ink: "var(--text)",
        muted: "var(--muted)",
        dim: "var(--dim)",
        sig: {
          red: "var(--sig-red)",
          amber: "var(--sig-amber)",
          green: "var(--sig-green)",
          dim: "var(--sig-dim)",
        },
        link: "var(--link)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      borderRadius: {
        DEFAULT: "2px",
        sm: "1px",
      },
    },
  },
  plugins: [],
};

export default config;
