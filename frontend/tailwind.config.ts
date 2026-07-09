import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: [
    "./pages/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        // Brand palette - Clean Indigo/Violet (Apple/Vercel inspired premium theme)
        brand: {
          50: "hsl(240 100% 98%)",
          100: "hsl(240 100% 95%)",
          200: "hsl(240 100% 90%)",
          350: "hsl(240 100% 80%)",
          500: "hsl(240 85% 65%)", // Primary brand color
          600: "hsl(240 85% 55%)",
          700: "hsl(240 85% 45%)",
          900: "hsl(240 85% 20%)",
        },
        // Semantic status palettes
        success: {
          50: "hsl(142 76% 96%)",
          100: "hsl(142 76% 90%)",
          500: "hsl(142 76% 36%)",
          600: "hsl(142 76% 28%)",
        },
        warning: {
          50: "hsl(38 92% 96%)",
          100: "hsl(38 92% 90%)",
          500: "hsl(38 92% 50%)",
          600: "hsl(38 92% 40%)",
        },
        danger: {
          50: "hsl(0 84% 97%)",
          100: "hsl(0 84% 92%)",
          500: "hsl(0 84% 60%)",
          600: "hsl(0 84% 50%)",
        },
        info: {
          50: "hsl(200 95% 97%)",
          100: "hsl(200 95% 90%)",
          500: "hsl(200 95% 48%)",
          600: "hsl(200 95% 38%)",
        },
        // Custom background layers for glassmorphic elements
        bg: {
          base: "var(--bg-base)",
          elevated: "var(--bg-elevated)",
          overlay: "var(--bg-overlay)",
          sunken: "var(--bg-sunken)",
        },
        // Shadcn defaults compatibility
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        "sm": "6px",
        "md": "10px",
        "lg": "14px",
        "xl": "20px",
        "2xl": "28px",
      },
      boxShadow: {
        xs: "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
        sm: "0 2px 4px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.02)",
        md: "0 4px 12px 0 rgba(0, 0, 0, 0.05), 0 2px 4px 0 rgba(0, 0, 0, 0.02)",
        lg: "0 8px 24px 0 rgba(0, 0, 0, 0.06), 0 4px 8px 0 rgba(0, 0, 0, 0.04)",
        xl: "0 16px 40px -10px rgba(0, 0, 0, 0.08), 0 8px 20px -5px rgba(0, 0, 0, 0.04)",
        "2xl": "0 24px 60px -15px rgba(0, 0, 0, 0.12)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
        shimmer: {
          "100%": {
            transform: "translateX(100%)",
          },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
