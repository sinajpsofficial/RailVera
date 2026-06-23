/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          light: "#2B6CB0",
          DEFAULT: "#1A365D",
          dark: "#0A192F",
        },
      },
    },
  },
  plugins: [],
}
