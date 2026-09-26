import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  integrations: [mdx()],
  // common.css is the Tailwind entry (`@import "tailwindcss"`); the Vite
  // plugin compiles it. There is no Astro integration for Tailwind 4.
  vite: { plugins: [tailwindcss()] },
  // Astro 7 defaults to 'jsx', which strips newline whitespace between inline
  // elements and glues words together in prose. Keep the old behaviour;
  // tests/test_inline_whitespace.py guards it.
  compressHTML: true,
});
