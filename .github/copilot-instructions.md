# Copilot Instructions for Fabric CI/CD Reference Architecture

## Project Overview

This is a **reference architecture** for Microsoft Fabric CI/CD supporting **multiple workspaces** from a single repository. Uses a **medallion architecture** (Bronze → Silver → Gold) for data engineering. The codebase defines Fabric workspace items as code, enabling Git-based version control, collaboration, and automated deployment workflows.

**Key Purpose**: Serve as a company-wide template for Fabric projects following Microsoft best practices for lifecycle management with multi-workspace support.

## Multi-Workspace Architecture

This repository supports deploying multiple Fabric workspaces from a single repository:

```
workspaces/
├── Fabric Blueprint/
│   ├── config.yml             # Workspace names per environment
│   ├── parameter.yml          # ID transformation rules
│   ├── 1_Bronze/
│   ├── 2_Silver/
│   ├── 3_Gold/
│   └── 4_Analytics/
├── Analytics Hub/
│   ├── config.yml
│   ├── parameter.yml
│   └── ...
└── Data Engineering/
    ├── config.yml
    ├── parameter.yml
    └── ...
```

**Workspace Naming**: Names are explicitly configured in `config.yml` per workspace folder:
- Dev: Defined in `config.yml` under `core.workspace.dev` (e.g., `[D] Fabric Blueprint`)
- Test: Defined in `config.yml` under `core.workspace.test` (e.g., `[T] Fabric Blueprint`)
- Prod: Defined in `config.yml` under `core.workspace.prod` (e.g., `[P] Fabric Blueprint`)

**Atomic Rollback (Planned Feature)**: Atomic rollback is planned for future implementation. When implemented, if any workspace deployment fails, all previously deployed workspaces in that run would be automatically rolled back.

## Git Integration & CI/CD Strategy

### Workspace-to-Git Mapping

This project follows **Fabric Git Integration** patterns where:
- **Private development workspaces only** are connected to Git (feature branches)
- **Dev, Test, Prod workspaces** are NOT connected to Git - they receive deployments via CI/CD pipelines
- Developers use isolated workspaces connected to their feature branches for development

### Supported Git Providers

- **GitHub** (including GitHub Enterprise)

### Branch Strategy

