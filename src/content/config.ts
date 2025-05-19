import { defineCollection, z } from 'astro:content';

const posts = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    date: z.string(),
    image: z.string().startsWith('/'),
    draft: z.boolean().optional().default(false),
  }),
});

export const collections = {
  posts: posts,
};
