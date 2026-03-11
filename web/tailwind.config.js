/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'drx-dark': '#0f172a',
        'drx-accent': '#38bdf8'
      }
    },
  },
  plugins: [],
}