# Landing Page

## Run locally

```bash
docker compose up --build
```

## Install git hooks

Copy the pre-push hook to enable automatic testing before pushing:
```bash
cp githooks/pre-push .git/hooks/pre-push
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
* needs to look good on mobile
* make the blog button more prominent because its a significant part of my website and i want users to find it. maybe its a good thing if i add the carrousel of my top 3 articles, that will give more visibility to the blog. 
* the date feild in the articles should be extracted from te doc name
* a newsletter 


## DONE

* create backlinks for pages, especially about VSM, etc
