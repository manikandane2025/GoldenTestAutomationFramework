import yaml
import logging
import os
import time
import asyncio
import base64
from playwright.async_api import async_playwright, Playwright, expect, Page, Locator, \
    TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError
from Utility.frameworkDataContext import CustomContext
from typing import Callable

logger = logging.getLogger("TestAutomationLogger")

class PlaywrightClient:
    """
    A comprehensive and complete Playwright client migrated to use the ASYNC API.
    """

    def __init__(self, config_path="config/browser_settings.yaml", application_url=None):
        if not application_url:
            raise ValueError("Application URL must be provided when initializing PlaywrightClient.")

        try:
            if not os.path.exists(config_path):
                logger.warning(f"Configuration file not found at {config_path}. Using default settings.")
                self.config = {'browser': {'type': 'chromium', 'headless': False, 'slow_mo': 0}}
            else:
                with open(config_path, "r") as f:
                    self.config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            raise

        self.playwright: Playwright = None
        self.browser = None
        self.context = None
        self._page: Page = None
        self.trace_enabled = False
        self.application_url = application_url

    @classmethod
    async def create(cls, config_path="config/browser_settings.yaml", application_url=None):
        instance = cls(config_path, application_url)
        await instance._start_browser_session()
        return instance

    @property
    def page(self) -> Page:
        if not self._page:
            raise RuntimeError("Playwright Page is not initialized. Browser session failed to start.")
        return self._page

    async def capture_and_embed_screenshot(self, label: str = "Diagnostic_Snapshot"):
        """
        Captures a screenshot of the current page and embeds it into the CustomContext
        for JSON report inclusion (Called by BasePage).

        The Page object is accessed directly via self.page.
        """
        # Use the label, defaulting to a descriptive name if missing or none
        safe_label = label if label else "Diagnostic_Snapshot"
        action_name = f"MANUAL_CAPTURE_{safe_label.replace(' ', '_')}"

        try:
            # 1. Capture screenshot bytes using self.page
            screenshot_bytes = await self.page.screenshot(type="png", full_page=True, timeout=5000)

            # 2. Encode to Base64
            base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')

            # 3. Store in CustomContext using a UNIQUE, timestamped key
            contextdata = CustomContext()
            unique_key = "screenshot"

            contextdata.set_user_data(unique_key, {
                "mime_type": "image/png",
                "data": base64_screenshot
            })

            logger.info(f"CAPTURED: Manual screenshot '{safe_label}' embedded in report.")

        except Exception as e:
            # Note: In an async environment, the cleanup logic often handles errors.
            logger.error(f"ERROR: Failed to capture manual screenshot '{safe_label}': {e}")

    async def _client_capture_failure(page: Page, action_name: str, exception: Exception):
        """Utility to capture and store screenshot on PlaywrightClient failures."""
        try:
            await asyncio.sleep(0.5)
            screenshot_bytes = await page.screenshot(type="png", full_page=True, timeout=5000)
            base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
            contextdata = CustomContext()

            key_name = f"screenshot_{action_name}_{int(time.time())}"

            contextdata.set_user_data(key_name, {
                "mime_type": "image/png",
                "data": base64_screenshot
            })
            logger.error(f"CLIENT FAIL: Screenshot captured for unhandled action: {action_name}")
        except Exception as e:
            logger.error(f"FATAL: Could not capture screenshot during client failure: {e}")

    async def _start_browser_session(self):
        try:
            self.playwright = await async_playwright().start()
            browser_config = self.config.get('browser', {})
            browser_type = browser_config.get("type", "chromium").lower()
            env_browser = os.getenv("PLAYWRIGHT_BROWSER")
            if env_browser:
                browser_type = env_browser.lower()
            env_headless = os.getenv("PLAYWRIGHT_HEADLESS")
            if env_headless is not None:
                browser_config["headless"] = env_headless.lower() in ["1", "true", "yes"]

            channel = None
            if browser_type == 'chromium':
                playwright_browser_type = self.playwright.chromium
            elif browser_type == 'edge':
                playwright_browser_type = self.playwright.chromium
                channel = 'msedge'
            elif browser_type == 'chrome':
                logger.info("Using Chrome browser channel.")
                playwright_browser_type = self.playwright.chromium
                channel = 'chrome'
            elif browser_type == 'firefox':
                playwright_browser_type = self.playwright.firefox
            elif browser_type == 'webkit':
                playwright_browser_type = self.playwright.webkit
            else:
                raise ValueError(f"Unsupported browser type: {browser_type}. Supported: chrome, firefox, webkit, edge")

            launch_options = {
                "headless": browser_config.get("headless", True),
                "slow_mo": browser_config.get("slow_mo", 0),
                "channel": channel,
                "executable_path": browser_config.get("driver_path")
            }

            download_dir = None
            if browser_type in ['chrome', 'edge']:
                download_dir = browser_config.get(f'{browser_type}_options', {}).get('prefs', {}).get(
                    'download.default_directory')
            if not download_dir:
                download_dir = browser_config.get('additional_capabilities', {}).get('prefs', {}).get(
                    'download.default_directory')
            if download_dir:
                launch_options['downloads_path'] = download_dir
                logger.info(f"Set download directory to {download_dir}.")

            browser_args = []
            if browser_config.get("disable_gpu"):
                browser_args.append('--disable-gpu')

            additional_args = browser_config.get('additional_capabilities', {}).get('args', {})
            if additional_args.get('disable_logging'):
                browser_args.append('--disable-logging')

            if browser_type in ['chrome', 'edge']:
                specific_options = browser_config.get(f'{browser_type}_options', {})
                chrome_edge_args = specific_options.get('args', {})
                if chrome_edge_args.get('no_sandbox'):
                    browser_args.append('--no-sandbox')
                if chrome_edge_args.get('window_size'):
                    browser_args.append(f'--window-size={chrome_edge_args["window_size"]}')

            if browser_args:
                launch_options['args'] = browser_args

            if browser_type == 'firefox':
                firefox_prefs = browser_config.get('firefox_options', {}).get('prefs', {})
                if firefox_prefs:
                    launch_options['firefox_user_prefs'] = firefox_prefs

            self.browser = await playwright_browser_type.launch(**launch_options)
            logger.info(f"Browser '{browser_type}' launched with headless={launch_options['headless']}.")

            context_options = {"ignore_https_errors": True}

            is_incognito = browser_config.get('incognito', False)
            if is_incognito:
                logger.info("Starting in incognito (non-persistent) mode.")

            window_size = browser_config.get("window_size")
            if window_size and isinstance(window_size, str):
                try:
                    width, height = map(int, window_size.lower().replace('x', ' ').split('x'))
                    context_options["viewport"] = {"width": width, "height": height}
                    logger.info(f"Set viewport size to: {width}x{height}")
                except ValueError:
                    logger.warning(f"Invalid window_size format: '{window_size}'. Must be 'WIDTHxHEIGHT'.")

            if os.path.exists("auth_state.json") and not is_incognito:
                context_options["storage_state"] = "auth_state.json"
                logger.info("Loaded authentication state from auth_state.json")

            if browser_config.get("proxy"):
                context_options["proxy"] = browser_config["proxy"]
            if browser_config.get("http_credentials"):
                context_options["http_credentials"] = browser_config["http_credentials"]

            self.context = await self.browser.new_context(**context_options)

            if browser_config.get("geolocation"):
                await self.context.set_geolocation(browser_config["geolocation"])
            if browser_config.get("permissions"):
                await self.context.grant_permissions(browser_config["permissions"])

            tracing_config = self.config.get('tracing', {})
            if tracing_config.get('enabled', False):
                await self.context.tracing.start(
                    screenshots=tracing_config.get('screenshots', True),
                    snapshots=tracing_config.get('snapshots', True),
                    sources=tracing_config.get('sources', True)
                )
                self.trace_enabled = True

            self._page = await self.context.new_page()

            if browser_config.get('disable_images', False):
                await self._page.route(
                    "**/*.{png,jpg,jpeg,gif,svg,webp}",
                    lambda route: asyncio.create_task(route.abort())
                )
                logger.info("Image loading disabled via page routing.")

            if self.application_url:
                await self.navigate(self.application_url)

        except Exception as e:
            logger.error(f"Failed to start browser: {e}")
            await self.close_browser()
            raise

    async def close_browser(self):
        """Closes the browser session and stops the Playwright instance."""
        if self.trace_enabled and self.context:
            output_dir = self.config.get('tracing', {}).get('output_dir', 'traces')
            os.makedirs(output_dir, exist_ok=True)
            trace_path = os.path.join(output_dir, f"trace-{os.getpid()}-{int(time.time())}.zip")
            await self.context.tracing.stop(path=trace_path)
            logger.info(f"Trace file saved to {trace_path}")

        try:
            if self._page: await self._page.close()
            if self.context: await self.context.close()
            if self.browser: await self.browser.close()
            if self.playwright: await self.playwright.stop()
        except PlaywrightError as e:
            logger.warning(f"Error during browser closure: {e}")

        logger.info("Browser and playwright instance closed.")

    async def quit(self):
        """Alias for close_browser."""
        await self.close_browser()

    async def navigate(self, url, timeout=30000, wait_state="load"):
        """Navigates to a URL, automatically waiting for the page to reach a specified load state."""
        action_name = f"Navigation to {url}"
        try:
            await self.page.goto(url, timeout=timeout)
            logger.info(action_name)
            await self.wait_for_load_state(state=wait_state, timeout=timeout)
        except (PlaywrightTimeoutError, PlaywrightError, Exception) as e:
            await self._client_capture_failure(self.page, action_name, e)
            logger.error(f"{action_name} failed: {e}")
            raise

    async def take_screenshot(self, path):
        """Takes a basic screenshot of the current page."""
        try:
            await self.page.screenshot(path=path)
            logger.info(f"Screenshot saved to: {path}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")

    async def save_authentication_state(self, path="auth_state.json"):
        """Saves the current authentication state (cookies, local storage, etc.) to a file."""
        if self.context:
            await self.context.storage_state(path=path)
            logger.info(f"Authentication state saved to {path}")
        else:
            logger.warning("Cannot save authentication state: Browser context is not available.")

    def get_locator(self, selector):
        """Returns a generic locator for a given CSS/XPath selector."""
        return self.page.locator(selector)

    def get_by_text(self, text, **kwargs):
        """Locates an element by its text content."""
        return self.page.get_by_text(text, **kwargs)

    def get_by_role(self, role, name, **kwargs):
        """Locates an element by its accessibility role."""
        return self.page.get_by_role(role, name=name, **kwargs)

    def get_by_label(self, label, **kwargs):
        """Locates an element by its associated label."""
        return self.page.get_by_label(label, **kwargs)

    def get_by_placeholder(self, placeholder, **kwargs):
        """Locates an input element by its placeholder text."""
        return self.page.get_by_placeholder(placeholder, **kwargs)

    def get_by_title(self, title, **kwargs):
        """Locates an element by its title attribute."""
        return self.page.get_by_title(title, **kwargs)

    def get_by_test_id(self, test_id, **kwargs):
        """Locates an element by its data-testid attribute."""
        return self.page.get_by_test_id(test_id, **kwargs)

    async def click(self, locator: Locator):
        """Performs a click action on a locator."""
        try:
            await locator.click()
            logger.info(f"Clicked on element with locator.")
        except PlaywrightError as e:
            logger.error(f"Failed to click on element: {e}")
            raise

    async def fill_and_submit(self, locator: Locator, text):
        """Fills a form field and submits by pressing Enter."""
        await locator.fill(text)
        await locator.press("Enter")
        logger.info(f"Filled text and submitted form for locator.")

    async def type_text(self, locator: Locator, text, clear_first=True):
        """Types text into a field. Can optionally clear the field first."""
        if clear_first:
            await locator.clear()
        await locator.type(text)
        logger.info(f"Typed '{text}' into element.")

    async def upload_file(self, locator: Locator, file_path):
        """Uploads a file to a file input field."""
        await locator.set_input_files(file_path)
        logger.info(f"Uploaded file '{file_path}' to locator.")

    async def drag_and_drop(self, source_locator: Locator, target_locator: Locator):
        """Performs a drag-and-drop action."""
        await source_locator.drag_to(target_locator)
        logger.info(f"Dragged element from source to target locator.")

    async def wait_for_selector(self, selector, state="visible", timeout=10000):
        """
        Waits for an element matching the selector to satisfy a state condition.
        States: 'attached', 'detached', 'visible', 'hidden'.
        """
        action_name = f"Wait for selector '{selector}' to be '{state}'"
        try:
            await self.page.wait_for_selector(selector, state=state, timeout=timeout)
            logger.info(action_name)
        except PlaywrightTimeoutError as e:
            await self._client_capture_failure(self.page, action_name, e)
            logger.error(f"{action_name} failed: {e}")
            raise

    async def wait_for_load_state(self, state="load", timeout=30000):
        """
        Waits until the page reaches a certain load state.
        States: 'load', 'domcontentloaded', 'networkidle'.
        """
        action_name = f"Wait for load state '{state}'"
        try:
            await self.page.wait_for_load_state(state=state, timeout=timeout)
            logger.info(action_name)
        except (PlaywrightTimeoutError, PlaywrightError) as e:
            await self._client_capture_failure(self.page, action_name, e)
            logger.error(f"{action_name} failed: {e}")
            raise

    def is_checked(self, locator: Locator):
        """Returns True if a checkbox or radio button is checked."""
        # NOTE: This property access returns an awaitable coroutine in async mode,
        # but in sync mode, it returns the result immediately. Here, it returns a Locator
        # which exposes the async method.
        # This will be replaced by the AWAIT in the WebElement wrapper.
        return locator.is_checked()

    def is_enabled(self, locator: Locator):
        """Returns True if an element is enabled."""
        return locator.is_enabled()

    def is_visible(self, locator: Locator):
        """Returns True if an element is visible."""
        return locator.is_visible()

    def get_attribute(self, locator: Locator, name):
        """Gets the value of an element's attribute."""
        return locator.get_attribute(name)

    async def check_box(self, locator: Locator):
        """Checks a checkbox."""
        await locator.check()
        logger.info(f"Checked element.")

    async def uncheck_box(self, locator: Locator):
        """Unchecks a checkbox."""
        await locator.uncheck()
        logger.info(f"Unchecked element.")

    async def select_option(self, locator: Locator, value):
        """Selects an option in a dropdown or select element."""
        await locator.select_option(value)
        logger.info(f"Selected option with value '{value}' from locator.")

    async def get_new_tab(self, action):
        """
        Performs an action that opens a new tab and returns the new page object.
        """
        async with self.page.context.expect_page() as new_page_event:
            await action()
        return new_page_event.value

    async def close_current_tab(self):
        """Closes the currently active page."""
        await self.page.close()
        logger.info("Closed the current page.")

    def switch_to_tab(self, page_object: Page):
        """Switches the client's active page to a given page object."""
        self._page = page_object
        logger.info("Switched to a new tab.")

    async def get_new_popup(self, action):
        """
        Performs an action that opens a new pop-up window and returns the page object.
        """
        async with self.page.expect_popup() as new_page_info:
            await action()
        return new_page_info.value

    async def assert_visual_equality(self, locator: Locator, name):
        """
        Compares an element's screenshot to a baseline image for visual regression testing.
        """
        await expect(locator).to_have_screenshot(name=name)
        logger.info(f"Visual assertion passed for element: {name}")

    async def assert_page_visual_equality(self, name):
        """
        Compares a full-page screenshot to a baseline image.
        """
        await expect(self.page).to_have_screenshot(name=name)
        logger.info(f"Visual assertion passed for page: {name}")

    async def block_url(self, url_pattern):
        """Blocks requests to a specified URL pattern."""
        self.page.route(url_pattern, lambda route: route.abort())
        logger.info(f"Blocked requests to URL pattern: {url_pattern}")

    async def mock_response(self, url_pattern, body, content_type='application/json'):
        """Mocks a network response with a custom body and content type."""
        self.page.route(url_pattern, lambda route: route.fulfill(
            status=200,
            content_type=content_type,
            body=body
        ))
        logger.info(f"Mocks requests to '{url_pattern}' with a custom response.")

    async def check_visibility(self, locator: Locator, timeout=10000):
        """Asserts that an element is visible within a given timeout."""
        try:
            await expect(locator).to_be_visible(timeout=timeout)
            logger.info("Element is visible as expected.")
        except AssertionError as e:
            logger.error(f"Element is NOT visible: {e}")
            raise

    async def verify_page_url(self, expected_url):
        """Verifies that the current page URL matches the expected URL."""
        await expect(self.page).to_have_url(expected_url)
        logger.info(f"Current URL matches expected URL: {expected_url}")

    async def verify_title_contains(self, text):
        """Verifies that the page title contains the specified text."""
        await expect(self.page).to_have_title(text=text)
        logger.info(f"Page title contains '{text}' as expected.")

