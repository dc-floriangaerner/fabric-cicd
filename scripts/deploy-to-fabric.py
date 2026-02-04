# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Deploy workspaces to Fabric via GitHub Actions with continue-on-failure support"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from fabric_cicd import FabricWorkspace, change_log_level, publish_all_items, unpublish_all_orphan_items
from fabric_workspace_manager import ensure_workspace_exists


def get_stage_prefix(environment: str) -> str:
    """Return the stage prefix for workspace naming."""
    prefixes = {
        "dev": "[D] ",
        "test": "[T] ",
        "prod": "[P] "
    }
    return prefixes.get(environment.lower(), "")


def get_workspace_folders(workspaces_dir: str) -> List[str]:
    """Get all workspace folders from the workspaces directory."""
    workspaces_path = Path(workspaces_dir)
    if not workspaces_path.exists():
        print(f"ERROR: Workspaces directory not found: {workspaces_dir}")
        return []
    
    workspace_folders = [
        folder.name for folder in workspaces_path.iterdir() 
        if folder.is_dir() and (folder / "parameter.yml").exists()
    ]
    
    return sorted(workspace_folders)


def deploy_workspace(
    workspace_folder: str,
    workspaces_dir: str,
    environment: str,
    token_credential,
    capacity_id: str = None,
    service_principal_object_id: str = None,
    entra_admin_group_id: str = None
) -> tuple[bool, str]:
    """Deploy a single workspace.
    
    Args:
        workspace_folder: Name of the workspace folder
        workspaces_dir: Root directory containing workspace folders
        environment: Target environment (dev/test/prod)
        token_credential: Azure credential for authentication
        capacity_id: Fabric capacity ID used when creating the workspace.
            Required if the workspace does not already exist and must be auto-created;
            optional if the target workspace already exists.
        service_principal_object_id: Azure AD Object ID of the service principal used for
            role assignment when a new workspace is created. Required for auto-creation
            scenarios where the service principal should be granted access; optional if
            the workspace already exists and no new role assignment is needed.
        entra_admin_group_id: Optional Azure AD Object ID of Entra ID group to grant
            admin permissions. If provided, the group will be assigned as a workspace admin.
        
    Returns:
        Tuple of (success: bool, error_message: str). Error message is empty string if successful.
    """
    try:
        # Construct workspace name with stage prefix
        stage_prefix = get_stage_prefix(environment)
        workspace_name = f"{stage_prefix}{workspace_folder}"
        
        # Construct repository directory path
        repository_directory = os.path.join(workspaces_dir, workspace_folder)
        
        print(f"\n{'='*60}")
        print(f"Deploying workspace: {workspace_name}")
        print(f"Folder: {workspace_folder}")
        print(f"Environment: {environment}")
        print(f"Repository directory: {repository_directory}")
        print(f"{'='*60}\n")
        
        # Ensure workspace exists (create if necessary)
        workspace_id = ensure_workspace_exists(
            workspace_name=workspace_name,
            capacity_id=capacity_id,
            service_principal_object_id=service_principal_object_id,
            token_credential=token_credential,
            entra_admin_group_id=entra_admin_group_id
        )
        print(f"→ Workspace ensured with ID: {workspace_id}")
        
        # Initialize the FabricWorkspace object
        target_workspace = FabricWorkspace(
            workspace_name=workspace_name,
            environment=environment,
            repository_directory=repository_directory,
            token_credential=token_credential,
        )
        
        print(f"→ Workspace initialized: {workspace_name}")
        
        # Publish all items defined in item_type_in_scope
        print(f"→ Publishing all items...")
        publish_all_items(target_workspace)
        print(f"  ✓ All items published successfully")
        
        # Unpublish all items defined in item_type_in_scope not found in repository
        print(f"→ Cleaning up orphan items...")
        unpublish_all_orphan_items(target_workspace)
        print(f"  ✓ Orphan items removed successfully")
        
        print(f"\n✓ Deployment to {workspace_name} completed successfully!\n")
        return True, ""
        
    except Exception as e:
        error_message = str(e)
        print(f"\n✗ ERROR: Deployment failed for workspace '{workspace_folder}': {error_message}\n")
        return False, error_message


