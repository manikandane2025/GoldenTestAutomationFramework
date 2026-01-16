import logging
import base64
import time
from playwright.async_api import Page, Locator, expect, TimeoutError as PlaywrightTimeoutError, FrameLocator, Dialog, \
    Error as PlaywrightError
from typing import List, Dict, Any, Union, Callable
from Utility.frameworkDataContext import CustomContext
from enum import Enum
import asyncio

logger = logging.getLogger("TestAutomationLogger")


# --- SELECTOR TYPE ENUM DEFINITION ---
class SelectorType(Enum):
    CSS = "css"
    XPATH = "xpath"
    ID = "id"
    TEXT = "text"


# --- WEB ELEMENT CLASSES ---
class WebElement:

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):

        selector_value = selector_type.value

        if selector_value == SelectorType.XPATH.value:
            locator_string = f"xpath={selector}"
        elif selector_value == SelectorType.ID.value:
            locator_string = f"#{selector}"
        elif selector_value == SelectorType.TEXT.value:
            locator_string = f"text={selector}"
        elif selector_value == SelectorType.CSS.value:
            locator_string = selector
        else:
            locator_string = selector

        self.page = page
        self.selector_raw = selector
        self.selector = locator_string
        self.name = name if name else f"Element ({self.selector})"
        self.locator: Locator = page.locator(self.selector)
        logger.debug(f"Initialized {self.__class__.__name__}: {self.name} with selector: {self.selector}")

    async def _capture_on_failure(self, action: str):
        """Internal method to capture and store a Base64 screenshot on failure."""
        try:
            await asyncio.sleep(0.5)

            screenshot_bytes = await self.page.screenshot(
                type="png",
                full_page=True,
                timeout=5000
            )

            base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')

            contextdata = CustomContext()
            key_name = f"screenshot_{self.name.replace(' ', '_')}_{action.replace(' ', '_')}_{int(time.time())}"

            contextdata.set_user_data(key_name, {
                "mime_type": "image/png",
                "data": base64_screenshot
            })
            logger.info(f"CAPTURED: Screenshot on failure of '{action}' for {self.name}.")

        except Exception as e:
            logger.error(f"FATAL: Failed to capture or store screenshot inside element wrapper: {e}")

    @staticmethod
    async def assert_page_action(page: Page, action_func: Callable, action_name: str):
        """
        Generic wrapper to execute any risky page-level action and capture a screenshot.
        """

        async def _static_capture(page: Page, error_type: str):
            try:
                await asyncio.sleep(0.5)
                screenshot_bytes = await page.screenshot(type="png", full_page=True, timeout=5000)
                base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
                contextdata = CustomContext()

                key_name = f"screenshot_PAGE_{action_name.replace(' ', '_')}_{error_type.replace(' ', '_')}_{int(time.time())}"
                contextdata.set_user_data(key_name, {
                    "mime_type": "image/png",
                    "data": base64_screenshot
                })
                logger.error(f"FATAL: Screenshot captured for unhandled page action: {action_name}")
            except Exception as e:
                logger.error(f"FATAL: Could not capture screenshot for static failure: {e}")

        try:
            if asyncio.iscoroutinefunction(action_func):
                await action_func()
            else:
                action_func()

        except (PlaywrightTimeoutError, PlaywrightError, AssertionError, RuntimeError, Exception) as e:
            await _static_capture(page, e.__class__.__name__)
            # 🌟 FIX: Ensure all captured failures are re-raised as AssertionError for Behave compatibility
            if not isinstance(e, AssertionError):
                raise AssertionError(f"UNEXPECTED ERROR IN ACTION '{action_name}': {e}") from e
            raise e

    # --- CORE ACTION METHODS (ASYNC) --------------------

    async def click(self, log_message: str, timeout: int = 30000):
        """Performs a click action on the element."""
        try:
            await self.locator.click(timeout=timeout)
            logger.info(f"ACTION: Clicked {self.name} - {log_message}")
        except PlaywrightTimeoutError as e:
            await self._capture_on_failure("Click_Timeout")
            # 🌟 FIX: Re-raise as AssertionError
            raise AssertionError(f"FAILURE: Timeout while clicking {self.name}. Selector: {self.selector}: {e}") from e
        except PlaywrightError as e:
            await self._capture_on_failure("Click_Error")
            # 🌟 FIX: Re-raise as AssertionError
            raise AssertionError(f"FAILURE: General error clicking {self.name}: {e}") from e

    async def double_click(self, log_message: str, timeout: int = 30000):
        """Performs a double click action on the element."""
        try:
            await self.locator.dblclick(timeout=timeout)
            logger.info(f"ACTION: Double-clicked {self.name} - {log_message}")
        except PlaywrightTimeoutError as e:
            await self._capture_on_failure("DblClick_Timeout")
            raise AssertionError(f"FAILURE: Timeout while double-clicking {self.name}: {e}") from e
        except PlaywrightError as e:
            await self._capture_on_failure("DblClick_Error")
            raise AssertionError(f"FAILURE: General error double-clicking {self.name}: {e}") from e

    async def hover(self, log_message: str, timeout: int = 30000):
        """Hovers the mouse over the element."""
        try:
            await self.locator.hover(timeout=timeout)
            logger.info(f"ACTION: Hovered over {self.name} - {log_message}")
        except PlaywrightTimeoutError as e:
            await self._capture_on_failure("Hover_Timeout")
            raise AssertionError(f"FAILURE: Timeout while hovering {self.name}: {e}") from e
        except PlaywrightError as e:
            await self._capture_on_failure("Hover_Error")
            raise AssertionError(f"FAILURE: General error hovering {self.name}: {e}") from e

    # --- STATE / QUERY METHODS (ASYNC) ------------------
    # (Query methods do not cause test failures, only return data/warnings)

    async def get_text(self) -> str:
        """Returns the inner text of the element, trimming whitespace."""
        try:
            await self.locator.wait_for(state="visible", timeout=5000)
            text = await self.locator.text_content()
            text = text.strip() if text is not None else ""
            logger.debug(f"QUERY: Retrieved text from {self.name}: '{text}'")
            return text
        except PlaywrightError as e:
            logger.warning(f"QUERY ERROR: Could not retrieve text from {self.name}. {e}")
            return ""

    async def get_attribute(self, attr_name: str) -> str:
        """Returns the value of a specified attribute."""
        try:
            value = await self.locator.get_attribute(attr_name, timeout=5000)
            logger.debug(f"QUERY: Retrieved attribute '{attr_name}' from {self.name}: '{value}'")
            return value if value is not None else ""
        except PlaywrightError as e:
            logger.warning(f"QUERY ERROR: Could not retrieve attribute '{attr_name}' from {self.name}. {e}")
            return ""

    async def is_visible(self, log_message: str, timeout: int = 10000) -> bool:
        """Checks if the element is visible on the page (Soft assertion/Query)."""
        is_visible = await self.locator.is_visible(timeout=timeout)
        logger.info(f"QUERY: {self.name} - Visibility check ({log_message}) - Result: {is_visible}")
        return is_visible

    async def is_enabled(self, log_message: str, timeout: int = 10000) -> bool:
        """Checks if the element is enabled (Soft assertion/Query)."""
        is_enabled = await self.locator.is_enabled(timeout=timeout)
        logger.info(f"QUERY: {self.name} - Enabled check ({log_message}) - Result: {is_enabled}")
        return is_enabled

    # --- HARD ASSERTIONS (ASYNC) ------------------------

    async def assert_is_visible(self, log_message: str, timeout: int = 10000):
        """Asserts that the element is visible, reliably catching the failure for screenshot."""
        try:
            await self.locator.wait_for(state="visible", timeout=timeout)
            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Is Visible in {timeout / 1000}s).")
        except PlaywrightTimeoutError as e:
            await self._capture_on_failure("Assert_Visible_Timeout")
            logger.error(f"ASSERT FAILED: Element {self.name} was not visible within {timeout / 1000}s.")
            # 🌟 FIX: Re-raise as AssertionError
            raise AssertionError(f"Element {self.name} not visible: {e}") from e

    async def assert_is_enabled(self, log_message: str, timeout: int = 10000):
        """
        Asserts that the element is enabled (not disabled).
        """
        try:
            await self.locator.wait_for(timeout=timeout)

            if not await self.locator.is_enabled(timeout=100):
                # Raise an error that is converted to AssertionError below
                raise PlaywrightTimeoutError(f"Element failed to become enabled within {timeout / 1000}s.")

            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Is Enabled).")

        except PlaywrightTimeoutError as e:
            await self._capture_on_failure("Assert_Enabled_Timeout")
            logger.error(f"ASSERT FAILED: Element {self.name} is NOT enabled.")
            # 🌟 FIX: Re-raise as AssertionError
            raise AssertionError(f"Element {self.name} not enabled: {e}") from e

        except AssertionError as e:
            await self._capture_on_failure("Assert_Enabled_Failed")
            raise e

    async def assert_is_not_visible(self, log_message: str, timeout: int = 10000):
        """Asserts that the element is hidden or not present."""
        try:
            await expect(self.locator).to_be_hidden(timeout=timeout)
            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Is Hidden/Detached).")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Hidden_Failed")
            raise e

    async def assert_has_text(self, expected_text: str, log_message: str, ignore_case: bool = False):
        """Asserts that the element contains the expected text."""
        try:
            await expect(self.locator).to_contain_text(expected_text, ignore_case=ignore_case)
            logger.info(f"ASSERT: {self.name} - {log_message} - Expected text: '{expected_text}'. Passed.")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Text_Failed")
            raise e

    async def assert_matches_regex(self, pattern: str, log_message: str):
        """Asserts that the element's text matches a regular expression."""
        try:
            await expect(self.locator).to_match_text(pattern)
            logger.info(f"ASSERT: {self.name} - {log_message} - Matches pattern '{pattern}'. Passed.")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Regex_Failed")
            raise e


