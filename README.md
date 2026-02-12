# Landing Page

## TODO

* check out the RSS feed - is it working? can peopl subscribe to it?

## Lean Coffee Email Signup

The lean coffee page (`/lean-coffee`) has an email signup form powered by **Substack**. Currently the form `action` is a placeholder (`TODO_REPLACE_WITH_SUBSTACK_URL`) — **emails are not being collected yet**.

To wire it up:

1. Create a Substack publication at [substack.com](https://substack.com)
2. Go to **Settings → Publication details** and grab your publication URL (e.g. `https://yourname.substack.com`)
3. Get the embed form action URL from **Settings → Publishing → Embeds**
4. Replace `TODO_REPLACE_WITH_SUBSTACK_URL` in `src/pages/lean-coffee.astro` with your Substack form action URL

Substack handles double opt-in, unsubscribe, GDPR compliance, and bounce management. You can export your full subscriber list and posts at any time (Dashboard → Settings → Exports).

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

