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
- Its own `config.yml` configuration file (defines workspace names per environment)
- Its own `parameter.yml` configuration file (defines ID transformations)
- Fabric items (Lakehouses, Notebooks, Pipelines, etc.)

Workspace names are explicitly configured in `config.yml`:
- **Dev**: `[D] <workspace-name>`
- **Test**: `[T] <workspace-name>`
- **Prod**: `[P] <workspace-name>`

## Step 1: Create Azure Service Principal

### Option A: Using Azure Portal

1. Navigate to **Microsoft Entra ID** → **App registrations**
2. Click **New registration**
3. Name: `dc-fabric-cicd-deployment`
4. Click **Register**
5. Copy the **Application (client) ID** (this is `AZURE_CLIENT_ID`)
6. Copy the **Directory (tenant) ID** (this is `AZURE_TENANT_ID`)
7. **IMPORTANT**: Copy the **Object ID** for role assignments:
   - Go to **Azure Active Directory** → **Enterprise Applications**
   - Search for your application by the **Application (client) ID** you just copied
   - Click on the application
   - Copy the **Object ID** (this is `DEPLOYMENT_SP_OBJECT_ID`)
   - ⚠️ **Note**: This is different from the Application (client) ID!
8. Go back to **App registrations** → Your app → **Certificates & secrets** → **New client secret**
9. Add description: `GitHub Actions`
10. Copy the **secret value** (this is `AZURE_CLIENT_SECRET`)

### Option B: Using Azure CLI

> **Note:** These commands require `jq` to be installed for JSON parsing. Install it via your package manager (e.g., `apt-get install jq`, `brew install jq`) or use the alternative command below for a simpler approach without `jq`.

```bash
# Login to Azure
az login

# Create Service Principal
SP_OUTPUT=$(az ad sp create-for-rbac --name "dc-fabric-cicd-deployment" --skip-assignment)

# Extract values
echo "AZURE_CLIENT_ID:" $(echo $SP_OUTPUT | jq -r '.clientId')
echo "AZURE_CLIENT_SECRET:" $(echo $SP_OUTPUT | jq -r '.clientSecret')
echo "AZURE_TENANT_ID:" $(echo $SP_OUTPUT | jq -r '.tenantId')

# Get Object ID for the Service Principal (needed for workspace role assignment)
CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.clientId')
OBJECT_ID=$(az ad sp show --id $CLIENT_ID --query id -o tsv)
echo "DEPLOYMENT_SP_OBJECT_ID: $OBJECT_ID"
```

**Alternative without jq:**
```bash
# Create Service Principal and display as table
az ad sp create-for-rbac --name "dc-fabric-cicd-deployment" --skip-assignment --output table

# Get Object ID separately (use Client ID from above)
az ad sp show --id <YOUR-CLIENT-ID> --query id -o tsv
```

## Step 1b: Configure Service Principal for Workspace Creation (For Auto-Creation)

**This step is required for automatic workspace creation. Skip if you plan to manually create all workspaces.**

The Service Principal needs **TWO separate configurations** to create workspaces:

### 1. Enable Fabric Tenant Setting

1. Open **Fabric Admin Portal**: https://app.fabric.microsoft.com/admin-portal
2. Navigate to **Tenant Settings** → **Developer Settings**
3. Find setting: **Service principals can create workspaces, connections, and deployment pipelines**
4. Enable the setting
5. Under **Apply to**, select **Specific security groups**
6. Add your Service Principal:
   - Search by the Service Principal name (`dc-fabric-cicd-deployment`)
   - Or create a security group and add the Service Principal to it
7. Click **Apply**

### 2. Assign Service Principal as Capacity Administrator

**⚠️ CRITICAL**: Even with the tenant setting enabled, the Service Principal **must be added as a Capacity Administrator** to create workspaces on that capacity.

1. Open **Azure Portal**: https://portal.azure.com
2. Navigate to your **Fabric Capacity** resource (search for "Fabric capacities" or find it in your resource group)
3. Go to **Settings** → **Capacity administrators**
4. Click **Add** under the "Accounts" section
5. Enter one of the following:
   - The Service Principal's **Client ID** (Application ID)
   - Or search for the **Enterprise Application** by name (`dc-fabric-cicd-deployment`)
6. Click **Add** to confirm

