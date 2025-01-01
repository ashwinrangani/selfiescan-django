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

    },
  },
  plugins: [
    require('flyonui'), 
    require('flyonui/plugin')
  ],
  flyonui: {
    themes: ["light", "dark", "gourmet", "luxury", "soft"]
  },
  
}

