---
applyTo: "workspaces/**"
description: "Microsoft Fabric workspace items and configurations"
---

# Fabric Workspace Items Instructions

## Specific Guidelines for workspaces/ Directory

### Directory Structure

Each workspace folder represents a separate Fabric workspace deployment target:

```
workspaces/
├── <Workspace Name>/
│   ├── config.yml              # Workspace names per environment
│   ├── parameter.yml           # ID transformation rules
│   ├── 1_Bronze/              # Bronze layer items
│   ├── 2_Silver/              # Silver layer items
│   ├── 3_Gold/                # Gold layer items
│   └── 4_Analytics/           # Analytics layer items
```

### Configuration Files

**config.yml** - Workspace deployment configuration:
```yaml
core:
  workspace:
    dev: "[D] Workspace Name"
    test: "[T] Workspace Name"
    prod: "[P] Workspace Name"
  repository_directory: "."
  parameter: "parameter.yml"

features:
  - enable_experimental_features
  - enable_config_deploy
```

**parameter.yml** - ID transformation rules:
```yaml
find_replace:
  - find_value: "dev-lakehouse-id-guid"
    replace_value:
      _ALL_: "$items.Lakehouse.lakehouse_name.id"
    item_type: "Notebook"
    is_regex: "false"
    description: "Replace lakehouse references"
```

### Fabric Item Types

**Lakehouse** - Data storage:
```
lakehouse_name.Lakehouse/
├── lakehouse.metadata.json     # {"defaultSchema":"dbo"}
├── alm.settings.json          # ALM configuration
└── shortcuts.metadata.json    # Shortcuts (can be empty: [])
```

**Notebook** - PySpark/Python notebooks:
```
nb_name.Notebook/
├── notebook-content.py        # Python with METADATA blocks
└── notebook.metadata.json
```

**DataPipeline** - Copy jobs and pipelines:
```
cp_name.DataPipeline/
├── pipeline-content.json      # Pipeline definition
└── pipeline.metadata.json
```

### Naming Conventions

**Item Prefixes:**
- `cp_` - Copy jobs (data pipelines)
- `nb_` - Notebooks (PySpark/Python)
- `lakehouse_` - Lakehouse data stores
- `da_` - Data agents

**Layer Prefixes:**
- `br_` - Bronze layer (raw ingestion)
- `sl_` - Silver layer (transformation)
- `gd_` - Gold layer (modeling/analytics)

**Example:** `nb_sl_transform.Notebook` = Silver layer transformation notebook

### Notebook METADATA Structure

**CRITICAL**: Never modify or break METADATA blocks:

```python
# METADATA ********************
# META {
# META   "kernel_info": {"name": "synapse_pyspark"},
# META   "dependencies": {}
# META }

# CELL ********************
# Your code here

# CELL ********************
# More code
```

### JSON File Conventions

- All JSON must be valid and properly formatted
- Use `python -m json.tool file.json` to validate
- No trailing commas
- Consistent indentation (2 or 4 spaces)

### YAML File Conventions

- Use 2 spaces for indentation (not tabs)
- Add descriptive comments for complex transformations
- Escape special regex characters in `find_value` patterns
- Quote string values containing special characters

### Files That Should NEVER Be Modified

- `**/.platform` files (Fabric platform metadata)
- GUID-like IDs in file content (environment-specific)
- Notebook METADATA blocks (breaks Fabric compatibility)

### Adding New Items

1. Create item directory with correct naming: `<name>.<ItemType>/`
2. Add required metadata files (see examples in existing items)
3. Parameterize all environment-specific IDs
4. Update workspace `parameter.yml` with transformation rules
5. Test locally before committing

### Security

**NEVER commit:**
- Workspace IDs in plain text (use parameter.yml transformations)
- Connection strings with credentials
- Service Principal secrets
- Personal Access Tokens
