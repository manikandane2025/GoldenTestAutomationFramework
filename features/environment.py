import base64
import time
from collections.abc import Iterable
from behave.api.async_step import async_run_until_complete
from playwright.async_api import Page, async_playwright
from Utility.frameworkDataContext import CustomContext
from constants import SCENARIO_MAX_RETRIES, SCENARIO_RETRY_DELAY


# Fix: Make before_all async and use the decorator
@async_run_until_complete
async def before_all(context):
    print("async before_all hook starting")
    # Optional: Start Playwright if you need a shared instance
    context.playwright = await async_playwright().start()


def _get_all_clients(context):
    """Find all PlaywrightClient instances in the context."""
    clients_found = set()

    for attr_value in vars(context).values():
        if attr_value.__class__.__name__ == 'PlaywrightClient':
            clients_found.add(attr_value)
        elif hasattr(attr_value, 'client') and attr_value.client.__class__.__name__ == 'PlaywrightClient':
            clients_found.add(attr_value.client)
        elif isinstance(attr_value, (list, tuple, set)):
            for item in attr_value:
                if item.__class__.__name__ == 'PlaywrightClient':
                    clients_found.add(item)
                elif isinstance(item, dict):
                    for value in item.values():
                        if value.__class__.__name__ == 'PlaywrightClient':
                            clients_found.add(value)

    return list(clients_found)


# You can leave this sync if it doesn't use async functions
def after_step(context, step):
    context.user_data = {
        "step_name": step.name,
        "status": step.status,
        "error_message": step.error_message if step.status == "failed" else "",
    }

    print(f"User data before step: {context.user_data}")

    if step.status == "failed":
        active_page = None

        if hasattr(context, 'client') and hasattr(context.client, 'page'):
            active_page = context.client.page
        elif hasattr(context, 'page') and isinstance(context.page, Page):
            active_page = context.page

        if active_page:
            print("INFO: Found active Playwright Page object for screenshot.")
            try:
                # ⚠️ NOTE: If using Playwright async, you cannot use sync code here
                # So make sure this function is eventually converted to async if needed

                # Schedule a coroutine to run screenshot (see note)
                # Bad workaround: run loop here (not ideal inside hooks)
                import asyncio
                loop = asyncio.get_event_loop()
                screenshot_bytes = loop.run_until_complete(
                    active_page.screenshot(
                        type="png",
                        full_page=True,
                        timeout=5000
                    )
                )

                base64_screenshot = base64.b64encode(screenshot_bytes).decode('utf-8')
                contextdata = CustomContext()
                contextdata.set_user_data("screenshot", {
                    "mime_type": "image/png",
                    "data": base64_screenshot
                })

                print("Screenshot captured and saved to CustomContext.")

            except Exception as e:
                print(f"ERROR: Failed to capture/store screenshot: {e}")
        else:
            print("WARNING: No Playwright Page found for screenshot.")
    CustomContext().reset_step_data()
    return context



MAX_RETRIES = SCENARIO_MAX_RETRIES
RETRY_DELAY = SCENARIO_RETRY_DELAY


# Optionally retry failed scenarios (currently disabled)
def retry_scenario(context, scenario, retries=MAX_RETRIES, delay=RETRY_DELAY):
    pass


# Safely close all browser clients after each scenario
@async_run_until_complete
async def after_scenario(context, scenario):
    if scenario.status == 'failed':
        print(f"Scenario '{scenario.name}' failed...")

    clients_to_close = _get_all_clients(context)
    closed_client_ids = set()
    captured_count = 0

    for client in clients_to_close:
        client_id = id(client)
        if client_id in closed_client_ids:
            continue
        try:
            await client.close_browser()
            closed_client_ids.add(client_id)
            captured_count += 1
            print(f"Closed Playwright client.")
        except Exception as e:
            print(f"WARNING: Failed to close PlaywrightClient: {e}")

    if captured_count == 0:
        print("WARNING: No PlaywrightClient instances were found and closed.")

    # Optional: Stop Playwright globally if started in before_all
    if hasattr(context, "playwright"):
        await context.playwright.stop()
        print("Playwright stopped.")


def after_feature(context, feature):
    CustomContext().reset_feature_data()