class TextBox(WebElement):
    """Specialized class for <input type='text'> and <textarea>."""

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, selector, name, selector_type)

    async def fill(self, text: str, log_message: str, clear_first: bool = True, timeout: int = 30000):
        """Fills the input field with text."""
        try:
            if clear_first:
                await self.locator.clear()
            await self.locator.fill(text, timeout=timeout)
            logger.info(f"ACTION: {self.name} - {log_message}: Entered '{text}'")
        except PlaywrightTimeoutError as e:
            await self._capture_on_failure("Fill_Timeout")
            raise AssertionError(f"FAILURE: Timeout while filling {self.name}: {e}") from e
        except PlaywrightError as e:
            await self._capture_on_failure("Fill_Error")
            raise AssertionError(f"FAILURE: General error filling {self.name}: {e}") from e

    async def press_key(self, key: str, log_message: str):
        """Presses a specific keyboard key (e.g., 'Enter', 'Tab', 'ArrowDown')."""
        try:
            await self.locator.press(key)
            logger.info(f"ACTION: {self.name} - {log_message}: Pressed key '{key}'")
        except PlaywrightError as e:
            await self._capture_on_failure(f"PressKey_{key}_Error")
            raise AssertionError(f"FAILURE: Error pressing key {key} on {self.name}: {e}") from e


