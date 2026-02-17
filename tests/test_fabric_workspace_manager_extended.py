# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Extended tests for fabric_workspace_manager.py - covering missing functions."""

from unittest.mock import Mock, patch

import pytest
from azure.core.exceptions import HttpResponseError

from scripts.fabric_workspace_manager import (
    add_entra_id_group_admin,
    add_workspace_admin,
    check_role_assignment_exists,
    create_workspace,
)


class TestCheckRoleAssignmentExists:
    """Test suite for check_role_assignment_exists function."""

    def test_role_assignment_exists(self, mock_fabric_client):
        """Test checking role assignment that exists."""
        mock_assignment = Mock()
        mock_assignment.principal.id = "test-principal-123"
        mock_assignment.role = "Admin"
        mock_fabric_client.core.workspaces.list_workspace_role_assignments.return_value = [mock_assignment]

        result = check_role_assignment_exists("workspace-id", "test-principal-123", "Admin", mock_fabric_client)

        assert result is True

    def test_role_assignment_not_exists(self, mock_fabric_client):
        """Test checking role assignment that doesn't exist."""
        mock_assignment = Mock()
        mock_assignment.principal.id = "different-principal"
        mock_assignment.role = "Admin"
        mock_fabric_client.core.workspaces.list_workspace_role_assignments.return_value = [mock_assignment]

        result = check_role_assignment_exists("workspace-id", "test-principal-123", "Admin", mock_fabric_client)

        assert result is False

    def test_role_assignment_different_role(self, mock_fabric_client):
        """Test checking role assignment with different role."""
        mock_assignment = Mock()
        mock_assignment.principal.id = "test-principal-123"
        mock_assignment.role = "Contributor"
        mock_fabric_client.core.workspaces.list_workspace_role_assignments.return_value = [mock_assignment]

        result = check_role_assignment_exists("workspace-id", "test-principal-123", "Admin", mock_fabric_client)

        assert result is False

    def test_role_assignment_empty_list(self, mock_fabric_client):
        """Test checking role assignment when no assignments exist."""
        mock_fabric_client.core.workspaces.list_workspace_role_assignments.return_value = []

        result = check_role_assignment_exists("workspace-id", "test-principal-123", "Admin", mock_fabric_client)

        assert result is False

    def test_role_assignment_api_error(self, mock_fabric_client):
        """Test handling API errors when checking role assignments."""
        mock_fabric_client.core.workspaces.list_workspace_role_assignments.side_effect = HttpResponseError(
            message="API Error"
        )

        with pytest.raises(Exception, match="Failed to list workspace role assignments"):
            check_role_assignment_exists("workspace-id", "test-principal-123", "Admin", mock_fabric_client)


class TestCreateWorkspaceErrorHandling:
    """Test suite for create_workspace error handling."""

    def test_create_workspace_403_forbidden(self, mock_fabric_client):
        """Test workspace creation with 403 Forbidden error."""
        error = HttpResponseError(message="Forbidden")
        error.status_code = 403
        mock_fabric_client.core.workspaces.create_workspace.side_effect = error

        with pytest.raises(Exception, match="Service Principal lacks workspace creation permissions"):
            create_workspace("[D] Test", "capacity-id", mock_fabric_client)

    def test_create_workspace_404_not_found(self, mock_fabric_client):
        """Test workspace creation with 404 Not Found error (invalid capacity)."""
        error = HttpResponseError(message="Not Found")
        error.status_code = 404
        mock_fabric_client.core.workspaces.create_workspace.side_effect = error

        with pytest.raises(Exception, match="Invalid capacity ID"):
            create_workspace("[D] Test", "invalid-capacity", mock_fabric_client)

    def test_create_workspace_400_bad_request(self, mock_fabric_client):
        """Test workspace creation with 400 Bad Request error."""
        error = HttpResponseError(message="Bad Request")
        error.status_code = 400
        mock_fabric_client.core.workspaces.create_workspace.side_effect = error

        with pytest.raises(Exception, match="Invalid workspace creation request"):
            create_workspace("[D] Test", "capacity-id", mock_fabric_client)


