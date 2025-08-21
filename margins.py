import requests # type: ignore
import json
from tqdm import tqdm # type: ignore
import os
import urllib3
import pandas as pd
import concurrent.futures
import threading
import time
from typing import List, Dict, Optional

# Suppress the insecure request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Connection Settings ---
CLIENT_ID = "QA2FNBZCKUAUH7QB_TRN~H80EoFmxpr1RMXqY4TeW-u2c5vCw1sGRIr18qppHoPY"
CLIENT_SECRET = "rmmqE4W5K3ANN-hid34kbC7r78mYHGIs9Wg6fzCdLImCH33JCt6L3x8ThLzBbvwS49f6PunHG8eMM19z_u1diw"
TOKEN_ENDPOINT = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2"
SERVICE_ACCOUNT_ACCESS_KEY = "QA2FNBZCKUAUH7QB_TRN#OXBbg16XPKc5tDaOb_v2MzynsS2bnjFtvTBiOuUJhWXrO62s7arC7juObUL2iqYkWVWsCPV26XzB0VDXAvq1mw"
SERVICE_ACCOUNT_SECRET_KEY = "Xp6Iam1HR4So1rs4KfbKOZmWOf1oFEWQkC1m55TvbBS7vql-HpSMd4J37ioB3tm-B1bpSo5apjwxxdxAw1WJsg"
DEALER_MARGIN_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/C_GD_DealerMargin"

# --- Optimized Constants ---
REQUEST_TIMEOUT = 60  # Increased timeout
ITEMS_PER_PAGE = 1000  # Larger page size
MAX_WORKERS = 8  # Concurrent requests
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

