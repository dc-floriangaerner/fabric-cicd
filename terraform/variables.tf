variable "workspace_name_fabric_blueprint" {
  type        = string
  description = "Display name of the Fabric Blueprint workspace for the target environment."
}

variable "capacity_id" {
  type        = string
  description = "Fabric capacity GUID to attach to all workspaces in this environment."
  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", lower(var.capacity_id)))
    error_message = "capacity_id must be a valid GUID (e.g. xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)."
  }
}

variable "entra_admin_group_object_id" {
  type        = string
  description = "Azure AD Object ID of the Entra ID group to assign as workspace Admin."
  validation {
    condition     = can(regex("^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", lower(var.entra_admin_group_object_id)))
    error_message = "entra_admin_group_object_id must be a valid GUID (e.g. xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)."
  }
}
