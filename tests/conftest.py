# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Pytest configuration and fixtures for dc-fabric-cicd tests."""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_azure_credential():
    """Create a mock Azure ClientSecretCredential for testing."""
    mock_cred = MagicMock()
    return mock_cred


@pytest.fixture
def sample_workspace_config() -> dict[str, Any]:
    """Return a sample workspace configuration."""
    return {
        "core": {"workspace": {"dev": "[D] Test Workspace", "test": "[T] Test Workspace", "prod": "[P] Test Workspace"}}
    }


@pytest.fixture
def sample_parameter_config() -> dict[str, Any]:
    """Return a sample parameter configuration."""
    return {"find_replace": [{"find_value": "old-value", "replace_value": {"_ALL_": "new-value"}, "is_regex": "false"}]}


@pytest.fixture
def temp_workspace_dir(tmp_path: Path) -> Path:
    """Create a temporary workspace directory structure for testing."""
    workspace_dir = tmp_path / "workspaces" / "Test Workspace"
    workspace_dir.mkdir(parents=True)

    # Create config.yml
    config_file = workspace_dir / "config.yml"
    config_file.write_text("""
core:
  workspace:
    dev: "[D] Test Workspace"
    test: "[T] Test Workspace"
    prod: "[P] Test Workspace"
""")

    # Create parameter.yml
    parameter_file = workspace_dir / "parameter.yml"
    parameter_file.write_text("""
find_replace:
  - find_value: "old-id"
    replace_value:
      _ALL_: "new-id"
    is_regex: "false"
""")

    # Create sample item
    item_dir = workspace_dir / "sample.Lakehouse"
    item_dir.mkdir()
    (item_dir / "lakehouse.metadata.json").write_text('{"defaultSchema": "dbo"}')

    return tmp_path / "workspaces"


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        "AZURE_CLIENT_ID": "test-client-id",
        "AZURE_TENANT_ID": "test-tenant-id",
        "AZURE_CLIENT_SECRET": "test-client-secret",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars
