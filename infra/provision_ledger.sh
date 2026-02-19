#!/bin/bash
# Provision the SpecDrift_Ledger Table
aws dynamodb create-table --cli-input-json file://infra/dynamodb_schema.json
