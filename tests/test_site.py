import unittest
import os
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import subprocess
import json
import time
import os

class TestSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Called once before all tests in this class"""
        cls.BASE_URL = "http://localhost:4444"
        cls.project_root = Path(__file__).parent.parent
        cls._we_started_containers = False

        force_build = os.environ.get("FORCE_BUILD") == "1"

        if force_build:
            print("FORCE_BUILD=1 — rebuilding containers from scratch...")
            subprocess.run(["docker", "compose", "down"], check=True)
            subprocess.run(["docker", "compose", "up", "--build", "-d"], check=True)
            cls._we_started_containers = True
        elif cls._is_server_running():
            print("Docker Compose is already running — skipping build.")
        else:
            print("Server not running — starting Docker Compose...")
            subprocess.run(["docker", "compose", "up", "--build", "-d"], check=True)
            cls._we_started_containers = True

        # Wait for server to be ready
        cls._wait_for_server()

    @classmethod
    def tearDownClass(cls):
        """Leave containers running after tests for faster dev cycles."""
        print("Leaving containers running.")

    @classmethod
    def _is_server_running(cls):
        """Check if docker compose is already running and serving requests."""
        try:
            response = requests.get(cls.BASE_URL, timeout=3)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    @classmethod
    def _wait_for_server(cls, timeout=60):
        """Wait for server to be ready with up to 60 second timeout"""
        start_time = time.time()
        message_found = False
        server_responding = False

        print(f"Waiting up to {timeout} seconds for server to start...")

        while time.time() - start_time < timeout:
            # Check for startup message in logs
            if not message_found:
                result = subprocess.run(
                    ["docker", "compose", "logs"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if "localhost:4444" in result.stdout:
                    message_found = True
                    print("Found server startup message in logs!")

            # Check if server is responding
            if not server_responding:
                try:
                    response = requests.get(cls.BASE_URL, timeout=2)
                    if response.status_code == 200:
                        server_responding = True
                        print("Server is responding to HTTP requests!")
                except requests.exceptions.RequestException:
                    pass

            # If both checks passed, we're good
            if message_found and server_responding:
                print(f"Server is ready after {int(time.time() - start_time)} seconds")
                return True

            # Wait before trying again
            time.sleep(3)
            print(f"Still waiting... ({int(time.time() - start_time)}s elapsed)")

        # Final check with detailed error messages
        if not message_found:
            result = subprocess.run(["docker", "compose", "logs"], capture_output=True, text=True, check=False)
            raise RuntimeError(
                f"Server startup message not found after {timeout} seconds.\n"
                f"Expected: 'localhost:4444' in logs\n"
                f"Last 1000 chars of logs:\n{result.stdout[-1000:]}"
            )

        if not server_responding:
            raise RuntimeError(f"Server not responding at {cls.BASE_URL} after {timeout} seconds")

    def test_homepage_loads(self):
        """Test that the homepage loads successfully."""
        response = requests.get(self.BASE_URL, timeout=10)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])

    def test_calendly_link(self):
        """Test that the Calendly link is present and accessible."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        calendly_link = soup.find("a", href=lambda x: x and "calendly.com" in x)
        self.assertIsNotNone(calendly_link)

        # Test the Calendly link
        calendly_url = calendly_link["href"]
        response = requests.head(calendly_url, timeout=10)
        self.assertIn(response.status_code, [200, 301, 302])

    def test_all_pages_load(self):
        """Test that all pages in the site load successfully."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Expected links that must be present
        expected_links = {
            # Header
            "/about": "Header About link",
            "/blog": "Header Blog link + Footer Latest Posts link",
            "/contact": "Header Contact link + Footer Get in Touch link",
            # Offerings section
            "/workshops/intro": "Offerings Short workshop link",
            "/workshops/facilitation": "Offerings Facilitation training link",

            # Footer
            "/#testimonial": "Footer Testimonials link",
            "/privacy": "Footer Privacy Policy link",
        }

        # External links that should be present
        external_links = {
            "https://www.linkedin.com/in/migueldiaseu/": "LinkedIn link Footer",
            "https://calendly.com/migueldiaseu": "Footer Book a Call link",
        }

        # Find all links in the page
        all_links = soup.find_all("a", href=True)
        found_links = {a["href"]: a.text.strip() for a in all_links}

        # Check internal links
        for expected_path, description in expected_links.items():
            self.assertIn(
                expected_path,
                found_links,
                f"\nExpected to find {description} with path '{expected_path}'\n"
                f"Found these paths instead:\n"
                f"{json.dumps(found_links, indent=2)}"
            )

            # Test the page loads
            response = requests.get(f"{self.BASE_URL}{expected_path}", timeout=10)

            self.assertEqual(
                response.status_code,
                200,
                f"\nFailed to load {description} at path '{expected_path}'\n"
                f"Status code: {response.status_code}\n"
                f"Response text:\n{response.text[:500]}..."
            )
            self.assertIn(
                "text/html",
                response.headers["content-type"],
                f"\nWrong content type for {description} at path '{expected_path}'\n"
                f"Expected: text/html\n"
                f"Got: {response.headers['content-type']}"
            )

        # Check external links
        for expected_url, description in external_links.items():
            self.assertIn(
                expected_url,
                found_links,
                f"\nExpected to find {description} with URL '{expected_url}'\n"
                f"Found these URLs instead:\n"
                f"{json.dumps(found_links, indent=2)}"
            )

            # Just verify the link exists, but don't fail if it can't be accessed
            try:
                response = requests.head(expected_url, timeout=10)
                if response.status_code not in [200, 301, 302]:
                    print(f"WARNING: External link {description} returned status {response.status_code}")
            except Exception as e:
                print(f"WARNING: Could not access external link {description}: {str(e)}")

    def test_article_images_load(self):
        """Test that all images in articles load successfully."""
        response = requests.get(f"{self.BASE_URL}/articles", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all article links
        article_links = [
            a["href"] for a in soup.find_all("a", href=True)
            if "/articles/" in a["href"]
        ]

        # Test each article
        for article_link in article_links:
            response = requests.get(f"{self.BASE_URL}{article_link}", timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            # Find all images in the article
            images = soup.find_all("img")
            for img in images:
                if "src" in img.attrs:
                    img_url = img["src"]
                    if not img_url.startswith(("http://", "https://")):
                        img_url = f"{self.BASE_URL}{img_url}"
                    response = requests.head(img_url, timeout=10)
                    self.assertEqual(response.status_code, 200)

    def test_testimonials_section(self):
        """Test that testimonials exist, have content, and have valid links."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find testimonials section by ID
        testimonials_section = soup.find("section", id="testimonial")
        self.assertIsNotNone(testimonials_section, "Testimonials section not found")

        # Find all testimonial quotes (paragraphs with quotes)
        quotes = testimonials_section.find_all("p")
        self.assertTrue(len(quotes) > 0, "No testimonial quotes found")

        # Find all authors
        authors = testimonials_section.find_all("cite")
        self.assertTrue(len(authors) > 0, "No testimonial authors found")

        # Check links to full testimonials
        links = testimonials_section.find_all("a", href=lambda x: x and "/blog/" in x)
        self.assertTrue(len(links) > 0, "No links to full testimonials found")

        # Check each link is valid
        for link in links:
            response = requests.get(f"{self.BASE_URL}{link['href']}", timeout=10)
            self.assertEqual(response.status_code, 200, f"Failed to load testimonial at {link['href']}")

    # --- Offerings (Short workshop, Facilitation, Consulting) & Workshop Pages ---

    def test_main_page_offerings_section(self):
        """Homepage has an offerings section with 3 items: short workshop, facilitation training, consulting (contact)."""
        response = requests.get(self.BASE_URL, timeout=10)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.text, "html.parser")

        section = soup.find("section", id="offerings")
        self.assertIsNotNone(section, "Homepage must have a section with id='offerings'")

        # Each item must be a link (or contain a link) with the right data-offering and href
        short = section.find("a", attrs={"data-offering": "short-workshop"})
        self.assertIsNotNone(short, "Offerings section must have a link with data-offering='short-workshop'")
        self.assertEqual(short.get("href"), "/workshops/intro",
            f"Short workshop link must point to /workshops/intro. Got: {short.get('href')}")

        facilitation = section.find("a", attrs={"data-offering": "facilitation-training"})
        self.assertIsNotNone(facilitation, "Offerings section must have a link with data-offering='facilitation-training'")
        self.assertEqual(facilitation.get("href"), "/workshops/facilitation",
            f"Facilitation training link must point to /workshops/facilitation. Got: {facilitation.get('href')}")

    def test_short_workshop_page_exists_and_links_to_flowtopia(self):
        """Short workshop page (/workshops/intro) exists and has a register link to Flowtopia."""
        intro_url = "https://www.flowtopia.io/c/events/introduction-to-value-stream-mapping"
        response = requests.get(f"{self.BASE_URL}/workshops/intro", timeout=10)
        self.assertEqual(response.status_code, 200,
            f"/workshops/intro must return 200. Got: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")

        register_link = soup.find("a", attrs={"data-workshop-register": "intro"})
        self.assertIsNotNone(register_link,
            "Short workshop page must have a register link with data-workshop-register='intro'")
        self.assertEqual(register_link.get("href"), intro_url,
            f"Intro register link must point to Flowtopia. Got: {register_link.get('href')}")

        # Flowtopia link must be reachable
        try:
            head_resp = requests.head(intro_url, timeout=10, allow_redirects=True)
            self.assertIn(head_resp.status_code, [200, 301, 302],
                f"Flowtopia intro URL must be reachable. Got status {head_resp.status_code}")
        except requests.exceptions.RequestException as e:
            self.fail(f"Flowtopia intro URL must be loadable: {e}")

    def test_facilitation_training_page_exists_and_links_to_contact(self):
        """Facilitation training page (/workshops/facilitation) exists and has a CTA linking to Calendly (private training)."""
        calendly_url = "https://calendly.com/migueldiaseu"
        response = requests.get(f"{self.BASE_URL}/workshops/facilitation", timeout=10)
        self.assertEqual(response.status_code, 200,
            f"/workshops/facilitation must return 200. Got: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")

        register_link = soup.find("a", attrs={"data-workshop-register": "facilitation"})
        self.assertIsNotNone(register_link,
            "Facilitation page must have a register/CTA link with data-workshop-register='facilitation'")
        self.assertIn(calendly_url, register_link.get("href", ""),
            f"Facilitation CTA must point to Calendly. Got: {register_link.get('href')}")

    def test_social_proof_band(self):
        """Homepage offerings section has a social proof band with quote and metric chips."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        section = soup.find("section", id="offerings")
        self.assertIsNotNone(section)

        band = section.find(attrs={"data-social-proof": True})
        self.assertIsNotNone(band, "Social proof band must exist in offerings section")

        text = band.get_text()
        self.assertIn("deploying changes", text, "Social proof must contain the featured quote")
        self.assertIn("Mika", text, "Social proof must contain the attribution")
        self.assertIn("64%", text, "Social proof must contain 64% metric")

    def test_workshop_cards_have_images(self):
        """The first two workshop cards in the offerings section have images."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        section = soup.find("section", id="offerings")

        short = section.find("a", attrs={"data-offering": "short-workshop"})
        img = short.find("img")
        self.assertIsNotNone(img, "Short workshop card must have an image")
        img_url = img.get("src")
        resp = requests.head(f"{self.BASE_URL}{img_url}", timeout=10)
        self.assertEqual(resp.status_code, 200, f"Image {img_url} must load")

        facilitation = section.find("a", attrs={"data-offering": "facilitation-training"})
        img = facilitation.find("img")
        self.assertIsNotNone(img, "Facilitation card must have an image")
        img_url = img.get("src")
        resp = requests.head(f"{self.BASE_URL}{img_url}", timeout=10)
        self.assertEqual(resp.status_code, 200, f"Image {img_url} must load")

    def test_resources_carousel(self):
        """Homepage has a resources carousel with 3 items: blog, short, talk."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        carousel = soup.find(attrs={"data-resources-carousel": True})
        self.assertIsNotNone(carousel, "Homepage must have a resources carousel")

        blog = carousel.find("a", attrs={"data-carousel-item": "blog"})
        self.assertIsNotNone(blog, "Carousel must have a blog item")
        self.assertIn("/blog/2025-05-19-what-is-vsm", blog.get("href", ""))

        short = carousel.find("a", attrs={"data-carousel-item": "short"})
        self.assertIsNotNone(short, "Carousel must have a short item")
        self.assertIn("youtube.com/shorts/FGXKSSGeUX4", short.get("href", ""))

        talk = carousel.find("a", attrs={"data-carousel-item": "talk"})
        self.assertIsNotNone(talk, "Carousel must have a talk item")
        self.assertIn("youtube.com/watch", talk.get("href", ""))

    def test_offerings_ctas_are_buttons(self):
        """Both offering cards have button-styled CTAs."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        section = soup.find("section", id="offerings")
        cards = section.find_all("a", attrs={"data-offering": True})
        self.assertEqual(len(cards), 2, "Must have exactly 2 offering cards")

        for card in cards:
            btn = card.find(attrs={"data-cta": True})
            self.assertIsNotNone(btn,
                f"Card {card.get('data-offering')} must have a CTA element with data-cta")

    def test_intro_workshop_pricing_block(self):
        """Intro workshop page has public and private pricing."""
        response = requests.get(f"{self.BASE_URL}/workshops/intro", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        pricing = soup.find(attrs={"data-pricing": "intro"})
        self.assertIsNotNone(pricing, "Intro page must have a pricing block with data-pricing='intro'")

        text = pricing.get_text()
        self.assertIn("50", text, "Must mention €50 price")
        self.assertIn("1,000", text, "Must mention €1,000 private price")
        self.assertIn("2,000", text, "Must mention €2,000 package")

    def test_facilitation_mika_testimonial_links_to_post(self):
        """Mika Schafroth testimonial on facilitation page links to her full testimonial post."""
        response = requests.get(f"{self.BASE_URL}/workshops/facilitation", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        link = soup.find("a", attrs={"data-testimonial": "mika-schafroth"})
        self.assertIsNotNone(link,
            "Facilitation page must have a testimonial link with data-testimonial='mika-schafroth'")
        self.assertEqual(link.get("href"), "/blog/2025-02-17-mika-schafroth-testimonial",
            f"Mika testimonial must link to her blog post. Got: {link.get('href')}")

        # Verify the linked page loads
        resp = requests.get(f"{self.BASE_URL}{link['href']}", timeout=10)
        self.assertEqual(resp.status_code, 200,
            f"Testimonial post must load. Got status {resp.status_code}")

    def test_facilitation_pricing_block(self):
        """Facilitation page has public and private pricing."""
        response = requests.get(f"{self.BASE_URL}/workshops/facilitation", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        pricing = soup.find(attrs={"data-pricing": "facilitation"})
        self.assertIsNotNone(pricing, "Facilitation page must have a pricing block with data-pricing='facilitation'")

        text = pricing.get_text()
        self.assertIn("500", text, "Must mention €500 public price")
        self.assertIn("1,500", text, "Must mention €1,500 private price")

    # --- Cookie Banner & Analytics Tests ---

    def test_cookie_banner_present(self):
        """Test that the cookie banner HTML is present on all main pages."""
        pages = ['/', '/about', '/contact', '/privacy', '/blog', '/workshops/intro', '/workshops/facilitation']
        for page in pages:
            response = requests.get(f"{self.BASE_URL}{page}", timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            banner = soup.find(id="cookie-banner")
            self.assertIsNotNone(banner, f"Cookie banner not found on {page}")
            accept_btn = soup.find(id="cookie-accept")
            decline_btn = soup.find(id="cookie-decline")
            self.assertIsNotNone(accept_btn, f"Accept button not found on {page}")
            self.assertIsNotNone(decline_btn, f"Decline button not found on {page}")

    def test_book_call_buttons_have_tracking_attribute(self):
        """Test that all Book a Call links pointing to Calendly have the data-track-book-call attribute."""
        pages_with_book_call = {
            '/': ['ready-to-improve', 'header'],
            '/about': ['about'],
            '/contact': ['contact'],
        }
        for page, expected_labels in pages_with_book_call.items():
            response = requests.get(f"{self.BASE_URL}{page}", timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            tracked_links = soup.find_all("a", attrs={"data-track-book-call": True})
            found_labels = [link.get("data-track-book-call") for link in tracked_links]
            for label in expected_labels:
                self.assertIn(label, found_labels,
                    f"Missing data-track-book-call='{label}' on {page}. Found: {found_labels}")

    def test_footer_has_tracking_on_book_call(self):
        """Test that the footer Book a Call link has tracking on every page."""
        pages = ['/', '/about', '/contact', '/blog', '/workshops/intro', '/workshops/facilitation']
        for page in pages:
            response = requests.get(f"{self.BASE_URL}{page}", timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            footer_tracked = soup.find("a", attrs={"data-track-book-call": "footer"})
            self.assertIsNotNone(footer_tracked,
                f"Footer 'Book a Call' link missing data-track-book-call='footer' on {page}")

    def test_offering_cards_have_tracking_attribute(self):
        """Test that homepage workshop cards have data-track-offering for analytics."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        tracked = soup.find_all("a", attrs={"data-track-offering": True})
        labels = [link.get("data-track-offering") for link in tracked]

        self.assertIn("short-workshop", labels,
            f"Missing data-track-offering='short-workshop'. Found: {labels}")
        self.assertIn("facilitation-training", labels,
            f"Missing data-track-offering='facilitation-training'. Found: {labels}")

    def test_workshop_register_links_have_tracking_attribute(self):
        """Test that workshop register CTAs have data-track-workshop-register for analytics."""
        response = requests.get(f"{self.BASE_URL}/workshops/intro", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        tracked = soup.find_all("a", attrs={"data-track-workshop-register": True})
        labels = [link.get("data-track-workshop-register") for link in tracked]

        self.assertIn("intro", labels,
            f"Missing data-track-workshop-register='intro' on /workshops/intro. Found: {labels}")
        self.assertIn("intro-cohort-2", labels,
            f"Missing data-track-workshop-register='intro-cohort-2' on /workshops/intro. Found: {labels}")

    def test_footer_work_together_links(self):
        """Footer Work Together section links to workshops and testimonials."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Find the page-level footer (the last one, not blockquote footers)
        footers = soup.find_all("footer")
        footer = footers[-1]
        self.assertIsNotNone(footer)

        links = footer.find_all("a", href=True)
        hrefs = [a["href"] for a in links]

        self.assertIn("/workshops/intro", hrefs,
            f"Footer must link to /workshops/intro. Found: {hrefs}")
        self.assertIn("/workshops/facilitation", hrefs,
            f"Footer must link to /workshops/facilitation. Found: {hrefs}")
        self.assertIn("/#testimonial", hrefs,
            f"Footer must link to /#testimonial. Found: {hrefs}")

    def test_about_page_bio_content(self):
        """About page has updated bio with background, 2024 results, and 2025 results."""
        response = requests.get(f"{self.BASE_URL}/about", timeout=10)
        self.assertEqual(response.status_code, 200)
        text = response.text

        self.assertIn("6+ years of experience", text,
            "About page must mention years of experience")
        self.assertIn("DevOps, Cloud Infrastructure, Data Engineering", text,
            "About page must mention background areas")
        self.assertIn("RELEX", text, "About page must mention RELEX")
        self.assertIn("Bond Touch", text, "About page must mention Bond Touch")
        self.assertIn("Lisbon Data Science Academy", text,
            "About page must mention Lisbon Data Science Academy")
        self.assertIn("Berlin VSM", text,
            "About page must mention Berlin VSM community")

    def test_manage_cookies_link_in_footer(self):
        """Test that a 'Manage Cookies' button exists in the footer for consent withdrawal."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        manage_btn = soup.find(id="manage-cookies")
        self.assertIsNotNone(manage_btn, "Manage Cookies button not found in footer")

    def test_privacy_page_mentions_cookies(self):
        """Test that the privacy page contains required cookie-related information."""
        response = requests.get(f"{self.BASE_URL}/privacy", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text().lower()
        self.assertIn("google analytics", text, "Privacy page must mention Google Analytics")
        self.assertIn("cookie_consent", text, "Privacy page must mention the consent cookie")
        self.assertIn("manage cookies", text, "Privacy page must explain how to withdraw consent")

    # --- Lean Coffee Page Tests ---

    def test_lean_coffee_page_loads(self):
        """Lean coffee page loads at /lean-coffee."""
        response = requests.get(f"{self.BASE_URL}/lean-coffee", timeout=10)
        self.assertEqual(response.status_code, 200,
            f"/lean-coffee must return 200. Got: {response.status_code}")
        self.assertIn("text/html", response.headers["content-type"])

    def test_lean_coffee_has_cover_image(self):
        """Lean coffee page has the cover image that loads successfully."""
        response = requests.get(f"{self.BASE_URL}/lean-coffee", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        img = soup.find("img", attrs={"data-lean-coffee": "cover"})
        self.assertIsNotNone(img, "Lean coffee page must have a cover image with data-lean-coffee='cover'")
        img_url = img.get("src")
        self.assertIn("lean-coffee", img_url, "Cover image src must reference lean-coffee folder")

        resp = requests.head(f"{self.BASE_URL}{img_url}", timeout=10)
        self.assertEqual(resp.status_code, 200, f"Cover image {img_url} must load")

    def test_lean_coffee_has_description(self):
        """Lean coffee page has the session description."""
        response = requests.get(f"{self.BASE_URL}/lean-coffee", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        self.assertIn("Monday", text,
            "Page must mention Monday")
        self.assertIn("lightly facilitated conversation", text,
            "Page must describe the lean coffee format")

    def test_lean_coffee_links_to_communities(self):
        """Lean coffee page links to Flow Collective and Flowtopia."""
        response = requests.get(f"{self.BASE_URL}/lean-coffee", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        flow_collective = soup.find("a", href="https://flowcollective.org/")
        self.assertIsNotNone(flow_collective,
            "Page must link to Flow Collective (https://flowcollective.org/)")

        flowtopia = soup.find("a", href=lambda x: x and "flowtopia.io" in x)
        self.assertIsNotNone(flowtopia,
            "Page must link to Flowtopia")

    def test_lean_coffee_has_email_signup(self):
        """Lean coffee page has a Supascribe widget for email signup."""
        response = requests.get(f"{self.BASE_URL}/lean-coffee", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        signup = soup.find(attrs={"data-lean-coffee": "signup"})
        self.assertIsNotNone(signup, "Page must have a signup section with data-lean-coffee='signup'")

        widget = signup.find(attrs={"data-supascribe-subscribe": True})
        self.assertIsNotNone(widget, "Signup section must contain a Supascribe widget")

    @unittest.skipUnless(os.environ.get("FORCE_BUILD"), "Supascribe script test only runs on pre-push (FORCE_BUILD=1)")
    def test_lean_coffee_supascribe_script_loads(self):
        """Supascribe script is reachable."""
        response = requests.get(f"{self.BASE_URL}/lean-coffee", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        script = soup.find("script", src=lambda s: s and "supascribe.com" in s)
        self.assertIsNotNone(script, "Page must include the Supascribe script")

        resp = requests.get(script["src"], timeout=10)
        self.assertEqual(resp.status_code, 200,
            f"Supascribe script must be reachable. Got status {resp.status_code}")

    def test_lean_coffee_community_links_have_tracking(self):
        """Lean coffee community links have data-track-lean-coffee for analytics."""
        response = requests.get(f"{self.BASE_URL}/lean-coffee", timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        tracked = soup.find_all(attrs={"data-track-lean-coffee": True})
        labels = [el.get("data-track-lean-coffee") for el in tracked]

        self.assertIn("flow-collective", labels,
            f"Missing data-track-lean-coffee='flow-collective'. Found: {labels}")
        self.assertIn("flowtopia", labels,
            f"Missing data-track-lean-coffee='flowtopia'. Found: {labels}")
        self.assertIn("signup", labels,
            f"Missing data-track-lean-coffee='signup'. Found: {labels}")

if __name__ == '__main__':
    unittest.main()
