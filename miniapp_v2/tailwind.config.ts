import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          yellow: "#FFC400",
          dark: "#0F172A",
          soft: "#FFF4C2",
        },
      },
      fontFamily: {
        sans: ["Outfit", "sans-serif"],
        display: ["Outfit", "sans-serif"],
      },
    },
  },
};

export default config;