class Button(WebElement):
    """Specialized class for <button> and <input type='submit/button'> elements."""

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, selector, name, selector_type)

    async def submit(self, log_message: str, timeout: int = 30000):
        """Performs a click action, typically used for form submission buttons."""
        await self.click(f"Submit action - {log_message}", timeout)
        logger.info(f"ACTION: Submitted form via {self.name}")

    async def force_click(self, log_message: str, timeout: int = 30000):
        """
        Forces a click action, ignoring element state (like obscured by another element).
        """
        try:
            await self.locator.click(force=True, timeout=timeout)
            logger.info(f"ACTION: Force-clicked {self.name} - {log_message}")
        except PlaywrightTimeoutError as e:
            await self._capture_on_failure("ForceClick_Timeout")
            raise AssertionError(f"FAILURE: Timeout while force-clicking {self.name}: {e}") from e
        except PlaywrightError as e:
            await self._capture_on_failure("ForceClick_Error")
            raise AssertionError(f"FAILURE: General error force-clicking {self.name}: {e}") from e

    async def assert_is_disabled(self, log_message: str, timeout: int = 10000):
        """Asserts that the button is currently disabled."""
        try:
            await expect(self.locator).to_be_disabled(timeout=timeout)
            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Is Disabled).")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Disabled_Failed")
            raise e