**⚠️ Important Notes:**
- This is **NOT** done through "Access Control (IAM)" - it's a dedicated **Capacity administrators** setting
- Without this assignment, workspace creation will fail with a 403 error even if tenant settings are correct
- You need to add the SP as capacity admin for **each capacity** (Dev, Test, Prod if using separate capacities)

**Why these permissions are needed:**
- Tenant setting: Grants organization-wide permission for service principals to create workspaces
- Capacity admin: Grants permission to create workspaces on the specific capacity
- Both are required; having only one will result in a 403 Forbidden error

## Step 2: Get Fabric Capacity IDs (For Auto-Creation)

**This step is required for automatic workspace creation. Skip if you plan to manually create all workspaces.**

Get the Capacity ID for each environment (Dev, Test, Prod):

### Option A: Using Fabric Portal

1. Go to **Fabric Admin Portal** → **Capacity Settings**
2. Click on your capacity for Dev environment
3. Copy the capacity ID from the URL or capacity details
4. Repeat for Test and Prod capacities

### Option B: Using PowerShell

```powershell
# Install required module
Install-Module -Name MicrosoftPowerBIMgmt -Force

# Connect to Power BI (Fabric uses same authentication)
Connect-PowerBIServiceAccount

# List all capacities
Get-PowerBICapacity | Select-Object -Property Id, DisplayName, State

# Copy the capacity IDs for your Dev, Test, and Prod environments
```

## Step 3: Grant Fabric Workspace Permissions

**Option 1: Manual Workspace Creation (Traditional Approach)**

For **each workspace** in **each environment** (Dev, Test, Prod):

1. Manually create the workspace in Fabric portal
2. Name it with correct prefix: `[D] <folder-name>`, `[T] <folder-name>`, `[P] <folder-name>`
3. Click **Workspace settings** → **Manage access**
4. Click **Add people or groups**
5. Search for your Service Principal name (`dc-fabric-cicd-deployment`)
6. Assign role: **Admin** or **Contributor**
7. Click **Add**

**Example: For "Fabric Blueprint" workspace, grant permissions to:**
- `[D] Fabric Blueprint` (Dev)
- `[T] Fabric Blueprint` (Test)
- `[P] Fabric Blueprint` (Prod)

Repeat for all workspace folders in your repository.

**Option 2: Automatic Workspace Creation (New Feature)**

If you completed Step 1b (Workspace Creator permission), the deployment pipeline will:
1. Detect if workspace exists
2. Create workspace automatically if missing
3. Assign it to the configured capacity
4. Grant the Service Principal admin access
5. Proceed with item deployment

**No manual workspace creation needed!** Just add a new folder to `workspaces/` and the CI/CD will handle the rest.


## Step 4: Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

### Required Secrets (Always Needed)

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `AZURE_CLIENT_ID` | Service Principal Client ID | Azure AD App Registration → Overview |
| `AZURE_CLIENT_SECRET` | Service Principal Secret | Azure AD App Registration → Certificates & secrets |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | Azure AD App Registration → Overview |

### Optional Secrets (For Auto-Creation Feature)

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `FABRIC_CAPACITY_ID_DEV` | Dev Fabric capacity GUID | Fabric Admin Portal → Capacity Settings → Dev capacity |
| `FABRIC_CAPACITY_ID_TEST` | Test Fabric capacity GUID | Fabric Admin Portal → Capacity Settings → Test capacity |
| `FABRIC_CAPACITY_ID_PROD` | Prod Fabric capacity GUID | Fabric Admin Portal → Capacity Settings → Prod capacity |
| `DEPLOYMENT_SP_OBJECT_ID` | Service Principal Object ID (NOT Client ID) | Azure AD → Enterprise Applications → Your app → Object ID |
| `FABRIC_ADMIN_GROUP_ID` | Entra ID (Azure AD) group for workspace admin access | Azure AD → Groups → Your admin group → Object ID |

**⚠️ Important: Object ID vs Client ID**
- `AZURE_CLIENT_ID` = Application (Client) ID from App Registration
- `DEPLOYMENT_SP_OBJECT_ID` = Object ID from Enterprise Application
- These are **different values**! The Object ID is needed for workspace role assignments.

**How to find Object ID:**
1. Azure Portal → **Azure Active Directory** → **Enterprise Applications**
2. Search for your application using the **Client ID** (Application ID)
3. Click on the application
4. Copy the **Object ID** field at the top

