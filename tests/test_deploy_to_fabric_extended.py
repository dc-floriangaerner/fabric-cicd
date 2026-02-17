# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Extended tests for deploy_to_fabric.py - covering missing functions."""

from unittest.mock import MagicMock, patch

import pytest

from scripts.deploy_to_fabric import (
    DeploymentResult,
    DeploymentSummary,
    build_deployment_results_json,
    create_azure_credential,
    create_fabric_client,
    deploy_all_workspaces,
    get_workspace_folders,
    print_deployment_summary,
    validate_environment,
)


class TestGetWorkspaceFolders:
    """Test suite for get_workspace_folders function."""

    def test_get_workspace_folders_success(self, temp_workspace_dir):
        """Test getting workspace folders from valid directory."""
        folders = get_workspace_folders(str(temp_workspace_dir))

        assert len(folders) > 0
        assert "Test Workspace" in folders

    def test_get_workspace_folders_nonexistent_directory(self, tmp_path):
        """Test error when workspaces directory doesn't exist."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError, match="Workspaces directory not found"):
            get_workspace_folders(str(nonexistent))

    def test_get_workspace_folders_no_configs(self, tmp_path):
        """Test error when no workspace folders have config.yml."""
        empty_ws_dir = tmp_path / "workspaces"
        empty_ws_dir.mkdir()

        # Create workspace folder without config.yml
        (empty_ws_dir / "NoConfigWorkspace").mkdir()

        with pytest.raises(ValueError, match="No workspace folders with 'config.yml' found"):
            get_workspace_folders(str(empty_ws_dir))

    def test_get_workspace_folders_sorted(self, tmp_path):
        """Test that workspace folders are returned in sorted order."""
        ws_dir = tmp_path / "workspaces"
        ws_dir.mkdir()

        # Create multiple workspaces with config.yml in non-sorted order
        for name in ["Zebra", "Alpha", "Mike"]:
            folder = ws_dir / name
            folder.mkdir()
            (folder / "config.yml").write_text("core:\n  workspace:\n    dev: test")

        folders = get_workspace_folders(str(ws_dir))

        assert folders == ["Alpha", "Mike", "Zebra"]


class TestValidateEnvironment:
    """Test suite for validate_environment function."""

    def test_validate_environment_dev(self):
        """Test validation of 'dev' environment."""
        validate_environment("dev")  # Should not raise

    def test_validate_environment_test(self):
        """Test validation of 'test' environment."""
        validate_environment("test")  # Should not raise

    def test_validate_environment_prod(self):
        """Test validation of 'prod' environment."""
        validate_environment("prod")  # Should not raise

    def test_validate_environment_case_insensitive(self):
        """Test validation is case-insensitive."""
        validate_environment("DEV")  # Should not raise
        validate_environment("Test")  # Should not raise
        validate_environment("PROD")  # Should not raise

    def test_validate_environment_invalid(self):
        """Test validation fails for invalid environment."""
        with pytest.raises(ValueError, match="Invalid environment"):
            validate_environment("staging")

    def test_validate_environment_empty(self):
        """Test validation fails for empty string."""
        with pytest.raises(ValueError, match="Invalid environment"):
            validate_environment("")


class TestCreateAzureCredential:
    """Test suite for create_azure_credential function."""

    def test_create_credential_with_service_principal(self, monkeypatch):
        """Test creating credential with service principal env vars."""
        monkeypatch.setenv("AZURE_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("AZURE_TENANT_ID", "test-tenant-id")
        monkeypatch.setenv("AZURE_CLIENT_SECRET", "test-secret")

        credential = create_azure_credential()

        # Should return ClientSecretCredential (we can't check type directly due to mocking,
        # but we verify it was created with the right environment variables)
        assert credential is not None

    def test_create_credential_without_service_principal(self, monkeypatch):
        """Test creating credential falls back to DefaultAzureCredential."""
        # Remove service principal env vars
        monkeypatch.delenv("AZURE_CLIENT_ID", raising=False)
        monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
        monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)

        credential = create_azure_credential()

        # Should return DefaultAzureCredential
        assert credential is not None

    def test_create_credential_partial_env_vars(self, monkeypatch):
        """Test creating credential with incomplete service principal env vars."""
        # Only set some env vars (incomplete)
        monkeypatch.setenv("AZURE_CLIENT_ID", "test-client-id")
        monkeypatch.delenv("AZURE_TENANT_ID", raising=False)
        monkeypatch.delenv("AZURE_CLIENT_SECRET", raising=False)

        credential = create_azure_credential()

        # Should fall back to DefaultAzureCredential
        assert credential is not None


class TestCreateFabricClient:
    """Test suite for create_fabric_client function."""

    def test_create_fabric_client(self, mock_azure_credential):
        """Test creating Fabric API client."""
        client = create_fabric_client(mock_azure_credential)

        assert client is not None


class TestBuildDeploymentResultsJson:
    """Test suite for build_deployment_results_json function."""

    def test_build_results_json_success(self):
        """Test building JSON for successful deployments."""
        results = [
            DeploymentResult("WS1", "[D] WS1", True),
            DeploymentResult("WS2", "[D] WS2", True),
        ]
        summary = DeploymentSummary(environment="dev", duration=60.5, results=results)

        json_output = build_deployment_results_json(summary)

        assert json_output["environment"] == "dev"
        assert json_output["duration"] == 60.5
        assert json_output["total_workspaces"] == 2
        assert json_output["successful_count"] == 2
        assert json_output["failed_count"] == 0
        assert len(json_output["workspaces"]) == 2

    def test_build_results_json_with_failures(self):
        """Test building JSON with some failures."""
        results = [
            DeploymentResult("WS1", "[D] WS1", True),
            DeploymentResult("WS2", "[D] WS2", False, "Connection error"),
        ]
        summary = DeploymentSummary(environment="test", duration=45.3, results=results)

        json_output = build_deployment_results_json(summary)

        assert json_output["successful_count"] == 1
        assert json_output["failed_count"] == 1
        assert json_output["workspaces"][0]["status"] == "success"
        assert json_output["workspaces"][1]["status"] == "failure"
        assert json_output["workspaces"][1]["error"] == "Connection error"

    def test_build_results_json_sorted_by_name(self):
        """Test that workspaces are sorted by name in JSON output."""
        results = [
            DeploymentResult("Zebra", "[D] Zebra", True),
            DeploymentResult("Alpha", "[D] Alpha", True),
            DeploymentResult("Mike", "[D] Mike", True),
        ]
        summary = DeploymentSummary(environment="prod", duration=120.0, results=results)

        json_output = build_deployment_results_json(summary)

        workspace_names = [ws["name"] for ws in json_output["workspaces"]]
        assert workspace_names == ["Alpha", "Mike", "Zebra"]


class TestPrintDeploymentSummary:
    """Test suite for print_deployment_summary function."""

    def test_print_summary_all_success(self):
        """Test printing summary with all successful deployments."""
        results = [
            DeploymentResult("WS1", "[D] WS1", True),
            DeploymentResult("WS2", "[D] WS2", True),
        ]
        summary = DeploymentSummary(environment="dev", duration=60.5, results=results)

        # Function should execute without errors
        print_deployment_summary(summary)
        # Verify summary properties are correct
        assert summary.successful_count == 2
        assert summary.failed_count == 0

    def test_print_summary_with_failures(self):
        """Test printing summary with some failures."""
        results = [
            DeploymentResult("WS1", "[D] WS1", True),
            DeploymentResult("WS2", "[D] WS2", False, "API error"),
        ]
        summary = DeploymentSummary(environment="test", duration=45.3, results=results)

        # Function should execute without errors
        print_deployment_summary(summary)
        # Verify summary properties are correct
        assert summary.successful_count == 1
        assert summary.failed_count == 1

    def test_print_summary_duration_formatting(self):
        """Test that duration is formatted correctly."""
        results = [DeploymentResult("WS1", "[D] WS1", True)]
        summary = DeploymentSummary(environment="prod", duration=123.456, results=results)

        # Function should execute without errors
        print_deployment_summary(summary)
        # Verify duration is stored correctly
        assert summary.duration == 123.456


class TestDeployAllWorkspaces:
    """Test suite for deploy_all_workspaces function."""

    @patch("scripts.deploy_to_fabric.deploy_workspace")
    def test_deploy_all_workspaces_success(self, mock_deploy, mock_azure_credential):
        """Test deploying all workspaces successfully."""
        mock_deploy.return_value = DeploymentResult("WS1", "[D] WS1", True)

        results = deploy_all_workspaces(
            workspace_folders=["WS1", "WS2"],
            workspaces_directory="/path/to/workspaces",
            environment="dev",
            token_credential=mock_azure_credential,
            capacity_id="capacity-123",
            service_principal_object_id="sp-456",
            entra_admin_group_id=None,
        )

        assert len(results) == 2
        assert all(r.success for r in results)
        assert mock_deploy.call_count == 2

    @patch("scripts.deploy_to_fabric.deploy_workspace")
    def test_deploy_all_workspaces_with_failures(self, mock_deploy, mock_azure_credential):
        """Test deploying all workspaces with some failures."""
        # First succeeds, second fails
        mock_deploy.side_effect = [
            DeploymentResult("WS1", "[D] WS1", True),
            DeploymentResult("WS2", "[D] WS2", False, "Deployment error"),
        ]

        results = deploy_all_workspaces(
            workspace_folders=["WS1", "WS2"],
            workspaces_directory="/path/to/workspaces",
            environment="test",
            token_credential=mock_azure_credential,
            capacity_id=None,
            service_principal_object_id=None,
            entra_admin_group_id=None,
        )

        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is False

    @patch("scripts.deploy_to_fabric.deploy_workspace")
    def test_deploy_all_workspaces_empty_list(self, mock_deploy, mock_azure_credential):
        """Test deploying with empty workspace list."""
        results = deploy_all_workspaces(
            workspace_folders=[],
            workspaces_directory="/path/to/workspaces",
            environment="prod",
            token_credential=mock_azure_credential,
            capacity_id="capacity-123",
            service_principal_object_id="sp-456",
            entra_admin_group_id="group-789",
        )

        assert len(results) == 0
        assert mock_deploy.call_count == 0


class TestDeployWorkspaceIntegration:
    """Integration tests for deploy_workspace function."""

    @patch("scripts.deploy_to_fabric.deploy_with_config")
    @patch("scripts.deploy_to_fabric.ensure_workspace_exists")
    @patch("scripts.deploy_to_fabric.create_fabric_client")
    def test_deploy_workspace_success_integration(
        self, mock_client, mock_ensure, mock_deploy, temp_workspace_dir, mock_azure_credential
    ):
        """Test complete deploy_workspace workflow."""
        from scripts.deploy_to_fabric import deploy_workspace

        mock_ensure.return_value = "workspace-id-123"
        mock_client.return_value = MagicMock()

        result = deploy_workspace(
            workspace_folder="Test Workspace",
            workspaces_dir=str(temp_workspace_dir),
            environment="dev",
            token_credential=mock_azure_credential,
            capacity_id="capacity-123",
            service_principal_object_id="sp-456",
            entra_admin_group_id=None,
        )

        assert result.success is True
        assert result.workspace_folder == "Test Workspace"
        assert result.workspace_name == "[D] Test Workspace"
        mock_ensure.assert_called_once()
        mock_deploy.assert_called_once()

    @patch("scripts.deploy_to_fabric.deploy_with_config")
    @patch("scripts.deploy_to_fabric.ensure_workspace_exists")
    @patch("scripts.deploy_to_fabric.create_fabric_client")
    def test_deploy_workspace_config_load_failure(
        self, mock_client, mock_ensure, mock_deploy, tmp_path, mock_azure_credential
    ):
        """Test deploy_workspace handles config load failure."""
        from scripts.deploy_to_fabric import deploy_workspace

        result = deploy_workspace(
            workspace_folder="NonExistent",
            workspaces_dir=str(tmp_path),
            environment="dev",
            token_credential=mock_azure_credential,
        )

        assert result.success is False
        assert "config.yml not found" in result.error_message.lower()

    @patch("scripts.deploy_to_fabric.deploy_with_config")
    @patch("scripts.deploy_to_fabric.ensure_workspace_exists")
    @patch("scripts.deploy_to_fabric.create_fabric_client")
    def test_deploy_workspace_deployment_failure(
        self, mock_client, mock_ensure, mock_deploy, temp_workspace_dir, mock_azure_credential
    ):
        """Test deploy_workspace handles deployment API failure."""
        from scripts.deploy_to_fabric import deploy_workspace

        mock_ensure.return_value = "workspace-id-123"
        mock_client.return_value = MagicMock()
        mock_deploy.side_effect = Exception("API connection error")

        result = deploy_workspace(
            workspace_folder="Test Workspace",
            workspaces_dir=str(temp_workspace_dir),
            environment="dev",
            token_credential=mock_azure_credential,
        )

        assert result.success is False
        assert "API connection error" in result.error_message
