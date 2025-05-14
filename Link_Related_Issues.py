import requests
import json
from urllib.parse import quote_plus

# Jira API URL
jira_base_url = 'https://example-org.atlassian.net/rest/api/2'

# Jira credentials (replace with your own credentials)
username = 'example@org.es'
api_token = 'ThIs#IsAToKen'

# Function to search for an issue based on JQL query
def search_jira_issue(jql_query):
    # URL-encode the JQL query to ensure proper formatting in the URL
    encoded_jql = quote_plus(jql_query)  # Use quote_plus for proper encoding of spaces as '+'
    url = f'{jira_base_url}/search?jql={encoded_jql}&maxResults=1'
    headers = {
        'Content-Type': 'application/json',
    }
    auth = (username, api_token)

    response = requests.get(url, headers=headers, auth=auth)

    # Check the response status
    if response.status_code == 200:
        issues = response.json().get('issues', [])
        if issues:
            # If issues are found, print the common fields
            found_issue = issues[0]
            common_fields = {
                "Issue Key": found_issue['key'],
                "Summary": found_issue['fields']['summary'],
                "Status": found_issue['fields']['status']['name'],
                "Created": found_issue['fields']['created'],
            }
            print("Similar issue found:")
            for field, value in common_fields.items():
                print(f"{field}: {value}")
            return found_issue
        else:
            print("No similar events found.")
            return None
    else:
        print(f"Failed to search issues. Status code: {response.status_code}")
        print(response.text)
        return None

# Function to create a link between two issues, linking the oldest (parent) to the newest (child)
def create_issue_link(source_issue_key, target_issue_key):
    url = f'{jira_base_url}/issueLink'
    headers = {
        'Content-Type': 'application/json',
    }
    auth = (username, api_token)
    
    link_data = {
        "type": {
            "id": "10003"  # "Relates" link type
        },
        "inwardIssue": {
            "key": source_issue_key  # Oldest issue as parent
        },
        "outwardIssue": {
            "key": target_issue_key  # Newest issue as child
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(link_data), auth=auth)
    
    if response.status_code == 201:
        print(f"Issues {source_issue_key} and {target_issue_key} are now linked.")
        return True
    else:
        print(f"Failed to create issue link. Status code: {response.status_code}")
        print(response.text)
        return False

# Function to transition the status of the new issue to match the oldest issue's status
def transition_issue_to_status(issue_key, status_id):
    # Get the available transitions for the issue
    url = f'{jira_base_url}/issue/{issue_key}/transitions'
    headers = {
        'Content-Type': 'application/json',
    }
    auth = (username, api_token)
    
    # Request available transitions for the issue
    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        transitions = response.json().get('transitions', [])
        for transition in transitions:
            if transition['to']['id'] == status_id:
                # Perform the transition if the status matches
                transition_url = f'{jira_base_url}/issue/{issue_key}/transitions'
                transition_data = {
                    "transition": {
                        "id": transition['id']
                    }
                }
                transition_response = requests.post(transition_url, headers=headers, data=json.dumps(transition_data), auth=auth)
                if transition_response.status_code == 204:
                    print(f"Issue {issue_key} has been transitioned to the status: {status_id}.")
                    return True
                else:
                    print(f"Failed to transition issue {issue_key}. Status code: {transition_response.status_code}")
                    print(transition_response.text)
                    return False
    else:
        print(f"Failed to get transitions for issue {issue_key}. Status code: {response.status_code}")
        print(response.text)
        return False

# Main function to search and link the issue
def main():
    # Specify the key of the already created issue
    created_issue_key = "$jira_issue.#.body.key"  # Replace with your actual created issue key

    # Define the values for the custom fields (modify these as needed)
    var_1_value = "$html_to_json.#.tool"
    var_2_value = "$html_to_json.#.organization"
    var_3_value = "$html_to_json.#.identities_0.label"
    var_4_value = "$html_to_json.#.domain"
    var_5_value = "$html_to_json.#.policycategories_0.label"
    var_6_value = "$html_to_json.#.date"
    
    # Define the JQL search query
    jql_query = f'project = "TEST - MERGE" AND "VAR_1[Paragraph]" ~ "{var_1_value}" ' \
                f'AND "VAR_2[Paragraph]" ~ "{var_2_value}" ' \
                f'AND "VAR_3[Paragraph]" ~ "{var_3_value}" ' \
                f'AND "VAR_4[Paragraph]" ~ "{var_4_value}" ' \
                f'AND "VAR_5[Paragraph]" ~ "{var_5_value}" ' \
                f'AND "VAR_6[Paragraph]" ~ "{var_6_value}" ' \
                f'ORDER BY created ASC'

    # Print for debugging the query format
    print(f"JQL Query: {jql_query}")

    # Search for an existing issue based on JQL query
    existing_issue = search_jira_issue(jql_query)
    
    if existing_issue:
        existing_issue_key = existing_issue['key']
        existing_issue_status_id = existing_issue['fields']['status']['id']  # Get status ID of the oldest issue

        # If an existing issue is found, create the link between issues
        link_successful = create_issue_link(created_issue_key, existing_issue_key)

        # Transition the new issue to match the status of the oldest issue if the link is successful
        if link_successful:
            transition_successful = transition_issue_to_status(created_issue_key, existing_issue_status_id)
            if not transition_successful:
                print(f"Failed to transition issue {created_issue_key}.")
        else:
            print(f"Failed to link issue {created_issue_key}.")
    else:
        print("No existing issue found matching the JQL search criteria.")
    
if __name__ == '__main__':
    main()