**How to find Entra ID Group Object ID (for FABRIC_ADMIN_GROUP_ID):**
1. Azure Portal → **Azure Active Directory** → **Groups**
2. Search for your admin group
3. Click on the group
4. Copy the **Object ID** field

**Note about FABRIC_ADMIN_GROUP_ID:**
- This is **optional** but recommended for centralized access management
- If configured, all members of this Entra ID group will automatically receive **Admin** permissions to all deployed workspaces
- This allows you to manage workspace access through Azure AD group membership instead of individual user assignments
- The group is assigned admin access when workspaces are created or updated via the deployment pipeline
- **Security**: The group ID must be stored as a GitHub Secret, never commit it to the repository

**Note**: If you don't configure the capacity secrets, you must manually create all workspaces before deployment.

## Step 5: Configure GitHub Environments

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

## Step 6: Create Fabric Workspaces (Manual Creation Only)

**Skip this step if you configured the automatic workspace creation feature (Step 1b and capacity secrets).**

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
- If auto-creation is enabled, these workspaces will be created automatically on first deployment

## Step 6b: Create config.yml for Each Workspace

Each workspace folder requires a `config.yml` file that defines workspace names for each environment.

**Example: `workspaces/Fabric Blueprint/config.yml`**

```yaml
core:
  workspace:
    dev: "[D] Fabric Blueprint"
    test: "[T] Fabric Blueprint"
    prod: "[P] Fabric Blueprint"

  repository_directory: "."  # Relative to config.yml location

  parameter: "parameter.yml"  # References parameter.yml in same folder

publish:
  skip:
    dev: false
    test: false
    prod: false

unpublish:
  skip:
    dev: false
    test: false
    prod: false

features:
  - enable_experimental_features
  - enable_config_deploy
```

**Create config.yml for each workspace folder:**
- Fabric Blueprint: `workspaces/Fabric Blueprint/config.yml`
- Fabric Bronze: `workspaces/Fabric Bronze/config.yml`
- Fabric Autocreated Workspace: `workspaces/Fabric Autocreated Workspace/config.yml`

**Important**: The `config.yml` uses experimental fabric-cicd features. The workspace names should match your intended target workspaces.

## Step 7: Update Workspace parameter.yml Files

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
    # Valid optional fields: is_regex, item_type, item_name, file_path
```

Each workspace has its own independent configuration file.


## Step 8: Test the Pipeline

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
   - Items published for each workspace
   - No errors or rollback triggered

## Deployment Workflow Summary

| Environment | Trigger | When to Use |
|------------|---------|-------------|
| **Dev** | Automatic on merge to `main` | After PR approval and merge |
| **Test** | Manual workflow dispatch | After Dev deployment verified |
| **Production** | Manual workflow dispatch | After Test deployment verified |

### Atomic Rollback (Planned Feature)

Atomic rollback is a planned enhancement for future implementation. This feature would ensure that if any workspace deployment fails, all previously deployed workspaces in that run are automatically rolled back:

```
Workspace A → Success ✓
Workspace B → Success ✓  
Workspace C → FAILURE ✗
→ Rollback B and A (PLANNED)
→ Exit with error
```

This would ensure environments remain in a consistent state. Currently, deployments proceed independently for each workspace.


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
- Each workspace folder must contain both `config.yml` and `parameter.yml` files
- Verify folder structure: `workspaces/<workspace-name>/config.yml` and `workspaces/<workspace-name>/parameter.yml`

### Deployment Not Triggered

**Error**: Pipeline doesn't run after merge to main

**Solution**:
- Automatic Dev deployments only trigger on changes in `workspaces/**` paths
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

## Adding New Workspaces

To add a new workspace to the repository:

1. **Create workspace folder structure**:
```bash
mkdir workspaces/"New Workspace"
```

2. **Create config.yml**:
```yaml
# workspaces/New Workspace/config.yml
core:
  workspace:
    dev: "[D] New Workspace"
    test: "[T] New Workspace"
    prod: "[P] New Workspace"

  repository_directory: "."
  parameter: "parameter.yml"

publish:
  skip:
    dev: false
    test: false
    prod: false

unpublish:
  skip:
    dev: false
    test: false
    prod: false

features:
  - enable_experimental_features
  - enable_config_deploy
```

3. **Create parameter.yml**:
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

The pipeline will automatically deploy the new workspace on merge to main.

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