**Trunk-based development** workflow:
- **main**: Single source of truth for all deployments
- **feature/***: Short-lived feature branches that merge to main
- **Private dev branches**: Individual developer branches for isolated work

### Deployment Approach: Git-based with Build Environments

This architecture uses **Git-based deployments with Build environments** for configuration transformation between stages.

**Why Git-based with Build Environments**
- Single source of truth in `main` branch (trunk-based workflow)
- Build environments allow modification of workspace-specific attributes (connectionId, lakehouseId, parameters)
- Custom scripts can adjust configurations for each stage (Dev/Test/Prod)
- Uses `fabric-cicd` library for deploying items programmatically

**Deployment Flow:**

1. **PR merged to main** → Triggers build pipeline
2. **Build Pipeline** (per stage: Dev → Test → Prod):
   - Spin up Build environment
   - Run unit tests
   - Execute configuration scripts to modify item definitions for target stage
   - Adjust connections, data sources, parameters
3. **Release Pipeline**:
   - Use `fabric-cicd` library to deploy items to workspace
   - Run post-deployment ingestion/configuration tasks
4. **Approval Gates**: Release managers approve progression between stages

**Deployment Tool:**
- `fabric-cicd` library: Handles deployment of modified item content to workspaces

### Best Practices for This Architecture

- **Multiple workspaces per repository**: Each workspace folder in `workspaces/` is a separate deployment target
- **Separate workspaces per stage**: Dev, Test, Prod workspaces with different capacities for each workspace folder
- **Explicit workspace naming**: Workspace names defined in `config.yml` per environment
- **Dual configuration approach**: Each workspace has `config.yml` (deployment config) and `parameter.yml` (ID transformations)
- **Parameterize everything**: All stage-specific configs (connections, lakehouse IDs, data sources) must be parameterizable
- **Small, frequent merges to main**: Keep feature branches short-lived
- **Commit related changes together**: Group changes that must deploy atomically across workspaces
- **Private development branches**: Each developer works in isolated branch/workspace
- **Pull request workflow**: All changes to main require PR approval
- **Atomic operations**: All workspace deployments succeed or all are rolled back

## Commands

### Common Development Commands

```bash
# Setup and Installation
pip install fabric-cicd azure-identity  # Install dependencies

# Local Development - Deploys all workspaces with config.yml
python -m scripts.deploy_to_fabric \
  --workspaces_directory workspaces \
  --environment dev

# Note: The script automatically discovers all workspace folders
# that contain a config.yml file. No need to specify workspace names.

# Deployment Commands (via GitHub Actions)
# Deploy to Dev: Automatic on merge to main
# Deploy to Test: Manual workflow dispatch (select "test" environment)
# Deploy to Production: Manual workflow dispatch (select "prod" environment)

# Validation
python -m json.tool "workspaces/Fabric Blueprint/1_Bronze/lakehouse_bronze.Lakehouse/lakehouse.metadata.json"  # Validate JSON files

# View deployment configuration
cat scripts/deployment_config.py  # View centralized configuration constants
```

### Workflow Triggers

- **Dev Environment**: Automatically deploys when PR is merged to `main` with changes in `workspaces/**` paths (all workspaces deploy)
- **Test Environment**: Manual trigger via GitHub Actions (select "test" environment)
- **Production Environment**: Manual trigger via GitHub Actions (select "prod" environment)
- **Non-workspace changes**: Changes to `.github/`, `scripts/`, documentation do NOT trigger automatic deployment

## Fabric MCP Server Integration

**When working with Microsoft Fabric tasks, always prefer using the Fabric MCP server.**

The Fabric MCP (Model Context Protocol) server provides specialized tools and context for:
- Querying Fabric workspaces, items, and metadata
- Managing OneLake files, directories, and shortcuts
- Accessing Fabric API specifications and best practices
- Working with Fabric item definitions (notebooks, lakehouses, pipelines, semantic models)
- Retrieving official Microsoft Fabric documentation

**Use the Fabric MCP server for:**
- Creating or modifying Fabric workspace items
- Querying workspace structure and item relationships
- Understanding Fabric API patterns and schemas
- Getting context-aware Fabric best practices
- Working with OneLake storage operations

**Benefits:**
- Access to latest Fabric API specifications
- Context-aware guidance for Fabric-specific tasks
- Integration with Microsoft Fabric API SDK
- Official Microsoft documentation and examples

**When MCP server is not available:**

If the Fabric MCP server is not available or doesn't have the appropriate tools for your task, use the official web documentation:
- **fabric-cicd library**: https://microsoft.github.io/fabric-cicd/latest/
- **fabric-cli tool**: https://microsoft.github.io/fabric-cli/

These resources provide:
- Comprehensive API references
- Usage examples and code samples
- Configuration options and parameters
- Troubleshooting guides
- Latest feature documentation

## Architecture

### Medallion Layers

1. **Bronze Layer** (`1_Bronze/`): Raw data ingestion
   - `lakehouse_bronze.Lakehouse/`: Source data storage
   - `ingestion/cp_br_source.CopyJob/`: Data pipeline copy jobs (batch mode)

2. **Silver Layer** (`2_Silver/`): Transformed/cleansed data
   - `lakehouse_silver.Lakehouse/`: Cleaned data storage
   - `transformation/nb_sl_transform.Notebook/`: PySpark transformation notebooks

3. **Gold Layer** (`3_Gold/`): Business-ready analytics
   - `lakehouse_gold.Lakehouse/`: Aggregated/modeled data
   - `modeling/nb_gd_modeling.Notebook/`: Data modeling notebooks

4. **Analytics** (`4_Analytics/`): Semantic models, reports, and agents
   - Semantic models: Power BI semantic models for analytics
   - Reports: Power BI reports and dashboards
   - `Data Agents/da_agent.DataAgent/`: AI agent definitions (schema: 2.1.0)
   - `env.Environment/`: Workspace environment settings

## File Structure Conventions

### Fabric Item Structure

Each Fabric item follows this pattern:
```
<item-name>.<ItemType>/
  ├── <item-type>-content.json/py  # Main definition
  ├── <item-type>.metadata.json    # Item metadata
  ├── alm.settings.json            # ALM/deployment config (for lakehouses)
  └── shortcuts.metadata.json      # OneLake shortcuts (for lakehouses)
```

### Key File Types

- **Notebooks**: `notebook-content.py` with inline `# METADATA` blocks
  - Kernel: `synapse_pyspark`
  - Structure: Python source with META comments for cell boundaries
  
- **Copy Jobs**: `copyjob-content.json` with `properties.jobMode` (typically "Batch")

- **Lakehouses**: 
  - `lakehouse.metadata.json`: Schema config (`{"defaultSchema":"dbo"}`)
  - `alm.settings.json`: Controls ALM for shortcuts, data access roles
  - `shortcuts.metadata.json`: OneLake/ADLS/S3/Dataverse shortcuts

- **Environments**: `Sparkcompute.yml` for cluster config
  - Runtime version 2.0
  - Driver/executor cores and memory settings
  - Dynamic executor allocation enabled

- **Data Agents**: `data_agent.json` follows schema `2.1.0` from Microsoft

## Development Workflow

### Naming Conventions

**Item Prefixes**:
- `cp_`: Copy jobs (data pipelines)
- `nb_`: Notebooks (PySpark/Python)
- `lakehouse_`: Lakehouse data stores
- `da_`: Data agents

**Layer Prefixes**:
- `br_`: Bronze layer (raw ingestion)
- `sl_`: Silver layer (transformation)
- `gd_`: Gold layer (modeling/analytics)

**Restrictions** (from Microsoft Fabric):
- Display names: Max 256 characters
- Cannot end with `.` or space
- Forbidden characters: `" / : < > \ * ? |`
- Branch names: Max 244 characters
- File paths: Max 250 characters
- Max file size: 25 MB
- Folder depth: Max 10 levels

### Working with Fabric Items

- **Isolated development**: Use private workspace or feature branch per developer
- **Folder structure**: Workspace folders sync to Git repo folders (empty folders ignored)
- **Workspace limit**: Max 1,000 items per workspace
- **Version control**: Always commit related changes together for atomic deployments

### Making Changes to This Repository

**REQUIRED GitHub Workflow for All Changes:**

Whenever making changes to this repository (code, documentation, Fabric items, configuration), follow this mandatory process:

1. **Create a GitHub Issue**:
   - Document what you're changing and why
   - Include acceptance criteria
   - Apply appropriate labels (e.g., `enhancement`, `bug`, `documentation`)
   - Example title: "Add lakehouse_platinum to Gold layer"

2. **Create a Feature Branch from main**:
   - Use descriptive branch names: `feature/<issue-number>-brief-description`
   - Example: `feature/42-add-platinum-lakehouse`
   - Branch from latest `main`: `git checkout main && git pull && git checkout -b feature/42-add-platinum-lakehouse`

3. **Work on the Issue**:
   - Make changes in your feature branch
   - Commit frequently with clear messages referencing the issue: `git commit -m "Add platinum lakehouse structure #42"`
   - Test changes locally when applicable
   - Keep commits focused and atomic

4. **Create a Pull Request**:
   - Push your feature branch to GitHub: `git push -u origin feature/42-add-platinum-lakehouse`
   - Create PR from your branch to `main`
   - Reference the issue in the PR description: "Closes #42"
   - Add reviewers (at least one required)
   - Ensure PR description includes:
     - What changed and why
     - Testing performed
     - Any deployment considerations

5. **PR Review and Merge**:
   - Address review feedback
   - Ensure CI/CD checks pass
   - Once approved, merge to `main` (squash commits for clean history)
   - Delete feature branch after merge

**This workflow applies to:**
- Adding/modifying Fabric items (lakehouses, notebooks, pipelines)
- Updating deployment scripts or workflows
- Documentation changes
- Configuration updates (`parameter.yml`, `alm.settings.json`)
- Any changes to scripts, workflows, or repository structure

**Why this matters:**
- Maintains audit trail of all changes
- Enables code review and knowledge sharing
- Prevents conflicts and broken deployments
- Aligns with trunk-based development best practices
- Facilitates CI/CD automation (Dev deployments trigger on merge to main)

### Notebook Development

Fabric notebooks use special comment syntax:
```python
# METADATA ********************
# META {
# META   "kernel_info": {"name": "synapse_pyspark"},
# META   "dependencies": {}
# META }
# CELL ********************
# Your code here
```

Always preserve this structure when editing notebooks.

### ALM Settings

The `alm.settings.json` version `1.0.1` controls deployment behavior:
- **Shortcuts**: Can enable/disable OneLake, ADLS Gen2, Dataverse, S3, GCS shortcuts
- **DataAccessRoles**: Typically disabled in CI/CD scenarios

## Spark Configuration

Environment Spark settings (`Sparkcompute.yml`):
- **Native execution engine**: Enabled
- **Driver**: 8 cores, 56GB memory
- **Executors**: 8 cores, 56GB memory, dynamic allocation (1 min, 1 max)
- **Runtime**: Version 2.0

## Git Integration

This is a Git-based deployment model where:
- Each Fabric workspace item is a directory
- Changes are version controlled
- Structure mirrors Fabric workspace organization

### Git Status States

Items in workspace show Git status:
- **Synced**: Item matches Git branch
- **Conflict**: Changed in both workspace and Git
- **Uncommitted changes**: Workspace ahead of Git
- **Update required**: Git ahead of workspace
- **Unsupported item**: Item type not supported in Git

### Commit and Update Rules

- **Commit**: Push workspace changes to Git (can select specific items)
- **Update**: Pull Git changes to workspace (always full branch update)
- **Conflicts**: Must be resolved before update can proceed
- **Direction**: Can only sync one direction at a time

When creating new items, follow the exact folder/file naming patterns observed in existing items.

## Common Tasks

**⚠️ GitHub Workflow Required**: Before performing any of the tasks below, always follow the GitHub workflow:
1. Create an issue documenting the change
2. Create a feature branch from `main`
3. Make your changes in the feature branch
4. Create a PR and get it reviewed
5. Merge to `main` after approval

See [Making Changes to This Repository](#making-changes-to-this-repository) for detailed instructions.

### Adding a New Lakehouse
1. Create `<name>.Lakehouse/` directory in appropriate layer
2. Add `lakehouse.metadata.json` with `{"defaultSchema":"dbo"}`
3. Add `alm.settings.json` (copy from existing lakehouse)
4. Add empty `shortcuts.metadata.json` (`[]`)
5. **Important**: Lakehouse IDs must be transformed by build scripts for each environment
6. **GitHub**: Create issue → feature branch → PR → merge to main

### Adding a New Notebook
1. Create `<name>.Notebook/` directory
2. Add `notebook-content.py` with proper METADATA structure
3. Use `synapse_pyspark` kernel
4. Include cell boundaries with `# CELL` comments
5. **Important**: Parameterize any lakehouse references or connections
6. **GitHub**: Create issue → feature branch → PR → merge to main

### Adding a Copy Job
1. Create `<name>.CopyJob/` directory
2. Add `copyjob-content.json` with `properties.jobMode`
3. Define `activities` array for pipeline steps
4. **Important**: Connection IDs and data source paths must be parameterized for build transformation
5. **GitHub**: Create issue → feature branch → PR → merge to main

### Build Pipeline Configuration (Future Implementation)

Build scripts should handle:
- **Connection transformations**: Replace connection IDs for target environment
- **Lakehouse ID substitution**: Update lakehouse references in notebooks, pipelines
- **Parameter updates**: Environment-specific values (data source URLs, storage paths)
- **Item relationships**: Adjust logical IDs for cross-item references

### CI/CD Pipeline Structure (Future Implementation)

```
.github/workflows/ or .azure-pipelines/
├── build-dev.yml        # Build & deploy to Dev
├── build-test.yml       # Build & deploy to Test  
├── build-prod.yml       # Build & deploy to Prod
└── scripts/
    ├── transform-config.ps1   # Configuration transformation
    └── deploy-items.ps1       # Fabric API deployment
```

## Testing Requirements

### No Automated Tests Required

This is a **reference architecture** project focused on demonstrating Fabric CI/CD patterns. It does not include automated tests for the following reasons:
- Fabric item definitions are declarative (JSON/YAML configuration)
- Notebooks contain example PySpark code for demonstration purposes
- Deployment validation happens through the actual Fabric workspace deployment

### Manual Validation Process

After deployment, validate that:
1. **Items are deployed**: Check target workspace in Fabric portal
2. **Item types are correct**: Verify Lakehouses, Notebooks, Pipelines, Semantic Models
3. **IDs are transformed**: Confirm lakehouse/workspace IDs match target environment
4. **No deployment errors**: Review GitHub Actions logs for successful completion

### Deployment Script Validation

The `scripts/deploy_to_fabric.py` script can be validated locally:

```bash
# View available arguments
python -m scripts.deploy_to_fabric --help

# Validate parameter.yml syntax
python -c "import yaml; yaml.safe_load(open('parameter.yml'))"

# View deployment configuration constants
python -c "from scripts.deployment_config import *; print(f'Valid environments: {VALID_ENVIRONMENTS}')"
```

## Coding Conventions

### Python Scripts

- **Python Version**: 3.11+
- **Style**: Follow PEP 8 conventions
- **Type Hints**: Use type hints for function arguments and return values
- **Error Handling**: Always catch specific exceptions, use sys.exit(1) for errors
- **Logging**: Use print statements for GitHub Actions visibility

**Example: Good Python Style**
```python
from typing import Optional
from azure.identity import ClientSecretCredential

def deploy_workspace(
    workspace_name: str,
    environment: str,
    token_credential: ClientSecretCredential
) -> bool:
    """Deploy workspace items to Fabric.
    
    Args:
        workspace_name: Name of the target Fabric workspace
        environment: Target environment (dev/test/prod)
        token_credential: Azure credential for authentication
        
    Returns:
        True if deployment succeeds, False otherwise
    """
    try:
        print(f"Starting deployment to {workspace_name}")
        # deployment logic here
        return True
    except Exception as e:
        print(f"ERROR: Deployment failed: {str(e)}")
        return False
```

### Fabric Item Definitions

- **JSON Formatting**: All JSON files must be valid and properly formatted
- **METADATA Preservation**: Never modify `# METADATA` or `# CELL` comments in notebooks
- **Naming Conventions**: Follow established prefixes (`cp_`, `nb_`, `lakehouse_`, `da_`)
- **Layer Prefixes**: Use `br_`, `sl_`, `gd_` for Bronze, Silver, Gold layers

**Example: Valid Notebook Structure**
```python
# METADATA ********************
# META {
# META   "kernel_info": {"name": "synapse_pyspark"},
# META   "dependencies": {}
# META }

# CELL ********************
# Import libraries
from pyspark.sql import SparkSession

# CELL ********************
# Your transformation code here
df = spark.read.format("delta").load("Tables/source_table")
df_transformed = df.filter(df["status"] == "active")
df_transformed.write.format("delta").mode("overwrite").save("Tables/target_table")
```

### YAML Configuration

- **Indentation**: Use 2 spaces (not tabs)
- **Comments**: Add descriptive comments for complex transformations
- **Regex Patterns**: Escape special characters properly in `find_value` patterns

**Example: Valid parameter.yml Entry**
```yaml
find_replace:
  - find_value: 'database\s*=\s*Sql\.Database\s*\(\s*"([^"]+)"'
    replace_value:
      _ALL_: "$items.Lakehouse.lakehouse_silver.sqlendpoint"
    is_regex: "true"
    item_type: "SemanticModel"
    description: "Replace SQL endpoint in semantic models"
```

## Prohibited Areas

### Files and Directories That Should NEVER Be Modified

**❌ Do Not Edit:**
- `.git/` - Git internal files
- `.github/workflows/` - GitHub Actions workflows (unless explicitly requested)
- `workspaces/**/.platform` - Fabric platform-specific metadata files
- Any files with GUID-like IDs in their content (these are environment-specific)

**❌ Do Not Remove:**
- `alm.settings.json` files (required for lakehouse ALM behavior)
- `.platform` files (required by Fabric for item type identification)
- `shortcuts.metadata.json` files (even if empty, they declare shortcut configuration)

**⚠️ Modify With Extreme Care:**
- `parameter.yml` - Changes affect all environment deployments
- `.github/copilot-instructions.md` - Repository-wide Copilot behavior
- Notebook METADATA blocks - Breaking these makes notebooks unreadable in Fabric

### Security-Sensitive Operations

**Never commit:**
- Azure Service Principal secrets or credentials
- Fabric workspace IDs in plain text (use GitHub secrets/variables instead)
- Personal Access Tokens (PATs)
- Connection strings with embedded credentials
- Any `.env` files with secrets

**Always use:**
- GitHub Secrets for sensitive values (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`)
- Environment-specific transformations via workspace `parameter.yml` files for IDs and endpoints
- Workspace name configuration via `config.yml` per workspace folder

