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

def get_all_dealer_margins_optimized(series_filters: Optional[List[str]] = None) -> bool:
    """Optimized version with correct page size detection and better error handling"""

    session = requests.Session()
    token_manager = TokenManager()

    print("🚀 Starting optimized dealer margins download...")
    
    filter_query = ""
    if series_filters:
        # Deduplicate the list while preserving order for logging
        unique_series = list(dict.fromkeys(series_filters))
        print(f"🔍 Filtering for series: {unique_series}")
        filter_conditions = [f"C_Series eq '{s}'" for s in unique_series]
        filter_string = " or ".join(filter_conditions)
        filter_query = f"&$filter={filter_string}"

    metadata = get_download_metadata(session, token_manager, filter_query)
    if not metadata:
        print("❌ Could not retrieve download metadata. Aborting.")
        return False

    total_items, _ = metadata

    if total_items == 0:
        print("\n✅ No items found matching the filter criteria. Nothing to download.")
        file_path = 'margins_optimized.json'
        empty_data = {
            "items": [],
            "totalItems": 0,
            "downloadedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pagesDownloaded": 0
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(empty_data, f, indent=2)
        return True

    try:
        # Detect actual items per page from first page
        with tqdm(total=total_items, unit=' records', desc="Downloading Margins", dynamic_ncols=True) as pbar:
            first_page_items = fetch_page_with_retry(session, token_manager, 1, ITEMS_PER_PAGE, pbar, filter_query)
            if not first_page_items:
                print("❌ Could not fetch first page. Exiting.")
                return False

            actual_items_per_page = len(first_page_items)
            if actual_items_per_page == 0:
                print("❌ First page returned zero items. Exiting.")
                return False

            total_pages = (total_items + actual_items_per_page - 1) // actual_items_per_page
            print(f"🔎 totalItems: {total_items}, actual_items_per_page: {actual_items_per_page}, total_pages: {total_pages}")

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
                return False

            print(f"\n✅ Successfully downloaded {len(all_items):,} records from {total_pages} pages")

            # Save results
            full_margins_data = {
                "items": all_items,
                "totalItems": len(all_items),
                "downloadedAt": time.strftime("%Y-%m-%d %H:%M:%S"),
                "pagesDownloaded": total_pages
            }

            file_path = 'margins_optimized.json'
            print(f"💾 Saving data to {file_path}...")

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(full_margins_data, f, indent=2)

            print(f"✅ Data saved successfully to: {file_path}")
            return True

    except KeyboardInterrupt:
        print("\n⏹️  Download interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error during download: {e}")
        return False
    finally:
        session.close()

def convert_json_to_csv_optimized(json_path: str = 'margins_optimized.json', csv_path: str = 'margins_optimized.csv') -> bool:
    """Optimized CSV conversion with better error handling and append support"""
    try:
        print(f"\n🔄 Appending {json_path} to {csv_path}...")
        
        # Use pandas to read JSON directly for better performance
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        column_rename_map = {
            'C_DealerName': 'DealerName',
            'C_DealerId': 'DealerId', 
            'C_Series': 'Series',
            'C_Volume': 'Volume_Margin_Percent',
            'C_BaseBoat': 'BaseBoat_Margin_Percent',
            'C_Engine': 'Engine_Margin_Percent',
            'C_Options': 'Options_Margin_Percent',
            'C_Freight': 'Freight_Margin_Dollars',
            'C_Prep': 'Prep_Margin_Dollars',
            'C_Enabled': 'IsEnabled',
            'C_Dealer': 'Dealer_GUID'
        }

        items = data.get('items')
        if items is None:
            print("❌ 'items' key not found in the JSON file")
            return False
        
        file_exists = os.path.isfile(csv_path)

        if not items:
            print("✅ JSON file contains no items. Nothing to append.")
            if not file_exists:
                # Create an empty file with headers if it doesn't exist
                pd.DataFrame(columns=column_rename_map.values()).to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f"✅ Created empty CSV with headers: {csv_path}")
            return True
        
        print(f"📊 Processing {len(items):,} records...")
        
        # Create DataFrame
        df = pd.DataFrame(items)
        
        # Filter out metadata columns
        columns_to_keep = [col for col in df.columns if not col.startswith('_')]
        df_filtered = df[columns_to_keep].copy()
        
        existing_renames = {k: v for k, v in column_rename_map.items() if k in df_filtered.columns}
        df_filtered.rename(columns=existing_renames, inplace=True)

        # Ensure consistent column order for appending
        df_filtered = df_filtered.reindex(columns=list(column_rename_map.values()))
        
        # Save to CSV with better performance settings
        df_filtered.to_csv(csv_path, index=False, encoding='utf-8-sig', mode='a', header=not file_exists)
        
        print(f"✅ Successfully appended {len(df_filtered):,} records to: {csv_path}")
        if not file_exists:
            # Only print columns for the first write
            print(f"📝 Renamed {len(existing_renames)} columns for clarity")
            print(f"📄 Columns: {', '.join(df_filtered.columns)}")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ File not found: {json_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in {json_path}: {e}")
        return False
    except PermissionError:
        print(f"❌ Error during CSV conversion: Permission denied for '{csv_path}'.")
        print("   Please make sure the file is not open in another program (like Excel) and try again.")
        return False
    except Exception as e:
        print(f"❌ Error during CSV conversion: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting optimized dealer margins downloader...")
    start_time = time.time()
    
    try:
        series_to_download = [
            'Q', 'R', 'S', 'L', 'M'
        ]
        
        csv_output_path = 'margins_optimized.csv'
        
        # Clean up old CSV file before starting
        if os.path.exists(csv_output_path):
            os.remove(csv_output_path)
            print(f"🧹 Removed old CSV file: {csv_output_path}")

        all_series_successful = True
        for i, series in enumerate(series_to_download):
            print(f"\n--- Processing series {i+1}/{len(series_to_download)}: '{series}' ---")
            
            # Download data for a single series
            download_success = get_all_dealer_margins_optimized(series_filters=[series])
            
            if download_success:
                print(f"✅ Download for series '{series}' completed.")
                
                # Convert the downloaded JSON and append to the main CSV
                csv_success = convert_json_to_csv_optimized(csv_path=csv_output_path)
                
                if not csv_success:
                    print(f"⚠️ CSV conversion failed for series '{series}'.")
                    all_series_successful = False
            else:
                print(f"❌ Download failed for series '{series}'.")
                all_series_successful = False

        if all_series_successful:
            print(f"\n🎉 All operations completed successfully!")
            print(f"⏱️  Total time: {time.time() - start_time:.1f} seconds")
        else:
            print(f"\n⚠️  Some operations failed. Please review the logs.")
            print(f"⏱️  Total time: {time.time() - start_time:.1f} seconds")
            
    except KeyboardInterrupt:
        print(f"\n⏹️  Process interrupted after {time.time() - start_time:.1f} seconds")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print(f"⏱️  Runtime: {time.time() - start_time:.1f} seconds")