class TestAssignWorkspaceRoleInternal:
    """Test suite for _assign_workspace_role internal function."""

    @patch("scripts.fabric_workspace_manager.check_role_assignment_exists")
    def test_assign_role_skips_if_exists(self, mock_check, mock_fabric_client):
        """Test that role assignment is skipped if already exists."""
        from scripts.fabric_workspace_manager import _assign_workspace_role

        mock_check.return_value = True

        _assign_workspace_role(
            workspace_id="ws-id",
            principal_id="principal-id",
            principal_type="ServicePrincipal",
            role="Admin",
            fabric_client=mock_fabric_client,
            principal_description="Service Principal",
        )

        # Should check but not attempt to assign
        mock_check.assert_called_once()
        mock_fabric_client.core.workspaces.add_workspace_role_assignment.assert_not_called()

    @patch("scripts.fabric_workspace_manager.check_role_assignment_exists")
    def test_assign_role_none_principal_id_service_principal(self, mock_check, mock_fabric_client, capsys):
        """Test that None principal_id for Service Principal logs warning."""
        from scripts.fabric_workspace_manager import _assign_workspace_role

        _assign_workspace_role(
            workspace_id="ws-id",
            principal_id=None,
            principal_type="ServicePrincipal",
            role="Admin",
            fabric_client=mock_fabric_client,
            principal_description="Service Principal",
        )

        # Should not check or assign
        mock_check.assert_not_called()
        mock_fabric_client.core.workspaces.add_workspace_role_assignment.assert_not_called()

    @patch("scripts.fabric_workspace_manager.check_role_assignment_exists")
    def test_assign_role_none_principal_id_group(self, mock_check, mock_fabric_client):
        """Test that None principal_id for Entra ID group logs info."""
        from scripts.fabric_workspace_manager import _assign_workspace_role

        # Should not raise any exceptions
        _assign_workspace_role(
            workspace_id="ws-id",
            principal_id=None,
            principal_type="Group",
            role="Admin",
            fabric_client=mock_fabric_client,
            principal_description="Entra ID group",
        )

        # Should not check or assign
        mock_check.assert_not_called()
        mock_fabric_client.core.workspaces.add_workspace_role_assignment.assert_not_called()

    @patch("scripts.fabric_workspace_manager.check_role_assignment_exists")
    def test_assign_role_404_service_principal(self, mock_check, mock_fabric_client):
        """Test role assignment with 404 error for Service Principal."""
        from scripts.fabric_workspace_manager import _assign_workspace_role

        mock_check.return_value = False
        error = HttpResponseError(message="Not Found")
        error.status_code = 404
        mock_fabric_client.core.workspaces.add_workspace_role_assignment.side_effect = error

        with pytest.raises(Exception, match="Invalid Service Principal Object ID"):
            _assign_workspace_role(
                workspace_id="ws-id",
                principal_id="invalid-sp-id",
                principal_type="ServicePrincipal",
                role="Admin",
                fabric_client=mock_fabric_client,
                principal_description="Service Principal",
            )

    @patch("scripts.fabric_workspace_manager.check_role_assignment_exists")
    def test_assign_role_404_group(self, mock_check, mock_fabric_client):
        """Test role assignment with 404 error for Entra ID group."""
        from scripts.fabric_workspace_manager import _assign_workspace_role

        mock_check.return_value = False
        error = HttpResponseError(message="Not Found")
        error.status_code = 404
        mock_fabric_client.core.workspaces.add_workspace_role_assignment.side_effect = error

        with pytest.raises(Exception, match="Invalid Entra ID group Object ID"):
            _assign_workspace_role(
                workspace_id="ws-id",
                principal_id="invalid-group-id",
                principal_type="Group",
                role="Admin",
                fabric_client=mock_fabric_client,
                principal_description="Entra ID group",
            )


class TestAddWorkspaceAdmin:
    """Test suite for add_workspace_admin function."""

    @patch("scripts.fabric_workspace_manager._assign_workspace_role")
    def test_add_workspace_admin_calls_internal(self, mock_assign, mock_fabric_client):
        """Test add_workspace_admin calls _assign_workspace_role correctly."""
        add_workspace_admin("ws-id", "sp-object-id", mock_fabric_client)

        mock_assign.assert_called_once_with(
            workspace_id="ws-id",
            principal_id="sp-object-id",
            principal_type="ServicePrincipal",
            role="Admin",
            fabric_client=mock_fabric_client,
            principal_description="Service Principal",
        )


