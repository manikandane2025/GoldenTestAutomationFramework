# features/steps/swaplabs_steps.py
import asyncio
import base64

from behave import given, when, then

from Utility.frameworkDataContext import CustomContext
from pages.GoogleSearchPage import GoogleSearchPage
from pages.swagapi import SwagLabsLoginPage
from clients.PlayWrightClient import PlaywrightClient
from clients.WebElements import WebElement
from playwright.async_api import expect
import logging

logger = logging.getLogger("TestAutomationLogger")


@given('a new Playwright client is initialized for Swag Labs')
async def step_client_init(context):
    """
    Initializes multiple Playwright clients for parallel application testing (ASYNC mode).
    """
    # 1. Initialize Client A (Swag Labs) - AWAIT factory method
    context.client = await PlaywrightClient.create(application_url="https://www.saucedemo.com/")

    # 2. Initialize Client B (Google) - AWAIT factory method
    context.googleclient = await PlaywrightClient.create(application_url="https://www.google.com/")

    # 3. Instantiate Page Objects (Synchronous)
    context.login_page = SwagLabsLoginPage(context.client)
    context.googlepage = GoogleSearchPage(context.googleclient)

    # 4. Expose Pages (Synchronous)
    context.page = context.client.page

    logger.info("Successfully initialized multiple Playwright clients.")


@when('the user logs in with a valid standard username and password')
async def step_login_valid(context):
    """Logs in using the valid standard credentials."""
    await context.login_page.login("standard_user", "secret_sauce") # FIX: ADD await



@when('the user attempts to log in with an invalid username and password')
async def step_login_invalid(context):
    """Attempts login with known invalid credentials."""
    await context.login_page.login("locked_out_user", "bad_password") # FIX: ADD await


@then('the user should be on the inventory page')
async def step_on_inventory_page(context):
    """Asserts that the URL matches the expected inventory page URL."""
    await context.login_page.assert_inventory_page_loaded() # FIX: ADD await
    logger.info("ASSERT: User is on the Inventory Page.")


@then('the page title should contain "{expected_title}" for swaplabs')
async def step_page_title_contains(context, expected_title):
    """Asserts that the page title contains the expected text."""

    async def title_check():
        await context.login_page.assert_loginpage_title_contains(expected_title)

    # Await the static utility wrapper
    await WebElement.assert_page_action(
        page=context.client.page,
        action_func=title_check,
        action_name="Verify_Title_Contains"
    )
    logger.info(f"ASSERT: Page title contains '{expected_title}'.")


@then('the login error message should be visible on the page')
async def step_error_message_visible(context):
    """Asserts that the login error message element is visible."""
    await context.login_page.assert_error_message_is_visible() # FIX: ADD await
    logger.info("ASSERT: Login error message is visible.")