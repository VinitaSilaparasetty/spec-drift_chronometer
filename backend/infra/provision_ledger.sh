#!/bin/bash
# Spec-Drift Chronometer: Sovereign Infrastructure Provisioning
# Targets: AWS DynamoDB (eu-central-1)

set -e

REGION="eu-central-1"
TABLE_NAME="SpecDrift_Sovereign_Ledger"

echo "Checking for existing table: $TABLE_NAME in $REGION..."

if aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION >/dev/null 2>&1; then
    echo "SUCCESS: Table already exists. Skipping creation."
else
    echo "ACTION: Creating Sovereign Ledger..."
    aws dynamodb create-table \
        --cli-input-json file://infra/dynamodb_schema.json \
        --region $REGION
    
    echo "WAITING: Waiting for table to reach ACTIVE status..."
    aws dynamodb wait table-exists --table-name $TABLE_NAME --region $REGION
    echo "SUCCESS: Sovereign Ledger is live."
fi
