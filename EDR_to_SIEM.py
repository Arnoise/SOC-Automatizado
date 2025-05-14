import requests
import base64
import json
import logging
import socket
import concurrent.futures
from datetime import datetime, timedelta
import pytz
from EDR_API import EDR_CREDENTIALS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to get the Authorization header using Basic Auth
def get_auth_header(client_id, api_key):
    credentials = f"{client_id}:{api_key}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
    return {"Authorization": f"Basic {encoded_credentials}"}

# Function to get events from Cisco EDR API
def get_events(start_date, event_types, limit=500, offset=0, client_id=None, api_key=None):
    headers = get_auth_header(client_id, api_key)
    params = {
        "start_date": start_date,
        "event_type[]": event_types,  # Pass the list of event types as a query parameter
        "limit": limit,
        "offset": offset
    }
    
    try:
        # Make the GET request to the Cisco AMP for Endpoints API
        response = requests.get(f'https://{EDR_CREDENTIALS[0]["HOST"]}/v1/events', headers=headers, params=params)
        if response.status_code == 200:
            response_data = response.json()
            events = response_data.get('data', [])
            return events, response_data.get('metadata', {})
        else:
            logging.error(f"Error fetching events: {response.status_code} - {response.text}")
            return None, None
    except Exception as e:
        logging.error(f"Exception occurred: {str(e)}")
        return None, None

# Function to send data to Graylog via UDP
def send_to_graylog(org, events):
    if not events:  # If there are no events to send, return early.
        return

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    graylog_host = '127.0.0.1'
    graylog_port = 12201

    logging.info(f"Sending {len(events)} events from {org} to Graylog...")

    # Get Madrid timezone (CET or CEST based on daylight savings)
    madrid_tz = pytz.timezone('Europe/Madrid')

    for event in events:
        # Extract the event timestamp and convert to Madrid timezone
        event_date = event.get('date')
        if event_date:
            try:
                # Parse the date field from the event (ISO 8601 format)
                event_datetime_utc = datetime.fromisoformat(event_date)  # Parse the string into a datetime object

                # Convert to Madrid timezone
                event_datetime_madrid = event_datetime_utc.astimezone(madrid_tz)

                # Extract only the date part (YYYY-MM-DD)
                main_date = event_datetime_madrid.strftime('%Y-%m-%d')  # Properly format the date to 'YYYY-MM-DD'
                event_time = event_datetime_madrid.strftime('%H:%M:%S')  # Time in HH:MM:SS format
            except Exception as e:
                logging.error(f"Error parsing date for event: {e}")
                main_date = event_time = None  # If there's an error, set them to None
        else:
            main_date = event_time = None  # Fallback if no date is found

        # Add the additional labels to the event
        event['organization'] = org
        event['tool'] = 'EDR'
        event['main_date'] = main_date  # Correctly formatted as 'YYYY-MM-DD'
        event['time'] = event_time  # Time in HH:MM:SS format

        message = json.dumps(event)
        try:
            udp_socket.sendto(message.encode('utf-8'), (graylog_host, graylog_port))
        except Exception as e:
            logging.error(f"Error sending event to Graylog: {e}")
    
    udp_socket.close()

# Function to fetch events for a specific organization and send them to Graylog
def fetch_and_send_for_org(org, start_date, event_types, client_id, api_key):
    logging.info(f"Fetching events from {org}...")

    events = []
    offset = 0
    limit = 500  # Setting a reasonable limit to fetch large number of events

    # Fetch all events with pagination
    while True:
        fetched_events, metadata = get_events(start_date, event_types, limit, offset, client_id, api_key)

        if fetched_events:
            events.extend(fetched_events)
            total_events = metadata.get('results', {}).get('total', 0)

            if total_events > offset + limit:
                offset += limit
            else:
                break
        else:
            break

    # Send events to Graylog only once per organization after all events are fetched
    send_to_graylog(org, events)

    return len(events)  # Return the number of events fetched and sent

# Function to fetch and process events for all organizations concurrently
def fetch_and_process_events_for_orgs():
    # Set start time for fetching events (5 minutes ago)
    start_date = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z"

    # Define event types (same as in your original script)
    event_types = [
        1090519054, 553648168, 1090519081, 1090519084, 1090519105, 1107296257, 
        1107296258, 1107296261, 1107296262, 1107296263, 1107296264, 1107296266, 
        1107296267, 1107296268, 1107296269, 1107296270, 1107296271, 1107296272, 
        1107296273, 1107296274, 1107296275, 1107296276, 1107296277, 1107296278, 
        1107296280, 1107296281, 1107296282, 1107296283, 1107296284, 1091567628, 
        2165309453, 1090524040, 1090524041, 1107296279, 553648202, 2164260939, 
        553648204, 2164260941, 553648206, 2164260943, 553648215, 1090519102, 
        553648222, 553648225
    ]

    # Initialize total event counters
    total_events_fetched = 0
    total_events_sent = 0

    # Process each organization concurrently
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []

        for creds in EDR_CREDENTIALS:
            org = creds['ORG']
            client_id = creds['CID']
            api_key = creds['API']

            futures.append(executor.submit(fetch_and_send_for_org, org, start_date, event_types, client_id, api_key))

        for future in concurrent.futures.as_completed(futures):
            fetched = future.result()  # Get the result (fetched events and sent events)
            total_events_fetched += fetched
            total_events_sent += fetched

    # Log the final summary
    logging.info(f"Total events fetched: {total_events_fetched}")
    logging.info(f"Total events sent to Graylog: {total_events_sent}")

# Main function
if __name__ == "__main__":
    fetch_and_process_events_for_orgs()