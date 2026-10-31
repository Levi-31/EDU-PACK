/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Theme tokens via CSS RGB variables (supports full opacity modifiers like /30, /80)
        surface: {
          DEFAULT: 'rgb(var(--surface) / <alpha-value>)',
          dim: 'rgb(var(--surface-dim) / <alpha-value>)',
          bright: 'rgb(var(--surface-bright) / <alpha-value>)',
        },
        background: 'rgb(var(--surface) / <alpha-value>)',
        'surface-container': {
          lowest: 'rgb(var(--surface-lowest) / <alpha-value>)',
          low: 'rgb(var(--surface-low) / <alpha-value>)',
          DEFAULT: 'rgb(var(--surface-container) / <alpha-value>)',
          high: 'rgb(var(--surface-high) / <alpha-value>)',
          highest: 'rgb(var(--surface-highest) / <alpha-value>)',
        },
        'surface-variant': 'rgb(var(--surface-highest) / <alpha-value>)',
        'on-surface': {
          DEFAULT: 'rgb(var(--on-surface) / <alpha-value>)',
          variant: 'rgb(var(--on-surface-variant) / <alpha-value>)',
        },
        'on-background': 'rgb(var(--on-surface) / <alpha-value>)',
        primary: {
          DEFAULT: 'rgb(var(--primary) / <alpha-value>)',
          container: 'rgb(var(--primary-container) / <alpha-value>)',
        },
        'on-primary': {
          DEFAULT: 'rgb(var(--on-primary) / <alpha-value>)',
          container: 'rgb(var(--on-primary-container) / <alpha-value>)',
        },
        secondary: {
          DEFAULT: 'rgb(var(--secondary) / <alpha-value>)',
          container: 'rgb(var(--secondary-container) / <alpha-value>)',
        },
        tertiary: {
          DEFAULT: 'rgb(var(--tertiary) / <alpha-value>)',
          container: 'rgb(var(--tertiary-container) / <alpha-value>)',
        },
        'on-tertiary': {
          DEFAULT: 'rgb(var(--on-tertiary) / <alpha-value>)',
        },
        outline: {
          DEFAULT: 'rgb(var(--outline) / <alpha-value>)',
          variant: 'rgb(var(--outline-variant) / <alpha-value>)',
        },
        error: {
          DEFAULT: 'rgb(var(--error) / <alpha-value>)',
          container: 'rgb(var(--error-container) / <alpha-value>)',
        },
        brand: {
          50: '#f0f9ff',
          100: '#dfe0ff',
          200: '#bdc2ff',
          300: '#7bd0ff',
          400: '#8ba2ff',
          500: '#5e6ad2',
          600: '#4854bb',
          700: '#3131c0',
          800: '#121f8b',
          900: '#0d0e13',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        geist: ['Geist', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
}