def main():
    """Main deployment orchestration with rollback support."""
    # Parse arguments from GitHub Actions workflow
    parser = argparse.ArgumentParser(description="Deploy Fabric Workspaces with Rollback")
    parser.add_argument("--workspaces_directory", type=str, required=True, 
                       help="Root directory containing workspace folders")
    parser.add_argument("--environment", type=str, required=True, 
                       help="Environment to use for parameter.yml (dev/test/prod)")
    parser.add_argument("--workspace_folders", type=str, required=False,
                       help="Comma-separated list of workspace folders to deploy (default: all)")
    
    args = parser.parse_args()
    
    workspaces_directory = args.workspaces_directory
    environment = args.environment
    workspace_folders_arg = args.workspace_folders
    
    # Force unbuffered output for GitHub Actions logs
    sys.stdout.reconfigure(line_buffering=True, write_through=True)
    sys.stderr.reconfigure(line_buffering=True, write_through=True)
    
    # Enable debugging if ACTIONS_RUNNER_DEBUG is set
    if os.getenv("ACTIONS_RUNNER_DEBUG", "false").lower() == "true":
        change_log_level("DEBUG")
    
    print("\n" + "="*70)
    print("FABRIC MULTI-WORKSPACE DEPLOYMENT")
    print("="*70)
    print(f"Environment: {environment.upper()}")
    print(f"Workspaces directory: {workspaces_directory}")
    print("="*70 + "\n")
    
    try:
        # Authenticate
        client_id = os.getenv("AZURE_CLIENT_ID")
        tenant_id = os.getenv("AZURE_TENANT_ID")
        client_secret = os.getenv("AZURE_CLIENT_SECRET")
        
        if client_id and tenant_id and client_secret:
            print("→ Using ClientSecretCredential for authentication")
            token_credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )
        else:
            print("→ Using DefaultAzureCredential for authentication (local development)")
            token_credential = DefaultAzureCredential()
        
        # Get workspace creation configuration from environment
        capacity_id = None
        if environment.lower() == "dev":
            capacity_id = os.getenv("FABRIC_CAPACITY_ID_DEV")
        elif environment.lower() == "test":
            capacity_id = os.getenv("FABRIC_CAPACITY_ID_TEST")
        elif environment.lower() == "prod":
            capacity_id = os.getenv("FABRIC_CAPACITY_ID_PROD")
        
        service_principal_object_id = os.getenv("DEPLOYMENT_SP_OBJECT_ID")
        entra_admin_group_id = os.getenv("FABRIC_ADMIN_GROUP_ID")
        
        # Determine which workspaces to deploy
        if workspace_folders_arg:
            workspace_folders = [f.strip() for f in workspace_folders_arg.split(",")]
            print(f"→ Deploying specified workspaces: {', '.join(workspace_folders)}\n")
        else:
            workspace_folders = get_workspace_folders(workspaces_directory)
            print(f"→ Deploying all workspaces: {', '.join(workspace_folders)}\n")
        
        if not workspace_folders:
            print("✗ ERROR: No workspace folders found to deploy")
            sys.exit(1)
        
        # Track deployment results
        deployed_workspaces: List[str] = []
        failed_deployments: List[Dict[str, str]] = []
        
        # Track deployment duration
        deployment_start_time = time.time()
        
        # Deploy each workspace (continue on failure)
        print(f"Starting deployment of {len(workspace_folders)} workspace(s)...\n")
        for i, workspace_folder in enumerate(workspace_folders, 1):
            print(f"[{i}/{len(workspace_folders)}] Processing workspace: {workspace_folder}")
            
            success, error_message = deploy_workspace(
                workspace_folder=workspace_folder,
                workspaces_dir=workspaces_directory,
                environment=environment,
                token_credential=token_credential,
                capacity_id=capacity_id,
                service_principal_object_id=service_principal_object_id,
                entra_admin_group_id=entra_admin_group_id
            )
            
            if success:
                deployed_workspaces.append(workspace_folder)
            else:
                failed_deployments.append({
                    "workspace": workspace_folder,
                    "error": error_message
                })
        
        # Calculate deployment duration
        deployment_duration = time.time() - deployment_start_time
        
        # Print comprehensive deployment summary
        print("\n" + "="*70)
        print("DEPLOYMENT SUMMARY")
        print("="*70)
        print(f"Environment: {environment.upper()}")
        print(f"Duration: {deployment_duration:.2f} seconds")
        print(f"Total workspaces: {len(workspace_folders)}")
        print(f"Successful: {len(deployed_workspaces)}")
        print(f"Failed: {len(failed_deployments)}")
        print("="*70)
        
        # Report successful deployments
        if deployed_workspaces:
            print("\n✓ SUCCESSFUL DEPLOYMENTS:")
            stage_prefix = get_stage_prefix(environment)
            for workspace in deployed_workspaces:
                print(f"  ✓ {stage_prefix}{workspace}")
        
        # Report failed deployments
        if failed_deployments:
            print("\n✗ FAILED DEPLOYMENTS:")
            for failure in failed_deployments:
                print(f"  ✗ {failure['workspace']}")
                print(f"    Error: {failure['error']}")
        
        print("\n" + "="*70)
        
        # Exit with appropriate code
        if failed_deployments:
            print(f"\nDeployment completed with {len(failed_deployments)} failure(s)\n")
            sys.exit(1)
        else:
            print(f"\nAll {len(deployed_workspaces)} workspace(s) deployed successfully!\n")
            sys.exit(0)
        
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
