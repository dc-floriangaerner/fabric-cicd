# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for fabric_workspace_manager.py workspace management functions."""

from unittest.mock import Mock, patch

import pytest
from azure.core.exceptions import HttpResponseError

from scripts.fabric_workspace_manager import (
    assign_workspace_role,
    check_workspace_exists,
    create_workspace,
    ensure_workspace_exists,
)


class TestCheckWorkspaceExists:
    """Test suite for check_workspace_exists function."""

    def test_workspace_exists(self, mock_fabric_client):
        """Test checking for an existing workspace."""
        # Mock workspace list with one workspace
        mock_workspace = Mock()
        mock_workspace.display_name = "[D] Test Workspace"
        mock_workspace.id = "test-workspace-id-123"
        mock_fabric_client.core.workspaces.list_workspaces.return_value = [mock_workspace]

        result = check_workspace_exists("[D] Test Workspace", mock_fabric_client)

        assert result == "test-workspace-id-123"

    def test_workspace_not_exists(self, mock_fabric_client):
        """Test checking for a non-existent workspace."""
        # Mock empty workspace list
        mock_fabric_client.core.workspaces.list_workspaces.return_value = []

        result = check_workspace_exists("[D] NonExistent", mock_fabric_client)

        assert result is None

    def test_workspace_exists_case_sensitive(self, mock_fabric_client):
        """Test that workspace name matching is case-sensitive."""
        mock_workspace = Mock()
        mock_workspace.display_name = "[D] Test Workspace"
        mock_workspace.id = "test-workspace-id-123"
        mock_fabric_client.core.workspaces.list_workspaces.return_value = [mock_workspace]

        # Different case should not match
        result = check_workspace_exists("[d] test workspace", mock_fabric_client)

        assert result is None

    def test_workspace_api_error(self, mock_fabric_client):
        """Test handling API errors when checking workspace."""
        mock_fabric_client.core.workspaces.list_workspaces.side_effect = HttpResponseError(message="API Error")

        with pytest.raises(Exception, match="Failed to list workspaces"):
            check_workspace_exists("[D] Test", mock_fabric_client)


class TestCreateWorkspace:
    """Test suite for create_workspace function."""

    def test_create_workspace_success(self, mock_fabric_client):
        """Test successful workspace creation."""
        capacity_id = "test-capacity-id"
        workspace_name = "[D] New Workspace"

        mock_response = Mock()
        mock_response.id = "new-workspace-id-456"
        mock_fabric_client.core.workspaces.create_workspace.return_value = mock_response

        result = create_workspace(workspace_name, capacity_id, mock_fabric_client)

        assert result == "new-workspace-id-456"

    def test_create_workspace_missing_capacity(self, mock_fabric_client):
        """Test workspace creation fails without capacity ID."""
        with pytest.raises(Exception, match="Capacity ID is required"):
            create_workspace("[D] Test", "", mock_fabric_client)

    def test_create_workspace_none_capacity(self, mock_fabric_client):
        """Test workspace creation fails with None capacity ID."""
        with pytest.raises(Exception, match="Capacity ID is required"):
            create_workspace("[D] Test", None, mock_fabric_client)

    def test_create_workspace_api_error(self, mock_fabric_client):
        """Test handling API errors during workspace creation."""
        mock_fabric_client.core.workspaces.create_workspace.side_effect = HttpResponseError(message="API Error")

        with pytest.raises(HttpResponseError):
            create_workspace("[D] Test", "capacity-id", mock_fabric_client)

    def test_create_workspace_invalid_response(self, mock_fabric_client):
        """Test handling workspace creation with invalid response (no ID)."""
        capacity_id = "test-capacity-id"

        mock_response = Mock()
        mock_response.id = None  # Invalid response without ID
        mock_fabric_client.core.workspaces.create_workspace.return_value = mock_response

        with pytest.raises(Exception, match="response did not contain a valid 'id' field"):
            create_workspace("[D] Test", capacity_id, mock_fabric_client)


