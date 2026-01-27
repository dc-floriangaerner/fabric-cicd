# Setup Guide: GitHub Actions CI/CD for Microsoft Fabric

This guide walks you through setting up the CI/CD pipeline for multi-workspace Fabric deployments.

## Prerequisites Checklist

- [ ] Microsoft Fabric workspace access (Admin or Contributor)
- [ ] Azure AD (Entra ID) tenant access to create Service Principal
- [ ] GitHub repository with Actions enabled
- [ ] Dev, Test, and Prod Fabric workspaces created for each workspace folder

## Architecture Overview

This setup supports deploying **multiple Fabric workspaces** from a single repository:

```
workspaces/
├── Fabric Blueprint/    → [D] Fabric Blueprint, [T] Fabric Blueprint, [P] Fabric Blueprint
├── Analytics Hub/       → [D] Analytics Hub, [T] Analytics Hub, [P] Analytics Hub
└── Data Engineering/    → [D] Data Engineering, [T] Data Engineering, [P] Data Engineering
```

Each workspace folder contains:
- Its own `parameter.yml` configuration file
- Fabric items (Lakehouses, Notebooks, Pipelines, etc.)

Workspace names are dynamically constructed with stage prefixes:
- **Dev**: `[D] <workspace-name>`
- **Test**: `[T] <workspace-name>`
- **Prod**: `[P] <workspace-name>`

## Step 1: Create Azure Service Principal

### Option A: Using Azure Portal

1. Navigate to **Microsoft Entra ID** → **App registrations**
2. Click **New registration**
3. Name: `fabric-cicd-deployment`
4. Click **Register**
5. Copy the **Application (client) ID** (this is `AZURE_CLIENT_ID`)
6. Copy the **Directory (tenant) ID** (this is `AZURE_TENANT_ID`)
7. Go to **Certificates & secrets** → **New client secret**
8. Add description: `GitHub Actions`
9. Copy the **secret value** (this is `AZURE_CLIENT_SECRET`)

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create Service Principal
az ad sp create-for-rbac --name "fabric-cicd-deployment" --skip-assignment

# Output will show:
# {
#   "clientId": "xxx",      # AZURE_CLIENT_ID
#   "clientSecret": "xxx",  # AZURE_CLIENT_SECRET
#   "tenantId": "xxx"       # AZURE_TENANT_ID
# }
```

## Step 2: Grant Fabric Workspace Permissions

For **each workspace** in **each environment** (Dev, Test, Prod):

1. Open the Fabric workspace
2. Click **Workspace settings** → **Manage access**
3. Click **Add people or groups**
4. Search for your Service Principal name (`fabric-cicd-deployment`)
5. Assign role: **Admin** or **Contributor**
6. Click **Add**

**Example: For "Fabric Blueprint" workspace, grant permissions to:**
- `[D] Fabric Blueprint` (Dev)
- `[T] Fabric Blueprint` (Test)
- `[P] Fabric Blueprint` (Prod)

Repeat for all workspace folders in your repository.


## Step 3: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `AZURE_CLIENT_ID` | Service Principal Client ID | Azure AD App Registration |
| `AZURE_CLIENT_SECRET` | Service Principal Secret | Azure AD App Registration → Certificates & secrets |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | Azure AD App Registration |

**Note**: No workspace name variables needed - workspace names are automatically generated from folder names with stage prefixes.

## Step 4: Configure GitHub Environments

Create three environments for your deployments:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Create three environments:
   - `dev` (auto-deploys on merge to main for changed workspaces)
   - `test` (manual deployment via workflow dispatch)
   - `production` (manual deployment via workflow dispatch)

**Environment Configuration**:
- **Deployment branches**: Set to "Protected branches only" or "Selected branches"
- This controls which branches can deploy to each environment

> **Note**: Required reviewers and wait timers require GitHub Team/Enterprise plan. This setup uses manual workflow triggers for Test and Prod deployments instead.

## Step 5: Create Fabric Workspaces

For each workspace folder in `workspaces/`, create three Fabric workspaces:

**Example for "Fabric Blueprint" folder:**
- `[D] Fabric Blueprint` - Development
- `[T] Fabric Blueprint` - Test  
- `[P] Fabric Blueprint` - Production

**Example for "Analytics Hub" folder:**
- `[D] Analytics Hub` - Development
- `[T] Analytics Hub` - Test
- `[P] Analytics Hub` - Production

**Important**: 
- Workspace names MUST match the folder names with appropriate stage prefix
- Prefixes are case-sensitive: `[D] `, `[T] `, `[P] ` (with space after bracket)

## Step 6: Update Workspace parameter.yml Files

Get Item IDs from your **Dev workspace** for each workspace folder:

### Method 1: Using Fabric UI
1. Open item in Dev workspace
2. Check URL or item properties for GUID

### Method 2: Using Fabric API
```powershell
# Install Azure CLI (if not installed)
# Login to Azure
az login

