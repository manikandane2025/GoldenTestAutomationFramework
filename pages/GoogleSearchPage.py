# pages/GoogleSearchPage.py
from clients.WebElements import TextBox, Button, Link
from clients.PlayWrightClient import PlaywrightClient
from playwright.async_api import Page, expect

from pages.BasePage import BasePage


class GoogleSearchPage(BasePage):
    """
    Page Object Model for the Google Search home page and results page. Migrated to ASYNC.
    """

    def __init__(self, client: PlaywrightClient):
        super().__init__(client)
        self.client = client
        self.page: Page = client.page

        self.SEARCH_BOX = TextBox(self.page, "textarea[name='q']", "Google Search Input")
        self.SEARCH_BUTTON = Button(self.page, "input[value='Google Search'] >> nth=0", "Google Search Button")
        self.IM_FEELING_LUCKY_BUTTON = Button(self.page, "input[name='btnI']", "I'm Feeling Lucky Button")
        self.RESULT_LINK = Link(self.page, "h3", "First Search Result Heading")

    async def navigate_to(self):
        """Navigates to the Google search page."""
        await self.client.navigate("https://www.google.com")
        return self

    async def search_for(self, query: str):
        """Performs a search action on the page."""
        await self.SEARCH_BOX.fill(query, f"Entering search query: {query}")
        await self.SEARCH_BUTTON.click("Clicking Google search button")
        return self

    async def click_feeling_lucky(self):
        """Clicks the 'I'm Feeling Lucky' button."""
        await self.IM_FEELING_LUCKY_BUTTON.click("Clicking I'm Feeling Lucky")
        return self

    async def get_first_result_text(self):
        """Returns the text of the first search result."""
        return await self.RESULT_LINK.get_text()

    async def assert_page_title_contains(self, text: str):
        """Asserts that the page title contains the specified text."""
        await expect(self.page).to_have_title(text=text)