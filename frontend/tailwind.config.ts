import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // 品牌色 - 暖琥珀
        brand: {
          primary: "#FF9500",
          secondary: "#FFB347",
        },
        // 背景色 - 故事感深色
        bg: {
          primary: "#121212",
          secondary: "#1E1E1E",
          tertiary: "#2A2A2A",
          elevated: "#333333",
        },
        // 文字色
        text: {
          primary: "#FFFFFF",
          secondary: "#E0E0E0",
          tertiary: "#9E9E9E",
          muted: "#666666",
        },
        // 强调色
        accent: {
          warm: "#FF6B6B",
          cool: "#4ECDC4",
          purple: "#9B59B6",
          gold: "#FFD700",
        },
        // 功能色
        success: "#4ADE80",
        warning: "#FBBF24",
        error: "#EF4444",
        info: "#3B82F6",
      },
      fontFamily: {
        sans: ["var(--font-noto-sans)", "system-ui", "sans-serif"],
        serif: ["var(--font-noto-serif)", "Georgia", "serif"],
        display: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xs: "4px",
        sm: "8px",
        md: "12px",
        lg: "16px",
        xl: "24px",
      },
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
      },
      transitionDuration: {
        instant: "100ms",
        fast: "200ms",
        normal: "350ms",
        slow: "500ms",
        story: "700ms",
      },
      animation: {
        "glow-pulse": "glow-pulse 2s ease-in-out infinite",
        "slide-in-right": "slide-in-right 0.7s ease-out",
        "fade-in": "fade-in 0.5s ease-out",
        "fade-in-up": "fade-in-up 0.5s ease-out",
      },
      keyframes: {
        "glow-pulse": {
          "0%, 100%": {
            boxShadow: "0 0 20px rgba(255, 149, 0, 0.4)",
          },
          "50%": {
            boxShadow: "0 0 30px rgba(255, 149, 0, 0.6)",
          },
        },
        "slide-in-right": {
          "0%": {
            transform: "translateX(100%)",
            opacity: "0",
          },
          "100%": {
            transform: "translateX(0)",
            opacity: "1",
          },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "fade-in-up": {
          "0%": {
            opacity: "0",
            transform: "translateY(20px)",
          },
          "100%": {
            opacity: "1",
            transform: "translateY(0)",
          },
        },
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #FF9500 0%, #FFD93D 100%)",
        "cta-gradient": "linear-gradient(135deg, #FF9500 0%, #FF6B00 100%)",
      },
      boxShadow: {
        "glow-sm": "0 0 10px rgba(255, 149, 0, 0.3)",
        "glow-md": "0 0 20px rgba(255, 149, 0, 0.4)",
        "glow-lg": "0 0 30px rgba(255, 149, 0, 0.5)",
      },
    },
  },
  plugins: [],
};
export default config;
