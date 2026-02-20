terraform {
  required_version = ">= 1.9"

  required_providers {
    fabric = {
      source  = "microsoft/fabric"
      version = "~> 0.1"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-fabric-cicd-tfstate"
    storage_account_name = "stsfabriccicdtfstate"
    container_name       = "tfstate"
    key                  = "fabric-cicd.tfstate"
  }
}

provider "fabric" {}

# ──────────────────────────────────────────────
# Workspaces
# ──────────────────────────────────────────────

resource "fabric_workspace" "fabric_blueprint" {
  display_name = var.workspace_name_fabric_blueprint
  capacity_id  = var.capacity_id
}

# ──────────────────────────────────────────────
# Entra Admin Group → Admin on each workspace
# ──────────────────────────────────────────────

resource "fabric_workspace_role_assignment" "fabric_blueprint_admin_group" {
  workspace_id = fabric_workspace.fabric_blueprint.id
  principal_id = var.entra_admin_group_object_id
  role         = "Admin"
}
