/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        // Serifada com carater, para titulos e numeros grandes (rotulo de cafe artesanal)
        heading: ['Fraunces', 'serif'],
        // Sans-serif limpa, para corpo de texto e UI em geral
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}