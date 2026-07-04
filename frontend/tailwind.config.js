/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#f0f4ff',
          100: '#dce6fe',
          200: '#b9ccfd',
          300: '#86a8fb',
          400: '#5080f7',
          500: '#2d5ef3',
          600: '#1a40e8',
          700: '#162fd4',
          800: '#1828ac',
          900: '#1a2887',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
