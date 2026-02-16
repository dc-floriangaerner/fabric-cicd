# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Deploy workspaces to Fabric via GitHub Actions with continue-on-failure support"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional, Union, Any

from azure.identity import ClientSecretCredential, DefaultAzureCredential
from microsoft_fabric_api import FabricClient
from fabric_cicd import deploy_with_config, change_log_level, append_feature_flag
import yaml

# Import local modules using relative imports
from .fabric_workspace_manager import ensure_workspace_exists

# Import configuration constants
from .deployment_config import (
    VALID_ENVIRONMENTS,
    SEPARATOR_LONG,
    SEPARATOR_SHORT,
    RESULTS_FILENAME,
    CONFIG_FILE,
    EXIT_SUCCESS,
    EXIT_FAILURE,
    ENV_AZURE_CLIENT_ID,
    ENV_AZURE_TENANT_ID,
    ENV_AZURE_CLIENT_SECRET,
    ENV_FABRIC_CAPACITY_ID,
    ENV_DEPLOYMENT_SP_OBJECT_ID,
    ENV_FABRIC_ADMIN_GROUP_ID,
    ENV_ACTIONS_RUNNER_DEBUG
)


@dataclass
class DeploymentResult:
    """Result of a single workspace deployment."""
    workspace_folder: str
    workspace_name: str
    success: bool
    error_message: str = ""


@dataclass
class DeploymentSummary:
    """Summary of all workspace deployments."""
    environment: str
    duration: float
    results: List[DeploymentResult]
    
    @property
    def total_workspaces(self) -> int:
        return len(self.results)
    
    @property
    def successful_count(self) -> int:
        return sum(1 for r in self.results if r.success)
    
    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.success)


