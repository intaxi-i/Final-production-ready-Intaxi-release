import type { Config } from "tailwindcss";
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: { brand: { yellow: "#F5C242", dark: "#0F172A" } },
      fontFamily: { sans: ["Inter", "sans-serif"], display: ["Montserrat", "sans-serif"] }
    }
  }
};
export default config;