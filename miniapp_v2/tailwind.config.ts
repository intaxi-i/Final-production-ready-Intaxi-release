import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        brand: { yellow: "#F5C242", dark: "#1E293B", slate: "#94A3B8" }
      },
      borderRadius: { "3xl": "1.5rem" },
      boxShadow: { "premium": "0 10px 25px -5px rgba(0, 0, 0, 0.05)" }
    }
  },
  plugins: []
};
export default config;