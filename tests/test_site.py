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
        """Test that all testimonials are present and properly formatted."""
        response = requests.get(self.BASE_URL, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find the testimonials section
        testimonials_section = soup.find("section", attrs={"data-testid": "testimonial-section"})
        if not testimonials_section:
            print("\nCouldn't find testimonials section. Available sections:")
            for section in soup.find_all("section"):
                print(f"Section with classes: {section.get('class', [])} and data-testid: {section.get('data-testid')}")
        
        self.assertIsNotNone(testimonials_section, "Testimonials section not found")
        
        # Find all testimonial cards
        testimonial_cards = testimonials_section.find_all("div", class_="testimonial-card")
        
        # Debug output
        print(f"\nFound {len(testimonial_cards)} testimonial cards")
        if len(testimonial_cards) == 0:
            print("\nHTML of testimonials section:")
            print(testimonials_section.prettify())
        
        # Verify we have all 4 testimonials
        self.assertEqual(len(testimonial_cards), 4, f"Expected 4 testimonials, found {len(testimonial_cards)}")
        
        # Expected authors
        expected_authors = ["Jukka Palosaari", "Iker Garagarza", "Mark Sadler", "Mika Schafroth"]
        
        # Check each testimonial
        found_authors = []
        for card in testimonial_cards:
            author = card.find("h3")
            if author:
                found_authors.append(author.text.strip())
        
        # Debug output
        print("\nFound authors:", found_authors)
        
        # Verify all authors are present
        for author in expected_authors:
            self.assertIn(author, found_authors, f"Missing testimonial from {author}")

if __name__ == '__main__':
    unittest.main() 