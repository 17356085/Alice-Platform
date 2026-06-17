"""
conftest.py for tank module.
Provides module-level driver fixture and page object fixtures.
"""
import pytest
import allure
import logging
from base.browser_driver import BaseDriver
from page.tank_page.AlarmConfigPage import AlarmConfigPage
from base.cleanup_tracker import get_cleanup_tracker

logger = logging.getLogger(__name__)


@pytest.fixture(scope="module")
def driver_setup():
    """
    Module-scoped fixture for browser setup.
    - Opens a browser instance.
    - Ensures user is logged in.
    - Initializes the page object and navigates to the base path.
    Yields:
        tuple: (driver, page_object)
    """
    base_driver = BaseDriver()
    driver = base_driver.open_browser()
    base_driver.ensure_logged_in()
    # Initialize the primary page object for the module
    alarm_config_page = AlarmConfigPage(driver)
    alarm_config_page.navigate()
    yield driver, alarm_config_page

    # --- Teardown: Cleanup any test data created ---
    try:
        tracker = get_cleanup_tracker()
        tracker.clean_all()
        logger.info("Cleanup tracker executed successfully.")
    except Exception as e:
        # Cleanup failure should not fail the test suite, only warn
        logger.warning(f"Cleanup tracker encountered an issue: {e}")

    # Close the browser
    driver.quit()


@pytest.fixture(scope="module")
def alarm_config_page(driver_setup):
    """
    Fixture that provides the AlarmConfigPage object.
    The page is already navigated to its base URL.
    """
    _, page = driver_setup
    return page


@pytest.fixture(scope="module")
def driver(driver_setup):
    """Returns only the Selenium WebDriver instance."""
    driver_instance, _ = driver_setup
    return driver_instance