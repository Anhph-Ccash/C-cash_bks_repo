import pytest
from playwright.sync_api import sync_playwright
import subprocess
import time
import os

@pytest.fixture(scope="session")
def flask_app():
    """Start Flask app before tests"""
    # Set environment
    os.environ['FLASK_ENV'] = 'testing'
    
    # Start Flask app in subprocess
    process = subprocess.Popen(
        ['python', 'app.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    yield process
    
    # Cleanup
    process.terminate()
    process.wait()

@pytest.fixture(scope="session")
def browser():
    """Provide browser instance for all tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    """Provide new page for each test"""
    context = browser.new_context()
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture
def base_url():
    """Base URL for the application"""
    return "http://127.0.0.1:5001"
