import requests
import time
import urllib3
import warnings
import logging
from requests.exceptions import RequestException

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Setup logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
    ]
)
logger = logging.getLogger()

# Retry logic parameters
MAX_RETRIES = 3
RETRY_DELAY = 5  # Delay between retries in seconds

# Function to start the workflow
def start_workflow():
    url = "https://<IP>:<PORT>/api/v1/workflows/<Workflow_ID>/execute"
    headers = {
        "Authorization": "Bearer <Shuffle_API_Key>",
        "Content-Type": "application/json"
    }
    data = '{"execution_argument": "", "start": ""}'

    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, headers=headers, data=data, verify=False)
            response.raise_for_status()  # Raise for HTTP errors
            result = response.json()
            execution_id = result['execution_id']
            authorization = result['authorization']
            logger.info(f"Workflow started. Execution ID: {execution_id}, Authorization: {authorization}")
            return execution_id, authorization
        except RequestException as e:
            retries += 1
            logger.error(f"Failed to start workflow (Attempt {retries}/{MAX_RETRIES}): {e}")
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logger.critical("Max retries reached, could not start the workflow.")
                return None, None

# Function to check the status of the workflow
def check_status(execution_id, authorization):
    url = "https://<IP>:<PORT>/api/v1/streams/results"
    headers = {
        "Content-Type": "application/json"
    }
    data = f'{{"execution_id": "{execution_id}", "authorization": "{authorization}"}}'

    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = requests.post(url, headers=headers, data=data, verify=False)
            response.raise_for_status()  # Raise for HTTP errors
            status_data = response.text
            if '"status":"FINISHED"' in status_data:
                logger.info(f"Status: FINISHED for Execution ID: {execution_id}")
                return True
            else:
                logger.info(f"Status not finished yet. Waiting for completion...")
                time.sleep(5)  # Real-time wait for the response
                return False
        except RequestException as e:
            retries += 1
            logger.error(f"Failed to check status (Attempt {retries}/{MAX_RETRIES}): {e}")
            if retries < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logger.critical("Max retries reached, could not check status.")
                return False

# Main function to manage workflow execution and status check
def run_workflow():
    while True:
        # Step 1: Start the workflow and get execution_id and authorization
        execution_id, authorization = start_workflow()
        
        if execution_id and authorization:
            # Step 2: Check the status of the workflow until it is finished
            while True:
                if check_status(execution_id, authorization):
                    break  # Exit the loop once the workflow is finished
        else:
            logger.error("Workflow initiation failed. Skipping this iteration.")

        logger.info("Workflow completed. Waiting 1 second before starting the next one.")
        time.sleep(1)  # Wait 1 second before starting the next workflow

# Run the script
if __name__ == "__main__":
    run_workflow()
