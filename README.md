# Landing Page

## Run locally

```bash
docker compose up --build
```

## Install git hooks

Use git's "half-arsed-builtin" version control for git hooks (this is too verbose?)
```bash
touch .githooks/pre-push
chmod +x .githooks/pre-push
git config core.hooksPath .githooks
```

## How to Take a Scrolling Screenshot on Mac

### Using Chrome DevTools:
1. Open your website in **Google Chrome**.
2. Zoom out using **Cmd + Minus (–)** until the full page fits your screen.
3. Open DevTools with **Cmd + Option + I**.
4. Open the **Command Menu** with **Cmd + Shift + P**.
5. Type `"Capture full size screenshot"` and press **Enter**.

### Alternative Methods:
- **Firefox:** Right-click > "Take Screenshot" > "Save Full Page".
- **Third-Party Apps:**
  - **Snagit** (Paid, feature-rich)
  - **Capto** (Mac-exclusive, scrolling capture)
  - **Shottr** (Free, lightweight)

This method works best for capturing entire web pages without manually stitching screenshots together.

## TODO

* add the testimonial from Mark
  * lets shift jukka's testemonial do the left, put mark's testemonial bellow Iker's (extract one paragraph from mark's)

"I worked with Miguel in RELEX, and we worked together on multiple projects. However, our main collaboration saw us work together on value stream mapping. I always found Miguel excellent to work with and he added value whenever he was involved. He was always passionate with a great drive and took ownership of the work he was responsible for. He communicated very well with stakeholders at all levels and led meetings confidently and in a very organised manner. Miguel has a strong background and fantastic knowledge of DevOps, Data Engineering and Analytics. He used this effectively in bringing teams together and conducting Value Stream mapping and helping to identify how we could reduce process cycle times and implement process improvement. Miguel was always very professional, friendly and a great team player. He was also to fun to work with. Nothing was ever too much trouble, and he developed very strong relationships with internal team members and customers."

* have the tests also run on the github actins pipeline before the site is deployed
* add to the prod health checks: Real-Time Checks that each main component (contact, clanedly, all testemonials ar displayed correclty, blog, etc)
* needs to look good on mobile
* make the blog button more prominent because its a significant part of my website and i want users to find it. maybe its a good thing if i add the carrousel of my top 3 articles, that will give more visibility to the blog. 
* the date feild in the articles should be extracted from te doc name
* a newsletter 


## DONE

* create backlinks for pages, especially about VSM, etc
