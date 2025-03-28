import requests
import pytest

def test_server_is_running():
    """Test that the server is running and accessible."""
    response = requests.get('http://localhost:4444')
    assert response.status_code == 200
    assert 'text/html' in response.headers['content-type'] 