class TestAssignWorkspaceRole:
    """Test suite for assign_workspace_role function."""

    def test_assign_role_success(self, mock_fabric_client):
        """Test successful role assignment."""
        workspace_id = "test-workspace-id"
        principal_id = "test-principal-id"

        # Should not raise any exceptions
        assign_workspace_role(workspace_id, principal_id, "Contributor", mock_fabric_client)

        # Verify the API was called
        mock_fabric_client.core.workspaces.add_workspace_role_assignment.assert_called_once()

    def test_assign_role_admin(self, mock_fabric_client):
        """Test assigning Admin role."""
        workspace_id = "test-workspace-id"
        principal_id = "test-principal-id"

        assign_workspace_role(workspace_id, principal_id, "Admin", mock_fabric_client)

        mock_fabric_client.core.workspaces.add_workspace_role_assignment.assert_called_once()

    def test_assign_role_member(self, mock_fabric_client):
        """Test assigning Member role."""
        workspace_id = "test-workspace-id"
        principal_id = "test-principal-id"

        assign_workspace_role(workspace_id, principal_id, "Member", mock_fabric_client)

        mock_fabric_client.core.workspaces.add_workspace_role_assignment.assert_called_once()

    def test_assign_role_api_error(self, mock_fabric_client):
        """Test handling API errors during role assignment."""
        mock_fabric_client.core.workspaces.add_workspace_role_assignment.side_effect = HttpResponseError(
            message="API Error"
        )

        with pytest.raises(Exception, match="role assignment failed"):
            assign_workspace_role("ws-id", "principal-id", "Contributor", mock_fabric_client)


class TestEnsureWorkspaceExists:
    """Test suite for ensure_workspace_exists function."""

    @patch("scripts.fabric_workspace_manager.check_workspace_exists")
    def test_ensure_existing_workspace(self, mock_check, mock_fabric_client):
        """Test ensuring an existing workspace."""
        mock_check.return_value = "existing-workspace-id"

        result = ensure_workspace_exists("[D] Test", "capacity-id", None, None, mock_fabric_client)

        assert result == "existing-workspace-id"

    @patch("scripts.fabric_workspace_manager.check_workspace_exists")
    @patch("scripts.fabric_workspace_manager.create_workspace")
    def test_ensure_create_new_workspace(self, mock_create, mock_check, mock_fabric_client):
        """Test ensuring workspace when it doesn't exist."""
        mock_check.return_value = None
        mock_create.return_value = "new-workspace-id"

        result = ensure_workspace_exists("[D] Test", "capacity-id", None, None, mock_fabric_client)

        assert result == "new-workspace-id"
        mock_create.assert_called_once()

    @patch("scripts.fabric_workspace_manager.check_workspace_exists")
    @patch("scripts.fabric_workspace_manager.create_workspace")
    @patch("scripts.fabric_workspace_manager.add_workspace_admin")
    def test_ensure_workspace_with_role_assignment(self, mock_add_admin, mock_create, mock_check, mock_fabric_client):
        """Test ensuring workspace with role assignment."""
        mock_check.return_value = None
        mock_create.return_value = "new-workspace-id"

        result = ensure_workspace_exists("[D] Test", "capacity-id", "sp-object-id", None, mock_fabric_client)

        assert result == "new-workspace-id"
        mock_add_admin.assert_called_once_with("new-workspace-id", "sp-object-id", mock_fabric_client)

    @patch("scripts.fabric_workspace_manager.check_workspace_exists")
    def test_ensure_workspace_check_fails(self, mock_check, mock_fabric_client):
        """Test ensure workspace when check fails."""
        mock_check.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="API Error"):
            ensure_workspace_exists("[D] Test", "capacity-id", None, None, mock_fabric_client)


@pytest.mark.integration
class TestWorkspaceManagementIntegration:
    """Integration tests for workspace management workflow."""

    @patch("scripts.fabric_workspace_manager.FabricClient")
    def test_full_workspace_lifecycle(self, mock_client_class):
        """Test complete workspace creation and role assignment workflow."""
        pytest.xfail("Integration deployment workflow test not yet implemented")
