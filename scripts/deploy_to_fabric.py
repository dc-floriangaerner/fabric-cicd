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
from typing import Any

import yaml
from azure.identity import ClientSecretCredential, DefaultAzureCredential
from fabric_cicd import append_feature_flag, change_log_level, deploy_with_config
from microsoft_fabric_api import FabricClient

# Import local modules using relative imports
from .deployment_config import (
    CONFIG_FILE,
    ENV_ACTIONS_RUNNER_DEBUG,
    ENV_AZURE_CLIENT_ID,
    ENV_AZURE_CLIENT_SECRET,
    ENV_AZURE_TENANT_ID,
    ENV_DEPLOYMENT_SP_OBJECT_ID,
    ENV_FABRIC_ADMIN_GROUP_ID,
    ENV_FABRIC_CAPACITY_ID,
    ENV_GITHUB_ACTIONS,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    RESULTS_FILENAME,
    SEPARATOR_LONG,
    SEPARATOR_SHORT,
    VALID_ENVIRONMENTS,
    WIKI_SETUP_GUIDE_URL,
    WIKI_TROUBLESHOOTING_URL,
)
from .fabric_workspace_manager import ensure_workspace_exists
from .logger import get_logger

# Initialize logger
logger = get_logger(__name__)


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
    results: list[DeploymentResult]

    @property
    def total_workspaces(self) -> int:
        return len(self.results)

    @property
    def successful_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.success)


def load_workspace_config(workspace_folder: str, workspaces_dir: str) -> dict[str, Any]:
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

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_workspace_name_from_config(config: dict[str, Any], environment: str) -> str:
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
        ) from None


# Alias for backwards compatibility with tests
get_workspace_name_for_environment = get_workspace_name_from_config


def get_workspace_folders(workspaces_dir: str) -> list[str]:
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
        folder.name for folder in workspaces_path.iterdir() if folder.is_dir() and (folder / CONFIG_FILE).exists()
    ]

    if not workspace_folders:
        raise ValueError(
            f"No workspace folders with '{CONFIG_FILE}' found in {workspaces_dir}. "
            "Each workspace folder must contain a config.yml file."
        )

    return sorted(workspace_folders)


