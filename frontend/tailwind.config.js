/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        charcoal: {
          50: '#f6f7f8',
          100: '#eceeef',
          200: '#d5d7db',
          300: '#b1b6bc',
          400: '#868f9a',
          500: '#66707c',
          600: '#525a65',
          700: '#434952',
          800: '#393e45',
          900: '#1e2124',
          950: '#131517',
        },
        sage: {
          50: '#f4f7f4',
          100: '#e5ece5',
          500: '#4e7b58',
          600: '#3c6245',
          700: '#324e38',
        }
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
