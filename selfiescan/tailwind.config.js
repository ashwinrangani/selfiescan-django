/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./**/templates/**/*.html",
    "./static/js/**/*.js", 
    "./home/node_modules/flyonui/dist/js/*.js"
  ],
  theme: {
    extend: {
      fontFamily: {
        playwrite: ['"Playwrite IT Moderna"', 'cursive'],
        pacifico: ['"Pacifico"', 'cursive'],

      },
    },
  },
  plugins: [
    require('flyonui'), 
    require('flyonui/plugin')
  ],
  flyonui: {
    themes: ["light", "dark", "gourmet", "luxury", "soft"]
  },
  darkMode: ['class', '[data-theme="luxury"]']
  
}