## Security Best Practices

### Authentication and Authorization

1. **Service Principal Management**:
   - Use dedicated Service Principal per environment (recommended)
   - Or use single Service Principal with access to all workspaces (simpler)
   - Rotate client secrets every 90 days
   - Use least-privilege permissions (Workspace Contributor, not Admin unless needed)

2. **GitHub Secrets Protection**:
   - Never print secrets in logs (`echo ${{ secrets.AZURE_CLIENT_SECRET }}` is forbidden)
   - Use `***` masking by storing values as GitHub Secrets
   - Review GitHub Actions logs for accidental secret exposure

3. **Fabric Workspace Security**:
   - Use separate workspaces per environment (Dev, Test, Prod)
   - Apply different Fabric capacities per environment
   - Enable workspace audit logging
   - Restrict workspace access to service principals and authorized users only

### Code Security

1. **Dependency Management**:
   - Pin dependency versions in requirements.txt or workflow files
   - Review `fabric-cicd` library updates for breaking changes
   - Use `pip install --upgrade pip` before installing dependencies

2. **Secrets in Code**:
   - Never hardcode workspace IDs, connection strings, or credentials
   - Use `${{ secrets.* }}` and `${{ vars.* }}` in workflows
   - Use `parameter.yml` for ID transformations, not inline replacements

