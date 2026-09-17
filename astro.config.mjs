import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';

export default defineConfig({
  // common.css is the Tailwind entry: it carries the @tailwind directives, so
  // the integration must not inject a second copy of preflight.
  integrations: [tailwind({ applyBaseStyles: false }), mdx()],
});
