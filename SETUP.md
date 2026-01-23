# Setup Guide: GitHub Actions CI/CD for Microsoft Fabric

This guide walks you through setting up the CI/CD pipeline for your Fabric workspace.

## Prerequisites Checklist

- [ ] Microsoft Fabric workspace access (Admin or Contributor)
- [ ] Azure subscription with permissions to create Service Principal
- [ ] GitHub repository with Actions enabled
- [ ] Dev, Test, and Prod Fabric workspaces created

## Step 1: Create Azure Service Principal

### Option A: Using Azure Portal

1. Navigate to **Azure Active Directory** → **App registrations**
2. Click **New registration**
3. Name: `fabric-cicd-deployment`
4. Click **Register**
5. Copy the **Application (client) ID** (this is `AZURE_CLIENT_ID`)
6. Copy the **Directory (tenant) ID** (this is `AZURE_TENANT_ID`)
7. Go to **Certificates & secrets** → **New client secret**
8. Add description: `GitHub Actions`
9. Copy the **secret value** (this is `AZURE_CLIENT_SECRET`)
10. Note your **Subscription ID** from Azure portal home (this is `AZURE_SUBSCRIPTION_ID`)

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create Service Principal
az ad sp create-for-rbac --name "fabric-cicd-deployment" --role contributor --scopes /subscriptions/{subscription-id}

# Output will show:
# {
#   "clientId": "xxx",      # AZURE_CLIENT_ID
#   "clientSecret": "xxx",  # AZURE_CLIENT_SECRET
#   "tenantId": "xxx"       # AZURE_TENANT_ID
# }
```

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
| `AZURE_SUBSCRIPTION_ID` | Azure Subscription ID | Azure Portal → Subscriptions |

## Step 4: Configure GitHub Environments (Optional)

For approval gates on Test and Prod deployments:

1. Go to **Settings** → **Environments**
2. Click **New environment**
3. Create three environments:
   - `dev` (no protection rules)
   - `test` (add required reviewers)
   - `production` (add required reviewers)

**For test and production**:
- Check ☑️ **Required reviewers**
- Add team members who can approve deployments
- Optionally set **Wait timer** (e.g., 5 minutes)

## Step 5: Update parameter.yml

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

## Step 6: Create Fabric Workspaces

Create three workspaces with the naming convention:

- `[D] Fabric Blueprint` - Development
- `[T] Fabric Blueprint` - Test
- `[P] Fabric Blueprint` - Production

**Important**: Match these names exactly in [.github/workflows/fabric-deploy.yml](.github/workflows/fabric-deploy.yml) if different.

## Step 7: Test the Pipeline

### Test Dev Deployment

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
4. Watch the **Actions** tab for deployment to Dev

### Test Manual Promotion

1. After Dev deployment succeeds
2. Go to **Actions** → **Deploy to Microsoft Fabric**
3. Click **Run workflow**
4. Select:
   - ☑️ **Deploy to Test environment**
5. Click **Run workflow**
6. If approvals configured, approve the deployment

## Step 8: Verify Deployment

### Check Dev Workspace

1. Open `[D] Fabric Blueprint` workspace in Fabric
2. Verify items are deployed:
   - Lakehouses (lakehouse_bronze, lakehouse_silver, lakehouse_gold)
   - Notebooks (nb_sl_transform, nb_gd_modeling)
   - Pipelines (cp_br_source)

### Check Logs

1. In GitHub Actions, click on the workflow run
2. Expand "Deploy to Dev Workspace" step
3. Verify:
   - Authentication succeeded
   - Items published
   - No errors

## Troubleshooting

### Authentication Failed

**Error**: `DefaultAzureCredential failed to retrieve a token`

**Solution**:
- Verify GitHub secrets are correct
- Check Service Principal has Fabric workspace access
- Ensure subscription ID is correct

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