class Link(WebElement):
    """Specialized class for anchor tags (<a>) and navigation elements."""

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, selector, name, selector_type)

    async def get_href(self) -> str:
        """Returns the href attribute of the link."""
        href = await self.get_attribute('href')
        logger.debug(f"QUERY: Retrieved href from {self.name}: '{href}'")
        return href

    async def assert_href_matches(self, expected_value: str, log_message: str):
        """Asserts that the link's href attribute matches the expected value."""
        try:
            await expect(self.locator).to_have_attribute('href', expected_value)
            logger.info(f"ASSERT: {self.name} - {log_message} - Href is '{expected_value}'. Passed.")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Href_Failed")
            raise e


class CheckBox(WebElement):
    """Specialized class for <input type='checkbox'>."""

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, selector, name, selector_type)

    async def check(self, log_message: str):
        """Checks the checkbox (if not already checked)."""
        try:
            await self.locator.check()
            logger.info(f"ACTION: Checked {self.name} - {log_message}")
        except PlaywrightError as e:
            await self._capture_on_failure("Check_Error")
            raise AssertionError(f"FAILURE: Error checking checkbox {self.name}: {e}") from e

    async def uncheck(self, log_message: str):
        """Unchecks the checkbox (if not already unchecked)."""
        try:
            await self.locator.uncheck()
            logger.info(f"ACTION: Unchecked {self.name} - {log_message}")
        except PlaywrightError as e:
            await self._capture_on_failure("Uncheck_Error")
            raise AssertionError(f"FAILURE: Error unchecking checkbox {self.name}: {e}") from e

    async def assert_is_checked(self, log_message: str):
        """Asserts that the checkbox is checked."""
        try:
            await expect(self.locator).to_be_checked()
            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Is Checked).")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Checked_Failed")
            raise e

    async def assert_is_unchecked(self, log_message: str):
        """Asserts that the checkbox is unchecked."""
        try:
            await expect(self.locator).not_to_be_checked()
            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Is Unchecked).")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Unchecked_Failed")
            raise e


class RadioButton(WebElement):
    """Specialized class for <input type='radio'>."""

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, selector, name, selector_type)

    async def select(self, log_message: str):
        """Selects the radio button."""
        try:
            await self.locator.check()
            logger.info(f"ACTION: Selected Radio Button {self.name} - {log_message}")
        except PlaywrightError as e:
            await self._capture_on_failure("Select_Radio_Error")
            raise AssertionError(f"FAILURE: Error selecting radio button {self.name}: {e}") from e

    async def assert_is_selected(self, log_message: str):
        """Asserts that the radio button is selected."""
        try:
            await expect(self.locator).to_be_checked()
            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Is Selected).")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Selected_Radio_Failed")
            raise e

    async def assert_is_not_selected(self, log_message: str):
        """Asserts that the radio button is not selected."""
        try:
            await expect(self.locator).not_to_be_checked()
            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Is Not Selected).")
        except AssertionError as e:
            await self._capture_on_failure("Assert_NotSelected_Radio_Failed")
            raise e