def deploy_workspace(
    workspace_folder: str,
    workspaces_dir: str,
    environment: str,
    token_credential: ClientSecretCredential | DefaultAzureCredential,
    capacity_id: str | None = None,
    service_principal_object_id: str | None = None,
    entra_admin_group_id: str | None = None,
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
        logger.info(f"\n{SEPARATOR_SHORT}")
        logger.info(f"Deploying workspace: {workspace_folder}")
        logger.info(f"{SEPARATOR_SHORT}\n")

        # Load workspace config
        config = load_workspace_config(workspace_folder, workspaces_dir)
        workspace_name = get_workspace_name_from_config(config, environment)
        config_file_path = str(Path(workspaces_dir) / workspace_folder / CONFIG_FILE)

        logger.info(f"-> Target workspace: {workspace_name}")
        logger.info(f"-> Config file: {config_file_path}")
        logger.info(f"-> Environment: {environment}")

        # Create Fabric API client
        fabric_client = create_fabric_client(token_credential)

        # Ensure workspace exists (create if necessary)
        workspace_id = ensure_workspace_exists(
            workspace_name=workspace_name,
            capacity_id=capacity_id,
            service_principal_object_id=service_principal_object_id,
            entra_admin_group_id=entra_admin_group_id,
            fabric_client=fabric_client,
        )
        logger.info(f"-> Workspace ensured with ID: {workspace_id}")

        # Deploy using config.yml
        logger.info("-> Deploying items using config-based deployment...")
        deploy_with_config(
            config_file_path=config_file_path, environment=environment, token_credential=token_credential
        )

        logger.info(f"\n[OK] Deployment to {workspace_name} completed successfully!\n")
        return DeploymentResult(workspace_folder=workspace_folder, workspace_name=workspace_name, success=True)

    except Exception as e:
        error_message = str(e)
        display_name = workspace_name if workspace_name else workspace_folder
        logger.error(f"\n[FAIL] ERROR: Deployment failed for workspace '{display_name}': {error_message}\n")
        return DeploymentResult(
            workspace_folder=workspace_folder,
            workspace_name=workspace_name if workspace_name else workspace_folder,
            success=False,
            error_message=error_message,
        )


def create_azure_credential() -> ClientSecretCredential | DefaultAzureCredential:
    """Create and return the appropriate Azure credential based on environment.

    Raises:
        ValueError: If running in GitHub Actions but Service Principal secrets are not configured.
    """
    client_id = os.getenv(ENV_AZURE_CLIENT_ID)
    tenant_id = os.getenv(ENV_AZURE_TENANT_ID)
    client_secret = os.getenv(ENV_AZURE_CLIENT_SECRET)

    if client_id and tenant_id and client_secret:
        logger.info("-> Using ClientSecretCredential for authentication")
        return ClientSecretCredential(tenant_id=tenant_id, client_id=client_id, client_secret=client_secret)

    # Detect partial configuration — some vars set but not all
    provided = [v for v in [client_id, tenant_id, client_secret] if v]
    missing_vars = []
    if not client_id:
        missing_vars.append(ENV_AZURE_CLIENT_ID)
    if not tenant_id:
        missing_vars.append(ENV_AZURE_TENANT_ID)
    if not client_secret:
        missing_vars.append(ENV_AZURE_CLIENT_SECRET)

    is_ci = os.getenv(ENV_GITHUB_ACTIONS, "").lower() == "true"

    if is_ci or provided:
        # In GitHub Actions (or with partial creds): fail fast with actionable guidance
        if provided:
            hint = (
                f"The following secrets are set but incomplete — missing: {', '.join(missing_vars)}. "
                "All three must be configured together."
            )
        else:
            hint = (
                f"None of the required GitHub secrets are configured: "
                f"{ENV_AZURE_CLIENT_ID}, {ENV_AZURE_TENANT_ID}, {ENV_AZURE_CLIENT_SECRET}."
            )
        raise ValueError(
            f"{hint}\n"
            "\n"
            "  These secrets authenticate the deployment pipeline to Microsoft Fabric\n"
            "  using a Service Principal (Entra ID App Registration).\n"
            "\n"
            f"  Setup instructions : {WIKI_SETUP_GUIDE_URL}\n"
            f"  Troubleshooting    : {WIKI_TROUBLESHOOTING_URL}#clientsecretcredential-authentication-failed\n"
        )

    # Local development fallback — no CI env, no creds set
    logger.info("-> Using DefaultAzureCredential for authentication (local development)")
    return DefaultAzureCredential()


def create_fabric_client(token_credential: ClientSecretCredential | DefaultAzureCredential) -> FabricClient:
    """Create and return Microsoft Fabric API client.

    Args:
        token_credential: Azure credential for authentication

    Returns:
        Initialized FabricClient instance
    """
    return FabricClient(token_credential=token_credential)


def discover_workspace_folders(workspaces_directory: str) -> list[str]:
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
    logger.info(f"-> Discovered {len(workspace_folders)} workspace(s): {', '.join(workspace_folders)}\n")
    return workspace_folders


def build_deployment_results_json(summary: DeploymentSummary) -> dict[str, Any]:
    """Build the deployment results dictionary for JSON output.

    Args:
        summary: Deployment summary object

    Returns:
        Dictionary containing deployment results for JSON serialization
    """
    workspaces_list: list[dict[str, Any]] = []

    # Add all workspace results
    for result in summary.results:
        workspaces_list.append(
            {
                "name": result.workspace_folder,
                "full_name": result.workspace_name,
                "status": "success" if result.success else "failure",
                "error": result.error_message,
            }
        )

    # Sort workspaces by name for consistent output
    workspaces_list.sort(key=lambda x: x["name"])

    results_json = {
        "environment": summary.environment,
        "duration": summary.duration,
        "total_workspaces": summary.total_workspaces,
        "successful_count": summary.successful_count,
        "failed_count": summary.failed_count,
        "workspaces": workspaces_list,
    }

    return results_json


def print_deployment_summary(summary: DeploymentSummary) -> None:
    """Print comprehensive deployment summary to console.

    Args:
        summary: Deployment summary containing all results and metrics
    """
    logger.info(f"\n{SEPARATOR_LONG}")
    logger.info("DEPLOYMENT SUMMARY")
    logger.info(SEPARATOR_LONG)
    logger.info(f"Environment: {summary.environment.upper()}")
    logger.info(f"Duration: {summary.duration:.2f} seconds")
    logger.info(f"Total workspaces: {summary.total_workspaces}")
    logger.info(f"Successful: {summary.successful_count}")
    logger.info(f"Failed: {summary.failed_count}")
    logger.info(SEPARATOR_LONG)

    # Report successful and failed deployments by iterating through results once
    successful = []
    failed = []
    for result in summary.results:
        if result.success:
            successful.append(result.workspace_name)
        else:
            failed.append((result.workspace_name, result.error_message))

    if successful:
        logger.info("\n[OK] SUCCESSFUL DEPLOYMENTS:")
        for full_name in successful:
            logger.info(f"  [OK] {full_name}")

    if failed:
        logger.error("\n[FAIL] FAILED DEPLOYMENTS:")
        for full_name, error in failed:
            logger.error(f"  [FAIL] {full_name}")
            logger.error(f"    Error: {error}")

    logger.info(f"\n{SEPARATOR_LONG}")


def validate_environment(environment: str) -> None:
    """Validate that the environment is one of the expected values.

    Args:
        environment: Environment name to validate

    Raises:
        ValueError: If environment is not valid
    """
    if environment.lower() not in VALID_ENVIRONMENTS:
        raise ValueError(
            f"Invalid environment '{environment}'. Must be one of: {', '.join(sorted(VALID_ENVIRONMENTS))}"
        )


def deploy_all_workspaces(
    workspace_folders: list[str],
    workspaces_directory: str,
    environment: str,
    token_credential: ClientSecretCredential | DefaultAzureCredential,
    capacity_id: str | None,
    service_principal_object_id: str | None,
    entra_admin_group_id: str | None,
) -> list[DeploymentResult]:
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
    results: list[DeploymentResult] = []

    logger.info(f"Starting deployment of {len(workspace_folders)} workspace(s)...\n")
    for i, workspace_folder in enumerate(workspace_folders, 1):
        logger.info(f"[{i}/{len(workspace_folders)}] Processing workspace: {workspace_folder}")

        result = deploy_workspace(
            workspace_folder=workspace_folder,
            workspaces_dir=workspaces_directory,
            environment=environment,
            token_credential=token_credential,
            capacity_id=capacity_id,
            service_principal_object_id=service_principal_object_id,
            entra_admin_group_id=entra_admin_group_id,
        )

        results.append(result)

    return results


def main():
    """Main deployment orchestration."""
    # Enable experimental features for config-based deployment
    append_feature_flag("enable_experimental_features")
    append_feature_flag("enable_config_deploy")

    # Parse arguments from GitHub Actions workflow
    parser = argparse.ArgumentParser(description="Deploy Fabric Workspaces - Auto-discovers all workspace folders")
    parser.add_argument(
        "--workspaces_directory", type=str, required=True, help="Root directory containing workspace folders"
    )
    parser.add_argument(
        "--environment",
        type=str,
        required=True,
        choices=list(VALID_ENVIRONMENTS),
        help="Target environment (dev/test/prod)",
    )

    args = parser.parse_args()

    workspaces_directory = args.workspaces_directory
    environment = args.environment

    # Force unbuffered output for GitHub Actions logs
    sys.stdout.reconfigure(line_buffering=True, write_through=True)
    sys.stderr.reconfigure(line_buffering=True, write_through=True)

    # Enable debugging if ACTIONS_RUNNER_DEBUG is set
    # Note: This only affects fabric_cicd library logging.
    # Local script logger (from logger.py) remains at INFO level.
    if os.getenv(ENV_ACTIONS_RUNNER_DEBUG, "false").lower() == "true":
        change_log_level("DEBUG")

    logger.info(f"\n{SEPARATOR_LONG}")
    logger.info("FABRIC MULTI-WORKSPACE DEPLOYMENT")
    logger.info(SEPARATOR_LONG)
    logger.info(f"Environment: {environment.upper()}")
    logger.info(f"Workspaces directory: {workspaces_directory}")
    logger.info(f"{SEPARATOR_LONG}\n")

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
            entra_admin_group_id=entra_admin_group_id,
        )

        # Calculate deployment duration
        deployment_duration = time.time() - deployment_start_time

        # Create deployment summary
        summary = DeploymentSummary(environment=environment, duration=deployment_duration, results=results)

        # Write deployment results to JSON file for GitHub Actions summary
        deployment_results_json = build_deployment_results_json(summary)
        with open(RESULTS_FILENAME, "w", encoding="utf-8") as f:
            json.dump(deployment_results_json, f, indent=2)
        logger.info(f"\n-> Deployment results written to {RESULTS_FILENAME}")

        # Print comprehensive deployment summary
        print_deployment_summary(summary)

        # Exit with appropriate code
        if summary.failed_count > 0:
            logger.warning(f"\nDeployment completed with {summary.failed_count} failure(s)\n")
            sys.exit(EXIT_FAILURE)
        else:
            logger.info(f"\nAll {summary.successful_count} workspace(s) deployed successfully!\n")
            sys.exit(EXIT_SUCCESS)

    except (ValueError, FileNotFoundError) as e:
        logger.error(f"\n[FAIL] VALIDATION ERROR: {e!s}\n")
        sys.exit(EXIT_FAILURE)
    except Exception as e:
        logger.error(f"\n[FAIL] CRITICAL ERROR: {e!s}\n")
        sys.exit(EXIT_FAILURE)


if __name__ == "__main__":
    main()