def load_workspace_config(workspace_folder: str, workspaces_dir: str) -> Dict[str, Any]:
    """Load config.yml for a workspace.
    
    Args:
        workspace_folder: Name of workspace folder
        workspaces_dir: Root workspaces directory
        
    Returns:
        Parsed config dictionary
        
    Raises:
        FileNotFoundError: If config.yml doesn't exist
        yaml.YAMLError: If config.yml is invalid
    """
    config_path = Path(workspaces_dir) / workspace_folder / CONFIG_FILE
    if not config_path.exists():
        raise FileNotFoundError(f"{CONFIG_FILE} not found in {workspace_folder}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    return config


def get_workspace_name_from_config(
    config: Dict[str, Any], 
    environment: str
) -> str:
    """Extract workspace name for environment from config.
    
    Args:
        config: Parsed config.yml dictionary
        environment: Target environment (dev/test/prod)
        
    Returns:
        Workspace name for environment
        
    Raises:
        KeyError: If environment not defined in config
    """
    try:
        workspace_name = config["core"]["workspace"][environment]
        return workspace_name
    except KeyError:
        raise KeyError(
            f"Workspace name for environment '{environment}' not found in config.yml. "
            f"Expected: core.workspace.{environment}"
        )


def get_workspace_folders(workspaces_dir: str) -> List[str]:
    """Get all workspace folders from the workspaces directory.
    
    Args:
        workspaces_dir: Root directory containing workspace folders
        
    Returns:
        Sorted list of workspace folder names that contain config.yml
        
    Raises:
        FileNotFoundError: If workspaces directory doesn't exist
    """
    workspaces_path = Path(workspaces_dir)
    if not workspaces_path.exists():
        raise FileNotFoundError(f"Workspaces directory not found: {workspaces_dir}")
    
    workspace_folders = [
        folder.name for folder in workspaces_path.iterdir() 
        if folder.is_dir() and (folder / CONFIG_FILE).exists()
    ]
    
    if not workspace_folders:
        raise ValueError(f"No workspace folders with {CONFIG_FILE} found in: {workspaces_dir}")
    
    return sorted(workspace_folders)


def deploy_workspace(
    workspace_folder: str,
    workspaces_dir: str,
    environment: str,
    token_credential: Union[ClientSecretCredential, DefaultAzureCredential],
    capacity_id: Optional[str] = None,
    service_principal_object_id: Optional[str] = None,
    entra_admin_group_id: Optional[str] = None
) -> DeploymentResult:
    """Deploy a single workspace using config.yml.
    
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
        DeploymentResult object with success status and error message if applicable.
    """
    workspace_name = ""  # Initialize for error handling
    try:
        print(f"\n{SEPARATOR_SHORT}")
        print(f"Deploying workspace: {workspace_folder}")
        print(f"{SEPARATOR_SHORT}\n")
        
        # Load workspace config
        config = load_workspace_config(workspace_folder, workspaces_dir)
        workspace_name = get_workspace_name_from_config(config, environment)
        config_file_path = str(Path(workspaces_dir) / workspace_folder / CONFIG_FILE)
        
        print(f"→ Target workspace: {workspace_name}")
        print(f"→ Config file: {config_file_path}")
        print(f"→ Environment: {environment}")
        
        # Create Fabric API client
        fabric_client = create_fabric_client(token_credential)
        
        # Ensure workspace exists (create if necessary)
        workspace_id = ensure_workspace_exists(
            workspace_name=workspace_name,
            capacity_id=capacity_id,
            service_principal_object_id=service_principal_object_id,
            fabric_client=fabric_client,
            entra_admin_group_id=entra_admin_group_id
        )
        print(f"→ Workspace ensured with ID: {workspace_id}")
        
        # Deploy using config.yml
        print(f"→ Deploying items using config-based deployment...")
        deploy_with_config(
            config_file_path=config_file_path,
            environment=environment,
            token_credential=token_credential
        )
        
        print(f"\n✓ Deployment to {workspace_name} completed successfully!\n")
        return DeploymentResult(
            workspace_folder=workspace_folder,
            workspace_name=workspace_name,
            success=True
        )
        
    except Exception as e:
        error_message = str(e)
        display_name = workspace_name if workspace_name else workspace_folder
        print(f"\n✗ ERROR: Deployment failed for workspace '{display_name}': {error_message}\n")
        return DeploymentResult(
            workspace_folder=workspace_folder,
            workspace_name=workspace_name if workspace_name else workspace_folder,
            success=False,
            error_message=error_message
        )


def create_azure_credential() -> Union[ClientSecretCredential, DefaultAzureCredential]:
    """Create and return the appropriate Azure credential based on environment."""
    client_id = os.getenv(ENV_AZURE_CLIENT_ID)
    tenant_id = os.getenv(ENV_AZURE_TENANT_ID)
    client_secret = os.getenv(ENV_AZURE_CLIENT_SECRET)
    
    if client_id and tenant_id and client_secret:
        print("→ Using ClientSecretCredential for authentication")
        return ClientSecretCredential(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret
        )
    else:
        print("→ Using DefaultAzureCredential for authentication (local development)")
        return DefaultAzureCredential()


def create_fabric_client(token_credential: Union[ClientSecretCredential, DefaultAzureCredential]) -> FabricClient:
    """Create and return Microsoft Fabric API client.
    
    Args:
        token_credential: Azure credential for authentication
        
    Returns:
        Initialized FabricClient instance
    """
    return FabricClient(token_credential=token_credential)


def discover_workspace_folders(workspaces_directory: str) -> List[str]:
    """Discover and return all workspace folders to deploy.
    
    Automatically discovers all workspace folders in the workspaces directory
    that contain a config.yml file.
    
    Args:
        workspaces_directory: Root directory containing workspace folders
        
    Returns:
        Sorted list of workspace folder names to deploy
        
    Raises:
        ValueError: If no workspace folders are found
        FileNotFoundError: If workspaces directory doesn't exist
    """
    workspace_folders = get_workspace_folders(workspaces_directory)
    print(f"→ Discovered {len(workspace_folders)} workspace(s): {', '.join(workspace_folders)}\n")
    return workspace_folders


def build_deployment_results_json(summary: DeploymentSummary) -> Dict[str, Any]:
    """Build the deployment results dictionary for JSON output.
    
    Args:
        summary: Deployment summary object
        
    Returns:
        Dictionary containing deployment results for JSON serialization
    """
    results_json = {
        "environment": summary.environment,
        "duration": summary.duration,
        "total_workspaces": summary.total_workspaces,
        "successful_count": summary.successful_count,
        "failed_count": summary.failed_count,
        "workspaces": []
    }
    
    # Add all workspace results
    for result in summary.results:
        results_json["workspaces"].append({
            "name": result.workspace_folder,
            "full_name": result.workspace_name,
            "status": "success" if result.success else "failure",
            "error": result.error_message
        })
    
    # Sort workspaces by name for consistent output
    results_json["workspaces"].sort(key=lambda x: x["name"])
    
    return results_json


def print_deployment_summary(summary: DeploymentSummary) -> None:
    """Print comprehensive deployment summary to console.
    
    Args:
        summary: Deployment summary containing all results and metrics
    """
    print(f"\n{SEPARATOR_LONG}")
    print("DEPLOYMENT SUMMARY")
    print(SEPARATOR_LONG)
    print(f"Environment: {summary.environment.upper()}")
    print(f"Duration: {summary.duration:.2f} seconds")
    print(f"Total workspaces: {summary.total_workspaces}")
    print(f"Successful: {summary.successful_count}")
    print(f"Failed: {summary.failed_count}")
    print(SEPARATOR_LONG)
    
    # Report successful and failed deployments by iterating through results once
    successful = []
    failed = []
    for result in summary.results:
        if result.success:
            successful.append(result.workspace_name)
        else:
            failed.append((result.workspace_name, result.error_message))
    
    if successful:
        print("\n✓ SUCCESSFUL DEPLOYMENTS:")
        for full_name in successful:
            print(f"  ✓ {full_name}")
    
    if failed:
        print("\n✗ FAILED DEPLOYMENTS:")
        for full_name, error in failed:
            print(f"  ✗ {full_name}")
            print(f"    Error: {error}")
    
    print(f"\n{SEPARATOR_LONG}")


def validate_environment(environment: str) -> None:
    """Validate that the environment is one of the expected values.
    
    Args:
        environment: Environment name to validate
        
    Raises:
        ValueError: If environment is not valid
    """
    if environment.lower() not in VALID_ENVIRONMENTS:
        raise ValueError(
            f"Invalid environment '{environment}'. "
            f"Must be one of: {', '.join(sorted(VALID_ENVIRONMENTS))}"
        )


def deploy_all_workspaces(
    workspace_folders: List[str],
    workspaces_directory: str,
    environment: str,
    token_credential: Union[ClientSecretCredential, DefaultAzureCredential],
    capacity_id: Optional[str],
    service_principal_object_id: Optional[str],
    entra_admin_group_id: Optional[str]
) -> List[DeploymentResult]:
    """Deploy all specified workspaces and return results.
    
    Args:
        workspace_folders: List of workspace folder names to deploy
        workspaces_directory: Root directory containing workspace folders
        environment: Target environment (dev/test/prod)
        token_credential: Azure credential for authentication
        capacity_id: Optional Fabric workspace capacity ID for creation
        service_principal_object_id: Optional service principal object ID for role assignment
        entra_admin_group_id: Optional Entra ID group ID for admin permissions
        
    Returns:
        List of DeploymentResult objects, one per workspace
    """
    results: List[DeploymentResult] = []
    
    print(f"Starting deployment of {len(workspace_folders)} workspace(s)...\n")
    for i, workspace_folder in enumerate(workspace_folders, 1):
        print(f"[{i}/{len(workspace_folders)}] Processing workspace: {workspace_folder}")
        
        result = deploy_workspace(
            workspace_folder=workspace_folder,
            workspaces_dir=workspaces_directory,
            environment=environment,
            token_credential=token_credential,
            capacity_id=capacity_id,
            service_principal_object_id=service_principal_object_id,
            entra_admin_group_id=entra_admin_group_id
        )
        
        results.append(result)
    
    return results


def main():
    """Main deployment orchestration."""
    # Enable experimental features for config-based deployment
    append_feature_flag("enable_experimental_features")
    append_feature_flag("enable_config_deploy")
    
    # Parse arguments from GitHub Actions workflow
    parser = argparse.ArgumentParser(
        description="Deploy Fabric Workspaces - Auto-discovers all workspace folders"
    )
    parser.add_argument(
        "--workspaces_directory",
        type=str,
        required=True,
        help="Root directory containing workspace folders"
    )
    parser.add_argument(
        "--environment",
        type=str,
        required=True,
        choices=list(VALID_ENVIRONMENTS),
        help="Target environment (dev/test/prod)"
    )
    
    args = parser.parse_args()
    
    workspaces_directory = args.workspaces_directory
    environment = args.environment
    
    # Force unbuffered output for GitHub Actions logs
    sys.stdout.reconfigure(line_buffering=True, write_through=True)
    sys.stderr.reconfigure(line_buffering=True, write_through=True)
    
    # Enable debugging if ACTIONS_RUNNER_DEBUG is set
    if os.getenv(ENV_ACTIONS_RUNNER_DEBUG, "false").lower() == "true":
        change_log_level("DEBUG")
    
    print(f"\n{SEPARATOR_LONG}")
    print("FABRIC MULTI-WORKSPACE DEPLOYMENT")
    print(SEPARATOR_LONG)
    print(f"Environment: {environment.upper()}")
    print(f"Workspaces directory: {workspaces_directory}")
    print(f"{SEPARATOR_LONG}\n")
    
    try:
        # Validate environment
        validate_environment(environment)
        
        # Authenticate
        token_credential = create_azure_credential()
        
        # Get workspace creation configuration from environment
        capacity_id = os.getenv(ENV_FABRIC_CAPACITY_ID)
        service_principal_object_id = os.getenv(ENV_DEPLOYMENT_SP_OBJECT_ID)
        entra_admin_group_id = os.getenv(ENV_FABRIC_ADMIN_GROUP_ID)
        
        # Auto-discover all workspace folders
        workspace_folders = discover_workspace_folders(workspaces_directory)
        
        # Track deployment duration
        deployment_start_time = time.time()
        
        # Deploy all workspaces
        results = deploy_all_workspaces(
            workspace_folders=workspace_folders,
            workspaces_directory=workspaces_directory,
            environment=environment,
            token_credential=token_credential,
            capacity_id=capacity_id,
            service_principal_object_id=service_principal_object_id,
            entra_admin_group_id=entra_admin_group_id
        )
        
        # Calculate deployment duration
        deployment_duration = time.time() - deployment_start_time
        
        # Create deployment summary
        summary = DeploymentSummary(
            environment=environment,
            duration=deployment_duration,
            results=results
        )
        
        # Write deployment results to JSON file for GitHub Actions summary
        deployment_results_json = build_deployment_results_json(summary)
        with open(RESULTS_FILENAME, "w", encoding="utf-8") as f:
            json.dump(deployment_results_json, f, indent=2)
        print(f"\n→ Deployment results written to {RESULTS_FILENAME}")
        
        # Print comprehensive deployment summary
        print_deployment_summary(summary)
        
        # Exit with appropriate code
        if summary.failed_count > 0:
            print(f"\nDeployment completed with {summary.failed_count} failure(s)\n")
            sys.exit(EXIT_FAILURE)
        else:
            print(f"\nAll {summary.successful_count} workspace(s) deployed successfully!\n")
            sys.exit(EXIT_SUCCESS)
        
    except (ValueError, FileNotFoundError) as e:
        print(f"\n✗ VALIDATION ERROR: {str(e)}\n")
        sys.exit(EXIT_FAILURE)
    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {str(e)}\n")
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
