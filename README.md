# Landing Page

## TODO

* check out the RSS feed - is it working? can peopl subscribe to it?

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

