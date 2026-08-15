/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0E1420",
        panel: "#161D2C",
        panelLight: "#1D2739",
        border: "#293349",
        text: "#E8ECF4",
        muted: "#8A93A6",
        verified: "#4FD1C5",
        query: "#F2B84B",
        danger: "#E5697B",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        body: ["IBM Plex Sans", "sans-serif"],
        mono: ["IBM Plex Mono", "monospace"],
      },
    },
  },
  plugins: [],
};