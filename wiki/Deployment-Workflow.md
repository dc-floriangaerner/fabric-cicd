# Deployment Workflow

Understand the CI/CD pipeline workflow for deploying Microsoft Fabric workspaces.

## Overview

This repository uses a trunk-based development workflow with automated deployments to Dev and manual promotions to Test and Production.

## Deployment Pipeline Flow

```mermaid
graph LR
    A[PR Merged to Main] --> B[Auto Deploy to Dev]
    B --> C{Verify Dev}
    C -->|Success| D[Manual: Deploy to Test]
    D --> E{Verify Test}
    E -->|Success| F[Manual: Deploy to Prod]
```

## Deployment Environments

| Environment | Trigger | Use Case | Approval Required |
|-------------|---------|----------|-------------------|
| **Dev** | Automatic on merge to `main` | Rapid iteration and testing | No |
| **Test** | Manual workflow dispatch | Pre-production validation | Optional |
| **Production** | Manual workflow dispatch | Live environment | Optional |

## Deployment Process

For each workspace in the deployment:

1. **Auto-Discover Workspaces** - Automatically discovers all workspace folders with `config.yml`
2. **Authenticate** - Login using Service Principal (ClientSecretCredential)
3. **Capture State** - Store current workspace state for potential rollback
4. **Transform IDs** - Replace environment-specific IDs based on workspace `parameter.yml`
5. **Deploy Items** - Publish items using `fabric-cicd` library
6. **Clean Up Orphans** - Remove items not in repository (optional)
7. **Rollback on Failure** - If any workspace fails, rollback all previously deployed workspaces
8. **Report Status** - Display deployment summary in GitHub Actions

## Triggering Deployments

### Automatic Dev Deployment

Merging a PR to `main` with changes in `workspaces/**` paths triggers automatic deployment to Dev.

**Changes that trigger deployment:**
- Adding/modifying workspace items
- Updating `config.yml` or `parameter.yml`
- Changes to workspace folder structure

**Changes that DO NOT trigger deployment:**
- Updates to `.github/` workflows
- Changes to `scripts/` directory
- Documentation updates (`README.md`, `SETUP.md`)
- Changes outside `workspaces/` directory

### Manual Test/Production Deployment

1. Go to **Actions** tab in GitHub
2. Select **Deploy to Microsoft Fabric** workflow
3. Click **Run workflow**
4. Select target environment from dropdown:
   - `dev` - Development environment
   - `test` - Test environment
   - `prod` - Production environment
5. Click **Run workflow** button

## ID Transformation

The pipeline automatically replaces environment-specific IDs during deployment:

| Type | From (Dev) | To (Target Env) |
|------|-----------|-----------------|
| Lakehouse IDs | Dev lakehouse ID | Target env lakehouse ID |
| Workspace IDs | Dev workspace ID | Target env workspace ID |
| SQL Endpoints | Dev SQL endpoint | Target env SQL endpoint |
| Connections | Dev connection ID | Target env connection ID |

### How It Works

1. Deployment script reads `parameter.yml` from each workspace
2. For each transformation rule:
   - Find the Dev value in item definitions
   - Replace with target environment value
   - Use special variables like `$items.Lakehouse.<name>.id`
3. Deploy transformed items to target workspace

## Atomic Deployment with Rollback

All workspace deployments in a single workflow run must succeed together:

```
Deployment Order:
1. Workspace A → Success ✓
2. Workspace B → Success ✓
3. Workspace C → FAILURE ✗

Rollback Triggered:
1. Rollback Workspace B → Restored
2. Rollback Workspace A → Restored
3. Exit with error and failure report
```

This ensures environments remain in a consistent state even when deployments fail.

## Viewing Deployment Logs

1. Go to **Actions** tab in GitHub
2. Select the workflow run
3. Click on job name (e.g., "Deploy to Dev")
4. Expand steps to view detailed logs
5. Look for workspace-specific deployment sections

### Log Sections

- **Authentication** - Service Principal login status
- **Workspace Discovery** - List of workspaces detected
- **ID Transformation** - Applied transformation rules
- **Item Deployment** - Published items per workspace
- **Orphan Cleanup** - Removed items (if enabled)
- **Deployment Summary** - Overall status and statistics

## Multi-Workspace Deployment

The deployment script automatically discovers and deploys all workspace folders:

```
workspaces/
└── Fabric Blueprint/      → Deploys to [D/T/P] Fabric Blueprint
```

Additional workspaces can be added by duplicating the `Fabric Blueprint` folder structure.

> **Note**: Atomic rollback is a planned feature. Currently, if a workspace deployment fails, the pipeline stops and reports the error, but previously deployed workspaces in that run are not automatically rolled back.

## Best Practices

### Development Workflow

1. **Create feature branch** from `main`
2. **Make changes** to workspace items
3. **Test locally** with private dev workspace
4. **Create PR** to `main`
5. **Get review** and approval
6. **Merge PR** to trigger automatic Dev deployment
7. **Verify Dev** deployment succeeded
8. **Manually deploy to Test** for pre-production validation
9. **Verify Test** deployment succeeded
10. **Manually deploy to Prod** for production release

### Commit Guidelines

- **Small, atomic commits** - One logical change per commit
- **Clear messages** - Describe what and why
- **Group related changes** - Commit related workspace changes together
- **Reference issues** - Link commits to GitHub issues

### Deployment Guidelines

- **Verify before promoting** - Always test in Dev before Test
- **Use manual triggers** - Control when Test/Prod deployments happen
- **Monitor logs** - Review deployment logs for errors
- **Document changes** - Explain what changed and why in PR description

## Troubleshooting Deployments

### Deployment Failed

1. Check workflow logs for specific error message
2. Verify Service Principal has workspace permissions
3. Ensure workspace names match `config.yml`
4. Validate `parameter.yml` syntax and transformation rules
5. Check item definitions are valid JSON/Python

### Rollback Failed

1. Review logs to identify failure point
2. Check Service Principal permissions on all workspaces
3. May require manual restoration of workspace state
4. Verify workspace items can be modified/deleted by Service Principal

### Authentication Failed

1. Verify GitHub secrets are correctly configured
2. Check Service Principal exists in correct Azure AD tenant
3. Ensure client secret hasn't expired (max 2 years)
4. Verify Service Principal has Fabric workspace access

## Resources

- [GitHub Actions Workflows](.github/workflows/)
- [Troubleshooting Guide](Troubleshooting)
- [Workspace Configuration](Workspace-Configuration)
- [GitHub Actions Documentation](https://docs.github.com/actions)
