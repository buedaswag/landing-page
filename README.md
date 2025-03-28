# Landing Page

## Run locally

```bash
docker compose up --build
```

## Development

### Test Suite

The project includes a comprehensive test suite that verifies:
- Homepage loading
- Calendly link presence and accessibility
- All internal pages loading
- All images in articles loading

To run the tests:
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/test_site.py -v
```

### Git Hooks

The project includes a pre-push git hook that automatically runs the test suite before allowing pushes. This ensures that all changes are tested before being pushed to the repository.

The hook is located in `hooks/pre-push` and is automatically installed when you clone the repository.

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

* the date feild in the articles should be extracted from te doc name
* add the testemonial from Mark
* create backlinks for pages, especially about VSM, etcz`