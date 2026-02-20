variable "workspace_name_fabric_blueprint" {
  type        = string
  description = "Display name of the Fabric Blueprint workspace for the target environment."
}

variable "capacity_id" {
  type        = string
  description = "Fabric capacity GUID to attach to all workspaces in this environment."
}

variable "entra_admin_group_object_id" {
  type        = string
  description = "Azure AD Object ID of the Entra ID group to assign as workspace Admin."
}
