# features/steps/google_search_steps.py

from behave import given, when, then
from pages.GoogleSearchPage import GoogleSearchPage
from clients.PlayWrightClient import PlaywrightClient
from playwright.async_api import expect


@given('the user is on the Google search page')
async def step_user_is_on_google_search_page(context):
    """
    Instantiates PlaywrightClient using the async factory method.
    """
    context.client = await PlaywrightClient.create(application_url="https://www.google.com")
    context.google_page = GoogleSearchPage(context.client)
    context.page = context.client.page


@when('the user searches for "{query}"')
async def step_user_searches_for_query(context, query):
    await context.google_page.search_for(query) # FIX: ADD await


@then('the page title should contain "{expected_title}"')
async def step_page_title_should_contain(context, expected_title):
    await expect(context.googleclient.page).to_have_title(expected_title) # FIX: ADD await


@then('the first search result should contain "{expected_text}"')
async def step_first_search_result_should_contain(context, expected_text):
    first_result_text = await context.google_page.get_first_result_text() # FIX: ADD await
    assert expected_text in first_result_text