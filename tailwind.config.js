/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'reddi-green': '#57BAB5',
        'reddi-navyblue': '#2d4a74',
        'reddi-yellow': '#F5C122',
        brand: {
          navy: {
            900: '#0B0130',
            700: '#1C0A53',
            50: '#F2F1FA',
          },
          highlight1: '#6F56FF',
        },
        primary: {
          ink: '#000000',
        },
        text: {
          default: '#1A1A1A',
          muted: '#6B6B6B',
        },
        surface: {
          0: '#FFFFFF',
          alt: '#F7F7F7',
          border: '#E4E4E4',
        },
        state: {
          success: '#64C09B',
          warning: '#F5B547',
          error: '#F16063',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      fontSize: {
        'heading-xl': ['3.0rem', { lineHeight: '1.125', fontWeight: '900' }],
        'body-lg': ['1.125rem', { lineHeight: '1.4', fontWeight: '600' }],
        'body': ['1.0rem', { lineHeight: '1.5', fontWeight: '400' }],
        'caption': ['0.875rem', { lineHeight: '1.45', fontWeight: '400' }],
      },
      spacing: {
        '0': '0',
        '1': '4px',
        '2': '8px',
        '3': '12px',
        '4': '16px',
        '6': '24px',
        '8': '32px',
        '12': '48px',
      },
      borderRadius: {
        'none': '0',
        'sm': '6px',
        'md': '8px',
        'lg': '12px',
        'full': '9999px',
      },
      boxShadow: {
        'xs': '0 1px 2px rgba(0,0,0,.05)',
        'sm': '0 2px 4px rgba(0,0,0,.06)',
        'card': '0 4px 12px rgba(0,0,0,.08)',
        'modal': '0 8px 24px rgba(0,0,0,.12)',
      },
      transitionTimingFunction: {
        'standard': 'cubic-bezier(.4,0,.2,1)',
      },
      transitionDuration: {
        'fast': '150ms',
        'medium': '250ms',
      },
      zIndex: {
        'navigation': '50',
        'modal': '40',
        'dropdown': '30',
        'hover': '10',
        'base': '0',
      },
      maxWidth: {
        'container': '1360px',
      },
    },
  },
  plugins: [],
}