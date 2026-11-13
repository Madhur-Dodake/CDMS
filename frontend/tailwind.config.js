/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cricket: {
          pitch: "#166534",
          crease: "#f8fafc",
          gold: "#eab308",
        }
      }
    },
  },
  plugins: [],
}

