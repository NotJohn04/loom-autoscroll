import { defineConfig } from "vite";

export default defineConfig({
  root: ".",              // current folder
  build: {
    outDir: "dist",        // output folder for Vercel
  },
});
