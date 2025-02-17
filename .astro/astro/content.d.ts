declare module 'astro:content' {
	interface Render {
		'.mdx': Promise<{
			Content: import('astro').MarkdownInstance<{}>['Content'];
			headings: import('astro').MarkdownHeading[];
			remarkPluginFrontmatter: Record<string, any>;
		}>;
	}
}

declare module 'astro:content' {
	interface RenderResult {
		Content: import('astro/runtime/server/index.js').AstroComponentFactory;
		headings: import('astro').MarkdownHeading[];
		remarkPluginFrontmatter: Record<string, any>;
	}
	interface Render {
		'.md': Promise<RenderResult>;
	}

	export interface RenderedContent {
		html: string;
		metadata?: {
			imagePaths: Array<string>;
			[key: string]: unknown;
		};
	}
}

declare module 'astro:content' {
	type Flatten<T> = T extends { [K: string]: infer U } ? U : never;

	export type CollectionKey = keyof AnyEntryMap;
	export type CollectionEntry<C extends CollectionKey> = Flatten<AnyEntryMap[C]>;

	export type ContentCollectionKey = keyof ContentEntryMap;
	export type DataCollectionKey = keyof DataEntryMap;

	type AllValuesOf<T> = T extends any ? T[keyof T] : never;
	type ValidContentEntrySlug<C extends keyof ContentEntryMap> = AllValuesOf<
		ContentEntryMap[C]
	>['slug'];

	/** @deprecated Use `getEntry` instead. */
	export function getEntryBySlug<
		C extends keyof ContentEntryMap,
		E extends ValidContentEntrySlug<C> | (string & {}),
	>(
		collection: C,
		// Note that this has to accept a regular string too, for SSR
		entrySlug: E,
	): E extends ValidContentEntrySlug<C>
		? Promise<CollectionEntry<C>>
		: Promise<CollectionEntry<C> | undefined>;

	/** @deprecated Use `getEntry` instead. */
	export function getDataEntryById<C extends keyof DataEntryMap, E extends keyof DataEntryMap[C]>(
		collection: C,
		entryId: E,
	): Promise<CollectionEntry<C>>;

	export function getCollection<C extends keyof AnyEntryMap, E extends CollectionEntry<C>>(
		collection: C,
		filter?: (entry: CollectionEntry<C>) => entry is E,
	): Promise<E[]>;
	export function getCollection<C extends keyof AnyEntryMap>(
		collection: C,
		filter?: (entry: CollectionEntry<C>) => unknown,
	): Promise<CollectionEntry<C>[]>;

	export function getEntry<
		C extends keyof ContentEntryMap,
		E extends ValidContentEntrySlug<C> | (string & {}),
	>(entry: {
		collection: C;
		slug: E;
	}): E extends ValidContentEntrySlug<C>
		? Promise<CollectionEntry<C>>
		: Promise<CollectionEntry<C> | undefined>;
	export function getEntry<
		C extends keyof DataEntryMap,
		E extends keyof DataEntryMap[C] | (string & {}),
	>(entry: {
		collection: C;
		id: E;
	}): E extends keyof DataEntryMap[C]
		? Promise<DataEntryMap[C][E]>
		: Promise<CollectionEntry<C> | undefined>;
	export function getEntry<
		C extends keyof ContentEntryMap,
		E extends ValidContentEntrySlug<C> | (string & {}),
	>(
		collection: C,
		slug: E,
	): E extends ValidContentEntrySlug<C>
		? Promise<CollectionEntry<C>>
		: Promise<CollectionEntry<C> | undefined>;
	export function getEntry<
		C extends keyof DataEntryMap,
		E extends keyof DataEntryMap[C] | (string & {}),
	>(
		collection: C,
		id: E,
	): E extends keyof DataEntryMap[C]
		? Promise<DataEntryMap[C][E]>
		: Promise<CollectionEntry<C> | undefined>;

	/** Resolve an array of entry references from the same collection */
	export function getEntries<C extends keyof ContentEntryMap>(
		entries: {
			collection: C;
			slug: ValidContentEntrySlug<C>;
		}[],
	): Promise<CollectionEntry<C>[]>;
	export function getEntries<C extends keyof DataEntryMap>(
		entries: {
			collection: C;
			id: keyof DataEntryMap[C];
		}[],
	): Promise<CollectionEntry<C>[]>;

	export function render<C extends keyof AnyEntryMap>(
		entry: AnyEntryMap[C][string],
	): Promise<RenderResult>;

	export function reference<C extends keyof AnyEntryMap>(
		collection: C,
	): import('astro/zod').ZodEffects<
		import('astro/zod').ZodString,
		C extends keyof ContentEntryMap
			? {
					collection: C;
					slug: ValidContentEntrySlug<C>;
				}
			: {
					collection: C;
					id: keyof DataEntryMap[C];
				}
	>;
	// Allow generic `string` to avoid excessive type errors in the config
	// if `dev` is not running to update as you edit.
	// Invalid collection names will be caught at build time.
	export function reference<C extends string>(
		collection: C,
	): import('astro/zod').ZodEffects<import('astro/zod').ZodString, never>;

