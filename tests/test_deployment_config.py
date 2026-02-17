# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Tests for deployment_config.py constants."""

from scripts.deployment_config import (
    CONFIG_FILE,
    ENV_ACTIONS_RUNNER_DEBUG,
    ENV_AZURE_CLIENT_ID,
    ENV_AZURE_CLIENT_SECRET,
    ENV_AZURE_TENANT_ID,
    ENV_DEPLOYMENT_SP_OBJECT_ID,
    ENV_FABRIC_ADMIN_GROUP_ID,
    ENV_FABRIC_CAPACITY_ID,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    RESULTS_FILENAME,
    SEPARATOR_LONG,
    SEPARATOR_SHORT,
    VALID_ENVIRONMENTS,
)


class TestDeploymentConfig:
    """Test suite for deployment configuration constants."""

    def test_valid_environments_contains_all_stages(self):
        """Test that VALID_ENVIRONMENTS contains dev, test, and prod."""
        assert "dev" in VALID_ENVIRONMENTS
        assert "test" in VALID_ENVIRONMENTS
        assert "prod" in VALID_ENVIRONMENTS
        assert len(VALID_ENVIRONMENTS) == 3

    def test_valid_environments_is_set(self):
        """Test that VALID_ENVIRONMENTS is a set for O(1) lookup."""
        assert isinstance(VALID_ENVIRONMENTS, set)

    def test_separators_are_strings(self):
        """Test that separator constants are strings."""
        assert isinstance(SEPARATOR_LONG, str)
        assert isinstance(SEPARATOR_SHORT, str)
        assert len(SEPARATOR_LONG) > len(SEPARATOR_SHORT)

    def test_filenames_have_valid_extensions(self):
        """Test that filename constants have proper extensions."""
        assert RESULTS_FILENAME.endswith(".json")
        assert CONFIG_FILE.endswith(".yml")

    def test_exit_codes_are_integers(self):
        """Test that exit codes are integers."""
        assert isinstance(EXIT_SUCCESS, int)
        assert isinstance(EXIT_FAILURE, int)
        assert EXIT_SUCCESS == 0
        assert EXIT_FAILURE == 1

    def test_environment_variable_names_are_uppercase(self):
        """Test that environment variable names follow convention."""
        env_vars = [
            ENV_AZURE_CLIENT_ID,
            ENV_AZURE_TENANT_ID,
            ENV_AZURE_CLIENT_SECRET,
            ENV_FABRIC_CAPACITY_ID,
            ENV_DEPLOYMENT_SP_OBJECT_ID,
            ENV_FABRIC_ADMIN_GROUP_ID,
            ENV_ACTIONS_RUNNER_DEBUG,
        ]
        for var in env_vars:
            assert var.isupper(), f"{var} should be uppercase"
            assert isinstance(var, str)

    def test_azure_env_vars_start_with_azure(self):
        """Test that Azure-related environment variables start with AZURE_."""
        azure_vars = [
            ENV_AZURE_CLIENT_ID,
            ENV_AZURE_TENANT_ID,
            ENV_AZURE_CLIENT_SECRET,
        ]
        for var in azure_vars:
            assert var.startswith("AZURE_"), f"{var} should start with AZURE_"

    def test_fabric_env_vars_start_with_fabric(self):
        """Test that Fabric-related environment variables start with FABRIC_."""
        fabric_vars = [
            ENV_FABRIC_CAPACITY_ID,
            ENV_FABRIC_ADMIN_GROUP_ID,
        ]
        for var in fabric_vars:
            assert var.startswith("FABRIC_"), f"{var} should start with FABRIC_"
