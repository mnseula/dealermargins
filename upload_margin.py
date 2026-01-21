import requests
import pandas as pd
import concurrent.futures
import os
import argparse
import threading
from sqlalchemy import create_engine
import json
import time
from typing import List, Dict, Optional, Any
from tqdm import tqdm
import urllib3

# Suppress the insecure request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- Connection Settings ---
# Infor API Settings (Hardcoded for now - replace with your actual credentials)
CLIENT_ID = "QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8"
CLIENT_SECRET = "CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ"
TOKEN_ENDPOINT = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2"
SERVICE_ACCOUNT_ACCESS_KEY = "QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw"
SERVICE_ACCOUNT_SECRET_KEY = "pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug"
DEALER_MARGIN_ENDPOINT = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/C_GD_DealerMargin"

# MySQL Database Settings (Hardcoded for now - replace with your actual credentials)
MYSQL_HOST = "ben.c0fnidwvz1hv.us-east-1.rds.amazonaws.com"
MYSQL_USER = "awsmaster"
MYSQL_PASSWORD = "VWvHG9vfG23g7gD"
MYSQL_DATABASE = "warrantyparts"
MYSQL_TABLE = "DealerMargins"

# --- Optimized Constants ---
REQUEST_TIMEOUT = 60
MAX_WORKERS = 8
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
                print("✅ Using existing token.")
                return self.token
            return self._refresh_token(session)

    def force_refresh(self, session: requests.Session) -> Optional[str]:
        """Forces a token refresh, ignoring the cache."""
        with self.lock:
            print("🔄 Forcing token refresh due to 401 error...")
            return self._refresh_token(session)

    def _refresh_token(self, session: requests.Session) -> Optional[str]:
        """Internal method to refresh the token"""
        payload = {
            'grant_type': 'password', 'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
            'username': SERVICE_ACCOUNT_ACCESS_KEY, 'password': SERVICE_ACCOUNT_SECRET_KEY
        }
        try:
            print("🔄 Refreshing access token...")
            response = session.post(TOKEN_ENDPOINT, data=payload, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            token_data = response.json()
            self.token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)
            self.expires_at = time.time() + expires_in
            print("✅ Token refreshed successfully")
            return self.token
        except requests.exceptions.RequestException as e:
            print(f"❌ Error refreshing token: {e}")
            return None

def get_margins_from_mysql() -> Optional[pd.DataFrame]:
    """Connects to MySQL using SQLAlchemy and fetches the wide-format margin data."""
    try:
        print(f"🗄️  Connecting to MySQL database '{MYSQL_DATABASE}'...")
        # Create SQLAlchemy engine for robust connection management and to resolve pandas UserWarning
        db_uri = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{MYSQL_DATABASE}"
        engine = create_engine(db_uri)

        with engine.connect() as conn:
            query = f"SELECT * FROM {MYSQL_TABLE}"
            print(f"Executing query: {query}")
            df = pd.read_sql(query, conn)
            print(f"✅ Successfully fetched {len(df)} records from MySQL.")
        return df
    except Exception as e:
        print(f"❌ Error fetching data from MySQL: {e}")
        return None

def transform_margins_for_api(df_wide: pd.DataFrame) -> List[Dict[str, Any]]:
    """Transforms the wide DataFrame from MySQL into a long list of records for the API."""
    print("🔄 Transforming data for API...")
    # Mapping from database suffix to API field name
    margin_types = {
        'BASE_BOAT': 'C_BaseBoat', 'ENGINE': 'C_Engine', 'OPTIONS': 'C_Options',
        'FREIGHT': 'C_Freight', 'PREP': 'C_Prep', 'VOL_DISC': 'C_Volume'
    }

    # Dynamically discover the series from the DataFrame's column names
    series_set = set()
    db_suffixes = [f"_{suffix}" for suffix in margin_types.keys()]

    for col in df_wide.columns:
        if col in ['DealerID', 'Dealership', 'Enabled']: # Exclude non-margin columns
            continue
        for suffix in db_suffixes:
            if col.endswith(suffix):
                series_prefix_with_underscores = col[:-len(suffix)]  # e.g., 'S_23' from 'S_23_BASE_BOAT'
                series_name = series_prefix_with_underscores.replace('_', ' ')  # e.g., 'S 23'
                series_set.add(series_name)
                break  # Move to the next column once a suffix is matched

    series_list = sorted(list(series_set))
    print(f"🔍 Dynamically discovered series from columns: {series_list}")

    api_records = []
    for _, row in df_wide.iterrows():
        for series in series_list:
            # Safely get the 'Enabled' status, defaulting to False if the column doesn't exist or is null.
            is_enabled = bool(row.get('Enabled')) if pd.notna(row.get('Enabled')) else False
            api_record = {
                "C_DealerId": str(row['DealerID']), "C_DealerName": row['Dealership'],
                "C_Series": series, "C_Enabled": is_enabled
            }
            has_data = False
            for db_suffix, api_key in margin_types.items():
                col_name = f"{series.replace(' ', '_')}_{db_suffix}"
                if col_name in row and pd.notna(row[col_name]):
                    api_record[api_key] = int(row[col_name]) # API expects integers for these fields
                    has_data = True
            # Only add the record if it contains at least one margin value
            if has_data:
                api_records.append(api_record)

    if api_records:
        print(f"✅ Transformed into {len(api_records)} records with data to be synced.")
    else:
        print("⚠️ No records with data were found after transformation.")
    return api_records

