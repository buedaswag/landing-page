import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';
import mdx from '@astrojs/mdx';

export default defineConfig({
  integrations: [tailwind(), mdx()],
  content: {
    collections: {
      posts: {
        type: 'content',
        entrySchema: 'astro:content'
      }
    }
  }
});