class Dropdown(WebElement):
    """Specialized class for <select> elements."""

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, selector, name, selector_type)

    async def select_by_value(self, value: str, log_message: str):
        """Selects an option based on its 'value' attribute."""
        try:
            await self.locator.select_option(value=value)
            logger.info(f"ACTION: {self.name} - {log_message}: Selected by value '{value}'")
        except PlaywrightError as e:
            await self._capture_on_failure("Select_Value_Error")
            raise AssertionError(f"FAILURE: Error selecting value {value} from {self.name}: {e}") from e

    async def select_by_label(self, label: str, log_message: str):
        """Selects an option based on its visible text/label."""
        try:
            await self.locator.select_option(label=label)
            logger.info(f"ACTION: {self.name} - {log_message}: Selected by label '{label}'")
        except PlaywrightError as e:
            await self._capture_on_failure("Select_Label_Error")
            raise AssertionError(f"FAILURE: Error selecting label {label} from {self.name}: {e}") from e

    async def assert_selected_value(self, expected_value: str, log_message: str):
        """Asserts that the current selected option matches the expected value attribute."""
        try:
            await expect(self.locator).to_have_value(expected_value)
            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Selected value is '{expected_value}').")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Selected_Value_Failed")
            raise e


class FileInput(WebElement):
    """Specialized class for <input type='file'> elements."""

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, selector, name, selector_type)

    async def upload_file(self, file_path: str, log_message: str):
        """Uploads a single file to the input field."""
        try:
            await self.locator.set_input_files(file_path)
            logger.info(f"ACTION: {self.name} - {log_message}: Uploaded single file '{file_path}'")
        except PlaywrightError as e:
            await self._capture_on_failure("Upload_Single_Error")
            raise AssertionError(f"FAILURE: Error uploading file {file_path} to {self.name}: {e}") from e

    async def upload_multiple_files(self, file_paths: list[str], log_message: str):
        """Uploads multiple files to the input field."""
        try:
            await self.locator.set_input_files(file_paths)
            logger.info(f"ACTION: {self.name} - {log_message}: Uploaded {len(file_paths)} files: {file_paths}")
        except PlaywrightError as e:
            await self._capture_on_failure("Upload_Multiple_Error")
            raise AssertionError(f"FAILURE: Error uploading multiple files to {self.name}: {e}") from e


class Table(WebElement):
    """Specialized class for complex <table> elements, providing data access helpers."""

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, selector, name, selector_type)

    async def get_cell_text(self, row_index: int, col_index: int) -> str:
        """
        Retrieves the text from a specific cell (0-indexed).
        """
        try:
            cell_locator = self.locator.locator("tbody tr").nth(row_index).locator("td,th").nth(col_index)
            text = await cell_locator.text_content()
            result = text.strip() if text is not None else ""
            logger.debug(f"QUERY: Retrieved cell text at [{row_index}, {col_index}] in {self.name}: '{result}'")
            return result
        except PlaywrightError as e:
            logger.warning(
                f"QUERY ERROR: Could not retrieve cell text from {self.name} at [{row_index}, {col_index}]. {e}")
            return ""

    async def get_row_count(self) -> int:
        """Returns the number of rows in the table body (excluding header)."""
        count = await self.locator.locator("tbody tr").count()
        logger.debug(f"QUERY: Retrieved row count from {self.name}: {count}")
        return count

    async def find_row_by_text(self, text_content: str) -> Locator:
        """
        Returns the Locator for the first row containing the given text.
        """
        row_locator = self.locator.locator(f"tr:has-text('{text_content}')").first
        try:
            await expect(row_locator).to_be_visible()
            logger.info(f"QUERY: Found row containing text '{text_content}' in {self.name}")
            return row_locator
        except AssertionError as e:
            await self._capture_on_failure("Find_Row_Failed")
            raise e