3. **Deployment Safety**:
   - Test deployments in Dev before Test/Prod
   - Use manual approval for Test and Prod deployments
   - Review orphan cleanup behavior (`unpublish_all_orphan_items`)
   - Maintain deployment rollback capability (Git history)

## Troubleshooting

### Common Deployment Issues

**Issue: `ClientSecretCredential authentication failed`**
```
Solution:
1. Verify GitHub secrets are set correctly (CLIENT_ID, CLIENT_SECRET, TENANT_ID)
2. Check Service Principal exists in correct Azure AD tenant
3. Ensure client secret hasn't expired (max 2 years)
4. Verify Service Principal has Fabric workspace access
```

**Issue: `Workspace not found` error**
```
Solution:
1. Check workspace name is defined correctly in config.yml
2. Verify workspace name matches target workspace in Fabric (case-sensitive)
3. Ensure workspace folder has both config.yml and parameter.yml files
4. Confirm workspace exists in Fabric portal
5. Verify Service Principal has access to workspace
```

**Issue: Item deployment fails with invalid JSON**
```
Solution:
1. Validate JSON syntax: python -m json.tool <file>.json
2. Check for trailing commas in JSON files
3. Verify METADATA blocks in notebooks are not corrupted
4. Ensure no merge conflict markers remain in files
```

