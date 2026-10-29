/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        "ink": "#fbf7ec",
        "charcoal": {
          "DEFAULT": "#fbf7ec",
          "soft": "#f3ecdc",
          "line": "#c9b99b"
        },
        "brand": {
          "DEFAULT": "#b23a2f",
          "dim": "#8e2b22"
        },
        "stone": {
          "100": "#1b1913",
          "200": "#332f26",
          "300": "#4a4437",
          "400": "#6c6352",
          "500": "#8b806c"
        },
        "red": {
          "400": "#a32f27",
          "500": "#b23a2f",
          "700": "#7c221c"
        }
      },
      fontFamily: {
        "display": ["'Fraunces'", "Georgia", "serif"],
        "body": ["'Public Sans'", "system-ui", "sans-serif"],
        "mono": ["'Courier Prime'", "'Courier New'", "monospace"]
      },
    },
  },
  plugins: [],
};
