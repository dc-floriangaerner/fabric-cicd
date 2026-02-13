# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Fabric workspace management utilities for auto-creating workspaces and managing permissions."""

from typing import Optional, Literal
from microsoft_fabric_api import FabricClient
from microsoft_fabric_api.generated.core.models import (
    CreateWorkspaceRequest,
    AddWorkspaceRoleAssignmentRequest
)
from azure.core.exceptions import HttpResponseError


def check_workspace_exists(workspace_name: str, fabric_client: FabricClient) -> Optional[str]:
    """Check if a workspace with the given name exists using SDK.
    
    Args:
        workspace_name: Name of the workspace to check (e.g., "[D] Fabric Blueprint")
        fabric_client: Microsoft Fabric API client
        
    Returns:
        Workspace ID if exists, None if not found
        
    Raises:
        Exception: If API call fails
    """
    try:
        workspaces = list(fabric_client.core.workspaces.list_workspaces())
        
        for workspace in workspaces:
            if workspace.display_name == workspace_name:
                print(f"  ✓ Workspace '{workspace_name}' already exists (ID: {workspace.id})")
                return workspace.id
        
        return None
    except HttpResponseError as e:
        raise Exception(f"Failed to list workspaces: {e.message}")


def create_workspace(workspace_name: str, capacity_id: str, fabric_client: FabricClient) -> str:
    """Create a new Fabric workspace with the specified capacity using SDK.
    
    Args:
        workspace_name: Display name for the new workspace
        capacity_id: Fabric capacity ID (GUID) - mandatory
        fabric_client: Microsoft Fabric API client
        
    Returns:
        Workspace ID of the newly created workspace
        
    Raises:
        Exception: If workspace creation fails
    """
    if not capacity_id:
        raise Exception(
            "Capacity ID is required to auto-create a Fabric workspace. "
            f"Either manually create a workspace named '{workspace_name}' in Fabric, "
            "or set the appropriate FABRIC_CAPACITY_ID_* secret in GitHub to enable auto-creation."
        )
    
    print(f"  → Creating workspace '{workspace_name}' with capacity '{capacity_id}'...")
    
    try:
        request = CreateWorkspaceRequest(
            display_name=workspace_name,
            capacity_id=capacity_id
        )
        response = fabric_client.core.workspaces.create_workspace(request)
        
        if not response.id:
            raise Exception(
                "Workspace creation succeeded but response did not contain a valid 'id' field. "
                "Inspect Fabric API response for details."
            )
        
        print(f"  ✓ Workspace created successfully (ID: {response.id})")
        return response.id
        
    except HttpResponseError as e:
        if e.status_code == 400:
            raise Exception(f"Invalid workspace creation request: {e.message}")
        elif e.status_code == 403:
            raise Exception(
                "Service Principal lacks workspace creation permissions.\n\n"
                "Possible causes:\n"
                "1. Missing tenant setting: In Fabric Admin Portal → Tenant Settings → Developer Settings, "
                "enable 'Service principals can create workspaces, connections, and deployment pipelines'\n"
                "2. Missing capacity admin role: In Azure Portal → Fabric Capacity → Settings → Capacity administrators, "
                "add the Service Principal (by Client ID or Enterprise Application Object ID)"
            )
        elif e.status_code == 404:
            raise Exception(f"Invalid capacity ID '{capacity_id}'. Verify FABRIC_CAPACITY_ID_* secret is correct.")
        else:
            raise Exception(f"Workspace creation failed: {e.message}")


def check_role_assignment_exists(
    workspace_id: str,
    principal_id: str,
    role: str,
    fabric_client: FabricClient
) -> bool:
    """Check if a role assignment already exists for a principal in a workspace.
    
    Args:
        workspace_id: GUID of the workspace
        principal_id: Azure AD Object ID of the principal
        role: Role to check (typically "Admin")
        fabric_client: Microsoft Fabric API client
        
    Returns:
        True if the role assignment exists, False otherwise
        
    Raises:
        Exception: If API call fails
    """
    try:
        assignments = list(fabric_client.core.workspaces.list_workspace_role_assignments(workspace_id))
        
        for assignment in assignments:
            if assignment.principal.id == principal_id and assignment.role == role:
                return True
        
        return False
    except HttpResponseError as e:
        raise Exception(f"Failed to list workspace role assignments: {e.message}")


def _assign_workspace_role(
    workspace_id: str,
    principal_id: str,
    principal_type: Literal["ServicePrincipal", "Group"],
    role: str,
    fabric_client: FabricClient,
    principal_description: str
) -> None:
    """Internal helper to assign a role to a principal using SDK.
    
    Proactively checks if the role assignment exists before attempting to add it,
    avoiding unnecessary API calls and brittle error message parsing.
    
    Args:
        workspace_id: GUID of the workspace
        principal_id: Azure AD Object ID of the principal
        principal_type: Type of principal ("ServicePrincipal" or "Group")
        role: Role to assign (typically "Admin")
        fabric_client: Microsoft Fabric API client
        principal_description: Human-readable description for logging
        
    Raises:
        Exception: If role assignment fails
    """
    if not principal_id:
        if principal_description == "Entra ID group":
            print(f"  ℹ No {principal_description} configured. Skipping role assignment.")
        else:
            print(f"  ⚠ WARNING: {principal_description} ID not set. Skipping role assignment.")
        return
    
    # Proactively check if the role assignment already exists
    print(f"  → Checking {principal_description} {role} access...")
    if check_role_assignment_exists(workspace_id, principal_id, role, fabric_client):
        print(f"  ✓ {principal_description} already has {role} access (verified)")
        return
    
    # Role doesn't exist, add it
    print(f"  → Granting {principal_description} {role} access...")
    
    try:
        request = AddWorkspaceRoleAssignmentRequest(
            principal={
                "id": principal_id,
                "type": principal_type
            },
            role=role
        )
        fabric_client.core.workspaces.add_workspace_role_assignment(
            workspace_id=workspace_id,
            workspace_role_assignment_request=request
        )
        print(f"  ✓ {principal_description} granted {role} access successfully")
        
    except HttpResponseError as e:
        if e.status_code == 404:
            principal_type_hint = "Service Principal Object ID (not Client ID)" if principal_type == "ServicePrincipal" else "Entra ID group Object ID"
            raise Exception(
                f"Invalid {principal_description} Object ID '{principal_id}'. "
                f"Verify the secret contains a valid {principal_type_hint}. "
                "Find it in Azure Portal → Azure Active Directory."
            )
        else:
            raise Exception(f"{principal_description} role assignment failed: {e.message}")


