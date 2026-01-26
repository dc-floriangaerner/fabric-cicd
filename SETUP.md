# Setup Guide: GitHub Actions CI/CD for Microsoft Fabric

This guide walks you through setting up the CI/CD pipeline for your Fabric workspace.

## Prerequisites Checklist

- [ ] Microsoft Fabric workspace access (Admin or Contributor)
- [ ] Azure AD (Entra ID) tenant access to create Service Principal
- [ ] GitHub repository with Actions enabled
- [ ] Dev, Test, and Prod Fabric workspaces created

> **Note**: Azure subscription access is NOT required. The Service Principal only needs Microsoft Entra ID authentication and Fabric workspace permissions.

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

> **Important**: This Service Principal does NOT need any Azure subscription permissions. It only needs Microsoft Entra ID authentication and will be granted workspace-level permissions in Fabric.

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create Service Principal (without subscription role assignment)
az ad sp create-for-rbac --name "fabric-cicd-deployment" --skip-assignment

# Output will show:
# {
#   "clientId": "xxx",      # AZURE_CLIENT_ID
#   "clientSecret": "xxx",  # AZURE_CLIENT_SECRET
#   "tenantId": "xxx"       # AZURE_TENANT_ID
# }
```

> **Note**: We use `--skip-assignment` because this Service Principal does not need subscription-level permissions. All required permissions are granted at the Fabric workspace level.

## Step 2: Grant Fabric Workspace Permissions

For **each workspace** (Dev, Test, Prod):

1. Open the Fabric workspace
2. Click **Workspace settings** → **Manage access**
3. Click **Add people or groups**
4. Search for your Service Principal name (`fabric-cicd-deployment`)
5. Assign role: **Admin** or **Contributor**
6. Click **Add**

## Step 3: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `AZURE_CLIENT_ID` | Service Principal Client ID | Azure AD App Registration |
| `AZURE_CLIENT_SECRET` | Service Principal Secret | Azure AD App Registration → Certificates & secrets |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | Azure AD App Registration |

> **Note**: `AZURE_SUBSCRIPTION_ID` is NOT required. Microsoft Fabric API operations only need Entra ID authentication and workspace permissions.

## Step 4: Configure GitHub Environments

Create three environments for your deployments:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Create three environments:
   - `dev` (auto-deploys on merge to main)
   - `test` (manual deployment via workflow dispatch)
   - `production` (manual deployment via workflow dispatch)

**Environment Configuration**:
- **Deployment branches**: Set to "Protected branches only" or "Selected branches"
- This controls which branches can deploy to each environment

> **Note**: Required reviewers and wait timers require GitHub Team/Enterprise plan. This setup uses manual workflow triggers for Test and Prod deployments instead.

## Step 5: Configure GitHub Variables

1. Go to **Settings** → **Secrets and variables** → **Actions** → **Variables** tab
2. Click **New repository variable** for each:

| Variable Name | Description | Example Value |
|------------|-------------|---------------|
| `WORKSPACE_NAME_DEV` | Development workspace name | `[D] Fabric Blueprint` |
| `WORKSPACE_NAME_TEST` | Test workspace name | `[T] Fabric Blueprint` |
| `WORKSPACE_NAME_PROD` | Production workspace name | `[P] Fabric Blueprint` |

## Step 6: Update parameter.yml

Get Item IDs from your **Dev workspace**:

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

### Update parameter.yml

```yaml
find_replace:
  # Replace this with actual Dev lakehouse_bronze ID
  - find_value: "12345678-1234-1234-1234-123456789abc"
    replace_value:
      _ALL_: "$items.Lakehouse.lakehouse_bronze.id"
    item_type: "Notebook"
```

## Step 7: Create Fabric Workspaces

Create three workspaces with the naming convention:

- `[D] Fabric Blueprint` - Development
- `[T] Fabric Blueprint` - Test
- `[P] Fabric Blueprint` - Production

**Important**: These names should match the values you set in GitHub Variables (`WORKSPACE_NAME_DEV`, `WORKSPACE_NAME_TEST`, `WORKSPACE_NAME_PROD`).

## Step 8: Test the Pipeline

### Test Dev Deployment (Auto)

1. Create a test change:
```bash
git checkout -b feature/test-deployment
# Make a small change
echo "# Test" >> test.md
git add test.md
git commit -m "test: verify CI/CD pipeline"
git push origin feature/test-deployment
```

2. Create Pull Request to `main`
3. Merge the PR
4. Watch the **Actions** tab for automatic deployment to Dev

### Test Manual Deployment to Test

1. After Dev deployment succeeds
2. Go to **Actions** → **Deploy to Test**
3. Click **Run workflow**
4. In the confirmation field, type: `deploy-test`
5. Click **Run workflow** button
6. Monitor the deployment in the Actions tab

### Test Manual Deployment to Production

1. After Test deployment is verified
2. Go to **Actions** → **Deploy to Production**
3. Click **Run workflow**
4. In the confirmation field, type: `deploy-production`
5. (Optional) Add deployment notes
6. Click **Run workflow** button
7. Monitor the deployment in the Actions tab

## Step 9: Verify Deployment

### Check Workspace

1. Open the target workspace in Fabric (Dev/Test/Prod)
2. Verify items are deployed:
   - Lakehouses (lakehouse_bronze, lakehouse_silver, lakehouse_gold)
   - Notebooks (nb_sl_transform, nb_gd_modeling)
   - Pipelines (cp_br_source)

### Check Logs

1. In GitHub Actions, click on the workflow run
2. Expand the deployment step (e.g., "Deploy to Dev Workspace")
3. Verify:
   - Authentication succeeded
   - Items published
   - No errors

## Deployment Workflow Summary

| Environment | Trigger | Approval | When to Use |
|------------|---------|----------|-------------|
| **Dev** | Automatic on merge to `main` | None | After PR approval and merge |
| **Test** | Manual workflow dispatch | Typed confirmation: `deploy-test` | After Dev deployment verified |
| **Production** | Manual workflow dispatch | Typed confirmation: `deploy-production` | After Test deployment verified |

This approach gives you full control over Test and Prod deployments while automating Dev deployments for rapid iteration.

## Troubleshooting

### Authentication Failed

**Error**: `ClientSecretCredential authentication failed` or `DefaultAzureCredential failed to retrieve a token`

**Solution**:
- Verify GitHub secrets are correct (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
- Check Service Principal has Fabric workspace access (Admin or Contributor)
- Ensure the Service Principal is created in the correct Azure AD tenant
- Verify the client secret hasn't expired

### Workspace Not Found

**Error**: `Workspace '[D] Fabric Blueprint' not found`

**Solution**:
- Verify workspace name matches exactly (including prefix)
- Check Service Principal has access to workspace
- Update `DEV_WORKSPACE_NAME` in workflow file if different

### Item Deployment Failed

**Error**: `Failed to publish item: <item-name>`

**Solution**:
- Check item definition files are valid JSON/Python
- Verify metadata files are present
- Check item name follows Fabric naming restrictions
- Review parameter.yml for correct ID transformations

### No Items Deployed

**Error**: Pipeline succeeds but no items in workspace

**Solution**:
- Verify `repository_directory` points to correct folder (`Fabric Blueprint`)
- Check item structure matches expected format
- Ensure item types are in scope for deployment

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