class TokenManager:
    """Thread-safe token management with automatic refresh"""
    def __init__(self):
        self.token = None
        self.expires_at = 0
        self.lock = threading.Lock()
    
    def get_token(self, session: requests.Session) -> Optional[str]:
        """Get a valid token, refreshing if necessary"""
        with self.lock:
            # Check if current token is still valid (with 5 minute buffer)
            if self.token and time.time() < (self.expires_at - 300):
                return self.token
            
            # Get new token
            return self._refresh_token(session)
    
    def _refresh_token(self, session: requests.Session) -> Optional[str]:
        """Internal method to refresh the token"""
        payload = {
            'grant_type': 'password',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'username': SERVICE_ACCOUNT_ACCESS_KEY,
            'password': SERVICE_ACCOUNT_SECRET_KEY
        }
        
        try:
            print("🔄 Refreshing access token...")
            response = session.post(TOKEN_ENDPOINT, data=payload, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            
            token_data = response.json()
            self.token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
            self.expires_at = time.time() + expires_in
            
            print("✅ Token refreshed successfully")
            return self.token
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error refreshing token: {e}")
            return None

def fetch_page_with_retry(session: requests.Session, token_manager: TokenManager, page: int, items_per_page: int, pbar: tqdm, filter_query: str = "") -> Optional[List[Dict]]:
    """Fetch a single page with retry logic"""
    skip_count = (page - 1) * items_per_page
    url = f"{DEALER_MARGIN_ENDPOINT}?top={items_per_page}&skip={skip_count}{filter_query}"
    for attempt in range(MAX_RETRIES):
        try:
            token = token_manager.get_token(session)
            if not token:
                pbar.write(f"❌ No token available for page {page}")
                return None
            session.headers.update({'Authorization': f'Bearer {token}'})
            response = session.get(url, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            data = response.json()
            items = data.get('items', [])
            pbar.update(len(items))
            return items
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                pbar.write(f"⚠️  Page {page} attempt {attempt + 1} failed: {e}. Retrying...")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                pbar.write(f"❌ Page {page} failed after {MAX_RETRIES} attempts: {e}")
                return None
    return None

def get_download_metadata(session: requests.Session, token_manager: TokenManager, filter_query: str = "") -> Optional[tuple[int, int]]:
    """Gets the total number of items and pages to download."""
    token = token_manager.get_token(session)
    if not token:
        return None
    session.headers.update({'Authorization': f'Bearer {token}'})
    url = f"{DEALER_MARGIN_ENDPOINT}?top=1{filter_query}"
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()
        data = response.json()
        total_items = data.get('totalItems', 0)
        if total_items is None:
            print("❌ Could not find 'totalItems' in response.")
            return None
        total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
        print(f"📊 Found {total_items:,} total items across {total_pages} pages.")
        return total_items, total_pages
    except Exception as e:
        print(f"❌ Error fetching total pages: {e}")
        return None

def get_all_dealer_margins_optimized(series_filters: Optional[List[str]] = None) -> Optional[List[Dict]]:
    """Optimized version with correct page size detection and better error handling"""

    session = requests.Session()
    token_manager = TokenManager()

    print(f"🚀 Starting download for series: {series_filters}")
    
    filter_query = ""
    if series_filters:
        # Deduplicate the list while preserving order for logging
        unique_series = list(dict.fromkeys(series_filters))
        filter_conditions = [f"C_Series eq '{s}'" for s in unique_series]
        filter_string = " or ".join(filter_conditions)
        filter_query = f"&$filter={filter_string}"

    metadata = get_download_metadata(session, token_manager, filter_query)
    if not metadata:
        print("❌ Could not retrieve download metadata. Aborting.")
        return None

    total_items, _ = metadata

    if total_items == 0:
        print(f"\n✅ No items found for series: {series_filters}. Nothing to download.")
        return []

    try:
        # Detect actual items per page from first page
        with tqdm(total=total_items, unit=' records', desc=f"Downloading {series_filters}", dynamic_ncols=True) as pbar:
            first_page_items = fetch_page_with_retry(session, token_manager, 1, ITEMS_PER_PAGE, pbar, filter_query)
            if not first_page_items:
                print("❌ Could not fetch first page. Exiting.")
                return None

            actual_items_per_page = len(first_page_items)
            if actual_items_per_page == 0:
                print("❌ First page returned zero items. Exiting.")
                return []

            total_pages = (total_items + actual_items_per_page - 1) // actual_items_per_page
            
            all_items = []
            all_items.extend(first_page_items)

            with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                def download_task(page_num):
                    thread_session = requests.Session()
                    thread_session.verify = False
                    return fetch_page_with_retry(thread_session, token_manager, page_num, actual_items_per_page, pbar, filter_query)

                # Start from page 2 since page 1 is already fetched
                future_to_page = {executor.submit(download_task, page): page for page in range(2, total_pages + 1)}

                for future in concurrent.futures.as_completed(future_to_page):
                    items = future.result()
                    if items:
                        all_items.extend(items)

            if not all_items:
                print("❌ No data was successfully downloaded")
                return None

            print(f"\n✅ Successfully downloaded {len(all_items):,} records for series: {series_filters}")
            return all_items

    except KeyboardInterrupt:
        print("\n⏹️  Download interrupted by user")
        return None
    except Exception as e:
        print(f"\n❌ Unexpected error during download: {e}")
        return None
    finally:
        session.close()

def create_dealer_quotes_csv(items: List[Dict], csv_path: str = 'dealer_quotes.csv') -> bool:
    """Creates a wide-format CSV for dealer quotes from the downloaded JSON data."""
    try:
        print(f"\n🔄 Creating dealer quotes CSV...")
        
        if not items:
            print("✅ No items to process.")
            return True
            
        df = pd.DataFrame(items)
        
        # Initial column rename
        column_rename_map = {
            'C_DealerName': 'Dealership',
            'C_DealerId': 'DealerID',
            'C_Series': 'Series',
            'C_Volume': 'VOL_DISC',
            'C_BaseBoat': 'BASE_BOAT',
            'C_Engine': 'ENGINE',
            'C_Options': 'OPTIONS',
            'C_Freight': 'FREIGHT',
            'C_Prep': 'PREP',
        }
        df.rename(columns=column_rename_map, inplace=True)
        
        # We only need the columns that will be part of the pivot
        value_vars = ['VOL_DISC', 'BASE_BOAT', 'ENGINE', 'OPTIONS', 'FREIGHT', 'PREP']
        df_filtered = df[['DealerID', 'Dealership', 'Series'] + value_vars]
        
        # Pivot the table
        pivot_df = df_filtered.pivot_table(
            index=['DealerID', 'Dealership'],
            columns='Series',
            values=value_vars
        )
        
        # Flatten the multi-level column index
        pivot_df.columns = [f'{series.replace(" ", "_")}_{val}' for val, series in pivot_df.columns]
        
        # Reset index to make DealerID and Dealership columns
        pivot_df.reset_index(inplace=True)
        
        # Define the final column order
        final_columns = [
            'DealerID', 'Dealership',
            'Q_BASE_BOAT', 'Q_ENGINE', 'Q_OPTIONS', 'Q_FREIGHT', 'Q_PREP', 'Q_VOL_DISC',
            'QX_BASE_BOAT', 'QX_ENGINE', 'QX_OPTIONS', 'QX_FREIGHT', 'QX_PREP', 'QX_VOL_DISC',
            'QXS_BASE_BOAT', 'QXS_ENGINE', 'QXS_OPTIONS', 'QXS_FREIGHT', 'QXS_PREP', 'QXS_VOL_DISC',
            'R_BASE_BOAT', 'R_ENGINE', 'R_OPTIONS', 'R_FREIGHT', 'R_PREP', 'R_VOL_DISC',
            'RX_BASE_BOAT', 'RX_ENGINE', 'RX_OPTIONS', 'RX_FREIGHT', 'RX_PREP', 'RX_VOL_DISC',
            'RT_BASE_BOAT', 'RT_ENGINE', 'RT_OPTIONS', 'RT_FREIGHT', 'RT_PREP', 'RT_VOL_DISC',
            'G_BASE_BOAT', 'G_ENGINE', 'G_OPTIONS', 'G_FREIGHT', 'G_PREP', 'G_VOL_DISC',
            'S_BASE_BOAT', 'S_ENGINE', 'S_OPTIONS', 'S_FREIGHT', 'S_PREP', 'S_VOL_DISC',
            'SX_BASE_BOAT', 'SX_ENGINE', 'SX_OPTIONS', 'SX_FREIGHT', 'SX_PREP', 'SX_VOL_DISC',
            'L_BASE_BOAT', 'L_ENGINE', 'L_OPTIONS', 'L_FREIGHT', 'L_PREP', 'L_VOL_DISC',
            'LX_BASE_BOAT', 'LX_ENGINE', 'LX_OPTIONS', 'LX_FREIGHT', 'LX_PREP', 'LX_VOL_DISC',
            'LT_BASE_BOAT', 'LT_ENGINE', 'LT_OPTIONS', 'LT_FREIGHT', 'LT_PREP', 'LT_VOL_DISC',
            'S_23_BASE_BOAT', 'S_23_ENGINE', 'S_23_OPTIONS', 'S_23_FREIGHT', 'S_23_PREP', 'S_23_VOL_DISC',
            'SV_23_BASE_BOAT', 'SV_23_ENGINE', 'SV_23_OPTIONS', 'SV_23_FREIGHT', 'SV_23_PREP', 'SV_23_VOL_DISC',
            'M_BASE_BOAT', 'M_ENGINE', 'M_OPTIONS', 'M_FREIGHT', 'M_PREP', 'M_VOL_DISC'
        ]
        
        # Add missing columns with default value (e.g., 0 or NaN)
        for col in final_columns:
            if col not in pivot_df.columns:
                pivot_df[col] = pd.NA
                
        # Reorder columns
        pivot_df = pivot_df[final_columns]
        
        # Save to CSV
        pivot_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        print(f"✅ Successfully created dealer quotes CSV: {csv_path}")
        print(f"📄 Columns: {', '.join(pivot_df.columns)}")
        
        return True

    except FileNotFoundError:
        print(f"❌ File not found")
        return False
    except Exception as e:
        print(f"❌ Error during CSV creation: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting optimized dealer margins downloader...")
    start_time = time.time()
    
    try:
        series_to_download = [
            'Q', 'QX', 'QXS', 'R', 'RX', 'RT', 'G', 'S', 'SX', 'L', 'LX', 'LT', 'S 23', 'SV 23', 'M'
        ]
        
        csv_output_path = 'dealer_quotes.csv'
        
        # Clean up old CSV file before starting
        if os.path.exists(csv_output_path):
            os.remove(csv_output_path)
            print(f"🧹 Removed old CSV file: {csv_output_path}")

        all_downloaded_items = []
        all_series_successful = True
        for series in series_to_download:
            print(f"\n--- Processing series: '{series}' ---")
            
            # Download data for a single series
            downloaded_items = get_all_dealer_margins_optimized(series_filters=[series])
            
            if downloaded_items is not None:
                all_downloaded_items.extend(downloaded_items)
            else:
                print(f"❌ Download failed for series '{series}'.")
                all_series_successful = False

        if all_downloaded_items:
            # Create the final pivoted CSV
            csv_success = create_dealer_quotes_csv(all_downloaded_items, csv_output_path)
            
            if csv_success:
                print(f"\n🎉 All operations completed successfully!")
            else:
                print(f"\n⚠️ CSV creation failed. Please review the logs.")
        else:
            print(f"\n⚠️ No data was downloaded for any series. Please review the logs.")

        print(f"⏱️  Total time: {time.time() - start_time:.1f} seconds")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Process interrupted after {time.time() - start_time:.1f} seconds")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print(f"⏱️  Runtime: {time.time() - start_time:.1f} seconds")
