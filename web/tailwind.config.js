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
        md: {
          primary: {
            DEFAULT: 'var(--md-primary)',
            container: 'var(--md-primary-container)',
            on: 'var(--md-on-primary)',
            'on-container': 'var(--md-on-primary-container)',
          },
          secondary: {
            DEFAULT: 'var(--md-secondary)',
            container: 'var(--md-secondary-container)',
            on: 'var(--md-on-secondary)',
            'on-container': 'var(--md-on-secondary-container)',
          },
          surface: {
            DEFAULT: 'var(--md-surface)',
            on: 'var(--md-on-surface)',
            low: 'var(--md-surface-low)',
            container: 'var(--md-surface-container)',
            high: 'var(--md-surface-high)',
            highest: 'var(--md-surface-highest)',
          },
          outline: {
            DEFAULT: 'var(--md-outline)',
            variant: 'var(--md-outline-variant)',
          },
          success: {
            DEFAULT: '#198754',
            container: '#d1e7dd',
          },
          warning: {
            DEFAULT: '#b78103',
            container: '#fff3cd',
          }
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        'expressive-user': '22px 22px 6px 22px',
        'expressive-ai': '22px 22px 22px 6px',
        'expressive-card': '20px 20px 8px 20px',
      }
    },
  },
  plugins: [],
}
