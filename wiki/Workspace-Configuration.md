# Workspace Configuration

Learn how to configure workspace deployment settings using `config.yml` and `parameter.yml` files.

**⏱️ Estimated Time**: 15-20 minutes per workspace

## Overview

Each workspace folder in the repository contains two critical configuration files:
- **config.yml** - Workspace names and deployment settings
- **parameter.yml** - ID transformation rules for environment-specific values

> **Prerequisite**: Workspaces must exist in Fabric before the deployment pipeline can deploy items into them. Workspace lifecycle (create / configure) is managed by Terraform (`terraform.yml`). The workspace names in `config.yml` must match the names Terraform creates — that is the shared contract between the two pipelines.

## config.yml Structure

The `config.yml` file defines workspace names for each environment and controls deployment behavior.

### Example

```yaml
core:
  workspace:
    dev: "[D] Fabric Blueprint"
    test: "[T] Fabric Blueprint"
    prod: "[P] Fabric Blueprint"

  repository_directory: "."  # Relative to config.yml location

  parameter: "parameter.yml"  # References parameter.yml located in the same workspace directory

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

### Configuration Options

| Field | Description | Required |
|-------|-------------|----------|
| `core.workspace.dev` | Dev workspace name | Yes |
| `core.workspace.test` | Test workspace name | Yes |
| `core.workspace.prod` | Prod workspace name | Yes |
| `core.repository_directory` | Path to workspace items | Yes |
| `core.parameter` | Parameter file name | Yes |
| `publish.skip` | Skip publishing for environment | No |
| `unpublish.skip` | Skip orphan cleanup for environment | No |
| `features` | Enable experimental features | No |

## parameter.yml Structure

The `parameter.yml` file defines ID transformation rules to replace environment-specific values during deployment.

### Example

```yaml
find_replace:
  # Replace lakehouse ID in notebooks
  - find_value: "12345678-1234-1234-1234-123456789abc"
    replace_value:
      _ALL_: "$items.Lakehouse.lakehouse_bronze.id"
    item_type: "Notebook"
    description: "Replace bronze lakehouse references"

  # Replace workspace ID using regex
  - find_value: 'workspace\s*=\s*"([^"]+)"'
    replace_value:
      _ALL_: "$workspace.id"
    is_regex: "true"
    item_type: "Notebook"
    description: "Replace workspace ID references"
```

### Transformation Rules

| Field | Description | Required |
|-------|-------------|----------|
| `find_value` | Value to find (Dev environment) | Yes |
| `replace_value._ALL_` | Replacement value (Target environment) | Yes |
| `item_type` | Item type to apply to (e.g., Notebook) | No |
| `item_name` | Specific item name to apply to | No |
| `file_path` | Specific file path pattern | No |
| `is_regex` | Use regex matching (true/false) | No |
| `description` | Documentation for this rule | No |

### Replacement Variables

Use these special variables in `replace_value`:

| Variable | Description | Example |
|----------|-------------|---------|
| `$items.Lakehouse.<name>.id` | Lakehouse item ID | `$items.Lakehouse.lakehouse_bronze.id` |
| `$items.Lakehouse.<name>.sqlendpoint` | Lakehouse SQL endpoint | `$items.Lakehouse.lakehouse_silver.sqlendpoint` |
| `$workspace.id` | Target workspace ID | `$workspace.id` |

## How to Find Item IDs

Item IDs are GUIDs that uniquely identify items in your Dev workspace.

### Method 1: Using Fabric UI

1. Open item in Dev workspace
2. Check URL for GUID (e.g., `items/12345678-1234-1234-1234-123456789abc`)
3. Copy the GUID value

### Method 2: Using Fabric API

```bash
# Get workspace ID first
WORKSPACE_ID="<your-dev-workspace-id>"

# List all items
az rest --method get \
  --url "https://api.fabric.microsoft.com/v1/workspaces/$WORKSPACE_ID/items"
```

## Adding a New Workspace

> **Provision first**: Before running `fabric-deploy.yml` for a new workspace, add the corresponding Terraform resources in `terraform/main.tf` and `terraform/environments/*.tfvars`, then run `terraform.yml` to create the workspace.

1. Create workspace folder: `workspaces/<Workspace Name>/`
2. Create `config.yml` with workspace names (must match the Terraform `workspace_name_*` values exactly)
3. Create `parameter.yml` with transformation rules
4. Add workspace items (Lakehouses, Notebooks, etc.)
5. Add Terraform resources and run `terraform.yml` for each environment
6. Commit and push to trigger item deployment

## Best Practices

- **Parameterize everything** - No hardcoded IDs
- **Test transformations** - Verify regex patterns at [regex101.com](https://regex101.com/)
- **Document rules** - Use `description` field for clarity
- **Keep Dev IDs** - Always use Dev workspace IDs in `find_value`
- **Independent configs** - Each workspace has its own `config.yml` and `parameter.yml`

## Common Patterns

### Replace Lakehouse References

```yaml
- find_value: "dev-lakehouse-id-guid"
  replace_value:
    _ALL_: "$items.Lakehouse.lakehouse_bronze.id"
  item_type: "Notebook"
```

### Replace SQL Endpoint

```yaml
- find_value: 'database\s*=\s*Sql\.Database\s*\(\s*"([^"]+)"'
  replace_value:
    _ALL_: "$items.Lakehouse.lakehouse_silver.sqlendpoint"
  is_regex: "true"
  item_type: "SemanticModel"
```

### Replace Workspace ID

```yaml
- find_value: "dev-workspace-id-guid"
  replace_value:
    _ALL_: "$workspace.id"
  item_type: "DataPipeline"
```

## Troubleshooting

### IDs Not Transforming

1. Verify `find_value` matches Dev workspace ID exactly
2. Check item type matches (case-sensitive)
3. Test regex patterns if using `is_regex: "true"`
4. Ensure item names match exactly (case-sensitive)

### Deployment Fails

1. Validate YAML syntax: `python -c "import yaml; yaml.safe_load(open('config.yml'))"`
2. Check workspace names match Fabric portal (case-sensitive)
3. Verify parameter file path is correct
4. Review deployment logs for specific errors

## Resources

- [fabric-cicd Library Documentation](https://pypi.org/project/fabric-cicd/)
- [YAML Syntax Reference](https://yaml.org/spec/1.2/spec.html)
- [Regular Expressions Guide](https://regex101.com/)
