"""
Optimized Boat Cost Calculator using Selenium
- Much faster processing with headless mode and explicit waits
- Better error handling and retry logic
- Structured logging for easier debugging
- Processes multiple Excel files with threading
- Consolidated output in single run
"""

import time
import uuid
import logging
import threading
from queue import Queue
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager
import sys
import os
import csv
import glob
import argparse
import tempfile
from functools import wraps

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    StaleElementReferenceException,
    WebDriverException
)

import openpyxl
import requests
import json

# ==================== CONFIGURATION ====================

# Selenium Credentials
USERNAME = "svc_selenium"
PASSWORD = "auFLh*y0!aDNQ8"

# Infor API Settings
CLIENT_ID = "QA2FNBZCKUAUH7QB_PRD~nZuRG_bQdloMcPeh1fks-TL4nRgxhLWeO-eoIjhISJo"
CLIENT_SECRET = "4O7OIZ64sukP1N6YeGZ6IpzsFTG4T6RFkcTZgq6ZwAetb4VoNOOJ1qMkGQAlvnOqqcgaZDlXKux6YEQNvoZQgg"
TOKEN_ENDPOINT = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/as/token.oauth2"
SERVICE_ACCOUNT_ACCESS_KEY = "QA2FNBZCKUAUH7QB_PRD#-Qs95wmGj_zOYBT3pIxsTDEwM6sJ1_jQQafabeA4NGK9xuXKp_iYp49_M7JuB7UaEo0xjWDqTAE1Q15rQhxojw"
SERVICE_ACCOUNT_SECRET_KEY = "IZq8wArFnHi4rESTZ-3SQT5zMgiCQfre8aLM6KirsVmvBhXmGDZS_4TXvCZlD40AjpXX6igL7y8A3svCHV-glg"
COMPANY_WORKSPACE_NAME = "QA2FNBZCKUAUH7QB_PRD"
OPTION_LIST_ID = "bb38d84e-6493-40c7-b282-9cb9c0df26ae"
MODEL_LIST_ENDPOINT = f"https://mingle-ionapi.inforcloudsuite.com/{COMPANY_WORKSPACE_NAME}/CPQ/DataImport/{COMPANY_WORKSPACE_NAME}/v1/OptionLists/{OPTION_LIST_ID}/values"
DATA_IMPORT_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_PRD/CPQ/DataImport"

# URLs
LOGIN_URL = "https://mingle-portal.inforcloudsuite.com/v2/QA2FNBZCKUAUH7QB_PRD/1269022f-5216-4abd-938e-f4f130aa19ed?favoriteContext=/&LogicalId=lid://infor.cpqwb.cpqwb"
SIMULATOR_URL = "https://mingle-portal.inforcloudsuite.com/v2/QA2FNBZCKUAUH7QB_PRD/1269022f-5216-4abd-938e-f4f130aa19ed?favoriteContext=/configurator-simulator&LogicalId=lid://infor.cpqwb.cpqwb"

# Timeouts (in seconds)
DEFAULT_TIMEOUT = 15
LONG_TIMEOUT = 30
SHORT_TIMEOUT = 5

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2

# API request timeout
REQUEST_TIMEOUT = 60

# ==================== API TOKEN MANAGEMENT ====================

