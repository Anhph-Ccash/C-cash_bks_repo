"""Test statement config CRUD operations"""
import pytest
from playwright.sync_api import Page, expect

@pytest.fixture
def logged_in_page(page: Page, base_url: str, flask_app):
    """Provide logged in page"""
    page.goto(f"{base_url}/login")
    page.fill('input[name="username"]', 'testuser')
    page.fill('input[name="password"]', '123456')
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/dashboard")
    return page

def test_statement_config_table_headers(logged_in_page: Page):
    """Test statement config table has correct headers"""
    # Check all column headers
    headers = [
        'bank_code', 'keywords', 'col_keyword', 'col_value',
        'row_start', 'row_end', 'identify_info', 'cell_format', 'created_at'
    ]
    
    for header in headers:
        expect(logged_in_page.locator(f'th:has-text("{header}")')).to_be_visible()

def test_add_statement_config_modal(logged_in_page: Page):
    """Test add statement config modal"""
    # Find and click the second "Thêm mới" button (for statement config)
    buttons = logged_in_page.locator('button:has-text("Thêm mới")')
    buttons.nth(1).click()  # Second button
    
    # Check modal appeared
    expect(logged_in_page.locator('text=Thêm Cấu hình nhận diện Sổ phụ')).to_be_visible()
    
    # Check form fields
    expect(logged_in_page.locator('input[name="bank_code"]')).to_be_visible()
    expect(logged_in_page.locator('input[name="keywords"]')).to_be_visible()
    expect(logged_in_page.locator('input[name="col_keyword"]')).to_be_visible()
    expect(logged_in_page.locator('input[name="col_value"]')).to_be_visible()
    expect(logged_in_page.locator('input[name="row_start"]')).to_be_visible()
    expect(logged_in_page.locator('input[name="row_end"]')).to_be_visible()
    expect(logged_in_page.locator('textarea[name="identify_info"]')).to_be_visible()

def test_statement_config_scroll(logged_in_page: Page):
    """Test statement config table has scroll"""
    table_container = logged_in_page.locator('.table-responsive').nth(1)
    
    # Check max-height style is applied
    style = table_container.get_attribute('style')
    assert 'max-height: 400px' in style
    assert 'overflow-y: auto' in style

def test_company_selector_visible(logged_in_page: Page):
    """Test company selector is visible"""
    # Check company badge strip exists
    expect(logged_in_page.locator('.badge.bg-info')).to_be_visible()
