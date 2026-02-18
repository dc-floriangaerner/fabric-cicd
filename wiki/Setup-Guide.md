# Setup Guide: GitHub Actions CI/CD for Microsoft Fabric

This guide walks you through setting up the CI/CD pipeline for multi-workspace Fabric deployments.

**⏱️ Estimated Time**: 30-45 minutes

**📋 What You'll Accomplish**:
- Create Azure Service Principal for authentication
- Provision Fabric workspaces (manually or automatically)
- Configure GitHub repository secrets
- Test automated deployment to Dev environment

## Prerequisites Checklist

- [ ] Microsoft Fabric workspace access (Admin or Contributor)
- [ ] Microsoft Entra ID tenant access to create Service Principal
- [ ] GitHub repository with Actions enabled
- [ ] Dev, Test, and Prod Fabric workspaces — either **manually pre-created** or **auto-created by the Service Principal** (see Step 2)

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

## Step 2: Provision Fabric Workspaces

**⏱️ Time**: ~10 minutes (manual) / ~2 minutes (auto-creation)

> **Choose one approach** before continuing. You do not need to do both.

---

### Option A: Manually Pre-Create Workspaces (Traditional Approach)

Use this option if you want full control over workspace creation, or if your Fabric tenant does not allow Service Principals to create workspaces.

For **each workspace folder** in **each environment** (Dev, Test, Prod):

1. Open [Fabric portal](https://app.fabric.microsoft.com) and create the workspace
2. Name it with the correct environment prefix: `[D] <folder-name>`, `[T] <folder-name>`, `[P] <folder-name>`
   - Example for "Fabric Blueprint": `[D] Fabric Blueprint`, `[T] Fabric Blueprint`, `[P] Fabric Blueprint`
3. Click **Workspace settings** → **Manage access**
4. Click **Add people or groups**
5. Search for your Service Principal name (`fabric-cicd-deployment`)
6. Assign role: **Contributor** (minimum) or **Admin**
7. Click **Add**

Repeat for every workspace folder defined under `workspaces/` in the repository.

---

### Option B: Let the Service Principal Auto-Create Workspaces *(Optional)*

Use this option to skip manual workspace creation. The deployment pipeline will automatically create, configure, and grant access to all workspaces on first run.

**This requires additional one-time configuration:**

#### B1 — Enable Fabric Tenant Setting

1. Open **Fabric Admin Portal**: https://app.fabric.microsoft.com/admin-portal
2. Navigate to **Tenant Settings** → **Developer Settings**
3. Find: **Service principals can create workspaces, connections, and deployment pipelines**
4. Enable the setting and scope it to a security group that includes your Service Principal
5. Click **Apply**

#### B2 — Assign Service Principal as Capacity Administrator

> **⚠️ Required in addition to the tenant setting above.** Without this, workspace creation will fail with a 403 error.

1. Open **Azure Portal** → navigate to your **Fabric Capacity** resource
2. Go to **Settings** → **Capacity administrators**
3. Click **Add** and search for your Service Principal (`fabric-cicd-deployment`)
4. Repeat for **each capacity** (Dev, Test, Prod if using separate capacities)

#### B3 — Add Auto-Creation Secrets to GitHub

Add the following secrets to your GitHub repository (see Step 3 for how to add secrets):

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `FABRIC_CAPACITY_ID_DEV` | Dev Fabric capacity GUID | Fabric Admin Portal → Capacity Settings |
| `FABRIC_CAPACITY_ID_TEST` | Test Fabric capacity GUID | Fabric Admin Portal → Capacity Settings |
| `FABRIC_CAPACITY_ID_PROD` | Prod Fabric capacity GUID | Fabric Admin Portal → Capacity Settings |
| `DEPLOYMENT_SP_OBJECT_ID` | Service Principal Object ID | Azure AD → Enterprise Applications |
| `FABRIC_ADMIN_GROUP_ID` | Entra ID group for admin access | Azure AD → Groups → Object ID |

Once configured, adding a new workspace is as simple as adding a new folder under `workspaces/` — the CI/CD pipeline handles everything else.

---

## Step 3: Configure GitHub Secrets

**⏱️ Time**: ~5 minutes

1. Go to your GitHub repository
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** for each:

### Required Secrets (Always Needed)

| Secret Name | Description | Where to Find |
|------------|-------------|---------------|
| `AZURE_CLIENT_ID` | Service Principal Client ID | Azure AD App Registration → Overview |
| `AZURE_CLIENT_SECRET` | Service Principal Secret | Azure AD App Registration → Certificates & secrets |
| `AZURE_TENANT_ID` | Azure AD Tenant ID | Azure AD App Registration → Overview |

### Optional Secrets (For Auto-Creation — Option B only)

See [Step 2, Option B3](#b3--add-auto-creation-secrets-to-github) above for the full list and descriptions.

## Step 4: Test the Pipeline

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
- [ ] Workspaces are accessible to the Service Principal (either manually granted or auto-creation configured)
- [ ] All required GitHub secrets configured (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`)
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
