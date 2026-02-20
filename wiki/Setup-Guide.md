# Setup Guide: GitHub Actions CI/CD for Microsoft Fabric

This guide walks you through setting up the CI/CD pipeline for multi-workspace Fabric deployments.

**⏱️ Estimated Time**: 30-45 minutes

**📋 What You'll Accomplish**:
- Create Azure Service Principal for authentication
- Bootstrap Terraform state storage (one-time)
- Provision Fabric workspaces with Terraform
- Configure GitHub repository secrets
- Test automated deployment to Dev environment

## Prerequisites Checklist

- [ ] Microsoft Fabric workspace access (Admin or Contributor)
- [ ] Microsoft Entra ID tenant access to create Service Principal
- [ ] GitHub repository with Actions enabled
- [ ] Azure subscription access to create a storage account (for Terraform state)

## Step 1: Create Azure Service Principal

**⏱️ Time**: ~10 minutes

### Using Azure Portal

1. Navigate to **Microsoft Entra ID** → **App registrations**
2. Click **New registration**
3. Name: `fabric-cicd-deployment`
4. Click **Register**
5. Copy the **Application (client) ID** (this is `AZURE_CLIENT_ID`)
6. Copy the **Directory (tenant) ID** (this is `AZURE_TENANT_ID`)
7. Go to **Certificates & secrets** → **New client secret**
8. Add description: `GitHub Actions`
9. Copy the **secret value** (this is `AZURE_CLIENT_SECRET`)

### Using Azure CLI

```bash
# Login to Azure
az login

# Create Service Principal
SP_OUTPUT=$(az ad sp create-for-rbac --name "fabric-cicd-deployment" --skip-assignment)

# Extract values
echo "AZURE_CLIENT_ID:" $(echo $SP_OUTPUT | jq -r '.clientId')
echo "AZURE_CLIENT_SECRET:" $(echo $SP_OUTPUT | jq -r '.clientSecret')
echo "AZURE_TENANT_ID:" $(echo $SP_OUTPUT | jq -r '.tenantId')

# Get Object ID for the Service Principal
CLIENT_ID=$(echo $SP_OUTPUT | jq -r '.clientId')
OBJECT_ID=$(az ad sp show --id $CLIENT_ID --query id -o tsv)
echo "DEPLOYMENT_SP_OBJECT_ID: $OBJECT_ID"
```

## Step 2: Bootstrap Terraform State Storage (One-Time)

**⏱️ Time**: ~5 minutes

Terraform tracks what it has created using a state file. The file is stored in Azure Blob Storage so all CI/CD runs share the same state.

Create the storage account once — Terraform manages everything after that.

```bash
# Set variables (storage account name must be globally unique, lowercase, 3–24 chars)
RESOURCE_GROUP="rg-fabric-cicd-tfstate"
STORAGE_ACCOUNT="stsfabriccicdtfstate"
CONTAINER="tfstate"
LOCATION="westeurope"

# Create resource group and storage
az group create --name $RESOURCE_GROUP --location $LOCATION
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --sku Standard_LRS \
  --kind StorageV2 \
  --min-tls-version TLS1_2
az storage container create \
  --name $CONTAINER \
  --account-name $STORAGE_ACCOUNT \
  --auth-mode login
```

Then grant the Service Principal access to write state:

```bash
SP_OBJECT_ID=$(az ad sp show --id $AZURE_CLIENT_ID --query id -o tsv)
az role assignment create \
  --assignee $SP_OBJECT_ID \
  --role "Storage Blob Data Contributor" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/$RESOURCE_GROUP/storageAccounts/$STORAGE_ACCOUNT"
```

Update `terraform/main.tf` `backend "azurerm"` block if you used different names.

## Step 3: Provision Fabric Workspaces with Terraform

**⏱️ Time**: ~10 minutes

Workspace lifecycle is managed by Terraform — **not** by the Python deployment scripts.

### 3a — Populate tfvars files

Edit the three files under `terraform/environments/`:

| File | Purpose |
|---|---|
| `dev.tfvars` | Dev workspace name, capacity ID, Entra group OID |
| `test.tfvars` | Test workspace name, capacity ID, Entra group OID |
| `prod.tfvars` | Prod workspace name, capacity ID, Entra group OID |

| Variable | Where to find it |
|---|---|
| `workspace_name_*` | Already matches `workspaces/*/config.yml` — e.g. `[D] Fabric Blueprint` |
| `capacity_id` | Fabric Admin Portal → Capacity Settings → GUID |
| `entra_admin_group_object_id` | Azure AD → Groups → your admin group → Object ID |

### 3b — Run first apply

```bash
cd terraform
terraform init
terraform apply -var-file=environments/dev.tfvars
```

Repeat for `test.tfvars` and `prod.tfvars` as needed.

After this, the workspace exists and the CI/CD pipeline can deploy items into it.

> **Note**: The Service Principal that creates the workspace is automatically granted Admin access.
> No separate role assignment is needed for the SP itself.

## Step 4: Configure GitHub Secrets

**⏱️ Time**: ~5 minutes

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

### Required Secrets

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `AZURE_CLIENT_ID` | Service Principal Client ID | Azure AD App Registration → Overview |
| `AZURE_CLIENT_SECRET` | Service Principal Secret | Azure AD App Registration → Certificates & secrets |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | Azure AD App Registration → Overview |
| `ARM_SUBSCRIPTION_ID` | Azure subscription ID | Azure Portal → Subscriptions |

## Step 5: Test the Pipeline

**⏱️ Time**: ~15-20 minutes

### Test Dev Deployment (Automatic)

1. Create a test change in a workspace:
```bash
git checkout -b feature/test-deployment
echo "# Test" >> workspaces/"Fabric Blueprint"/test.md
git add workspaces/"Fabric Blueprint"/test.md
git commit -m "test: verify CI/CD pipeline"
git push origin feature/test-deployment
```

2. Create Pull Request to `main`
3. Merge the PR
4. Watch the **Actions** tab for automatic deployment to Dev

### Test Manual Deployment to Test/Production

1. Go to **Actions** → **Deploy to Microsoft Fabric**
2. Click **Run workflow**
3. Select environment (**test** or **prod**)
4. Click **Run workflow** button
5. Monitor the deployment in the Actions tab

## ✅ Success Criteria

You've successfully completed setup when:

- [ ] Service Principal created with Client ID, Secret, and Tenant ID recorded
- [ ] Terraform state storage created and SP granted access
- [ ] Workspaces provisioned for Dev (and Test/Prod as needed) via Terraform
- [ ] All required GitHub secrets configured
- [ ] Test deployment to Dev succeeded without errors
- [ ] Workspace items deployed correctly to Dev workspace
- [ ] GitHub Actions workflow completed with green checkmark

**What's Next?** If all criteria are met, you're ready to configure your workspaces and deploy!

## Next Steps

- Configure [Workspace Configuration](Workspace-Configuration) for your workspaces
- Review the [Deployment Workflow](Deployment-Workflow) to understand the deployment process
- Check [Troubleshooting](Troubleshooting) for common issues

## Resources

- [Full Setup Documentation (SETUP.md)](https://github.com/dc-floriangaerner/fabric-cicd/blob/main/SETUP.md)
- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
