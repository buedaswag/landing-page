---
name: Logos and testimonial
overview: Add Phil Clark's testimonial (homepage + blog post) and a "Trusted by" logo bar with Relex Solutions, Productized, Naviri, and NomidMDM logos above the testimonials section.
todos:
  - id: write-tests
    content: "Write failing tests: test_trust_bar_logos, test_phil_clark_testimonial, update tracked testimonial count"
    status: completed
  - id: commit-failing
    content: Commit failing tests and push to trigger rebuild
    status: cancelled
  - id: download-logos
    content: Fetch company websites and download logos to public/images/logos/
    status: completed
  - id: phil-blog-post
    content: Create 2026-02-25-phil-clark-testimonial.mdx blog post
    status: completed
  - id: update-index
    content: Add Phil to testimonials array + trust bar section in index.astro
    status: completed
  - id: commit-push
    content: Commit implementation and push
    status: completed
isProject: false
---

# Add Logos and Phil Clark Testimonial

## Phil Clark's Testimonial

**Homepage quote** (in `testimonials` array in [src/pages/index.astro](src/pages/index.astro)):

```javascript
{
  name: "Phil Clark",
  role: "VP Engineering",
  postSlug: "2026-02-25-phil-clark-testimonial",
  quote: "I've gotten to know Miguel both personally and professionally as a consultant. He's <strong>highly motivated, deeply knowledgeable</strong>, and he brings a common language that <strong>makes mapping sessions productive rather than academic</strong>.",
}
```

**Blog post** -- new file `src/content/posts/2026-02-25-phil-clark-testimonial.mdx`, following the same format as [src/content/posts/2025-02-17-mika-schafroth-testimonial.mdx](src/content/posts/2025-02-17-mika-schafroth-testimonial.mdx). Full text from the LinkedIn post:

> "If you're trying to improve flow (lead time, bottlenecks, WIP, dependencies), value stream mapping done well is one of the fastest ways to create alignment and unlock measurable improvement.
>
> I highly recommend Miguel Dias VSM. I've gotten to know Miguel both personally and professionally as a consultant. He's highly motivated, deeply knowledgeable, and he brings a common language that makes mapping sessions productive rather than academic."

Attribution links to his LinkedIn profile: `https://www.linkedin.com/in/philipwclark/`

## "Trusted by leaders at" Logo Bar

Add a new section on the homepage **above the testimonials section** in [src/pages/index.astro](src/pages/index.astro), between the "How We Work" and "What Clients Say" sections.

Structure: a simple row of grayscale logos with company names, similar to a standard trust bar. Each logo links to the company website. Uses `data-trust-bar` attribute for testability.

**Companies and logo sources:**

- **Relex Solutions** -- [https://www.relexsolutions.com](https://www.relexsolutions.com) -- logo from their website
- **Productized** -- [https://productized.co](https://productized.co) -- logo from their conference website
- **Naviri** -- [https://www.naviri.com/](https://www.naviri.com/) -- Startup OS platform
- **NomidMDM** -- [https://www.nomidmdm.com/en](https://www.nomidmdm.com/en) -- David's company

Logos stored in `public/images/logos/` (new directory). I will fetch each company's website, find logo assets (preferring SVG, falling back to PNG), and download them.

## TDD Approach

Per workspace rules, write tests first in [tests/test_site.py](tests/test_site.py):

1. `**test_trust_bar_logos**` -- Homepage has a trust bar (`data-trust-bar`) with 4 company logos that load, each linking to the company website
2. `**test_phil_clark_testimonial**` -- Phil Clark appears in the testimonials section with correct name and quote
3. Update `**test_testimonial_links_have_tracking**` -- bump expected count from 4 to 5

## Execution Order

1. Write failing tests
2. Commit and watch them fail
3. Download logos from company websites to `public/images/logos/`
4. Create Phil Clark blog post MDX
5. Update `index.astro`: add Phil to testimonials array, add trust bar section
6. Commit and push (triggers rebuild + test run)
