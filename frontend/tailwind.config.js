/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        blue: {
          50: '#f1f4f9', 100: '#e2e8f1', 200: '#c5d0e2', 300: '#9aaecb', 400: '#6b85ad',
          500: '#3f5f8f', 600: '#1f3a63', 700: '#172e4f', 800: '#12243f', 900: '#0f1f3d', 950: '#0a1429',
        },
        paper: '#f8f7f4',
        brand: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
          950: '#0b132b',
        },
        verdict: {
          true: '#10b981',
          mostly_true: '#34d399',
          context: '#f59e0b',
          mostly_false: '#f97316',
          false: '#ef4444',
          inconclusive: '#6b7280',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'Segoe UI', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
