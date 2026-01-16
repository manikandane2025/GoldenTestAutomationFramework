# pages/swagapi.py

from clients.WebElements import TextBox, Button, WebElement, SelectorType
from clients.PlayWrightClient import PlaywrightClient
from playwright.async_api import Page, expect

from pages.BasePage import BasePage


class SwagLabsLoginPage(BasePage):
    """
    Page Object Model for the Swag Labs login page. Migrated to ASYNC.
    """
    URL = "https://www.saucedemo.com/"

    def __init__(self, client: PlaywrightClient):
        super().__init__(client)
        self.client = client
        self.page: Page = client.page

        # --- Element Definitions ---
        self.USERNAME_INPUT = TextBox(self.page, "user-name", "Username Input Field", selector_type=SelectorType.ID)
        self.PASSWORD_INPUT = TextBox(self.page, "input[data-test='password']", "Password Input Field", selector_type=SelectorType.ID)
        self.LOGIN_BUTTON = Button(self.page, "//input[@id='login-button']", "Login Button", selector_type=SelectorType.XPATH)
        self.ERROR_MESSAGE = WebElement(self.page, "Epic sadface: Username and password do not match any user in this service", "Login Error Message", selector_type=SelectorType.TEXT)

    async def navigate_to(self):
        """Navigates to the Swag Labs login page using the client's auto-wait navigation."""
        await self.client.navigate(self.URL)
        return self

    async def login(self, username: str, password: str):
        """Performs the login action."""
        await self.USERNAME_INPUT.fill(username, f"Entering username: {username}")

        await self.PASSWORD_INPUT.fill(password, f"Entering password")
        await self.LOGIN_BUTTON.click("Clicking Login button")
        await PlaywrightClient.capture_and_embed_screenshot(self.client)

        return self

    async def assert_inventory_page_loaded(self):
        """Asserts successful navigation to the inventory page."""
        await expect(self.page).to_have_url("https://www.saucedemo.com/inventory.html")

    async def assert_error_message_is_visible(self):
        """Asserts that the specific error message is visible."""
        await self.ERROR_MESSAGE.assert_is_visible("Verifying login error message is visible")

    async def assert_loginpage_title_contains(self, expected_title: str):
        """Asserts that the page title contains the expected text."""
        await expect(self.page).to_have_title(expected_title, timeout=10000)