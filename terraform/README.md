# Terraform — Fabric Workspace Infrastructure

This directory manages the lifecycle of Microsoft Fabric workspaces using
the [microsoft/fabric Terraform provider](https://registry.terraform.io/providers/microsoft/fabric/latest).

**Rule:** Workspace provisioning lives here. Item deployment lives in `fabric-deploy.yml`.

---

## Architecture

```
terraform/
├── main.tf                   # Provider config, workspace resources, role assignments
├── variables.tf              # Input variables (workspace names, capacity ID, group ID)
├── outputs.tf                # Exported workspace IDs
├── environments/
│   ├── dev.tfvars            # Dev variable values
│   ├── test.tfvars           # Test variable values
│   └── prod.tfvars           # Prod variable values
└── README.md                 # This file
```

---

## One-Time Bootstrap (run manually before first `terraform apply`)

### 1 — Authenticate and select your Azure subscription

```powershell
# Login interactively
az login

# List available subscriptions
az account list --output table

# Set the target subscription
az account set --subscription "<subscription-id>"

# Verify
az account show --output table
```

### 2 — Create Terraform state storage

```powershell
# Set variables
$RESOURCE_GROUP = "rg-fabric-cicd-tfstate"
$STORAGE_ACCOUNT = "stsfabriccicdtfstate"  # Must be globally unique, lowercase, 3-24 chars
$CONTAINER = "tfstate"
$LOCATION = "westeurope"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create storage account
az storage account create `
  --name $STORAGE_ACCOUNT `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --sku Standard_LRS `
  --kind StorageV2 `
  --min-tls-version TLS1_2

# Create blob container
az storage container create `
  --name $CONTAINER `
  --account-name $STORAGE_ACCOUNT `
  --auth-mode login
```

Update `main.tf` `backend "azurerm"` block if you use different names.

### 3 — Grant the CI Service Principal access to the state storage

```powershell
$SP_OBJECT_ID = "<sp-object-id>"
$RESOURCE_GROUP = "rg-fabric-cicd-tfstate"
$STORAGE_ACCOUNT = "stsfabriccicdtfstate"
$SUBSCRIPTION_ID = "<your-subscription-id>"

az role assignment create `
  --assignee $SP_OBJECT_ID `
  --role "Storage Blob Data Contributor" `
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.Storage/storageAccounts/$STORAGE_ACCOUNT"
```

### 4 — Populate environments/*.tfvars

Edit `environments/dev.tfvars`, `test.tfvars`, and `prod.tfvars`:

| Variable | Where to find it |
|---|---|
| `workspace_name_*` | Already set — matches `workspaces/*/config.yml` names |
| `capacity_id` | Fabric Admin Portal → Capacity Settings → GUID |
| `entra_admin_group_object_id` | Azure AD → Groups → your admin group → Object ID |

### 5 — Add GitHub secrets

| Secret | Description |
|---|---|
| `AZURE_CLIENT_ID` | Service Principal Client ID (reused from CI/CD) |
| `AZURE_CLIENT_SECRET` | Service Principal Secret (reused from CI/CD) |
| `AZURE_TENANT_ID` | Azure AD Tenant ID (reused from CI/CD) |
| `ARM_SUBSCRIPTION_ID` | Azure subscription ID for state storage access |

### 6 — Run first apply for Dev

```powershell
# Authenticate
az login --service-principal `
  --username $AZURE_CLIENT_ID `
  --password $AZURE_CLIENT_SECRET `
  --tenant $AZURE_TENANT_ID

# Initialize
terraform init

# Apply
terraform apply -var-file=environments/dev.tfvars
```

---

## Adding a New Workspace

1. Add a `fabric_workspace` resource to `main.tf`
2. Add a `fabric_workspace_role_assignment` for the Entra Admin Group
3. Add the workspace name variable to `variables.tf`
4. Add the output to `outputs.tf`
5. Set the variable value in each `environments/*.tfvars`
6. Push to `main` — `terraform.yml` applies the change automatically

---

## State Management

Terraform state is stored in Azure Blob Storage with automatic state locking. Concurrent runs are prevented by the `concurrency` setting in `terraform.yml`.

---

## Notes

- The Service Principal that runs Terraform **automatically becomes Admin** on any workspace it creates — no explicit role assignment is needed for the SP itself.
- Workspace names in `environments/*.tfvars` must match the names in `workspaces/*/config.yml` exactly — that is the shared contract between Terraform (creates the workspace) and `fabric-cicd` (deploys items into it).
