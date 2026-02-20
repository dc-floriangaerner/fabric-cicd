# Fabric CI/CD Reference Architecture Wiki

Welcome to the Fabric CI/CD Reference Architecture documentation!

> **📋 Prerequisites**: Before you begin, ensure you have:
> - Microsoft Fabric workspace access (Admin or Contributor role)
> - Microsoft Entra ID access to create Service Principals
> - GitHub repository with Actions enabled
> - Basic familiarity with Git workflows and YAML configuration
>
> **⏱️ Estimated Setup Time**: 30-45 minutes for complete initial setup

## Quick Links

- [Setup Guide](Setup-Guide) - Get started with initial configuration
- [Workspace Configuration](Workspace-Configuration) - Configure workspace files
- [Deployment Workflow](Deployment-Workflow) - Understand the CI/CD pipeline
- [Troubleshooting](Troubleshooting) - Solve common issues
- [FAQ](FAQ) - Frequently asked questions

## Overview

This wiki provides comprehensive documentation for implementing CI/CD pipelines for Microsoft Fabric workspaces using GitHub Actions and the `fabric-cicd` Python library.

### Key Features

- **Multi-Workspace Support**: Deploy multiple Fabric workspaces from a single repository
- **Terraform-Managed Infrastructure**: Workspace lifecycle (create/configure) managed by Terraform
- **Medallion Architecture**: Bronze → Silver → Gold data layers
- **Multi-stage Deployment**: Dev → Test → Production with approval gates
- **Git-based Deployment**: Single source of truth in `main` branch
- **Separation of Concerns**: Infra (Terraform) and item deployment (fabric-cicd) are independent pipelines

## Getting Started

New to this project? Follow this recommended path:

1. **[Setup Guide](Setup-Guide)** (30-45 min) - Create Service Principal, bootstrap Terraform, provision workspaces
2. **[Workspace Configuration](Workspace-Configuration)** (15-20 min) - Set up workspace config files
3. **[Deployment Workflow](Deployment-Workflow)** (10-15 min read) - Understand the two-pipeline architecture
4. **[Troubleshooting](Troubleshooting)** (Reference) - Solve issues as they arise
5. **[FAQ](FAQ)** (Reference) - Find answers to common questions

## Repository Structure

```
workspaces/
├── Fabric Blueprint/
│   ├── config.yml              # Workspace deployment configuration
│   ├── parameter.yml           # ID transformation rules
│   ├── 1_Bronze/              # Raw data ingestion
│   ├── 2_Silver/              # Transformed/cleansed data
│   ├── 3_Gold/                # Business-ready analytics
│   └── 4_Analytics/           # Semantic models, reports, agents
```

## Contributing

See the [Wiki Contribution Guide](Wiki-Contribution) for how to update this documentation, or the main [README](https://github.com/dc-floriangaerner/dc-fabric-cicd/blob/main/README.md) for contribution guidelines.

## Resources

- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [fabric-cicd Library](https://pypi.org/project/fabric-cicd/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
