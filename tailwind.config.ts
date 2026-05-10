import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./src/app/**/*.{js,ts,jsx,tsx,mdx}', './src/components/**/*.{js,ts,jsx,tsx,mdx}', './src/context/**/*.{js,ts,jsx,tsx,mdx}', './src/lib/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-manrope)', 'system-ui', 'sans-serif'],
        display: ['var(--font-unbounded)', 'var(--font-manrope)', 'system-ui', 'sans-serif'],
      },
      colors: {
        app: {
          bg: 'var(--app-bg)',
          surface: 'var(--app-surface)',
          surfaceSoft: 'var(--app-surface-soft)',
          border: 'var(--app-border)',
          text: 'var(--app-text)',
          muted: 'var(--app-muted)',
          accent: 'var(--app-accent)',
          accentText: 'var(--app-accent-text)',
          header: 'var(--app-header)',
          dangerBg: 'var(--app-danger-bg)',
          dangerText: 'var(--app-danger-text)',
        },
        brand: {
          yellow: '#FFC400',
          yellowSoft: '#FFD84D',
          yellowDark: '#E0A800',
          graphite: '#111827',
          ink: '#0F172A',
        },
      },
      boxShadow: {
        soft: '0 10px 30px rgba(15, 23, 42, 0.08)',
        premium: '0 18px 50px rgba(15, 23, 42, 0.14)',
        yellow: '0 12px 30px rgba(255, 196, 0, 0.28)',
      },
      borderRadius: {
        '3xl': '1.75rem',
        '4xl': '2rem',
      },
    },
  },
  plugins: [],
};

export default config;