class TokenManager:
    """Thread-safe token management with automatic refresh"""
    def __init__(self):
        self.token = None
        self.expires_at = 0
        self.lock = threading.Lock()
        self.session = None

    def initialize_session(self):
        """Initialize requests session"""
        if not self.session:
            self.session = requests.Session()
            self.session.verify = False
        return self.session

    def get_token(self) -> str:
        """Get a valid token, refreshing if necessary"""
        with self.lock:
            # Check if current token is still valid (with 5 minute buffer)
            if self.token and time.time() < (self.expires_at - 300):
                logging.info("Using existing API token")
                return self.token
            return self._refresh_token()

    def force_refresh(self) -> str:
        """Forces a token refresh, ignoring the cache"""
        with self.lock:
            logging.info("Forcing API token refresh...")
            return self._refresh_token()

    def _refresh_token(self) -> str:
        """Internal method to refresh the token"""
        payload = {
            'grant_type': 'password',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'username': SERVICE_ACCOUNT_ACCESS_KEY,
            'password': SERVICE_ACCOUNT_SECRET_KEY
        }
        try:
            logging.info("Refreshing API access token...")
            session = self.initialize_session()
            response = session.post(TOKEN_ENDPOINT, data=payload, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            self.expires_at = time.time() + expires_in
            logging.info("API token refreshed successfully")
            return self.token
        except requests.exceptions.RequestException as e:
            logging.error(f"Error refreshing API token: {e}")
            return None

# Global token manager instance
api_token_manager = None

# ==================== LOGGING SETUP ====================

def setup_logging(log_file):
    """Setup structured logging with file and console output"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# ==================== UTILITY FUNCTIONS ====================

def retry_on_exception(max_retries=MAX_RETRIES, delay=RETRY_DELAY, exceptions=(Exception,)):
    """Decorator to retry functions that may fail transiently"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logging.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
                    else:
                        logging.error(f"All {max_retries} attempts failed for {func.__name__}")
            raise last_exception
        return wrapper
    return decorator

@contextmanager
def file_lock(filename, timeout=10, stale_threshold=5):
    """Context manager for file locking with aggressive stale removal"""
    lock_file = filename + '.lock'
    start_time = time.time()
    acquired = False

    def is_lock_stale():
        try:
            if os.path.exists(lock_file):
                return (time.time() - os.path.getmtime(lock_file)) > stale_threshold
            return False
        except Exception:
            return False

    while True:
        try:
            with open(lock_file, 'x') as lf:
                lf.write(str(os.getpid()))
            acquired = True
            break
        except FileExistsError:
            # Aggressively remove stale or blocking locks
            if is_lock_stale() or (time.time() - start_time) > (timeout - 1):
                try:
                    os.unlink(lock_file)
                    logging.info(f"Removed stale/blocking lock file: {lock_file}")
                    continue
                except Exception:
                    # Can't remove lock, proceed without it
                    logging.warning(f"Could not remove lock {lock_file}, proceeding without lock")
                    acquired = False
                    break

            if time.time() - start_time > timeout:
                # Don't raise error - proceed without lock to avoid deadlock
                logging.warning(f"Lock timeout for {filename}, proceeding without lock")
                acquired = False
                break
            time.sleep(0.1)

    try:
        yield
    finally:
        if acquired:
            try:
                if os.path.exists(lock_file):
                    os.unlink(lock_file)
            except Exception:
                pass  # Ignore cleanup errors

def remove_today_entries(csv_file, today_date):
    """Remove all entries for today's date to prevent duplicates when re-running"""
    csv_path = Path(csv_file)

    if not csv_path.exists():
        return 0

    try:
        # Read all existing data
        rows_to_keep = []
        removed_count = 0

        with open(csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header:
                rows_to_keep.append(header)

            for row in reader:
                if len(row) >= 3:
                    # Keep rows that don't match today's date
                    if row[2] != today_date:
                        rows_to_keep.append(row)
                    else:
                        removed_count += 1

        # Write back the filtered data
        if removed_count > 0:
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(rows_to_keep)
                f.flush()
                os.fsync(f.fileno())

            logging.info(f"Removed {removed_count} existing entries for {today_date} to prevent duplicates")

        return removed_count

    except Exception as e:
        logging.error(f"CRITICAL: Error removing today's entries from CSV: {e}")
        logging.error(f"Cannot safely update CSV file. Aborting job.")
        sys.exit(1)

def write_cost_to_csv(csv_file, model_id, cost, date):
    """Thread-safe CSV writing with monthly append support"""
    csv_path = Path(csv_file)

    try:
        with file_lock(str(csv_path)):
            # Create file with headers if it doesn't exist
            if not csv_path.exists():
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['model', 'cost_std', 'cost_date'])

            # Append data
            with open(csv_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([model_id, cost, date])
                f.flush()
                os.fsync(f.fileno())

        logging.info(f"Wrote cost for {model_id}: ${cost}")
        return True
    except Exception as e:
        logging.error(f"CRITICAL: Failed to write to CSV file {csv_file}: {e}")
        logging.error(f"Unable to save cost data for model {model_id}. Aborting job.")
        sys.exit(1)

def log_error(error_log, model_id, error_message, error_type=None, is_trim_package=False):
    """Log errors to file, optionally skip trim packages"""
    if is_trim_package:
        logging.info(f"Skipping error log for trim package {model_id}: {error_message}")
        return

    error_log_path = Path(error_log)
    error_log_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    error_line = f"{timestamp} - Model {model_id}"
    if error_type:
        error_line += f" - {error_type}"
    error_line += f": {error_message}\n"

    with file_lock(str(error_log_path)):
        with open(error_log_path, 'a', encoding='utf-8') as f:
            f.write(error_line)
            f.flush()
            os.fsync(f.fileno())

    logging.error(f"Model {model_id}: {error_message}")

def upload_cost_to_api(model_id, cost, date, token_manager):
    """Upload cost data to Infor CPQ DataImport API"""
    if not token_manager:
        logging.warning(f"API upload disabled - no token manager available for {model_id}")
        return False

    try:
        token = token_manager.get_token()
        if not token:
            logging.error(f"Failed to get API token for {model_id}")
            return False

        session = token_manager.initialize_session()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Prepare payload for DataImport API
        payload = {
            'model': model_id,
            'cost_std': cost,
            'cost_date': date
        }

        logging.info(f"Uploading cost data to API for {model_id}")
        response = session.post(
            DATA_IMPORT_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            verify=False
        )
        response.raise_for_status()

        logging.info(f"Successfully uploaded cost for {model_id} to API")
        return True

    except requests.exceptions.RequestException as e:
        # If 401, try refreshing token once
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 401:
            logging.warning(f"401 Unauthorized, refreshing token and retrying for {model_id}")
            try:
                token = token_manager.force_refresh()
                if token:
                    headers['Authorization'] = f'Bearer {token}'
                    response = session.post(
                        DATA_IMPORT_ENDPOINT,
                        json=payload,
                        headers=headers,
                        timeout=REQUEST_TIMEOUT,
                        verify=False
                    )
                    response.raise_for_status()
                    logging.info(f"Successfully uploaded cost for {model_id} to API (after retry)")
                    return True
            except Exception as retry_error:
                logging.error(f"Failed to upload {model_id} to API after token refresh: {retry_error}")
                return False

        logging.error(f"Failed to upload {model_id} to API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                logging.error(f"API Response: {e.response.text}")
            except:
                pass
        return False
    except Exception as e:
        logging.error(f"Unexpected error uploading {model_id} to API: {e}")
        return False

# ==================== SELENIUM HELPERS ====================

def create_driver(headless=True):
    """Create and configure Edge WebDriver"""
    from selenium.webdriver.edge.options import Options as EdgeOptions
    from selenium.webdriver.edge.service import Service as EdgeService

    options = EdgeOptions()

    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')

    # Performance optimizations
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_argument('--silent')

    # Set window size for consistency
    options.add_argument('--window-size=1920,1080')

    # Disable images for faster loading (optional - uncomment if needed)
    # prefs = {"profile.managed_default_content_settings.images": 2}
    # options.add_experimental_option("prefs", prefs)

    driver = webdriver.Edge(options=options)
    driver.set_page_load_timeout(LONG_TIMEOUT)

    return driver

def wait_for_element(driver, by, value, timeout=DEFAULT_TIMEOUT, condition=EC.presence_of_element_located):
    """Wait for element with explicit wait"""
    try:
        element = WebDriverWait(driver, timeout).until(condition((by, value)))
        return element
    except TimeoutException:
        logging.warning(f"Timeout waiting for element: {by}={value}")
        raise

def switch_to_frame_with_element(driver, by, value, max_depth=3):
    """Recursively search for element in iframes"""
    def search_frames(depth=0):
        if depth > max_depth:
            return False

        # Try current context first
        try:
            driver.find_element(by, value)
            return True
        except NoSuchElementException:
            pass

        # Search in iframes
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                if search_frames(depth + 1):
                    return True
                driver.switch_to.parent_frame()
            except (NoSuchElementException, StaleElementReferenceException):
                driver.switch_to.parent_frame()
                continue

        return False

    driver.switch_to.default_content()
    return search_frames()

@retry_on_exception(max_retries=MAX_RETRIES, exceptions=(TimeoutException, WebDriverException))
def safe_click(driver, by, value, timeout=DEFAULT_TIMEOUT):
    """Safely click an element with retries"""
    element = wait_for_element(driver, by, value, timeout, EC.element_to_be_clickable)
    try:
        element.click()
    except Exception:
        # Fallback to JavaScript click
        driver.execute_script("arguments[0].click();", element)
    return True

def wait_for_processing(driver, timeout=LONG_TIMEOUT):
    """Wait for any processing overlays to disappear"""
    try:
        WebDriverWait(driver, timeout).until(
            EC.invisibility_of_element_located((
                By.XPATH,
                '//*[contains(@class, "busy-indicator") and contains(@class, "active")]'
            ))
        )
    except TimeoutException:
        logging.warning("Processing indicator still visible after timeout")
        return False
    return True

# ==================== CPQ INTERACTION ====================

class CPQSession:
    """Manages a CPQ session for processing models"""

    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        self.logged_in = False

    def __enter__(self):
        self.driver = create_driver(self.headless)
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()

    @retry_on_exception(max_retries=2, exceptions=(TimeoutException, WebDriverException))
    def login(self):
        """Login to CPQ portal"""
        logging.info("Logging in to CPQ portal...")

        self.driver.get(LOGIN_URL)

        # Click on Dealer Login (not Polaris SSO)
        time.sleep(3)  # Wait for page to load
        dealer_login_btn = wait_for_element(self.driver, By.XPATH, "//*[contains(text(), 'Dealer Login')]", timeout=LONG_TIMEOUT)
        dealer_login_btn.click()

        # Wait for login form and enter credentials
        time.sleep(2)
        username_field = wait_for_element(self.driver, By.ID, "username", timeout=LONG_TIMEOUT)
        username_field.send_keys(USERNAME)

        password_field = wait_for_element(self.driver, By.ID, "pass")
        password_field.send_keys(PASSWORD)
        password_field.submit()

        # Navigate to simulator
        self.driver.get(SIMULATOR_URL)

        # Wait for iframes to load
        WebDriverWait(self.driver, LONG_TIMEOUT).until(
            lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0
        )

        self.logged_in = True
        logging.info("Successfully logged in")

    @retry_on_exception(max_retries=MAX_RETRIES, exceptions=(TimeoutException, WebDriverException))
    def navigate_to_simulator(self):
        """Navigate to simulator page"""
        self.driver.get(SIMULATOR_URL)
        WebDriverWait(self.driver, LONG_TIMEOUT).until(
            lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0
        )

    def process_model(self, model_id):
        """Process a single model and return its cost"""
        logging.info(f"Processing model: {model_id}")

        try:
            # Wait for page to be ready
            WebDriverWait(self.driver, LONG_TIMEOUT).until(
                lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0
            )
            time.sleep(5)  # Additional wait for iframes to fully load

            # Generate configuration ID
            config_id = str(uuid.uuid4())

            # Enter configuration ID
            if not switch_to_frame_with_element(self.driver, By.ID, "SelectedConfigurationId"):
                raise Exception("Configuration ID field not found")

            self.driver.execute_script("""
                var input = document.getElementById('SelectedConfigurationId');
                input.value = arguments[0];
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
            """, config_id)

            # Click Start Interactive Configuration
            if not switch_to_frame_with_element(self.driver, By.ID, "RunInteractive"):
                raise Exception("RunInteractive button not found")

            self.driver.execute_script("document.getElementById('RunInteractive').click();")

            # Wait for configuration to load
            time.sleep(10)  # Wait for UI to initialize
            wait_for_processing(self.driver, timeout=LONG_TIMEOUT)

            # Click hamburger menu
            if not switch_to_frame_with_element(self.driver, By.CLASS_NAME, "application-menu-trigger"):
                raise Exception("Hamburger menu not found")

            self.driver.execute_script(
                "document.getElementsByClassName('application-menu-trigger')[0].click();"
            )

            # Click MODEL tab
            if not switch_to_frame_with_element(self.driver, By.XPATH, '//a[@role="tab" and contains(text(), "MODEL")]'):
                raise Exception("MODEL tab not found")

            safe_click(self.driver, By.XPATH, '//a[@role="tab" and contains(text(), "MODEL")]')

            # Select model from dropdown
            self._select_model(model_id)

            # Wait for processing overlay to clear
            try:
                logging.info("Waiting for processing overlay to clear...")
                WebDriverWait(self.driver, LONG_TIMEOUT).until(
                    EC.invisibility_of_element_located((
                        By.XPATH,
                        '//*[contains(text(), "Processing") or contains(@class, "processing") or contains(@class, "busy-indicator") or contains(@class, "loading")]'
                    ))
                )
                logging.info("Processing overlay cleared")
            except TimeoutException:
                logging.warning("Processing overlay still present after timeout")

            time.sleep(2)  # Additional wait for UI stability

            # Verify ADDITIONAL tab exists (defaults populated)
            if not self._verify_defaults():
                raise Exception("ADDITIONAL tab not found - defaults not populated")

            # Navigate to ADDITIONAL tab and set runMfg
            cost = self._get_model_cost(model_id)

            # Reset for next model by reloading simulator page
            self._reset_for_next_model()

            logging.info(f"Successfully processed model {model_id}: ${cost}")
            return cost

        except Exception as e:
            logging.error(f"Error processing model {model_id}: {e}")
            raise

    def _select_model(self, model_id):
        """Select model from dropdown"""
        if not switch_to_frame_with_element(self.driver, By.CLASS_NAME, "dropdown"):
            raise Exception("Dropdown not found")

        # Find combobox
        dropdowns = self.driver.find_elements(By.CLASS_NAME, "dropdown")
        combobox = None
        for d in dropdowns:
            if d.get_attribute("role") == "combobox":
                combobox = d
                break

        if not combobox:
            raise Exception("Combobox not found")

        # Click to open dropdown
        combobox.click()
        time.sleep(0.5)

        # Find and type in search input
        try:
            search_input = self.driver.find_element(By.CLASS_NAME, "dropdown-search")
            search_input.clear()
            time.sleep(0.3)
            search_input.send_keys(model_id)
            logging.info(f"Entered model ID in search: {model_id}")
            time.sleep(1)

            # Wait for and select option
            try:
                option = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        f'//li[contains(@class, "dropdown-option") and @data-val="{model_id}"]'
                    ))
                )

                # Try clicking the option
                try:
                    self.driver.execute_script("arguments[0].click();", option)
                    time.sleep(0.5)
                except:
                    try:
                        option.click()
                        time.sleep(0.5)
                    except:
                        search_input.send_keys(Keys.ENTER)

                # Verify selection
                time.sleep(1)
                selected_value = search_input.get_attribute("value")
                if model_id != selected_value:
                    logging.warning(f"Selection verification failed. Expected: {model_id}, Got: {selected_value}")
                    search_input.send_keys(Keys.ENTER)
                    time.sleep(0.5)

                logging.info(f"Model selection completed: {model_id}")

            except Exception as e:
                logging.warning(f"First attempt to select model ID {model_id} failed: {e}")
                # Fallback: arrow down and enter
                try:
                    combobox.send_keys(Keys.ARROW_DOWN)
                    time.sleep(0.5)
                    combobox.send_keys(Keys.ENTER)
                    time.sleep(0.5)

                    selected_value = combobox.get_attribute("title") or combobox.text
                    if model_id not in selected_value:
                        raise Exception("Selection verification failed after keyboard navigation")

                except Exception as e2:
                    logging.warning(f"Second attempt to select model ID {model_id} failed: {e2}")
                    # Last resort: JavaScript
                    try:
                        self.driver.execute_script("""
                            var combo = arguments[0];
                            combo.value = arguments[1];
                            combo.dispatchEvent(new Event('change', { bubbles: true }));
                            combo.dispatchEvent(new Event('blur', { bubbles: true }));
                        """, combobox, model_id)
                        logging.info(f"Attempted to set model ID {model_id} via JavaScript")
                    except Exception as e3:
                        error_msg = f"All attempts to select model ID {model_id} failed"
                        raise Exception(error_msg)

        except Exception as e:
            logging.error(f"Error in model selection: {e}")
            raise

        time.sleep(2)  # Wait for any UI updates

    def _verify_defaults(self):
        """Verify that ADDITIONAL tab exists (defaults are populated)"""
        wait_for_processing(self.driver, timeout=LONG_TIMEOUT)

        tabs = self.driver.find_elements(By.XPATH, './/a[@role="tab"]')

        for tab in tabs:
            tab_text = tab.text.strip()
            tab_href = tab.get_attribute("href") or ""

            if tab_text.upper() == "ADDITIONAL" or "ADDITIONAL" in tab_href.upper():
                logging.info("ADDITIONAL tab found - defaults populated")
                return True

        logging.error("ADDITIONAL tab not found - defaults not populated")
        return False

    def _get_model_cost(self, model_id):
        """Navigate to ADDITIONAL tab, set runMfg, and get cost"""
        # Click ADDITIONAL tab
        additional_tab = wait_for_element(
            self.driver,
            By.XPATH,
            '//a[@role="tab" and contains(text(), "ADDITIONAL")]',
            timeout=DEFAULT_TIMEOUT,
            condition=EC.element_to_be_clickable
        )
        additional_tab.click()
        time.sleep(1)

        # Set runMfg to Yes
        yes_radio = self.driver.find_element(
            By.XPATH,
            '//div[@data-screen-option-name="runMfg"]//input[@type="radio" and @data-value="True"]'
        )
        self.driver.execute_script("arguments[0].click();", yes_radio)
        time.sleep(0.5)

        # Wait for cost calculation
        WebDriverWait(self.driver, LONG_TIMEOUT).until(
            EC.invisibility_of_element_located((By.XPATH,
                '//div[contains(@class, "busy-indicator") and contains(@class, "active")]'
            ))
        )

        # Check for error popups
        error_popups = self.driver.find_elements(
            By.XPATH,
            '//div[contains(@class, "error-message") or contains(@class, "alert-error")]'
        )

        if error_popups and any(popup.is_displayed() for popup in error_popups):
            error_msg = next((popup.text for popup in error_popups if popup.is_displayed()), "Unknown error")
            raise Exception(f"Error popup: {error_msg}")

        # Get cost value
        cost_input = self.driver.find_element(
            By.XPATH,
            '//div[@data-screen-option-name="calcCost"]//input[@type="text"]'
        )

        cost_value = cost_input.get_attribute("value")
        if not cost_value:
            raise Exception("Cost value is empty")

        # Clean cost value
        cost = ''.join(c for c in cost_value if c.isdigit() or c == '.')
        if not cost:
            raise Exception(f"Invalid cost value: {cost_value}")

        return cost

    def _reset_for_next_model(self):
        """Reset the page for the next model by reloading simulator"""
        try:
            logging.info("Resetting for next model...")
            self.driver.get(SIMULATOR_URL)

            # Wait for page to fully load
            WebDriverWait(self.driver, LONG_TIMEOUT).until(
                lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0
            )
            time.sleep(5)  # Match the timing from initial load

            logging.info("Ready for next model")
        except Exception as e:
            logging.warning(f"Error during reset: {e}")
            # Try one more time with a fresh page load
            try:
                self.driver.get(SIMULATOR_URL)
                WebDriverWait(self.driver, LONG_TIMEOUT).until(
                    lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0
                )
                time.sleep(5)
            except Exception as e2:
                logging.error(f"Failed to reset page: {e2}")
                raise