def add_workspace_admin(workspace_id: str, service_principal_object_id: str, fabric_client: FabricClient) -> None:
    """Add a service principal as admin to a workspace using SDK.
    
    Args:
        workspace_id: GUID of the workspace
        service_principal_object_id: Azure AD Object ID of the service principal (NOT Client ID)
        fabric_client: Microsoft Fabric API client
        
    Raises:
        Exception: If role assignment fails
    """
    _assign_workspace_role(
        workspace_id=workspace_id,
        principal_id=service_principal_object_id,
        principal_type="ServicePrincipal",
        role="Admin",
        fabric_client=fabric_client,
        principal_description="Service Principal"
    )


def add_entra_id_group_admin(workspace_id: str, entra_group_id: str, fabric_client: FabricClient) -> None:
    """Add an Entra ID (Azure AD) group as admin to a workspace using SDK.
    
    Args:
        workspace_id: GUID of the workspace
        entra_group_id: Azure AD Object ID of the Entra ID group
        fabric_client: Microsoft Fabric API client
        
    Raises:
        Exception: If role assignment fails
    """
    _assign_workspace_role(
        workspace_id=workspace_id,
        principal_id=entra_group_id,
        principal_type="Group",
        role="Admin",
        fabric_client=fabric_client,
        principal_description="Entra ID group"
    )


def ensure_workspace_exists(
    workspace_name: str,
    capacity_id: str,
    service_principal_object_id: str,
    fabric_client: FabricClient,
    entra_admin_group_id: Optional[str] = None
) -> str:
    """Ensure workspace exists using SDK, creating it if necessary.
    
    This is the main entry point for workspace management. It checks if the workspace
    exists, creates it if needed, and ensures the service principal and Entra ID admin
    group (if configured) have admin access.
    
    Args:
        workspace_name: Display name of the workspace (e.g., "[D] Fabric Blueprint")
        capacity_id: Fabric capacity ID for the environment
        service_principal_object_id: Azure AD Object ID of the deployment service principal
        fabric_client: Microsoft Fabric API client
        entra_admin_group_id: Optional Azure AD Object ID of Entra ID group for admin access
        
    Returns:
        Workspace ID (either existing or newly created)
        
    Raises:
        Exception: If workspace cannot be created or accessed
    """
    try:
        print(f"→ Ensuring workspace '{workspace_name}' exists...")
        
        workspace_id = check_workspace_exists(workspace_name, fabric_client)
        
        if workspace_id:
            print(f"  ℹ Workspace already exists, ensuring admin access...")
        else:
            print(f"  ℹ Workspace not found, creating new workspace...")
            workspace_id = create_workspace(workspace_name, capacity_id, fabric_client)
        
        # Ensure access for service principal and admin group
        add_workspace_admin(workspace_id, service_principal_object_id, fabric_client)
        add_entra_id_group_admin(workspace_id, entra_admin_group_id or "", fabric_client)
        
        print(f"  ✓ Workspace '{workspace_name}' is ready for deployment")
        return workspace_id
        
    except Exception as e:
        _print_troubleshooting_hints(str(e))
        raise


def _print_troubleshooting_hints(error_msg: str) -> None:
    """Print contextual troubleshooting hints based on error message.
    
    Args:
        error_msg: Error message to analyze for troubleshooting context
    """
    print(f"\n✗ ERROR: Failed to ensure workspace exists: {error_msg}\n")
    
    if "workspace creation permissions" in error_msg:
        print("TROUBLESHOOTING:")
        print("  1. Fabric Tenant Setting:")
        print("     - Open Fabric Admin Portal (https://app.fabric.microsoft.com/admin-portal)")
        print("     - Navigate to: Tenant Settings → Developer Settings")
        print("     - Enable: 'Service principals can create workspaces, connections, and deployment pipelines'")
        print("  2. Capacity Administrator Assignment:")
        print("     - Open Azure Portal → Your Fabric Capacity → Settings → Capacity administrators")
        print("     - Add the Service Principal by Client ID or Enterprise Application name")
        print()
    elif "capacity" in error_msg.lower():
        print("TROUBLESHOOTING:")
        print("  1. Verify FABRIC_CAPACITY_ID_* secrets are set in GitHub repository")
        print("  2. Get capacity ID from Fabric portal: Settings → Admin Portal → Capacity Settings")
        print("  3. Ensure capacity is active and not paused")
        print()
    elif "Object ID" in error_msg:
        print("TROUBLESHOOTING:")
        print("  1. Go to Azure Portal → Azure Active Directory → Enterprise Applications")
        print("  2. Search for your application by Client ID (Application ID)")
        print("  3. Copy the 'Object ID' field (NOT the Application ID)")
        print("  4. Set DEPLOYMENT_SP_OBJECT_ID secret to this Object ID value")
        print()
