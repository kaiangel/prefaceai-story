import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Wave 13 #9: front-end test runner (was missing — useETA.test.ts could not execute).
// jsdom env so React-hook tests can run later; setupFiles makes console.assert throw
// so the pre-existing useETA.test.ts assertions become real pass/fail signals.
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
  },
});
