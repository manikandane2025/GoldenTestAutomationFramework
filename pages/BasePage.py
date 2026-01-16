# pages/base_page.py

import asyncio
from clients.PlayWrightClient import PlaywrightClient
from playwright.async_api import Page
from clients.WebElements import WebElement


class BasePage:
    """
    Base class for all Page Object Models (POMs).
    Provides common asynchronous utilities and direct access to the client.
    """

    def __init__(self, client: PlaywrightClient):
        """Initializes the base page with the Playwright client."""
        # Every child Page Object must pass its client instance to the base constructor
        self.client: PlaywrightClient = client
        self.page: Page = client.page

    async def capture_state_screenshot(self, label: str):
        """
        Takes a screenshot of the current page state and embeds it into the report.

        This method is asynchronous because it calls the client's async method.
        """
        # CRITICAL: Await the client's async method call
        await PlaywrightClient.capture_and_embed_screenshot(self.client)
        return self

    # You could add other common async methods here, like:
    # async def verify_page_title(self, title):
    #     await expect(self.page).to_have_title(title)