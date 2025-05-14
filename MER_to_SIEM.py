import requests
import json
import socket
import logging
from datetime import datetime, timedelta
from MER_API import MER_CREDENTIALS
import concurrent.futures
import pytz

class NoRebuildAuthSession(requests.Session):
    """Custom session to preserve the Authorization header when redirected."""
    def rebuild_auth(self, prepared_request, response):
        pass

# Initialize the session
session = NoRebuildAuthSession()

# Function to get all organizations' IDs and names using the API key
def get_all_organizations(api_key):
    url = 'https://api.meraki.com/api/v1/organizations'
    headers = {'Authorization': f'Bearer {api_key}'}
    
    response = session.get(url, headers=headers)

    if response.status_code == 200:
        organizations = response.json()
        if organizations:
            return [(org["id"], org["name"]) for org in organizations]  # Return list of ID and Name
        else:
            logging.error("No organizations found.")
            return []
    else:
        logging.error(f"Failed to fetch organizations: {response.status_code}")
        return []

# Function to fetch security events for the organization
def fetch_security_events(api_key, organization_id):
    # Get the current time (t1) and subtract 5 minutes for t0
    t1 = datetime.utcnow()
    t0 = t1 - timedelta(minutes=5)

    # Format the times in ISO 8601 format for Meraki's API (YYYY-MM-DDTHH:MM:SSZ)
    t1_str = t1.strftime('%Y-%m-%dT%H:%M:%SZ')
    t0_str = t0.strftime('%Y-%m-%dT%H:%M:%SZ')

    url = f'https://api.meraki.com/api/v1/organizations/{organization_id}/appliance/security/events'
    headers = {'Authorization': f'Bearer {api_key}'}
    params = {
        't0': t0_str,  # Start time (5 minutes ago)
        't1': t1_str,  # End time (current time)
        'perPage': 1000,  # Number of events per page
        'sortOrder': 'descending'  # Sort by the most recent events first
    }
    
    events = []
    seen_events = {}  # Dictionary to track grouped events by (signature, message)

    while url:
        response = session.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data:
                for event in data:
                    event_signature = event.get('signature', '')
                    event_message = event.get('message', '')
                    event_key = (event_signature, event_message)

                    if event_key not in seen_events:
                        seen_events[event_key] = {
                            "signature": event_signature,
                            "message": event_message,
                            "count": 1,
                            "first_ts": event.get("ts"),
                            "last_ts": event.get("ts"),
                            "events": [event]
                        }
                    else:
                        last_ts = seen_events[event_key]["last_ts"]
                        last_time = datetime.strptime(last_ts, "%Y-%m-%dT%H:%M:%S.%fZ")
                        event_time = datetime.strptime(event.get("ts"), "%Y-%m-%dT%H:%M:%S.%fZ")

                        if (event_time - last_time).total_seconds() < 60:
                            seen_events[event_key]["count"] += 1
                            seen_events[event_key]["last_ts"] = event.get("ts")
                        else:
                            seen_events[event_key]["events"].append(event)
                            seen_events[event_key]["last_ts"] = event.get("ts")
            else:
                logging.info("No security events found.")
            
            next_page = response.links.get('next', None)
            if next_page:
                url = next_page['url']
            else:
                break
        else:
            logging.error(f"Failed to fetch security events: {response.status_code}")
            break
    
    return seen_events

# Function to send events to Graylog via UDP
def send_to_graylog(events, organization_name):
    graylog_host = '127.0.0.1'
    graylog_port = 12201
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    total_sent = 0

    # Madrid Timezone
    madrid_tz = pytz.timezone('Europe/Madrid')

    for event_key, event_info in events.items():
        for event in event_info["events"]:
            # Get the timestamp and extract time and date
            event_timestamp = event.get("ts")
            if event_timestamp:
                # Convert the event timestamp from UTC to Madrid time
                event_datetime_utc = datetime.strptime(event_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
                event_datetime_utc = pytz.utc.localize(event_datetime_utc)  # Localize to UTC
                event_datetime_madrid = event_datetime_utc.astimezone(madrid_tz)  # Convert to Madrid timezone
                
                # Format the time and date in the Madrid timezone
                event_time = event_datetime_madrid.strftime("%H:%M:%S")  # Time in HH:MM:SS format
                event_date = event_datetime_madrid.strftime("%Y-%m-%d")  # Date in YYYY-MM-DD format
            else:
                event_time = event_date = None  # In case timestamp is missing

            # Creating individual log entries with the new fields
            log_entry = {
                "timestamp": event.get("ts"),
                "organization": organization_name,
                "signature": event_info["signature"],
                "message": event_info["message"],
                "count": event_info["count"],
                "event": event,
                "tool": "MER",
                "time": event_time,  # Time in Madrid timezone
                "date": event_date   # Date in Madrid timezone
            }
            message = json.dumps(log_entry)
            udp_socket.sendto(message.encode(), (graylog_host, graylog_port))
            total_sent += 1

    udp_socket.close()
    return total_sent

# Main function to orchestrate the flow
def process_organization(credentials):
    api_key = credentials['API']

    # Get all organizations for the given API key
    organizations = get_all_organizations(api_key)
    total_events_fetched = 0
    total_events_sent = 0

    # Iterate over all organizations
    for organization_id, organization_name in organizations:
        logging.info(f"Fetching events from {organization_name}...")

        events = fetch_security_events(api_key, organization_id)
        total_events_fetched += sum(event_info["count"] for event_info in events.values())

        if events:
            logging.info(f"Sending {len(events)} events from {organization_name} to Graylog...")
            total_events_sent += send_to_graylog(events, organization_name)

    return total_events_fetched, total_events_sent

# Main function to execute the script
def main():
    total_events_fetched = 0
    total_events_sent = 0

    # Use ThreadPoolExecutor for concurrent execution
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_organization, credentials) for credentials in MER_CREDENTIALS]

        for future in concurrent.futures.as_completed(futures):
            fetched, sent = future.result()
            total_events_fetched += fetched
            total_events_sent += sent

    logging.info(f"Total events fetched: {total_events_fetched}")
    logging.info(f"Total events sent: {total_events_sent}")

# Run the script
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()