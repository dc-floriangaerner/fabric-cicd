#!/bin/bash
# Generate deployment summary for GitHub Actions
# Usage: ./generate-deployment-summary.sh <environment> <trigger_type> [workspaces_csv]
#
# Arguments:
#   environment: Target environment (dev/test/prod)
#   trigger_type: Deployment trigger (Automatic/Manual)
#   workspaces_csv: (Optional) Comma-separated list of workspaces deployed
#               If omitted, workspace count will be read from deployment-results.json

set -e

# Parse arguments
ENVIRONMENT="$1"
TRIGGER_TYPE="$2"
WORKSPACES_CSV="$3"

if [ -z "$ENVIRONMENT" ] || [ -z "$TRIGGER_TYPE" ]; then
    echo "Error: Missing required arguments" >&2
    echo "Usage: $0 <environment> <trigger_type> [workspaces_csv]" >&2
    exit 1
fi

# Capitalize environment name for display
ENV_DISPLAY=$(echo "$ENVIRONMENT" | sed 's/.*/\u&/')

# Start summary
echo "### Deployment Summary - $ENV_DISPLAY" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY
echo "- **Trigger Type**: $TRIGGER_TYPE" >> $GITHUB_STEP_SUMMARY

# Read deployment results from JSON file if it exists
if [ -f "deployment-results.json" ]; then
    total_workspaces=$(jq -r '.total_workspaces' deployment-results.json)
    successful_count=$(jq -r '.successful_count' deployment-results.json)
    failed_count=$(jq -r '.failed_count' deployment-results.json)
    duration=$(jq -r '.duration' deployment-results.json)
else
    # Fallback to counting from input
    if [ -n "$WORKSPACES_CSV" ]; then
        IFS=',' read -ra WORKSPACES <<< "$WORKSPACES_CSV"
        total_workspaces=${#WORKSPACES[@]}
    else
        total_workspaces=0
    fi
    successful_count=0
    failed_count=$total_workspaces
    duration="N/A"
fi

echo "- **Environment**: $ENVIRONMENT" >> $GITHUB_STEP_SUMMARY
echo "- **Total Workspaces**: $total_workspaces" >> $GITHUB_STEP_SUMMARY
echo "- **Successful**: $successful_count" >> $GITHUB_STEP_SUMMARY
echo "- **Failed**: $failed_count" >> $GITHUB_STEP_SUMMARY

# Format duration to 2 decimal places if it's a number
if [[ "$duration" =~ ^[0-9]+\.?[0-9]*$ ]]; then
    formatted_duration=$(printf "%.2f" "$duration")
    echo "- **Duration**: ${formatted_duration}s" >> $GITHUB_STEP_SUMMARY
else
    echo "- **Duration**: ${duration}s" >> $GITHUB_STEP_SUMMARY
fi

echo "- **Status**: ${JOB_STATUS}" >> $GITHUB_STEP_SUMMARY
echo "- **Completed**: $(date -u '+%Y-%m-%d %H:%M:%S UTC')" >> $GITHUB_STEP_SUMMARY
echo "" >> $GITHUB_STEP_SUMMARY

# List workspaces with individual status from JSON
if [ -f "deployment-results.json" ] && [ "$total_workspaces" -gt 0 ]; then
    echo "#### Deployment Results:" >> $GITHUB_STEP_SUMMARY
    echo "" >> $GITHUB_STEP_SUMMARY

    # Read and display each workspace status
    jq -r '.workspaces[] | "\(.status)|\(.full_name)|\(.error)"' deployment-results.json | while IFS='|' read -r status full_name error; do
        if [ "$status" == "success" ]; then
            echo "- ✓ $full_name" >> $GITHUB_STEP_SUMMARY
        else
            echo "- ✗ $full_name" >> $GITHUB_STEP_SUMMARY
            if [ -n "$error" ]; then
                echo "  - Error: $error" >> $GITHUB_STEP_SUMMARY
            fi
        fi
    done
fi

echo "Deployment summary generated successfully"
