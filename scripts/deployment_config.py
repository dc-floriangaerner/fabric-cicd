# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Configuration constants for Fabric deployment scripts."""

# Valid deployment environments
VALID_ENVIRONMENTS = {"dev", "test", "prod"}

# Console output separators
SEPARATOR_LONG = "=" * 70
SEPARATOR_SHORT = "=" * 60

# File names
RESULTS_FILENAME = "deployment-results.json"
CONFIG_FILE = "config.yml"

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

# Environment variable names
ENV_AZURE_CLIENT_ID = "AZURE_CLIENT_ID"
ENV_AZURE_TENANT_ID = "AZURE_TENANT_ID"
ENV_AZURE_CLIENT_SECRET = "AZURE_CLIENT_SECRET"
ENV_ACTIONS_RUNNER_DEBUG = "ACTIONS_RUNNER_DEBUG"
ENV_GITHUB_ACTIONS = "GITHUB_ACTIONS"

# Wiki URLs
WIKI_SETUP_GUIDE_URL = "https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki/Setup-Guide"
WIKI_TROUBLESHOOTING_URL = "https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki/Troubleshooting"