class TestAddEntraIdGroupAdmin:
    """Test suite for add_entra_id_group_admin function."""

    @patch("scripts.fabric_workspace_manager._assign_workspace_role")
    def test_add_entra_id_group_admin_calls_internal(self, mock_assign, mock_fabric_client):
        """Test add_entra_id_group_admin calls _assign_workspace_role correctly."""
        add_entra_id_group_admin("ws-id", "group-object-id", mock_fabric_client)

        mock_assign.assert_called_once_with(
            workspace_id="ws-id",
            principal_id="group-object-id",
            principal_type="Group",
            role="Admin",
            fabric_client=mock_fabric_client,
            principal_description="Entra ID group",
        )


class TestPrintTroubleshootingHints:
    """Test suite for _print_troubleshooting_hints function."""

    def test_print_hints_workspace_creation_permissions(self):
        """Test troubleshooting hints for workspace creation permissions."""
        from scripts.fabric_workspace_manager import _print_troubleshooting_hints

        # Should not raise any exceptions
        _print_troubleshooting_hints("Service Principal lacks workspace creation permissions")

    def test_print_hints_capacity_error(self):
        """Test troubleshooting hints for capacity errors."""
        from scripts.fabric_workspace_manager import _print_troubleshooting_hints

        # Should not raise any exceptions
        _print_troubleshooting_hints("Invalid capacity ID")

    def test_print_hints_object_id_error(self):
        """Test troubleshooting hints for Object ID errors."""
        from scripts.fabric_workspace_manager import _print_troubleshooting_hints

        # Should not raise any exceptions
        _print_troubleshooting_hints("Invalid Service Principal Object ID")

    def test_print_hints_generic_error(self):
        """Test troubleshooting hints for generic errors."""
        from scripts.fabric_workspace_manager import _print_troubleshooting_hints

        # Should not raise any exceptions
        _print_troubleshooting_hints("Some other error occurred")


class TestEnsureWorkspaceExistsExtended:
    """Extended test suite for ensure_workspace_exists function."""

    @patch("scripts.fabric_workspace_manager.check_workspace_exists")
    @patch("scripts.fabric_workspace_manager.add_workspace_admin")
    @patch("scripts.fabric_workspace_manager.add_entra_id_group_admin")
    def test_ensure_workspace_with_entra_group(self, mock_add_group, mock_add_admin, mock_check, mock_fabric_client):
        """Test ensuring workspace with Entra ID group assignment."""
        from scripts.fabric_workspace_manager import ensure_workspace_exists

        mock_check.return_value = "existing-workspace-id"

        result = ensure_workspace_exists(
            workspace_name="[D] Test",
            capacity_id="capacity-id",
            service_principal_object_id="sp-id",
            entra_admin_group_id="group-id",
            fabric_client=mock_fabric_client,
        )

        assert result == "existing-workspace-id"
        mock_add_admin.assert_called_once_with("existing-workspace-id", "sp-id", mock_fabric_client)
        mock_add_group.assert_called_once_with("existing-workspace-id", "group-id", mock_fabric_client)

    @patch("scripts.fabric_workspace_manager.check_workspace_exists")
    @patch("scripts.fabric_workspace_manager._print_troubleshooting_hints")
    def test_ensure_workspace_prints_hints_on_error(self, mock_print_hints, mock_check, mock_fabric_client):
        """Test that troubleshooting hints are printed when ensure_workspace_exists fails."""
        from scripts.fabric_workspace_manager import ensure_workspace_exists

        mock_check.side_effect = Exception("API connection failed")

        with pytest.raises(Exception, match="API connection failed"):
            ensure_workspace_exists(
                workspace_name="[D] Test",
                capacity_id="capacity-id",
                service_principal_object_id=None,
                entra_admin_group_id=None,
                fabric_client=mock_fabric_client,
            )

        mock_print_hints.assert_called_once()