**Issue: IDs not transforming between environments**
```
Solution:
1. Verify parameter.yml has correct Dev workspace IDs in find_value
2. Check regex patterns are valid (use is_regex: "true")
3. Confirm item_type matches the target item (e.g., "Notebook")
4. Test regex at https://regex101.com/ with sample content
```

**Issue: Orphan items not removed**
```
Solution:
1. Check if skip_orphan_cleanup is set in parameter.yml
2. Verify item types are in scope for deployment
3. Review deployment logs for orphan detection results
4. Manually remove orphaned items if cleanup is disabled
```

### Debugging GitHub Actions

**Enable Debug Logging:**
1. Go to Settings → Secrets and variables → Actions
2. Add secret: `ACTIONS_RUNNER_DEBUG` = `true`
3. Re-run failed workflow
4. Review expanded debug output in Actions logs

**Check Deployment Status:**
```bash
# View most recent workflow runs
gh run list --limit 5

# View logs for specific run
gh run view <run-id> --log

# Re-run failed workflow
gh run rerun <run-id>
```

### Getting Help

- **Fabric API Issues**: [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- **fabric-cicd Library**: [PyPI Package](https://pypi.org/project/fabric-cicd/)
- **GitHub Actions**: [GitHub Actions Documentation](https://docs.github.com/actions)
- **Service Principal Setup**: [Azure AD Documentation](https://learn.microsoft.com/azure/active-directory/develop/howto-create-service-principal-portal)