# Get workspace ID
$workspaceId = "<your-dev-workspace-id>"

# List all items
az rest --method get --url "https://api.fabric.microsoft.com/v1/workspaces/$workspaceId/items"
```

### Update Each Workspace's parameter.yml

**Example: `workspaces/Fabric Blueprint/parameter.yml`**

```yaml
find_replace:
  # Replace this with actual Dev lakehouse_bronze ID from [D] Fabric Blueprint workspace
  - find_value: "12345678-1234-1234-1234-123456789abc"
    replace_value:
      _ALL_: "$items.Lakehouse.lakehouse_bronze.id"
    item_type: "Notebook"
    description: "Replace bronze lakehouse references"
```

Each workspace has its own independent configuration file.


## Step 7: Test the Pipeline

### Test Dev Deployment (Auto)

1. Create a test change in a workspace:
```bash
git checkout -b feature/test-deployment
# Make a small change to a workspace
echo "# Test" >> workspaces/"Fabric Blueprint"/test.md
git add workspaces/"Fabric Blueprint"/test.md
git commit -m "test: verify CI/CD pipeline"
git push origin feature/test-deployment
```

2. Create Pull Request to `main`
3. Merge the PR
4. Watch the **Actions** tab for automatic deployment to Dev
5. Pipeline will detect changed workspace and deploy only that workspace

### Test Manual Deployment to Test

1. After Dev deployment succeeds
2. Go to **Actions** → **Deploy to Microsoft Fabric**
3. Click **Run workflow**
4. Select **"test"** from environment dropdown
5. Click **Run workflow** button
6. Monitor the deployment in the Actions tab
7. All workspaces will be deployed to Test environment

### Test Manual Deployment to Production

1. After Test deployment is verified
2. Go to **Actions** → **Deploy to Microsoft Fabric**
3. Click **Run workflow**
4. Select **"prod"** from environment dropdown
5. Click **Run workflow** button
6. Monitor the deployment in the Actions tab
7. All workspaces will be deployed to Production environment

## Step 8: Verify Deployment

### Check Workspaces

For each deployed workspace (e.g., "[D] Fabric Blueprint"):

1. Open the target workspace in Fabric
2. Verify items are deployed:
   - Lakehouses (lakehouse_bronze, lakehouse_silver, lakehouse_gold)
   - Notebooks (nb_sl_transform, nb_gd_modeling)
   - Pipelines (cp_br_source)

### Check Logs

1. In GitHub Actions, click on the workflow run
2. Expand the deployment step (e.g., "Deploy to Dev Workspaces")
3. Verify:
   - Authentication succeeded
   - Changed workspaces detected (for auto deployments)
   - Items published for each workspace
   - No errors or rollback triggered

## Deployment Workflow Summary

| Environment | Trigger | Workspace Selection | When to Use |
|------------|---------|---------------------|-------------|
| **Dev** | Automatic on merge to `main` with `workspaces/**` changes | Changed workspaces only | After PR approval and merge |
| **Test** | Manual workflow dispatch | All workspaces | After Dev deployment verified |
| **Production** | Manual workflow dispatch | All workspaces | After Test deployment verified |

### Change Detection

The pipeline automatically detects which workspaces have changed:

- **Push to main**: Only workspaces with file changes in `workspaces/<workspace-name>/**` are deployed
- **Manual trigger**: All workspaces are deployed regardless of changes
- **Non-workspace changes**: Changes to `.github/`, `scripts/`, `README.md` do NOT trigger deployments

### Atomic Rollback

If any workspace deployment fails, all previously deployed workspaces in that run are automatically rolled back:

```
Workspace A → Success ✓
Workspace B → Success ✓  
Workspace C → FAILURE ✗
→ Rollback B and A
→ Exit with error
```

This ensures environments remain in a consistent state.


## Troubleshooting

### Authentication Failed

**Error**: `ClientSecretCredential authentication failed` or `DefaultAzureCredential failed to retrieve a token`

**Solution**:
- Verify GitHub secrets are correct (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
- Check Service Principal has Fabric workspace access (Admin or Contributor) for ALL workspaces
- Ensure the Service Principal is created in the correct Azure AD tenant
- Verify the client secret hasn't expired

### Workspace Not Found

**Error**: `Workspace '[D] Fabric Blueprint' not found`

**Solution**:
- Verify workspace name matches folder name exactly (including case)
- Check stage prefix is correct: `[D] ` (with space), `[T] ` (with space), `[P] ` (with space)
- Ensure Service Principal has access to workspace
- Verify workspace exists in Fabric portal

### No Workspaces Detected

**Error**: `No workspace folders found to deploy`

**Solution**:
- Ensure workspace folders are directly under `workspaces/` directory
- Each workspace folder must contain a `parameter.yml` file
- Verify folder structure: `workspaces/<workspace-name>/parameter.yml`

### Deployment Not Triggered

**Error**: Pipeline doesn't run after merge to main

**Solution**:
- Check if changes were made in `workspaces/**` paths (required for auto-trigger)
- Changes to `.github/`, `scripts/`, documentation do NOT trigger automatic deployment
- Use manual workflow dispatch to deploy without workspace changes

### Item Deployment Failed

**Error**: `Failed to publish item: <item-name>`

**Solution**:
- Check item definition files are valid JSON/Python
- Verify metadata files are present
- Check item name follows Fabric naming restrictions
- Review workspace's `parameter.yml` for correct ID transformations

### Rollback Failed

**Error**: Some workspaces rolled back, others failed

**Solution**:
- Review deployment logs to identify failure point
- Check Service Principal permissions on all workspaces
- May require manual restoration of workspace state
- Verify workspace items can be modified/deleted by Service Principal

### Multiple Workspaces, Only One Deployed

**Error**: Only first workspace deployed, others skipped

**Solution**:
- This may be expected behavior if only one workspace changed (auto deployment)
- For manual deployment, verify all workspaces have `parameter.yml` files
- Check logs for workspace detection output

## Adding New Workspaces

To add a new workspace to the repository:

1. **Create workspace folder structure**:
```bash
mkdir workspaces/"New Workspace"
```

2. **Create parameter.yml**:
```yaml
# workspaces/New Workspace/parameter.yml
find_replace:
  - find_value: "dev-item-id"
    replace_value:
      _ALL_: "$items.Lakehouse.your_lakehouse.id"
    item_type: "Notebook"
    description: "Replace item references"
```

3. **Add workspace items**:
```bash
mkdir -p workspaces/"New Workspace"/1_Bronze
mkdir -p workspaces/"New Workspace"/2_Silver
# Add Lakehouses, Notebooks, etc.
```

4. **Create Fabric workspaces**:
   - Create `[D] New Workspace` in Fabric (Dev environment)
   - Create `[T] New Workspace` in Fabric (Test environment)
   - Create `[P] New Workspace` in Fabric (Prod environment)
   - Grant Service Principal access to all three workspaces

5. **Commit and deploy**:
```bash
git add workspaces/"New Workspace"
git commit -m "feat: add New Workspace"
git push
```

The pipeline will automatically detect and deploy the new workspace on merge to main.

## Next Steps

Once setup is complete:

1. ✅ Configure branch protection rules on `main`
2. ✅ Set up team notifications for deployment failures
3. ✅ Document your specific lakehouse IDs in parameter.yml
4. ✅ Train team on PR workflow
5. ✅ Schedule regular test deployments

## Support

For issues with:
- **Fabric API**: [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- **fabric-cicd library**: [PyPI Package](https://pypi.org/project/fabric-cicd/)
- **GitHub Actions**: [GitHub Actions Documentation](https://docs.github.com/actions)

## Security Best Practices

- ✅ Rotate Service Principal secrets regularly (every 90 days)
- ✅ Use GitHub environment secrets for sensitive values
- ✅ Enable branch protection rules on `main`
- ✅ Require PR reviews before merging
- ✅ Enable audit logging for Fabric workspaces
- ✅ Use least privilege for Service Principal permissions
