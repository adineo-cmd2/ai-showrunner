/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        ink: '#0c0a09',
        charcoal: {
          DEFAULT: '#1c1917',
          soft: '#292524',
          line: '#44403c',
        },
        brand: {
          DEFAULT: '#f59e0b',
          dim: '#b45309',
        },
      },
    },
  },
  plugins: [],
};
