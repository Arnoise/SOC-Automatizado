import json
import requests
import socket
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import sleep
from UMB_API import API_CREDENTIALS

# Graylog UDP host and port
GRAYLOG_HOST = '127.0.0.1'
GRAYLOG_PORT = 12201

# Configure logging for better error tracking
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to send logs to Graylog using UDP
def send_to_graylog(logs):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            for log in logs:
                msg = json.dumps(log)
                sock.sendto(msg.encode(), (GRAYLOG_HOST, GRAYLOG_PORT))
    except Exception as e:
        logging.error(f"Error sending logs to Graylog: {e}")

# Function to fetch and process logs for each organization
def fetch_and_process_logs(api_key, secret_key, org_name):
    # Step 1: Get the access token
    auth_url = 'https://api.umbrella.com/auth/v2/token'
    auth_data = {'grant_type': 'client_credentials'}
    auth_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        auth_response = requests.post(auth_url, auth_data, auth_headers, auth=(api_key, secret_key), timeout=10)
        auth_response.raise_for_status()
        access_token = auth_response.json().get('access_token')
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching access token for {org_name}: {e}")
        return []

    # Step 2: Fetch DNS activity logs
    logs_url = 'https://api.umbrella.com/reports/v2/activity?from=-5minutes&to=now&limit=4999&verdict=blocked&policycategories=65,64,150,110,61,66,67,108,68,109&timezone=EUROPE%2fMADRID'
    logs_headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    try:
        logs_response = requests.get(logs_url, headers=logs_headers, timeout=10)
        logs_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching logs for {org_name}: {e}")
        return []

    logs_data = logs_response.json().get('data', [])
    
    # Step 3: Flatten logs and add labels
    flattened_logs = []
    for log in logs_data:
        flattened_log = flatten_log(log)
        flattened_log['organization'] = org_name
        flattened_log['tool'] = 'UMB'
        flattened_logs.append(flattened_log)

    return flattened_logs

# Helper function to flatten nested log structure
def flatten_log(log):
    flattened = {}
    for key, value in log.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                flattened[f'{key}_{sub_key}'] = sub_value
        elif isinstance(value, list):
            for idx, item in enumerate(value):
                flattened[f'{key}_{idx}'] = item
        else:
            flattened[key] = value
    return flattened

# Function to handle the entire process for each organization
def process_organization(credentials):
    api_key = credentials['API']
    secret_key = credentials['KEY']
    org_name = credentials['ORG']

    logging.info(f"Fetching events from {org_name}...")
    logs = fetch_and_process_logs(api_key, secret_key, org_name)

    return org_name, logs

# Main execution with parallelization
def main():
    total_fetched_events = 0
    total_sent_events = 0
    
    # Use ThreadPoolExecutor to fetch logs concurrently
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_org = {executor.submit(process_organization, credentials): credentials for credentials in API_CREDENTIALS}

        # Process results as they complete
        for future in as_completed(future_to_org):
            try:
                org_name, logs = future.result()
                total_fetched_events += len(logs)

                if logs:
                    logging.info(f"Sending {len(logs)} events from {org_name} to Graylog...")
                    send_to_graylog(logs)
                    total_sent_events += len(logs)
            except Exception as e:
                logging.error(f"Error processing organization: {e}")
                sleep(5)  # Sleep for 5 seconds before retrying or continuing

    logging.info(f"Total events fetched: {total_fetched_events}")
    logging.info(f"Total events sent: {total_sent_events}")

if __name__ == "__main__":
    main()