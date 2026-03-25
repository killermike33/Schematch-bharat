/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Noto Serif"', 'Georgia', 'serif'],
        body: ['"Noto Sans"', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        saffron: {
          50:  '#fff8ed',
          100: '#ffefd0',
          200: '#ffd99a',
          300: '#ffbf5e',
          400: '#ff9d2a',
          500: '#ff7f00',
          600: '#e06200',
          700: '#b84700',
          800: '#943a00',
          900: '#7a3200',
        },
        navy: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          300: '#a5b4fc',
          400: '#818cf8',
          500: '#1a237e',
          600: '#17208c',
          700: '#141b7a',
          800: '#0f1660',
          900: '#0a1050',
        },
        india: {
          green:  '#138808',
          white:  '#FFFFFF',
          saffron:'#FF9933',
          navy:   '#000080',
          ashoka: '#002366',
        }
      },
      boxShadow: {
        'card': '0 2px 8px 0 rgba(0,0,64,0.08), 0 1px 2px 0 rgba(0,0,64,0.04)',
        'card-hover': '0 8px 24px 0 rgba(0,0,64,0.12), 0 2px 6px 0 rgba(0,0,64,0.06)',
        'input': '0 0 0 3px rgba(255,153,51,0.2)',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.4s ease-out forwards',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(16px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        }
      }
    },
  },
  plugins: [],
}
