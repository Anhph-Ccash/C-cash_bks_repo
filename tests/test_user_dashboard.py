"""Test user login and dashboard functionality"""
import pytest
from playwright.sync_api import Page, expect

def test_login_page_loads(page: Page, base_url: str):
    """Test login page loads correctly"""
    page.goto(f"{base_url}/login")
    
    # Check title
    expect(page).to_have_title("Login")
    
    # Check form elements exist
    expect(page.locator('input[name="username"]')).to_be_visible()
    expect(page.locator('input[name="password"]')).to_be_visible()
    expect(page.locator('button[type="submit"]')).to_be_visible()

def test_user_login(page: Page, base_url: str, flask_app):
    """Test user can login successfully"""
    page.goto(f"{base_url}/login")
    
    # Fill login form
    page.fill('input[name="username"]', 'testuser')
    page.fill('input[name="password"]', '123456')
    
    # Click login button
    page.click('button[type="submit"]')
    
    # Wait for navigation
    page.wait_for_url(f"{base_url}/dashboard")
    
    # Verify dashboard loaded
    expect(page.locator('text=Dashboard')).to_be_visible()

def test_user_dashboard_sections(page: Page, base_url: str, flask_app):
    """Test dashboard has all required sections"""
    # Login first
    page.goto(f"{base_url}/login")
    page.fill('input[name="username"]', 'testuser')
    page.fill('input[name="password"]', '123456')
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard")
    
    # Check for upload section
    expect(page.locator('text=Tải sổ phụ / Upload File')).to_be_visible()
    
    # Check for config sections
    expect(page.locator('text=Cấu hình nhận diện Ngân hàng')).to_be_visible()
    expect(page.locator('text=Cấu hình nhận diện Sổ phụ Ngân hàng')).to_be_visible()

def test_bank_config_table(page: Page, base_url: str, flask_app):
    """Test bank config table displays correctly"""
    # Login
    page.goto(f"{base_url}/login")
    page.fill('input[name="username"]', 'testuser')
    page.fill('input[name="password"]', '123456')
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard")
    
    # Check table headers
    expect(page.locator('th:has-text("bank_code")')).to_be_visible()
    expect(page.locator('th:has-text("keywords")')).to_be_visible()
    expect(page.locator('th:has-text("bank_name")')).to_be_visible()

def test_add_bank_config_modal(page: Page, base_url: str, flask_app):
    """Test add bank config modal opens"""
    # Login
    page.goto(f"{base_url}/login")
    page.fill('input[name="username"]', 'testuser')
    page.fill('input[name="password"]', '123456')
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard")
    
    # Click add button
    page.click('button:has-text("Thêm mới")')
    
    # Check modal appeared
    expect(page.locator('.modal.show')).to_be_visible()
    expect(page.locator('text=Thêm Cấu hình nhận diện Ngân hàng')).to_be_visible()