def sync_record_to_eq(session: requests.Session, token_manager: TokenManager, record: Dict[str, Any], dry_run: bool = False) -> str:
    """Syncs a single record to EQ by checking for existence then POSTing or PUTing."""
    dealer_id, series = record['C_DealerId'], record['C_Series']

    filter_query = f"$filter=C_DealerId eq '{dealer_id}' and C_Series eq '{series}'"
    query_url = f"{DEALER_MARGIN_ENDPOINT}?{filter_query}"

    for attempt in range(MAX_RETRIES):
        try:
            # Get a token for this specific attempt. This is critical for multi-threading and retries.
            token = token_manager.get_token(session)
            if not token: return f"❌ No token for {dealer_id}/{series}"
            session.headers.update({'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})

            response = session.get(query_url, timeout=REQUEST_TIMEOUT, verify=False)
            response.raise_for_status()
            response_data = response.json()
            existing_items = response_data.get('items', [])

            if existing_items:
                item = existing_items[0]
                item_id = item.get('Id')

                if item_id:
                    if dry_run:
                        return f"[DRY RUN] Would update {dealer_id}/{series} (Id: {item_id})"

                    # Record exists, so update it using PUT
                    # CRITICAL FIX: Remove single quotes around GUID - just use parentheses
                    update_url = f"{DEALER_MARGIN_ENDPOINT}({item_id})"

                    # Include Id in the payload (matching C# implementation)
                    record_with_id = dict(record)
                    record_with_id['Id'] = item_id

                    put_response = session.put(update_url, json=record_with_id, timeout=REQUEST_TIMEOUT, verify=False)
                    put_response.raise_for_status()
                    return f"✅ Updated {dealer_id}/{series} (Id: {item_id})"
                else:
                    return f"⚠️  Skipped {dealer_id}/{series}: Found existing record but it has no Id."
            else:
                if dry_run:
                    return f"[DRY RUN] Would create {dealer_id}/{series}"
                # Record does not exist, so create it
                post_response = session.post(DEALER_MARGIN_ENDPOINT, json=record, timeout=REQUEST_TIMEOUT, verify=False)
                post_response.raise_for_status()
                return f"✅ Created {dealer_id}/{series}"
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            # If we get a 401 Unauthorized, force a token refresh on the next retry.
            is_auth_error = hasattr(e, 'response') and e.response is not None and e.response.status_code == 401
            if is_auth_error:
                token_manager.force_refresh(session)

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                error_details = e
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_details = e.response.json()
                    except json.JSONDecodeError:
                        error_details = e.response.text
                return f"❌ Failed {dealer_id}/{series} after {MAX_RETRIES} attempts: {error_details}"
    return f"❌ Failed {dealer_id}/{series} unexpectedly"

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Upload dealer margins to Infor EQ.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without making any changes to the API.")
    args = parser.parse_args()

    if args.dry_run:
        print("💨 Performing a DRY RUN. No changes will be made to the API.")
    print("🚀 Starting Dealer Margins Upload to EQ...")
    start_time = time.time()

    # --- IMPORTANT: Your credentials are still hardcoded in this file. ---
    # For production use, it's highly recommended to move these to environment variables
    # or a configuration file (e.g., using python-dotenv as previously discussed).
    # This improves security and flexibility.
    # -------------------------------------------------------------------

    df_margins = get_margins_from_mysql()

    if df_margins is None or df_margins.empty:
        print("No data from MySQL. Exiting.")
        return

    records_to_upload = transform_margins_for_api(df_margins)
    if not records_to_upload:
        print("No records generated after transformation. Exiting.")
        return


    # --- Sync all records from MySQL to API using PUT or POST ---
    session = requests.Session()
    token_manager = TokenManager()
    session.verify = False

    print(f"📊 Total records to process: {len(records_to_upload)}")

    success_count = 0
    fail_count = 0
    failed_records = []

    # Use the existing sync_record_to_eq function which handles both CREATE and UPDATE
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_record = {
            executor.submit(sync_record_to_eq, requests.Session(), token_manager, record, args.dry_run): record
            for record in records_to_upload
        }

        # Process results with progress bar
        with tqdm(total=len(records_to_upload), desc="Syncing records") as pbar:
            for future in concurrent.futures.as_completed(future_to_record):
                record = future_to_record[future]
                try:
                    result = future.result()
                    if result.startswith("❌"):
                        fail_count += 1
                        failed_records.append(f"{record['C_DealerId']} - {record['C_DealerName']} - {record['C_Series']}")
                    else:
                        success_count += 1

                    # Print result (tqdm will handle the progress bar)
                    tqdm.write(result)
                except Exception as e:
                    fail_count += 1
                    failed_records.append(f"{record['C_DealerId']} - {record['C_DealerName']} - {record['C_Series']}")
                    tqdm.write(f"❌ Exception for {record['C_DealerId']}/{record['C_Series']}: {e}")
                finally:
                    pbar.update(1)

    print(f"\n✅ Sync complete. Success: {success_count}, Failed: {fail_count}")

    if failed_records:
        print("\n❌ FAILED RECORDS - Please review and fix the following:")
        print("=" * 60)
        for failed in sorted(failed_records):
            print(f"  • {failed}")
        print(f"\nTotal failed: {len(failed_records)}")
        print("=" * 60)
    else:
        print("\n🎉 All records synced successfully!")

    print(f"⏱️  Total time: {time.time() - start_time:.1f} seconds")
    if success_count > 0:
        print(f"📊 Average rate: {success_count / (time.time() - start_time):.2f} records/second")

if __name__ == "__main__":
    main()