# ==================== MAIN PROCESSING ====================

def fetch_model_ids_from_api(token_manager, max_retries=3):
    """Fetch model IDs from Infor CPQ OptionList API with retry logic"""
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            token = token_manager.get_token()
            if not token:
                logging.error("Failed to get API token for fetching models")
                return [], {}

            session = token_manager.initialize_session()
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/json'
            }

            logging.info(f"Fetching model list from API (attempt {attempt}/{max_retries})...")
            response = session.get(
                MODEL_LIST_ENDPOINT,
                headers=headers,
                timeout=120,  # Increased timeout to 120 seconds
                verify=False
            )
            response.raise_for_status()

            data = response.json()
            model_ids = []
            trim_package_lookup = {}  # Map model_id -> is_trim_package

            # Extract model IDs from the 'result' array
            if 'result' in data and isinstance(data['result'], list):
                for item in data['result']:
                    # Only include visible models
                    if 'value' in item and item.get('visible', True):
                        model_id = str(item['value']).strip()
                        model_ids.append(model_id)

                        # Track if this is a trim package
                        is_trim_package = False
                        if 'customProperties' in item and isinstance(item['customProperties'], dict):
                            is_trim_package = item['customProperties'].get('TrimPackage', False)
                        trim_package_lookup[model_id] = is_trim_package

                total_items = data.get('pageInfo', {}).get('totalItems', len(model_ids))
                logging.info(f"Successfully fetched {len(model_ids)} model IDs from API (Total: {total_items})")
                return model_ids, trim_package_lookup
            else:
                logging.warning(f"Unexpected API response structure: {list(data.keys())}")
                return [], {}

        except requests.exceptions.Timeout as e:
            last_error = e
            logging.warning(f"Attempt {attempt}/{max_retries} timed out: {e}")
            if attempt < max_retries:
                wait_time = attempt * 10  # Exponential backoff: 10s, 20s, 30s
                logging.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        except requests.exceptions.RequestException as e:
            last_error = e
            logging.error(f"Attempt {attempt}/{max_retries} failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logging.error(f"Response: {e.response.text[:500]}")
            if attempt < max_retries:
                wait_time = attempt * 10
                logging.info(f"Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
        except Exception as e:
            last_error = e
            logging.error(f"Unexpected error fetching models from API: {e}")
            break

    logging.error(f"Failed to fetch models after {max_retries} attempts")
    return [], {}

def read_model_ids_from_excel(excel_file):
    """Read model IDs from Excel file (legacy support)"""
    wb = openpyxl.load_workbook(excel_file)
    ws = wb.active
    model_ids = []

    for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
        if row[0]:
            model_ids.append(str(row[0]).strip())

    logging.info(f"Read {len(model_ids)} model IDs from {Path(excel_file).name}")
    return model_ids

def process_model_batch(model_ids, output_csv, error_log, headless=True, upload_to_api=False, trim_package_lookup=None):
    """Process a batch of models in a single session"""
    current_date = datetime.now().strftime('%m/%d/%Y')
    success_count = 0
    error_count = 0
    trim_package_skipped = 0
    api_upload_count = 0
    api_error_count = 0

    if trim_package_lookup is None:
        trim_package_lookup = {}

    with CPQSession(headless=headless) as session:
        for model_id in model_ids:
            try:
                cost = session.process_model(model_id)
                write_cost_to_csv(output_csv, model_id, cost, current_date)
                success_count += 1

                # Upload to API if enabled
                if upload_to_api and api_token_manager:
                    if upload_cost_to_api(model_id, cost, current_date, api_token_manager):
                        api_upload_count += 1
                    else:
                        api_error_count += 1

            except Exception as e:
                is_trim_package = trim_package_lookup.get(model_id, False)
                log_error(error_log, model_id, str(e), "PROCESSING_ERROR", is_trim_package=is_trim_package)

                if is_trim_package:
                    trim_package_skipped += 1
                else:
                    error_count += 1

                # Try to recover by navigating back to simulator
                try:
                    session.navigate_to_simulator()
                except Exception as nav_error:
                    logging.error(f"Failed to recover session: {nav_error}")
                    break

    logging.info(f"Batch complete - Success: {success_count}, Errors: {error_count}, Trim packages skipped: {trim_package_skipped}")
    if upload_to_api:
        logging.info(f"API Uploads - Success: {api_upload_count}, Errors: {api_error_count}")
    return success_count, error_count

def process_all_excel_files(input_dir, output_csv, error_log, headless=True, max_workers=4, upload_to_api=False, use_api_models=False):
    """Process all Excel files using thread pool, or fetch models from API"""

    trim_package_lookup = {}

    # Determine model source
    if use_api_models:
        logging.info("Fetching models from API...")
        if not api_token_manager:
            logging.error("API token manager not initialized. Cannot fetch models from API.")
            sys.exit(1)

        all_model_ids, trim_package_lookup = fetch_model_ids_from_api(api_token_manager)
        if not all_model_ids:
            logging.error("No models fetched from API. Exiting.")
            sys.exit(1)

        logging.info(f"Total models to process: {len(all_model_ids)}")

        # Process all models in a single batch
        success_count, error_count = process_model_batch(
            all_model_ids,
            output_csv,
            error_log,
            headless=headless,
            upload_to_api=upload_to_api,
            trim_package_lookup=trim_package_lookup
        )

        logging.info(f"Complete - Success: {success_count}, Errors: {error_count}")

    else:
        # Original Excel file processing logic
        excel_files = glob.glob(os.path.join(input_dir, "*.xlsx"))

        if not excel_files:
            logging.error(f"No Excel files found in {input_dir}")
            sys.exit(1)

        logging.info(f"Found {len(excel_files)} Excel files to process")

        all_model_ids = []
        for excel_file in excel_files:
            model_ids = read_model_ids_from_excel(excel_file)
            all_model_ids.extend(model_ids)

        logging.info(f"Total models to process: {len(all_model_ids)}")

        # Process all models in a single batch
        success_count, error_count = process_model_batch(
            all_model_ids,
            output_csv,
            error_log,
            headless=headless,
            upload_to_api=upload_to_api,
            trim_package_lookup=trim_package_lookup
        )

        logging.info(f"Complete - Success: {success_count}, Errors: {error_count}")

# ==================== ENTRY POINT ====================

def main():
    parser = argparse.ArgumentParser(description="Optimized Boat Cost Calculator")
    parser.add_argument("--input-dir", default=".", help="Directory containing Excel files")
    parser.add_argument("--output-csv", default="boat_costs.csv", help="Output CSV file")
    parser.add_argument("--error-log", default="errors.log", help="Error log file")
    parser.add_argument("--log-file", default="bot_log.txt", help="Main log file")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode (overrides --headless)")
    parser.add_argument("--workers", type=int, default=4, help="Number of concurrent workers")
    parser.add_argument("--upload-to-api", action="store_true", help="Upload results to API")
    parser.add_argument("--use-api-models", action="store_true", help="Fetch model IDs from API instead of Excel files")

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_file)

    # Initialize API token manager if API features are needed
    global api_token_manager
    if args.upload_to_api or args.use_api_models:
        logging.info("Initializing API token manager...")
        api_token_manager = TokenManager()
        # Test token retrieval
        if not api_token_manager.get_token():
            logging.error("Failed to initialize API token. Exiting.")
            sys.exit(1)

    # Override headless if visible mode is requested
    headless = args.headless and not args.visible

    logging.info("=" * 80)
    logging.info("OPTIMIZED BOAT COST CALCULATOR")
    logging.info("=" * 80)
    logging.info(f"Mode: {'Headless' if headless else 'Visible'}")
    logging.info(f"Output CSV: {args.output_csv}")
    logging.info(f"Error Log: {args.error_log}")
    logging.info(f"API Upload: {'Enabled' if args.upload_to_api else 'Disabled'}")
    logging.info(f"Model Source: {'API' if args.use_api_models else 'Excel Files'}")

    # Remove today's entries from CSV to prevent duplicates
    current_date = datetime.now().strftime('%m/%d/%Y')
    removed_count = remove_today_entries(args.output_csv, current_date)

    start_time = time.time()

    try:
        process_all_excel_files(
            args.input_dir,
            args.output_csv,
            args.error_log,
            headless=headless,
            max_workers=args.workers,
            upload_to_api=args.upload_to_api,
            use_api_models=args.use_api_models
        )
    except KeyboardInterrupt:
        logging.info("Process interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    elapsed = time.time() - start_time
    logging.info(f"Total execution time: {elapsed:.1f} seconds")
    logging.info("=" * 80)

if __name__ == "__main__":
    main()
