# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Deploy workspace to Fabric via GitHub Actions"""

import argparse
import os
import sys

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from fabric_cicd import FabricWorkspace, change_log_level, publish_all_items, unpublish_all_orphan_items

# Parse arguments from GitHub Actions workflow
parser = argparse.ArgumentParser(description="Deploy Fabric Workspace Parameters")
parser.add_argument("--repository_directory", type=str, required=True, help="Directory of the workspace files")
parser.add_argument("--environment", type=str, required=True, help="Environment to use for parameter.yml (dev/test/prod)")
parser.add_argument("--workspace_name", type=str, required=True, help="Name of the workspace to deploy")

args = parser.parse_args()

repository_directory = args.repository_directory
environment = args.environment
workspace_name = args.workspace_name

# Force unbuffered output for GitHub Actions logs
sys.stdout.reconfigure(line_buffering=True, write_through=True)
sys.stderr.reconfigure(line_buffering=True, write_through=True)

# Enable debugging if ACTIONS_RUNNER_DEBUG is set
if os.getenv("ACTIONS_RUNNER_DEBUG", "false").lower() == "true":
    change_log_level("DEBUG")

print(f"Starting deployment to workspace: {workspace_name}")
print(f"Environment: {environment}")
print(f"Repository directory: {repository_directory}")

try:
    # Use ClientSecretCredential for GitHub Actions or DefaultAzureCredential for local development
    # GitHub Actions will provide these environment variables
    client_id = os.getenv("AZURE_CLIENT_ID")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    
    if client_id and tenant_id and client_secret:
        print("Using ClientSecretCredential for authentication")
        token_credential = ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
    else:
        print("Using DefaultAzureCredential for authentication (local development)")
        token_credential = DefaultAzureCredential()

    # Initialize the FabricWorkspace object with the required parameters
    target_workspace = FabricWorkspace(
        workspace_name=workspace_name,
        environment=environment,
        repository_directory=repository_directory,
        token_credential=token_credential,
    )

    print(f"Workspace initialized: {target_workspace.workspace_name}")

    # Publish all items defined in item_type_in_scope
    print("Publishing all items...")
    publish_all_items(target_workspace)
    print("All items published successfully")

    # Unpublish all items defined in item_type_in_scope not found in repository
    print("Cleaning up orphan items...")
    unpublish_all_orphan_items(target_workspace)
    print("Orphan items removed successfully")

    print(f"Deployment to {workspace_name} completed successfully!")

except Exception as e:
    print(f"ERROR: Deployment failed: {str(e)}")
    sys.exit(1)
