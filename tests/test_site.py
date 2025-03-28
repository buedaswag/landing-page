import pytest
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import subprocess

# Constants
BASE_URL = "http://localhost:4444"
TIMEOUT = 10

def check_server_ready():
    """Check if server is ready by checking logs and response."""
    try:
        # Check container logs for startup message
        result = subprocess.run(
            ["docker", "compose", "logs"],
            capture_output=True,
            text=True,
            check=True
        )
        if "Server is running at" not in result.stdout:
            return False
        
        # Verify server is responding
        response = requests.get(BASE_URL, timeout=2)
        return response.status_code == 200
    except Exception:
        return False

def cleanup():
    """Clean up Docker containers."""
    subprocess.run(["docker", "compose", "down"], check=True)

@pytest.fixture(scope="session", autouse=True)
def setup_docker():
    """Set up Docker containers before tests and clean up after."""
    # Get project root
    project_root = Path(__file__).parent.parent
    
    # Stop any existing containers
    subprocess.run(["docker", "compose", "down"], cwd=project_root, check=True)
    
    # Build and start containers
    subprocess.run(["docker", "compose", "up", "--build", "-d"], cwd=project_root, check=True)
    
    # Wait for server to be ready
    if not check_server_ready():
        cleanup()
        pytest.fail("Server failed to start")
    
    yield
    
    # Cleanup after tests
    cleanup()

def test_homepage_loads():
    """Test that the homepage loads successfully."""
    response = requests.get(BASE_URL, timeout=TIMEOUT)
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_calendly_link():
    """Test that the Calendly link is present and accessible."""
    response = requests.get(BASE_URL, timeout=TIMEOUT)
    soup = BeautifulSoup(response.text, "html.parser")
    calendly_link = soup.find("a", href=lambda x: x and "calendly.com" in x)
    assert calendly_link is not None
    
    # Test the Calendly link
    calendly_url = calendly_link["href"]
    response = requests.head(calendly_url, timeout=TIMEOUT)
    assert response.status_code in [200, 301, 302]  # Allow redirects

def test_all_pages_load():
    """Test that all pages in the site load successfully."""
    response = requests.get(BASE_URL, timeout=TIMEOUT)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all internal links
    internal_links = [
        a["href"] for a in soup.find_all("a", href=True)
        if a["href"].startswith("/") and not a["href"].startswith("//")
    ]
    
    # Test each internal link
    for link in internal_links:
        response = requests.get(f"{BASE_URL}{link}", timeout=TIMEOUT)
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

def test_article_images_load():
    """Test that all images in articles load successfully."""
    response = requests.get(f"{BASE_URL}/articles", timeout=TIMEOUT)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all article links
    article_links = [
        a["href"] for a in soup.find_all("a", href=True)
        if "/articles/" in a["href"]
    ]
    
    # Test each article
    for article_link in article_links:
        response = requests.get(f"{BASE_URL}{article_link}", timeout=TIMEOUT)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find all images in the article
        images = soup.find_all("img")
        for img in images:
            if "src" in img.attrs:
                img_url = img["src"]
                if not img_url.startswith(("http://", "https://")):
                    img_url = f"{BASE_URL}{img_url}"
                response = requests.head(img_url, timeout=TIMEOUT)
                assert response.status_code == 200 