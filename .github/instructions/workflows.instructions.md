---
applyTo: ".github/workflows/**/*.yml,.github/workflows/**/*.yaml"
description: "GitHub Actions workflow configurations"
---

# GitHub Actions Workflows Instructions

## Specific Guidelines for .github/workflows/ Directory

### Workflow Structure

This repository uses a single workflow file for multi-environment deployment:

- `fabric-deploy.yml` - Main deployment workflow for Dev/Test/Prod

### Workflow Triggers

```yaml
# Automatic Dev deployment on merge to main (workspace changes only)
on:
  push:
    branches: [main]
    paths:
      - 'workspaces/**'

# Manual deployment via workflow dispatch
on:
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [dev, test, prod]
```

### Authentication Pattern

Use Service Principal authentication with GitHub Secrets:

```yaml
- name: Azure Login
  run: |
    python -m scripts.deploy_to_fabric \
      --client_id "${{ secrets.AZURE_CLIENT_ID }}" \
      --client_secret "${{ secrets.AZURE_CLIENT_SECRET }}" \
      --tenant_id "${{ secrets.AZURE_TENANT_ID }}"
```

### Required GitHub Secrets

**Always needed:**
- `AZURE_CLIENT_ID` - Service Principal Client ID
- `AZURE_CLIENT_SECRET` - Service Principal Secret
- `AZURE_TENANT_ID` - Azure AD Tenant ID

**For auto-creation (optional):**
- `FABRIC_CAPACITY_ID_DEV` - Dev capacity GUID
- `FABRIC_CAPACITY_ID_TEST` - Test capacity GUID
- `FABRIC_CAPACITY_ID_PROD` - Prod capacity GUID
- `DEPLOYMENT_SP_OBJECT_ID` - SP Object ID for role assignment
- `FABRIC_ADMIN_GROUP_ID` - Entra ID group for admin access

### Environment Configuration

Use GitHub Environments for deployment control:

```yaml
jobs:
  deploy:
    environment: ${{ inputs.environment || 'dev' }}
    runs-on: ubuntu-latest
```

**Environments:** `dev`, `test`, `production`

### Multi-Workspace Deployment

The deployment script automatically discovers all workspace folders:

```yaml
- name: Deploy All Workspaces
  run: |
    python -m scripts.deploy_to_fabric \
      --workspaces_directory workspaces \
      --environment "${{ inputs.environment || 'dev' }}"
```

No need to specify individual workspace names - auto-discovery handles it.

### Deployment Script Invocation

**Correct way** (as Python module):
```yaml
python -m scripts.deploy_to_fabric --workspaces_directory workspaces --environment dev
```

**Incorrect** (don't use hyphens):
```yaml
python scripts/deploy-to-fabric.py  # ❌ Won't work
```

### Security Best Practices

**DO:**
- Store all sensitive values in GitHub Secrets
- Use `${{ secrets.* }}` syntax in workflows
- Mask secrets automatically (GitHub masks secret values in logs)
- Use environment-specific secrets when needed

**DON'T:**
- Echo or print secret values (`echo ${{ secrets.SECRET }}` is forbidden)
- Hardcode workspace IDs or connection strings
- Commit credentials or tokens
- Use PATs instead of Service Principal

### Path Filters

Only trigger workflows for relevant changes:

```yaml
paths:
  - 'workspaces/**'          # Workspace item changes
  - 'scripts/**'             # Deployment script changes
  - '.github/workflows/**'   # Workflow changes
```

**Note:** Changes to `README.md`, `docs/`, `.github/copilot-instructions.md` will NOT trigger automatic deployment.

### Job Dependencies

Use job dependencies for multi-stage deployments:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    # Job logic

  verify:
    needs: deploy
    runs-on: ubuntu-latest
    # Verification logic
```

### Atomic Rollback

If any workspace deployment fails, all workspaces in that run are rolled back:
- The deployment script handles rollback automatically
- Check workflow logs for rollback status
- May require manual intervention if rollback fails

### Workflow File Naming

- Use descriptive names: `fabric-deploy.yml` (not `main.yml`)
- Use `.yml` extension (not `.yaml`) for consistency
- One workflow per logical deployment process

### Testing Workflow Changes

1. Test locally with `act` if possible
2. Push to feature branch and test with workflow_dispatch
3. Review workflow logs carefully before merging
4. Consider using a separate test workflow for experimentation

### Common Issues

**Authentication fails:**
- Verify secrets are set correctly in repository settings
- Check Service Principal has workspace access
- Ensure client secret hasn't expired

**Workflow doesn't trigger:**
- Check path filters match changed files
- Verify branch protection rules allow workflow runs
- Check workflow file YAML syntax is valid

**Deployment fails:**
- Review job logs for specific error messages
- Check workspace names match config.yml
- Verify Service Principal permissions on all workspaces
