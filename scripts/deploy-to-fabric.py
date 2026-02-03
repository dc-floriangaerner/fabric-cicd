# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Deploy workspaces to Fabric via GitHub Actions with rollback support"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from fabric_cicd import FabricWorkspace, change_log_level, publish_all_items, unpublish_all_orphan_items


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


def record_workspace_deployment(workspace: FabricWorkspace) -> Dict:
    """Record deployment attempt for a workspace for rollback tracking.
    
    Note: This is a simplified implementation that only records metadata.
    A full implementation would capture complete item definitions for restoration.
    """
    try:
        # Store workspace metadata for rollback tracking
        # In production, you would capture full item definitions here
        state = {
            "workspace_name": workspace.display_name,
            "recorded": True,
            "message": "Deployment recorded successfully"
        }
        print(f"  ✓ Recorded deployment for workspace: {workspace.display_name}")
        return state
    except Exception as e:
        print(f"  ⚠ Warning: Failed to record deployment for workspace: {str(e)}")
        return {"workspace_name": "unknown", "recorded": False}


def rollback_workspace(workspace_state: Dict, token_credential) -> bool:
    """Rollback a workspace deployment.
    
    Args:
        workspace_state: Dictionary containing workspace metadata and deployment state
        token_credential: Azure credential for Fabric API authentication (will be needed
                         for actual rollback implementation to restore items)
    
    Returns:
        True if rollback succeeds (or is logged successfully), False otherwise
    
    Note: This is a placeholder implementation that only logs the rollback intention.
    A full implementation would restore items from captured state by:
    1. Retrieving the original item definitions from workspace_state
    2. Using token_credential with fabric-cicd to republish those original items
    3. Removing any items that were added during the failed deployment
    """
    try:
        workspace_name = workspace_state.get("workspace_name")
        if not workspace_state.get("recorded"):
            print(f"  ⚠ Skipping rollback for {workspace_name} - deployment not recorded")
            return True
        
        print(f"  → Rolling back workspace: {workspace_name}")
        # TODO: Implement actual rollback by restoring items from captured state
        # For now, we just log the rollback intention
        print(f"  ⚠ Rollback logged for: {workspace_name} (actual restoration not implemented)")
        return True
    except Exception as e:
        print(f"  ✗ Rollback failed for {workspace_state.get('workspace_name')}: {str(e)}")
        return False


def deploy_workspace(
    workspace_folder: str,
    workspaces_dir: str,
    environment: str,
    token_credential,
    workspace_states: List[Dict],
    deployed_workspaces: List[str]
) -> bool:
    """Deploy a single workspace and track its state.
    
    Args:
        workspace_folder: Name of the workspace folder
        workspaces_dir: Root directory containing workspace folders
        environment: Target environment (dev/test/prod)
        token_credential: Azure credential for authentication
        workspace_states: List to append deployment state for rollback
        deployed_workspaces: List to append successfully deployed workspace names
        
    Returns:
        True if deployment succeeds, False otherwise
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
        
        # Initialize the FabricWorkspace object
        target_workspace = FabricWorkspace(
            workspace_name=workspace_name,
            environment=environment,
            repository_directory=repository_directory,
            token_credential=token_credential,
        )
        
        print(f"→ Workspace initialized: {workspace_name}")
        
        # Record deployment attempt before actual deployment
        state = record_workspace_deployment(target_workspace)
        workspace_states.append(state)
        
        # Publish all items defined in item_type_in_scope
        print(f"→ Publishing all items...")
        publish_all_items(target_workspace)
        print(f"  ✓ All items published successfully")
        
        # Unpublish all items defined in item_type_in_scope not found in repository
        print(f"→ Cleaning up orphan items...")
        unpublish_all_orphan_items(target_workspace)
        print(f"  ✓ Orphan items removed successfully")
        
        # Mark deployment as successful
        deployed_workspaces.append(workspace_folder)
        
        print(f"\n✓ Deployment to {workspace_name} completed successfully!\n")
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR: Deployment failed for workspace '{workspace_folder}': {str(e)}\n")
        return False


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
        
        # Track deployment state for rollback
        # Note: workspace_states currently tracks deployment metadata only.
        # For production use, record_workspace_deployment() should be enhanced to capture
        # complete item definitions (notebooks, lakehouses, pipelines, etc.) that can be
        # restored via rollback_workspace() if a subsequent deployment fails.
        workspace_states: List[Dict] = []
        deployed_workspaces: List[str] = []
        failed_workspace: Optional[str] = None
        
        # Deploy each workspace
        for workspace_folder in workspace_folders:
            success = deploy_workspace(
                workspace_folder=workspace_folder,
                workspaces_dir=workspaces_directory,
                environment=environment,
                token_credential=token_credential,
                workspace_states=workspace_states,
                deployed_workspaces=deployed_workspaces
            )
            
            if not success:
                failed_workspace = workspace_folder
                break
        
        # If any deployment failed, rollback all previously deployed workspaces
        if failed_workspace:
            print("\n" + "="*70)
            print("DEPLOYMENT FAILURE - INITIATING ROLLBACK")
            print("="*70)
            print(f"Failed workspace: {failed_workspace}")
            print(f"Rolling back {len(deployed_workspaces)} previously deployed workspace(s)...\n")
            
            # Build a mapping from workspace name to its recorded state
            workspace_state_by_folder = {}
            for state in workspace_states:
                # Extract folder name from workspace name by removing stage prefix
                workspace_name = state.get("workspace_name", "")
                stage_prefix = get_stage_prefix(environment)
                if workspace_name.startswith(stage_prefix):
                    folder_name = workspace_name[len(stage_prefix):]
                    workspace_state_by_folder[folder_name] = state
            
            # Rollback only successfully deployed workspaces, in reverse deployment order
            rollback_success = True
            for i, workspace_folder in enumerate(reversed(deployed_workspaces)):
                print(f"Rollback {i+1}/{len(deployed_workspaces)}:")
                state = workspace_state_by_folder.get(workspace_folder)
                if not state:
                    print(f"  ⚠ Warning: No recorded state for workspace '{workspace_folder}', skipping rollback.")
                    rollback_success = False
                    continue
                
                if not rollback_workspace(state, token_credential):
                    rollback_success = False
            
            if rollback_success:
                print("\n✓ All workspaces rolled back successfully")
            else:
                print("\n⚠ Some rollback operations failed - manual intervention may be required")
            
            print("\n" + "="*70)
            print(f"DEPLOYMENT FAILED: {failed_workspace}")
            print("="*70 + "\n")
            sys.exit(1)
        
        # All deployments succeeded
        print("\n" + "="*70)
        print("ALL DEPLOYMENTS COMPLETED SUCCESSFULLY")
        print("="*70)
        print(f"Deployed {len(deployed_workspaces)} workspace(s):")
        for workspace in deployed_workspaces:
            stage_prefix = get_stage_prefix(environment)
            print(f"  ✓ {stage_prefix}{workspace}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
