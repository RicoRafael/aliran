import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0b0d10",
        panel: "#14181d",
        edge: "#242b33",
        muted: "#8b97a5",
        red: { flag: "#e5484d" },
        amber: { flag: "#f5a524" },
        green: { flag: "#46a758" },
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
    },
  },
  plugins: [],
};

export default config;