class FrameElement:
    """
    Wrapper for interacting with IFRAMEs and their internal content.
    """

    def __init__(self, page: Page, selector: str, name: str = None, selector_type: SelectorType = SelectorType.CSS):

        selector_value = selector_type.value
        if selector_value == SelectorType.XPATH.value:
            locator_string = f"xpath={selector}"
        else:
            locator_string = selector

        self.page = page
        self.selector = locator_string
        self.name = name if name else f"IFrame ({self.selector})"
        self.frame_locator: FrameLocator = page.frame_locator(self.selector)
        logger.debug(f"Initialized Frame: {self.name} with selector: {self.selector}")

    def get_element_inside(self, child_selector: str, child_name: str,
                           child_selector_type: SelectorType = SelectorType.CSS) -> WebElement:
        """
        Retrieves a generic WebElement wrapper for an element *inside* this frame.
        """
        child_element_proxy = WebElement(self.page, child_selector, child_name, child_selector_type)

        child_element_proxy.locator = self.frame_locator.locator(child_element_proxy.selector)

        logger.debug(
            f"QUERY: Mapped element '{child_name}' inside frame '{self.name}' (Selector: {child_element_proxy.selector})")
        return child_element_proxy

    async def assert_frame_contains_text(self, text: str, log_message: str):
        """Asserts that the entire frame content contains the specified text."""
        try:
            await expect(self.frame_locator.locator("body")).to_contain_text(text)
            logger.info(f"ASSERT: {self.name} - {log_message} - Contains text '{text}'. Passed.")
        except AssertionError as e:
            await WebElement.assert_page_action(self.page,
                                                lambda: expect(self.frame_locator.locator("body")).to_contain_text(
                                                    text), "Assert_Frame_Text")
            raise e


class WebComponent(WebElement):
    """
    Wrapper for interacting with custom elements using the Shadow DOM.
    """

    def __init__(self, page: Page, host_selector: str, name: str = None,
                 selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, host_selector, name, selector_type)
        self.host_locator: Locator = self.locator

    def get_shadow_element(self, inner_selector: str, inner_name: str,
                           inner_selector_type: SelectorType = SelectorType.CSS) -> WebElement:
        """
        Retrieves a WebElement wrapper for an element located inside the Shadow Root.
        """
        element_proxy = WebElement(self.page, inner_selector, inner_name, inner_selector_type)

        element_proxy.locator = self.host_locator.locator(element_proxy.selector)

        logger.debug(
            f"QUERY: Mapped Shadow Element '{inner_name}' inside component '{self.name}' (Inner Selector: {element_proxy.selector})")
        return element_proxy


class Modal(WebElement):
    """
    Specialized class for interacting with transient, overlaid dialogs/modals.
    """

    def __init__(self, page: Page, selector: str, name: str = "Modal/Dialog",
                 selector_type: SelectorType = SelectorType.CSS):
        super().__init__(page, selector, name, selector_type)
        logger.debug(f"Modal initialized with name: {self.name}")

    async def assert_is_open(self, log_message: str):
        """Asserts that the modal is currently visible and focused."""
        try:
            await self.assert_is_visible(log_message)
            await expect(self.locator).to_have_attribute('role', 'dialog', timeout=5000)
            logger.info(f"ASSERT: {self.name} - {log_message} - Passed (Modal is Open).")
        except AssertionError as e:
            await self._capture_on_failure("Assert_Modal_Open_Failed")
            raise e

    async def close_by_escape(self, log_message: str):
        """Simulates pressing the ESC key to close the modal."""
        try:
            await self.page.keyboard.press("Escape")
            await self.assert_is_not_visible(f"Verifying modal closed after ESC - {log_message}")
            logger.info(f"ACTION: Closed {self.name} via Escape key.")
        except PlaywrightError as e:
            await self._capture_on_failure("Close_Modal_Error")
            raise AssertionError(f"FAILURE: Error closing modal {self.name} via ESC key: {e}") from e

    def get_title_element(self, title_selector: str = 'h2, [role="heading"]',
                          title_selector_type: SelectorType = SelectorType.CSS) -> WebElement:
        """Returns the WebElement for the title inside the modal."""
        title_element = WebElement(self.page, title_selector, f"{self.name} Title", title_selector_type)

        title_element.locator = self.locator.locator(title_element.selector)

        logger.debug(f"QUERY: Retrieved title element from {self.name}")
        return title_element


