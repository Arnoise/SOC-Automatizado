import time
import hmac
import hashlib
import base64
import requests
from datetime import datetime, timedelta
import urllib.parse
import json
import logging
import socket
import pytz  # Import pytz for time zone conversion
from DUO_API import ORG_CREDENTIALS

# Setup logging to customize the output format
logging.basicConfig(
    level=logging.INFO,  # Set to INFO to minimize log output
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Function to generate the HMAC signature for the request
def sign_request(http_method, host, endpoint, params, skey, ikey):
    params = {key: str(value) for key, value in params.items()}
    sorted_params = sorted(params.items())
    encoded_params = urllib.parse.urlencode(sorted_params)

    now_utc = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S -0000')
    canonical_string = f"{now_utc}\n{http_method}\n{host}\n{endpoint}\n{encoded_params}"

    signature = hmac.new(skey.encode('utf-8'), canonical_string.encode('utf-8'), hashlib.sha1).hexdigest()

    auth_header = f"Basic {base64.b64encode(f'{ikey}:{signature}'.encode('utf-8')).decode('utf-8')}"
    
    return auth_header, now_utc

# Function to flatten the nested logs and add date, time, tool, and organization
def flatten_json(nested_json, parent_key='', sep='_', org_name=None):
    items = []
    for k, v in nested_json.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        # Add date and time fields based on isotimestamp
        if k == 'isotimestamp':
            # Parse the isotimestamp (UTC time)
            isotimestamp = v
            dt = datetime.fromisoformat(isotimestamp)
            
            # Convert from UTC to Madrid's local time (CET/CEST)
            madrid_tz = pytz.timezone('Europe/Madrid')
            dt_madrid = dt.astimezone(madrid_tz)
            
            # Add date and time fields (without milliseconds in time)
            items.append(('date', dt_madrid.strftime('%Y-%m-%d')))  # Date in YYYY-MM-DD format
            items.append(('time', dt_madrid.strftime('%H:%M:%S')))  # Time in HH:MM:SS format (no milliseconds)
            
            # Add the original isotimestamp back to the items (optional)
            items.append(('isotimestamp', isotimestamp))  # Keep the original isotimestamp label
            
        elif isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep, org_name=org_name).items())
        else:
            items.append((new_key, v))

    # Add static fields for tool and organization
    if org_name:
        items.append(('tool', 'DUO'))  # Static tool label
        items.append(('organization', org_name))  # Organization from DUO_API

    return dict(items)

# Function to fetch logs from a given organization
def fetch_logs_from_org(org_name, credentials):
    IKEY = credentials['IKEY']
    SKEY = credentials['SKEY']
    HOST = credentials['HOST']
    ORG = credentials['ORG']
    ENDPOINT = '/admin/v2/logs/authentication'

    # Calculate mintime (5 minutes ago) and maxtime (now)
    now = datetime.now(pytz.timezone('Europe/Madrid'))  # Get the current time in Madrid timezone
    mintime = now - timedelta(minutes=7)  # 5 minutes ago in local time - here i modified to 7 minutes because it has a 2 minute delay
    maxtime = now  # Now in local time

    # Convert to the required ISO8601 format with timezone
    mintime_str = mintime.strftime('%Y-%m-%dT%H:%M:%S%z')
    maxtime_str = maxtime.strftime('%Y-%m-%dT%H:%M:%S%z')

    # Include both timeRange and mintime/maxtime parameters
    params = {
        'limit': 100,
        'timeRange': f'{mintime_str}~{maxtime_str}',  # Use timeRange in the correct format
        'mintime': int(mintime.timestamp() * 1000),  # Timestamp in milliseconds
        'maxtime': int(maxtime.timestamp() * 1000),  # Timestamp in milliseconds
    }
    
    headers, now_utc = sign_request('GET', HOST, ENDPOINT, params, SKEY, IKEY)
    
    try:
        response = requests.get(f'https://{HOST}{ENDPOINT}', headers={
            'Authorization': headers,
            'Date': now_utc
        }, params=params)

        if response.status_code == 200:
            data = response.json()
            authlogs = data.get('response', {}).get('authlogs', [])
            if authlogs:
                flattened_logs = []
                for log in authlogs:
                    flattened_log = flatten_json(log, org_name=ORG)  # Pass ORG to flatten_json
                    flattened_logs.append(flattened_log)

                logging.info(f"Sending {len(flattened_logs)} events from {ORG} to Graylog...")
                send_to_graylog(flattened_logs, org_name)
            else:
                logging.info(f"No authentication logs found for {ORG} in the last 5 minutes.")
        else:
            logging.error(f"Failed to fetch logs for {ORG}. HTTP Status code: {response.status_code}")
            logging.error(f"Error message: {response.json()}")
    except Exception as e:
        logging.error(f"Error fetching logs for {ORG}: {str(e)}")

def send_to_graylog(logs, org_name):
    graylog_host = '127.0.0.1'
    graylog_port = 12201

    # UDP socket to send logs to Graylog
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    total_sent = 0
    for log in logs:
        message = json.dumps(log)  # Convert log to JSON string
        try:
            sock.sendto(message.encode(), (graylog_host, graylog_port))
            total_sent += 1
        except Exception as e:
            logging.error(f"Error sending log to Graylog: {e}")
    
    logging.info(f"Total events sent: {total_sent} from {org_name} to Graylog")
    sock.close()

# Main function to fetch and send logs for all organizations
def main():
    for credentials in ORG_CREDENTIALS:
        org_name = credentials['ORG']
        logging.info(f"Fetching events from {org_name}...")
        fetch_logs_from_org(org_name, credentials)

if __name__ == "__main__":
    main()