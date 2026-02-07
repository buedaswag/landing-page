import unittest
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import subprocess
import json
import time

class TestSite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Called once before all tests in this class"""
        cls.BASE_URL = "http://localhost:4444"
        cls.project_root = Path(__file__).parent.parent
        
        # Clean up any existing containers
        subprocess.run(["docker", "compose", "down"], check=True)
        
        # Start containers
        subprocess.run(["docker", "compose", "up", "--build", "-d"], check=True)
        
        # Wait for server to be ready
        cls._wait_for_server()

    @classmethod
    def tearDownClass(cls):
        """Called once after all tests in this class"""
        subprocess.run(["docker", "compose", "down"], check=True)

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
            
            # Main Navigation/Content
            "/#case-study": "Case Study link",
            "/#how-we-work": "How We Work link",
            
            # Footer
            "/#testimonial": "Footer Testimony link",
            "/privacy": "Footer Privacy Policy link",
        }
        
        # External links that should be present
        external_links = {
            "https://www.linkedin.com/in/migueldiaseu/": "LinkedIn link Header = Footer",
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

    # --- Cookie Banner & Analytics Tests ---

    def test_cookie_banner_present(self):
        """Test that the cookie banner HTML is present on all main pages."""
        pages = ['/', '/about', '/contact', '/privacy', '/blog']
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
            '/': ['hero', 'ready-to-improve'],
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
        pages = ['/', '/about', '/contact', '/blog']
        for page in pages:
            response = requests.get(f"{self.BASE_URL}{page}", timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")
            footer_tracked = soup.find("a", attrs={"data-track-book-call": "footer"})
            self.assertIsNotNone(footer_tracked,
                f"Footer 'Book a Call' link missing data-track-book-call='footer' on {page}")

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

if __name__ == '__main__':
    unittest.main()