#!/bin/bash

# OpenSearch creds & endpoint
OS_HOST="https://localhost:9200"
OS_USER="myuser"
OS_PASS="yourpassword"

# Index to clear
INDEX="workflowexecution"

# Delete all documents from index
curl -X POST "$OS_HOST/$INDEX/_delete_by_query?conflicts=proceed" \
  -u "$OS_USER:$OS_PASS" -H 'Content-Type: application/json' \
  -d '{
    "query": { "match_all": {} }
  }' -k

echo "$(date): Cleared $INDEX" >> /var/log/clear_index.log