	type ReturnTypeOrOriginal<T> = T extends (...args: any[]) => infer R ? R : T;
	type InferEntrySchema<C extends keyof AnyEntryMap> = import('astro/zod').infer<
		ReturnTypeOrOriginal<Required<ContentConfig['collections'][C]>['schema']>
	>;

	type ContentEntryMap = {
		"posts": {
"2024-02-17-iker-garagarza-testimonial.md": {
	id: "2024-02-17-iker-garagarza-testimonial.md";
  slug: "2024-02-17-iker-garagarza-testimonial";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".md"] };
"2024-02-17-mika-schafroth-testimonial.md": {
	id: "2024-02-17-mika-schafroth-testimonial.md";
  slug: "2024-02-17-mika-schafroth-testimonial";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".md"] };
"2024-06-02-improving-large-scale-software-delivery-results.mdx": {
	id: "2024-06-02-improving-large-scale-software-delivery-results.mdx";
  slug: "2024-06-02-improving-large-scale-software-delivery-results";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-06-02-types-of-waste-in-technology-work.mdx": {
	id: "2024-06-02-types-of-waste-in-technology-work.mdx";
  slug: "2024-06-02-types-of-waste-in-technology-work";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-06-02-what-is-value-stream-mapping.mdx": {
	id: "2024-06-02-what-is-value-stream-mapping.mdx";
  slug: "2024-06-02-what-is-value-stream-mapping";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-06-03-deployment-lead-time.mdx": {
	id: "2024-06-03-deployment-lead-time.mdx";
  slug: "2024-06-03-deployment-lead-time";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-06-05-devoops.mdx": {
	id: "2024-06-05-devoops.mdx";
  slug: "2024-06-05-devoops";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-06-11-blameless-post-mortem-template.mdx": {
	id: "2024-06-11-blameless-post-mortem-template.mdx";
  slug: "2024-06-11-blameless-post-mortem-template";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-07-24-importance-of-improving-work.mdx": {
	id: "2024-07-24-importance-of-improving-work.mdx";
  slug: "2024-07-24-importance-of-improving-work";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-08-26-key-ingredients-for-a-blameless-post-mortem.mdx": {
	id: "2024-08-26-key-ingredients-for-a-blameless-post-mortem.mdx";
  slug: "2024-08-26-key-ingredients-for-a-blameless-post-mortem";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-09-11-continuous-improvement-with-value-stream-mapping.mdx": {
	id: "2024-09-11-continuous-improvement-with-value-stream-mapping.mdx";
  slug: "2024-09-11-continuous-improvement-with-value-stream-mapping";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-09-26-start-your-devops-journey.mdx": {
	id: "2024-09-26-start-your-devops-journey.mdx";
  slug: "2024-09-26-start-your-devops-journey";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-10-28-improving-engineering-quality copy.mdx": {
	id: "2024-10-28-improving-engineering-quality copy.mdx";
  slug: "2024-10-28-improving-engineering-quality-copy";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-10-31-validated-learning.mdx": {
	id: "2024-10-31-validated-learning.mdx";
  slug: "2024-10-31-validated-learning";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-11-07-vsm-structure.mdx": {
	id: "2024-11-07-vsm-structure.mdx";
  slug: "2024-11-07-vsm-structure";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-11-11-vsm-planning.mdx": {
	id: "2024-11-11-vsm-planning.mdx";
  slug: "2024-11-11-vsm-planning";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-11-12-vsm-current-state-mapping.mdx": {
	id: "2024-11-12-vsm-current-state-mapping.mdx";
  slug: "2024-11-12-vsm-current-state-mapping";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-11-15-lean-coffee.mdx": {
	id: "2024-11-15-lean-coffee.mdx";
  slug: "2024-11-15-lean-coffee";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-11-19-outcome-mapping-case-study.mdx": {
	id: "2024-11-19-outcome-mapping-case-study.mdx";
  slug: "2024-11-19-outcome-mapping-case-study";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-11-25-vsm-dependency-mapping.mdx": {
	id: "2024-11-25-vsm-dependency-mapping.mdx";
  slug: "2024-11-25-vsm-dependency-mapping";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-11-26-vsm-future-state-mapping.mdx": {
	id: "2024-11-26-vsm-future-state-mapping.mdx";
  slug: "2024-11-26-vsm-future-state-mapping";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-11-27-vsm-improvement-roadmap.mdx": {
	id: "2024-11-27-vsm-improvement-roadmap.mdx";
  slug: "2024-11-27-vsm-improvement-roadmap";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-11-29-lean-coffee.mdx": {
	id: "2024-11-29-lean-coffee.mdx";
  slug: "2024-11-29-lean-coffee";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2024-12-09-marcus-aurelius.mdx": {
	id: "2024-12-09-marcus-aurelius.mdx";
  slug: "2024-12-09-marcus-aurelius";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
"2025-01-23-new-york-lean-coffee.mdx": {
	id: "2025-01-23-new-york-lean-coffee.mdx";
  slug: "2025-01-23-new-york-lean-coffee";
  body: string;
  collection: "posts";
  data: InferEntrySchema<"posts">
} & { render(): Render[".mdx"] };
};

	};

	type DataEntryMap = {
		
	};

	type AnyEntryMap = ContentEntryMap & DataEntryMap;

	export type ContentConfig = typeof import("../../src/content/config.js");
}
