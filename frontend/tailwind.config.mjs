/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        "ink": "#0b0908",
        "charcoal": {
                "DEFAULT": "#191512",
                "soft": "#292524",
                "line": "#44403c"
        },
        "brand": {
                "DEFAULT": "#f59e0b",
                "dim": "#b45309"
        }
},
      fontFamily: {
        "display": [
                "'Archivo'",
                "system-ui",
                "sans-serif"
        ],
        "body": [
                "'Inter'",
                "system-ui",
                "sans-serif"
        ],
        "mono": [
                "'JetBrains Mono'",
                "ui-monospace",
                "monospace"
        ]
},
    },
  },
  plugins: [],
};