class BrowserAlert:
    """
    Handles native browser Alert, Confirm, and Prompt dialogs (non-HTML).
    """

    def __init__(self, page: Page):
        self.page = page
        self.dialog: Union[Dialog, None] = None
        self.contextdata = CustomContext()

        self.page.on("dialog", lambda dialog: self._handle_dialog(dialog))
        logger.debug("BrowserAlert listener initialized.")

    async def _capture_dialog_failure(self, action: str, dialog_type: str):
        """Internal method to capture and log screenshot on dialog failure."""
        try:
            await asyncio.sleep(0.5)
            screenshot_bytes = await self.page.screenshot(type="png", full_page=True, timeout=5000)
            base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')

            key_name = "screenshot"
            self.contextdata.set_user_data(key_name, {
                "mime_type": "image/png",
                "data": base64_screenshot
            })
            logger.info(f"CAPTURED: Screenshot on dialog failure: {action}.")
        except Exception as e:
            logger.error(f"FATAL: Failed to capture dialog screenshot: {e}")

    def _handle_dialog(self, dialog: Dialog):
        """Internal listener function to capture the active dialog."""
        self.dialog = dialog
        logger.info(f"ALERT: Dialog type '{dialog.type}' captured with message: '{dialog.message}'")

    async def accept_alert(self, log_message: str, timeout: int = 5000):
        """Accepts (clicks OK on) the current alert or confirmation dialog."""
        try:
            if not self.dialog:
                self.dialog = await self.page.wait_for_event("dialog", timeout=timeout)

            if self.dialog.type in ['alert', 'confirm', 'prompt']:
                await self.dialog.accept()
                logger.info(f"ACTION: Accepted browser dialog type '{self.dialog.type}' - {log_message}")
                self.dialog = None
            else:
                raise RuntimeError(f"No alert/confirm dialog found to accept. Found type: {self.dialog.type}")
        except PlaywrightTimeoutError as e:
            await self._capture_dialog_failure("Accept_Timeout", "Unknown")
            raise AssertionError(f"FAILURE: Timeout while waiting for dialog to appear: {e}") from e
        except RuntimeError as e:
            await self._capture_dialog_failure("Accept_Error", self.dialog.type if self.dialog else "Unknown")
            raise AssertionError(f"FAILURE: Runtime error accepting dialog: {e}") from e

    async def dismiss_alert(self, log_message: str, timeout: int = 5000):
        """Dismisses (clicks Cancel on) the current confirmation or prompt dialog."""
        try:
            if not self.dialog:
                self.dialog = await self.page.wait_for_event("dialog", timeout=timeout)

            if self.dialog.type in ['confirm', 'prompt']:
                await self.dialog.dismiss()
                logger.info(f"ACTION: Dismissed browser dialog type '{self.dialog.type}' - {log_message}")
                self.dialog = None
            else:
                raise RuntimeError(f"No confirm/prompt dialog found to dismiss. Found type: {self.dialog.type}")
        except PlaywrightTimeoutError as e:
            await self._capture_dialog_failure("Dismiss_Timeout", "Unknown")
            raise AssertionError(f"FAILURE: Timeout while waiting for dialog to appear: {e}") from e
        except RuntimeError as e:
            await self._capture_dialog_failure("Dismiss_Error", self.dialog.type if self.dialog else "Unknown")
            raise AssertionError(f"FAILURE: Runtime error dismissing dialog: {e}") from e

    async def assert_dialog_message(self, expected_message: str, log_message: str, timeout: int = 5000):
        """Asserts the text of the pending dialog message."""
        try:
            if not self.dialog:
                self.dialog = await self.page.wait_for_event("dialog", timeout=timeout)

            actual_message = self.dialog.message
            if actual_message != expected_message:
                raise AssertionError(
                    f"ASSERT FAILED: {log_message}. Expected: '{expected_message}', Actual: '{actual_message}'")
            logger.info(f"ASSERT: Dialog message verified - {log_message}")
            return True
        except PlaywrightTimeoutError as e:
            await self._capture_dialog_failure("Assert_Timeout", "Unknown")
            raise AssertionError(f"FAILURE: Timeout while waiting for dialog to assert message: {e}") from e
        except AssertionError as e:
            await self._capture_dialog_failure("Assert_Message", self.dialog.type if self.dialog else "Unknown")
            raise
        except Exception as e:
            await self._capture_dialog_failure("Assert_Unexpected", self.dialog.type if self.dialog else "Unknown")
            raise AssertionError(f"FAILURE: Unexpected error during dialog message assertion: {e}") from e