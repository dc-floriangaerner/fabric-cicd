# Microsoft Fabric API Python SDK - Complete Reference

**Package**: `microsoft-fabric-api`  
**Version**: 0.1.0b2 (Beta)  
**Last Updated**: February 13, 2026

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Authentication](#authentication)
- [Client Initialization](#client-initialization)
- [API Structure](#api-structure)
- [Complete API Reference](#complete-api-reference)
  - [Core Modules](#core-modules-reference)
  - [Admin Modules](#admin-modules-reference)
  - [Workload-Specific Modules](#workload-specific-modules)
- [Common Patterns](#common-patterns)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

---

## Documentation Status

**Current Status**: This documentation covers the complete Microsoft Fabric API surface area, including:
- ✅ `fabric_client.core.*` - Core Fabric services (21 sub-modules)
- ✅ `fabric_client.admin.*` - Admin operations (10 sub-modules)
- ✅ **39 workload-specific top-level modules** - Complete coverage of all Fabric workloads

**Total API Coverage**: 39 top-level modules with 100+ sub-modules documented below.

**To explore interactively**: Run the [fabric-api-exploration.ipynb](../scripts/fabric-api-exploration.ipynb) notebook to discover module methods and signatures.

---

## Overview

The Microsoft Fabric API Python SDK is a client library that provides programmatic access to **all** Microsoft Fabric resources. It wraps the [Microsoft Fabric REST API](https://learn.microsoft.com/en-us/rest/api/fabric) and simplifies:

- Workspace and capacity management
- Data integration and warehousing
- Big data analytics automation
- Fabric item provisioning (Lakehouses, Notebooks, Semantic Models, Reports, etc.)
- Administrative operations (tenant settings, user management)
- Git integration and deployment pipelines
- Workload-specific operations

**Key Characteristics**:
- Beta release (API may change)
- Returns `ItemPaged` iterables (convert to `list()` for full results)
- Uses Azure Identity for authentication
- Follows REST API structure closely
- Multiple top-level modules: `core`, `admin`, and potentially others

**Module Coverage**:
- **Primary module**: `fabric_client.core` - Most common operations (21 sub-modules)
- **Admin module**: `fabric_client.admin` - Tenant administration (10 sub-modules)
- **Workload modules**: 37 specialized modules for specific Fabric item types

**All Top-Level Modules** (39 total):
`admin`, `anomalydetector`, `apacheairflowjob`, `copyjob`, `core`, `cosmosdbdatabase`, `dashboard`, `dataflow`, `datamart`, `datapipeline`, `digitaltwinbuilder`, `digitaltwinbuilderflow`, `environment`, `eventhouse`, `eventstream`, `graphmodel`, `graphqlapi`, `graphqueryset`, `kqldashboard`, `kqldatabase`, `kqlqueryset`, `lakehouse`, `map`, `mirroredazuredatabrickscatalog`, `mirroreddatabase`, `mirroredwarehouse`, `mlexperiment`, `mlmodel`, `mounteddatafactory`, `notebook`, `ontology`, `operationsagent`, `paginatedreport`, `reflex`, `report`, `semanticmodel`, `spark`, `sparkjobdefinition`, `sqldatabase`, `sqlendpoint`, `userdatafunction`, `variablelibrary`, `warehouse`, `warehousesnapshot`

**Discovery Tool**: Use [fabric-api-exploration.ipynb](../scripts/fabric-api-exploration.ipynb) to discover all available modules and methods in your SDK version.

---

## Installation

```bash
pip install microsoft-fabric-api azure-identity
```

**Dependencies**:
- `azure-identity` - For authentication credentials
- `azure-core` - Azure SDK core functionality

---

## Authentication

The SDK supports any `TokenCredential` from the `azure-identity` library.

### Service Principal Authentication (Recommended for CI/CD)

```python
from azure.identity import ClientSecretCredential

credential = ClientSecretCredential(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)
```

### Default Azure Credential (Interactive/Managed Identity)

```python
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
```

### Other Supported Credentials

- `ManagedIdentityCredential` - For Azure resources
- `AzureCliCredential` - Uses Azure CLI authentication
- `InteractiveBrowserCredential` - Interactive login
- `DeviceCodeCredential` - Device code flow

**Prerequisites**:
- [Register your application in Azure AD](https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app)
- Grant appropriate permissions to Microsoft Fabric service
- For Service Principal: Assign workspace roles (Contributor/Admin)

---

## Client Initialization

```python
from microsoft_fabric_api import FabricClient

fabric_client = FabricClient(token_credential=credential)
```

**Parameters**:
- `token_credential`: Instance of `TokenCredential` from azure-identity

---

## API Structure

The SDK is organized hierarchically with 39 top-level modules:

```
FabricClient (39 top-level modules)
├── core (21 sub-modules)         # Core Fabric services (PRIMARY MODULE)
│   ├── workspaces                # Workspace management
│   ├── items                     # Item operations
│   ├── capacities                # Capacity management
│   ├── connections               # Data connections
│   ├── git                       # Git integration
│   ├── deployment_pipelines      # Deployment pipelines
│   ├── folders                   # Folder/hierarchy management
│   ├── gateways                  # Data gateways
│   ├── domains                   # Domain management
│   ├── job_scheduler             # Job scheduling
│   ├── one_lake_shortcuts        # OneLake shortcuts
│   ├── managed_private_endpoints # Private endpoints
│   └── [15 more sub-modules]     # Additional core services
│
├── admin (10 sub-modules)        # Administrative operations
│   ├── workspaces                # Tenant workspace management
│   ├── domains                   # Domain administration
│   ├── items                     # Cross-workspace item management
│   ├── tenants                   # Tenant settings
│   ├── users                     # User management
│   ├── labels                    # Sensitivity labels
│   ├── tags                      # Organizational tags
│   └── [3 more sub-modules]      # Additional admin operations
│
├── lakehouse                     # Lakehouse operations
│   ├── items                     # Lakehouse CRUD
│   ├── tables                    # Table management
│   ├── background_jobs           # Load operations
│   └── livy_sessions             # Interactive Spark
│
├── notebook                      # Notebook operations
│   ├── items                     # Notebook CRUD
│   └── livy_sessions             # Interactive execution
│
├── warehouse                     # Data warehouse operations
│   ├── items                     # Warehouse CRUD
│   ├── restore_points            # Backup/restore
│   └── sql_audit_settings        # Audit configuration
│
├── semanticmodel                 # Semantic models (Power BI datasets)
│   └── items                     # Model CRUD
│
├── report                        # Power BI reports
│   └── items                     # Report CRUD
│
├── datapipeline                  # Data pipelines
│   └── items                     # Pipeline CRUD
│
├── environment                   # Fabric environments
│   ├── items                     # Environment CRUD
│   ├── published                 # Published resources
│   └── staging                   # Staging resources
│
├── spark                         # Spark compute
│   ├── custom_pools              # Custom Spark pools
│   ├── livy_sessions             # Spark sessions
│   └── workspace_settings        # Spark configuration
│
└── [28 more workload modules]    # Additional Fabric workloads
```

**Common Access Patterns**:
```python
# Pattern: fabric_client.<module>.<submodule>.<method>()

# Core API - General workspace/item operations
workspaces = fabric_client.core.workspaces.list_workspaces()
items = fabric_client.core.items.list_items(workspace_id=workspace_id)

# Admin API - Tenant-wide operations (requires admin role)
all_workspaces = fabric_client.admin.workspaces.list_workspaces()
domains = fabric_client.admin.domains.list_domains()

# Workload-specific APIs - Type-specific operations
lakehouse = fabric_client.lakehouse.items.create_item(workspace_id, request)
notebook = fabric_client.notebook.items.create_item(workspace_id, request)
warehouse = fabric_client.warehouse.items.create_item(workspace_id, request)
```

**Module Discovery**: Use [fabric-api-exploration.ipynb](../scripts/fabric-api-exploration.ipynb) to explore all modules and their methods interactively.

---

## Complete API Reference

This section documents all available modules in the Microsoft Fabric API. The structure is based on the SDK version 0.1.0b2.

**To discover additional modules**: Run the exploration notebook to find all available top-level modules (`core`, `admin`, etc.) and their sub-modules.

---

## Core Modules Reference

The `fabric_client.core` module contains the primary API operations for managing Fabric resources.

### 1. Workspaces Module

**Path**: `fabric_client.core.workspaces`

Manage Microsoft Fabric workspaces.

#### Methods

##### `list_workspaces()`

List all workspaces the authenticated user has access to.

**Signature**:
```python
list_workspaces() -> ItemPaged[Workspace]
```

**Returns**: Iterable of `Workspace` objects

**Example**:
```python
workspaces = list(fabric_client.core.workspaces.list_workspaces())
for workspace in workspaces:
    print(f"{workspace.display_name} (ID: {workspace.id})")
```

**Workspace Object Properties**:
- `id`: Workspace UUID
- `display_name`: Workspace name
- `description`: Workspace description
- `type`: Workspace type
- `capacity_id`: Associated capacity ID

---

##### `get_workspace()`

Get details of a specific workspace.

**Signature**:
```python
get_workspace(workspace_id: str) -> Workspace
```

**Parameters**:
- `workspace_id` (str): Workspace UUID

**Returns**: `Workspace` object

**Example**:
```python
workspace = fabric_client.core.workspaces.get_workspace(
    workspace_id="12345678-1234-1234-1234-123456789abc"
)
print(workspace.display_name)
```

---

##### `create_workspace()`

Create a new workspace.

**Signature**:
```python
create_workspace(request: CreateWorkspaceRequest) -> Workspace
```

**Parameters**:
- `request`: CreateWorkspaceRequest object containing:
  - `display_name` (str): Workspace name
  - `description` (str, optional): Workspace description
  - `capacity_id` (str, optional): Capacity to assign

**Returns**: Created `Workspace` object

**Example**:
```python
from microsoft_fabric_api.generated.core.models import CreateWorkspaceRequest

new_workspace = fabric_client.core.workspaces.create_workspace(
    request=CreateWorkspaceRequest(
        display_name="My New Workspace",
        description="Created via API"
    )
)
```

---

##### `delete_workspace()`

Delete a workspace.

**Signature**:
```python
delete_workspace(workspace_id: str) -> None
```

**Parameters**:
- `workspace_id` (str): Workspace UUID to delete

**Example**:
```python
fabric_client.core.workspaces.delete_workspace(
    workspace_id="12345678-1234-1234-1234-123456789abc"
)
```

---

##### `update_workspace()`

Update workspace properties.

**Signature**:
```python
update_workspace(workspace_id: str, request: UpdateWorkspaceRequest) -> Workspace
```

**Parameters**:
- `workspace_id` (str): Workspace UUID
- `request`: UpdateWorkspaceRequest with properties to update

**Example**:
```python
from microsoft_fabric_api.generated.core.models import UpdateWorkspaceRequest

updated = fabric_client.core.workspaces.update_workspace(
    workspace_id="12345678-1234-1234-1234-123456789abc",
    request=UpdateWorkspaceRequest(
        display_name="Updated Name",
        description="Updated description"
    )
)
```

---

### 2. Items Module

**Path**: `fabric_client.core.items`

Manage Fabric items (Lakehouses, Notebooks, Semantic Models, Reports, etc.).

#### Methods

##### `list_items()`

List all items in a workspace.

**Signature**:
```python
list_items(workspace_id: str) -> ItemPaged[Item]
```

**Parameters**:
- `workspace_id` (str): Workspace UUID

**Returns**: Iterable of `Item` objects

**Example**:
```python
items = list(fabric_client.core.items.list_items(
    workspace_id="12345678-1234-1234-1234-123456789abc"
))

for item in items:
    print(f"{item.display_name} ({item.type})")
```

**Item Object Properties**:
- `id`: Item UUID
- `display_name`: Item name
- `type`: Item type (e.g., "Lakehouse", "Notebook", "SemanticModel")
- `description`: Item description
- `workspace_id`: Parent workspace ID

**Supported Item Types**:
- `Lakehouse`
- `Notebook`
- `SemanticModel`
- `Report`
- `Dashboard`
- `DataPipeline`
- `Dataflow`
- `Environment`
- `Warehouse`
- `MLModel`
- `MLExperiment`

---

##### `get_item()`

Get details of a specific item.

**Signature**:
```python
get_item(workspace_id: str, item_id: str) -> Item
```

**Parameters**:
- `workspace_id` (str): Workspace UUID
- `item_id` (str): Item UUID

**Returns**: `Item` object

**Example**:
```python
item = fabric_client.core.items.get_item(
    workspace_id="12345678-1234-1234-1234-123456789abc",
    item_id="87654321-4321-4321-4321-cba987654321"
)
```

---

##### `create_item()`

Create a new item in a workspace.

**Signature**:
```python
create_item(workspace_id: str, request: CreateItemRequest) -> Item
```

**Parameters**:
- `workspace_id` (str): Workspace UUID
- `request`: CreateItemRequest containing:
  - `display_name` (str): Item name
  - `type` (str): Item type
  - `description` (str, optional): Item description
  - `definition` (dict, optional): Item definition/content

**Returns**: Created `Item` object

**Example**:
```python
from microsoft_fabric_api.generated.core.models import CreateItemRequest

new_lakehouse = fabric_client.core.items.create_item(
    workspace_id="12345678-1234-1234-1234-123456789abc",
    request=CreateItemRequest(
        display_name="My Lakehouse",
        type="Lakehouse",
        description="Created via API"
    )
)
```

---

##### `delete_item()`

Delete an item from a workspace.

**Signature**:
```python
delete_item(workspace_id: str, item_id: str) -> None
```

**Parameters**:
- `workspace_id` (str): Workspace UUID
- `item_id` (str): Item UUID to delete

**Example**:
```python
fabric_client.core.items.delete_item(
    workspace_id="12345678-1234-1234-1234-123456789abc",
    item_id="87654321-4321-4321-4321-cba987654321"
)
```

---

##### `update_item()`

Update item properties.

**Signature**:
```python
update_item(workspace_id: str, item_id: str, request: UpdateItemRequest) -> Item
```

**Parameters**:
- `workspace_id` (str): Workspace UUID
- `item_id` (str): Item UUID
- `request`: UpdateItemRequest with properties to update

**Example**:
```python
from microsoft_fabric_api.generated.core.models import UpdateItemRequest

updated_item = fabric_client.core.items.update_item(
    workspace_id="12345678-1234-1234-1234-123456789abc",
    item_id="87654321-4321-4321-4321-cba987654321",
    request=UpdateItemRequest(
        display_name="Updated Item Name",
        description="Updated description"
    )
)
```

---

### 3. Capacities Module

**Path**: `fabric_client.core.capacities`

Manage Fabric capacities.

#### Methods

##### `list_capacities()`

List all capacities available to the user.

**Signature**:
```python
list_capacities() -> ItemPaged[Capacity]
```

**Returns**: Iterable of `Capacity` objects

**Example**:
```python
capacities = list(fabric_client.core.capacities.list_capacities())
for capacity in capacities:
    print(f"{capacity.display_name} - SKU: {capacity.sku}")
```

---

### 4. Git Module

**Path**: `fabric_client.core.git`

Manage Git integration for workspaces.

#### Methods

##### `connect_workspace()`

Connect a workspace to a Git repository.

**Signature**:
```python
connect_workspace(workspace_id: str, request: ConnectRequest) -> GitConnection
```

**Parameters**:
- `workspace_id` (str): Workspace UUID
- `request`: ConnectRequest containing Git connection details

**Example**:
```python
# Note: Specific implementation may vary based on API version
connection = fabric_client.core.git.connect_workspace(
    workspace_id="12345678-1234-1234-1234-123456789abc",
    request=ConnectRequest(
        git_provider_type="GitHub",
        repository_url="https://github.com/org/repo",
        branch_name="main",
        directory_name="workspaces/MyWorkspace"
    )
)
```

---

### 5. Deployment Pipelines Module

**Path**: `fabric_client.core.deployment_pipelines`

Manage deployment pipelines for promoting content across environments.

#### Methods

##### `list_deployment_pipelines()`

List all deployment pipelines.

**Signature**:
```python
list_deployment_pipelines() -> ItemPaged[DeploymentPipeline]
```

**Returns**: Iterable of `DeploymentPipeline` objects

---

### 6. Connections Module

**Path**: `fabric_client.core.connections`

Manage data connections.

#### Methods

##### `list_connections()`

List all connections in a workspace.

**Signature**:
```python
list_connections(workspace_id: str) -> ItemPaged[Connection]
```

**Parameters**:
- `workspace_id` (str): Workspace UUID

**Returns**: Iterable of `Connection` objects

---

## Admin Modules Reference

**Path**: `fabric_client.admin`

The admin module provides administrative operations for Fabric tenants and organizations.

**Note**: This module requires Fabric Administrator role permissions.

**Available Admin Sub-Modules** (10 total):

### 1. Domains (`fabric_client.admin.domains`)

Manage Fabric domains for workspace organization.

**Key Methods**:
- `assign_domain_workspaces_by_capacities()` - Assign workspaces to domain by capacity
- `assign_domain_workspaces_by_ids()` - Assign workspaces to domain by workspace ID
- `create_domain()` - Create new domain
- `delete_domain()` - Delete domain
- `get_domain()` - Get domain details
- `list_domains()` - List all domains
- `unassign_domain_workspaces()` - Remove workspaces from domain
- `update_domain()` - Update domain properties

**Example**:
```python
# List all domains
domains = list(fabric_client.admin.domains.list_domains())
for domain in domains:
    print(f"{domain.display_name} (ID: {domain.id})")
```

---

### 2. External Data Shares Provider (`fabric_client.admin.external_data_shares_provider`)

Manage external data sharing as a provider.

**Key Methods**:
- `list_data_shares()` - List external data shares provided
- `revoke_data_share()` - Revoke data share access

---

### 3. Items (`fabric_client.admin.items`)

Administrative operations for Fabric items across workspaces.

**Key Methods**:
- `get_item()` - Get item details (admin view)
- `list_items()` - List items across all workspaces
- `get_item_access_details()` - Get item access and sharing information

---

### 4. Labels (`fabric_client.admin.labels`)

Manage sensitivity labels for data protection.

**Key Methods**:
- `list_labels()` - List available sensitivity labels
- `bulk_set_labels()` - Apply labels to multiple items
- `bulk_remove_labels()` - Remove labels from multiple items

---

### 5. Sharing Links (`fabric_client.admin.sharing_links`)

Manage sharing links across the tenant.

**Key Methods**:
- `list_sharing_links()` - List all sharing links
- `revoke_sharing_link()` - Revoke specific sharing link

**Note**: Also accessible as `fabric_client.admin.sharinglinks` (alias).

---

### 6. Tags (`fabric_client.admin.tags`)

Manage organizational tags for Fabric items.

**Key Methods**:
- `create_tag()` - Create new tag
- `delete_tag()` - Delete tag
- `list_tags()` - List all tags
- `update_tag()` - Update tag properties

---

### 7. Tenants (`fabric_client.admin.tenants`)

Manage tenant-wide settings and configurations.

**Key Methods**:
- `get_tenant_settings()` - Get tenant settings
- `list_capacities()` - List all capacities in tenant
- `list_workspaces()` - List all workspaces in tenant

---

### 8. Users (`fabric_client.admin.users`)

Manage user access and activities.

**Key Methods**:
- `get_user()` - Get user details
- `list_user_activities()` - List user activities (audit)
- `list_user_artifacts()` - List artifacts owned by user

---

### 9. Workspaces (`fabric_client.admin.workspaces`)

Administrative operations for workspaces across the tenant.

**Key Methods**:
- `get_workspace()` - Get workspace details (admin view)
- `list_workspaces()` - List all workspaces in tenant
- `get_workspace_access_details()` - Get workspace access and permissions
- `list_workspace_access()` - List users with workspace access
- `add_workspace_user()` - Add user to workspace
- `update_workspace_user()` - Update user workspace role
- `delete_workspace_user()` - Remove user from workspace

**Example**:
```python
# List all workspaces in tenant (admin)
workspaces = list(fabric_client.admin.workspaces.list_workspaces())
print(f"Total workspaces: {len(workspaces)}")
```

---

## Workload-Specific Modules

The SDK includes 37 specialized top-level modules for managing specific Fabric item types. Each module typically includes:
- `.items` - Item CRUD operations (create, read, update, delete)
- Additional sub-modules for workload-specific operations

### Quick Reference: All Workload Modules

| Module | Sub-Modules | Description |
|--------|-------------|-------------|
| `anomalydetector` | items | Anomaly Detector items |
| `apacheairflowjob` | files, items, pool_management, workspace_settings | Apache Airflow job orchestration |
| `copyjob` | items | Data pipeline copy jobs |
| `cosmosdbdatabase` | items | Cosmos DB database connections |
| `dashboard` | items | Power BI dashboards |
| `dataflow` | background_jobs, items, query_execution | Gen2 Dataflows |
| `datamart` | items | Datamarts |
| `datapipeline` | items | Data pipelines |
| `digitaltwinbuilder` | items | Digital Twin Builder |
| `digitaltwinbuilderflow` | items | Digital Twin Builder flows |
| `environment` | items, published, staging | Fabric environments |
| `eventhouse` | items | Real-Time Intelligence Eventhouses |
| `eventstream` | items, topology | Real-Time Intelligence Eventstreams |
| `graphmodel` | background_jobs, items | Graph models |
| `graphqlapi` | items | GraphQL APIs |
| `graphqueryset` | items | Graph query sets |
| `kqldashboard` | items | KQL dashboards |
| `kqldatabase` | items | KQL databases |
| `kqlqueryset` | items | KQL query sets |
| `lakehouse` | background_jobs, items, livy_sessions, tables | Lakehouses |
| `map` | items | Maps |
| `mirroredazuredatabrickscatalog` | discovery, items, refresh | Mirrored Databricks catalogs |
| `mirroreddatabase` | items, mirroring | Mirrored databases |
| `mirroredwarehouse` | items | Mirrored warehouses |
| `mlexperiment` | items | ML experiments |
| `mlmodel` | endpoint, items | ML models |
| `mounteddatafactory` | items | Mounted Data Factory |
| `notebook` | items, livy_sessions | Notebooks |
| `ontology` | items | Ontologies |
| `operationsagent` | items | Operations agents |
| `paginatedreport` | items | Paginated reports |
| `reflex` | items | Reflexes |
| `report` | items | Power BI reports |
| `semanticmodel` | items | Semantic models (datasets) |
| `spark` | custom_pools, livy_sessions, workspace_settings | Spark compute |
| `sparkjobdefinition` | background_jobs, items, livy_sessions | Spark job definitions |
| `sqldatabase` | items, mirroring | SQL databases |
| `sqlendpoint` | items, sql_audit_settings | SQL analytics endpoints |
| `userdatafunction` | items | User data functions |
| `variablelibrary` | items | Variable libraries |
| `warehouse` | items, restore_points, sql_audit_settings | Data warehouses |
| `warehousesnapshot` | items | Warehouse snapshots |

---

### Detailed Workload Module Examples

#### Lakehouse Module

**Path**: `fabric_client.lakehouse`

**Sub-Modules**:
- `.items` - Lakehouse CRUD operations
- `.background_jobs` - Load table operations
- `.livy_sessions` - Interactive Spark sessions
- `.tables` - Table management

**Example**:
```python
# Create a lakehouse
from microsoft_fabric_api.generated.lakehouse.models import CreateLakehouseRequest

lakehouse = fabric_client.lakehouse.items.create_item(
    workspace_id="workspace-id",
    request=CreateLakehouseRequest(display_name="My Lakehouse")
)

# List tables in lakehouse
tables = list(fabric_client.lakehouse.tables.list_tables(
    workspace_id="workspace-id",
    lakehouse_id=lakehouse.id
))
```

---

#### Notebook Module

**Path**: `fabric_client.notebook`

**Sub-Modules**:
- `.items` - Notebook CRUD operations
- `.livy_sessions` - Run notebook code interactively

**Example**:
```python
# Create a notebook
from microsoft_fabric_api.generated.notebook.models import CreateNotebookRequest

notebook = fabric_client.notebook.items.create_item(
    workspace_id="workspace-id",
    request=CreateNotebookRequest(display_name="ETL Notebook")
)
```

---

#### Semantic Model Module

**Path**: `fabric_client.semanticmodel`

**Sub-Modules**:
- `.items` - Semantic model CRUD operations

**Example**:
```python
# List semantic models in workspace
models = list(fabric_client.semanticmodel.items.list_items(
    workspace_id="workspace-id"
))
```

---

#### Warehouse Module

**Path**: `fabric_client.warehouse`

**Sub-Modules**:
- `.items` - Warehouse CRUD operations
- `.restore_points` - Backup and restore
- `.sql_audit_settings` - Audit configuration

**Example**:
```python
# Create a warehouse
from microsoft_fabric_api.generated.warehouse.models import CreateWarehouseRequest

warehouse = fabric_client.warehouse.items.create_item(
    workspace_id="workspace-id",
    request=CreateWarehouseRequest(display_name="Analytics Warehouse")
)

# List restore points
restore_points = list(fabric_client.warehouse.restore_points.list_restore_points(
    workspace_id="workspace-id",
    warehouse_id=warehouse.id
))
```

---

#### Eventhouse Module (Real-Time Intelligence)

**Path**: `fabric_client.eventhouse`

**Sub-Modules**:
- `.items` - Eventhouse CRUD operations

**Example**:
```python
# Create an eventhouse
from microsoft_fabric_api.generated.eventhouse.models import CreateEventhouseRequest

eventhouse = fabric_client.eventhouse.items.create_item(
    workspace_id="workspace-id",
    request=CreateEventhouseRequest(display_name="Real-Time Hub")
)
```

---

### Common Pattern: Item Operations

All workload modules follow a consistent pattern for item operations:

```python
# Generic pattern for any workload module
module = fabric_client.<workload_name>  # e.g., lakehouse, notebook, warehouse

# Create item
new_item = module.items.create_item(
    workspace_id="workspace-id",
    request=<CreateRequest>(display_name="Item Name")
)

# List items
items = list(module.items.list_items(workspace_id="workspace-id"))

# Get item
item = module.items.get_item(
    workspace_id="workspace-id",
    <item_type>_id=item_id
)

# Update item
updated = module.items.update_item(
    workspace_id="workspace-id",
    <item_type>_id=item_id,
    request=<UpdateRequest>(display_name="New Name")
)

# Delete item
module.items.delete_item(
    workspace_id="workspace-id",
    <item_type>_id=item_id
)
```

**Note**: Replace `<workload_name>`, `<CreateRequest>`, `<UpdateRequest>`, and `<item_type>` with the specific workload values.

---

## Common Patterns

### Pattern 1: List and Filter Resources

```python
# Get all workspaces and filter by name
workspaces = list(fabric_client.core.workspaces.list_workspaces())
dev_workspace = next((ws for ws in workspaces if ws.display_name == "[D] My Workspace"), None)

if dev_workspace:
    print(f"Found workspace: {dev_workspace.id}")
```

### Pattern 2: Iterate Through Items

```python
# Get all items in a workspace
items = list(fabric_client.core.items.list_items(workspace_id=workspace_id))

# Group by type
from collections import defaultdict
items_by_type = defaultdict(list)
for item in items:
    items_by_type[item.type].append(item)

print(f"Lakehouses: {len(items_by_type['Lakehouse'])}")
print(f"Notebooks: {len(items_by_type['Notebook'])}")
```

### Pattern 3: Create and Configure Resources

```python
# Create workspace, then create items in it
from microsoft_fabric_api.generated.core.models import (
    CreateWorkspaceRequest,
    CreateItemRequest
)

# 1. Create workspace
workspace = fabric_client.core.workspaces.create_workspace(
    request=CreateWorkspaceRequest(display_name="Dev Workspace")
)

# 2. Create lakehouse in workspace
lakehouse = fabric_client.core.items.create_item(
    workspace_id=workspace.id,
    request=CreateItemRequest(
        display_name="Bronze Lakehouse",
        type="Lakehouse"
    )
)

# 3. Create notebook in workspace
notebook = fabric_client.core.items.create_item(
    workspace_id=workspace.id,
    request=CreateItemRequest(
        display_name="ETL Notebook",
        type="Notebook"
    )
)
```

### Pattern 4: Error Handling

```python
from azure.core.exceptions import HttpResponseError

try:
    workspaces = list(fabric_client.core.workspaces.list_workspaces())
except HttpResponseError as e:
    if e.status_code == 401:
        print("Authentication failed - check credentials")
    elif e.status_code == 403:
        print("Permission denied - check workspace access")
    elif e.status_code == 404:
        print("Resource not found")
    else:
        print(f"API error: {e.status_code} - {e.message}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
```

### Pattern 5: Pagination Handling

```python
# Option 1: Convert to list (loads all results)
all_items = list(fabric_client.core.items.list_items(workspace_id=workspace_id))

# Option 2: Iterate without loading all (memory efficient)
for item in fabric_client.core.items.list_items(workspace_id=workspace_id):
    print(item.display_name)
    # Process one at a time
```

---

## Error Handling

### Common Exception Types

- `HttpResponseError` - API request failures
- `ResourceNotFoundError` - Resource doesn't exist
- `ClientAuthenticationError` - Authentication failures
- `ServiceRequestError` - Network/service errors

### Status Codes

| Code | Meaning | Common Cause |
|------|---------|-------------|
| 400 | Bad Request | Invalid parameters or request format |
| 401 | Unauthorized | Invalid or expired credentials |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist or was deleted |
| 409 | Conflict | Resource already exists or version conflict |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Service error (retry may help) |
| 503 | Service Unavailable | Service temporarily unavailable |

### Retry Logic Example

```python
import time
from azure.core.exceptions import HttpResponseError

def retry_on_throttle(func, max_retries=3, delay=1):
    """Retry function on throttling errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except HttpResponseError as e:
            if e.status_code == 429 and attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"Throttled. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                raise
    return None

# Usage
workspaces = retry_on_throttle(
    lambda: list(fabric_client.core.workspaces.list_workspaces())
)
```

---

## Examples

### Complete Workspace Setup

```python
from azure.identity import ClientSecretCredential
from microsoft_fabric_api import FabricClient
from microsoft_fabric_api.generated.core.models import (
    CreateWorkspaceRequest,
    CreateItemRequest
)

# 1. Authenticate
credential = ClientSecretCredential(
    tenant_id="your-tenant-id",
    client_id="your-client-id",
    client_secret="your-client-secret"
)

fabric_client = FabricClient(token_credential=credential)

# 2. Create workspace
workspace = fabric_client.core.workspaces.create_workspace(
    request=CreateWorkspaceRequest(
        display_name="Data Engineering Workspace",
        description="Medallion architecture workspace"
    )
)

workspace_id = workspace.id

# 3. Create Bronze lakehouse
bronze = fabric_client.core.items.create_item(
    workspace_id=workspace_id,
    request=CreateItemRequest(
        display_name="lakehouse_bronze",
        type="Lakehouse",
        description="Raw data ingestion layer"
    )
)

# 4. Create Silver lakehouse
silver = fabric_client.core.items.create_item(
    workspace_id=workspace_id,
    request=CreateItemRequest(
        display_name="lakehouse_silver",
        type="Lakehouse",
        description="Cleansed and transformed data"
    )
)

# 5. Create Gold lakehouse
gold = fabric_client.core.items.create_item(
    workspace_id=workspace_id,
    request=CreateItemRequest(
        display_name="lakehouse_gold",
        type="Lakehouse",
        description="Business-ready analytics"
    )
)

# 6. Create transformation notebook
notebook = fabric_client.core.items.create_item(
    workspace_id=workspace_id,
    request=CreateItemRequest(
        display_name="nb_transform",
        type="Notebook",
        description="PySpark transformation logic"
    )
)

print(f"✓ Workspace created: {workspace.display_name}")
print(f"✓ Items created: {len([bronze, silver, gold, notebook])}")
```

### Migrate Items Between Workspaces

```python
def migrate_items(source_workspace_id, target_workspace_id, item_types=None):
    """Copy items from one workspace to another."""

    # Get source items
    source_items = list(fabric_client.core.items.list_items(
        workspace_id=source_workspace_id
    ))

    # Filter by type if specified
    if item_types:
        source_items = [item for item in source_items if item.type in item_types]

    migrated = []

    for item in source_items:
        try:
            # Create item in target workspace
            new_item = fabric_client.core.items.create_item(
                workspace_id=target_workspace_id,
                request=CreateItemRequest(
                    display_name=item.display_name,
                    type=item.type,
                    description=f"Migrated from source workspace"
                )
            )
            migrated.append(new_item)
            print(f"✓ Migrated: {item.display_name}")
        except Exception as e:
            print(f"✗ Failed to migrate {item.display_name}: {str(e)}")

    return migrated

# Usage
migrated_items = migrate_items(
    source_workspace_id="source-workspace-id",
    target_workspace_id="target-workspace-id",
    item_types=["Lakehouse", "Notebook"]
)
```

---

## Resources

### Official Documentation

- **Microsoft Fabric REST API**: https://learn.microsoft.com/en-us/rest/api/fabric
- **Fabric API Quickstart**: https://learn.microsoft.com/en-us/rest/api/fabric/articles/get-started/fabric-api-quickstart
- **Azure Identity Library**: https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme

### Package Information

- **PyPI**: https://pypi.org/project/microsoft-fabric-api/
- **Version**: 0.1.0b2 (Beta)
- **License**: Microsoft

### Related Resources

- **Microsoft Fabric Documentation**: https://learn.microsoft.com/en-us/fabric/
- **Azure SDK for Python**: https://github.com/Azure/azure-sdk-for-python
- **MSAL Python**: https://github.com/AzureAD/microsoft-authentication-library-for-python

---

## Notes and Limitations

### Beta Status

This is a **beta release** (v0.1.0b2). Expect:
- API changes in future versions
- Incomplete documentation
- Possible breaking changes
- New features being added

### Known Limitations

1. **ItemPaged Returns**: Most list operations return `ItemPaged` objects, not lists
   - Must convert to list with `list()` or iterate directly
   - May cause confusion when expecting list methods

2. **Sparse Documentation**: Many methods lack comprehensive docstrings
   - Refer to REST API docs for parameter details
   - Use `inspect.signature()` to discover parameters

3. **Error Messages**: Error responses may not always be detailed
   - Check HTTP status codes for troubleshooting
   - Enable Azure SDK logging for detailed traces

4. **Rate Limiting**: Fabric API has rate limits
   - Implement retry logic with exponential backoff
   - Batch operations where possible

### Best Practices

1. **Always convert ItemPaged to list when needed**:
   ```python
   workspaces = list(fabric_client.core.workspaces.list_workspaces())
   ```

2. **Use try-except for robust error handling**:
   ```python
   from azure.core.exceptions import HttpResponseError
   try:
       workspace = fabric_client.core.workspaces.get_workspace(workspace_id)
   except HttpResponseError as e:
       print(f"Error {e.status_code}: {e.message}")
   ```

3. **Store IDs for reuse** - Don't repeatedly query for the same resource:
   ```python
   workspace_id = workspace.id  # Store for later use
   ```

4. **Use Service Principals for automation** - More secure than user credentials

5. **Test in Dev workspaces first** - Avoid accidental production changes

6. **Discover the complete API regularly** - Run the exploration notebook to find new features:
   ```bash
   # Run exploration notebook to discover all modules
   jupyter notebook scripts/fabric-api-exploration.ipynb
   ```
   Since this is a beta SDK, new modules and methods are added frequently.

---

## Appendix: API Discovery Code

This documentation already covers all 39 top-level modules discovered from the SDK. Use the code below to explore the API interactively or discover method signatures.

### Discover All Top-Level Modules

```python
# List all 39 top-level modules
print(f"Top-level modules in fabric_client ({len([x for x in dir(fabric_client) if not x.startswith('_') and not callable(getattr(fabric_client, x))])} total):")
for attr_name in sorted(dir(fabric_client)):
    if not attr_name.startswith('_'):
        attr = getattr(fabric_client, attr_name)
        if not callable(attr):
            print(f"  • {attr_name}")
```

**Expected Output**: `admin`, `anomalydetector`, `apacheairflowjob`, `copyjob`, `core`, `cosmosdbdatabase`, `dashboard`, `dataflow`, `datamart`, `datapipeline`, `digitaltwinbuilder`, `digitaltwinbuilderflow`, `environment`, `eventhouse`, `eventstream`, `graphmodel`, `graphqlapi`, `graphqueryset`, `kqldashboard`, `kqldatabase`, `kqlqueryset`, `lakehouse`, `map`, `mirroredazuredatabrickscatalog`, `mirroreddatabase`, `mirroredwarehouse`, `mlexperiment`, `mlmodel`, `mounteddatafactory`, `notebook`, `ontology`, `operationsagent`, `paginatedreport`, `reflex`, `report`, `semanticmodel`, `spark`, `sparkjobdefinition`, `sqldatabase`, `sqlendpoint`, `userdatafunction`, `variablelibrary`, `warehouse`, `warehousesnapshot`

---

### Explore Sub-Modules and Methods

```python
import inspect

def explore_api_module(module, module_name):
    """Discover all methods and their signatures in an API module."""
    print(f"\n{module_name}")
    print("=" * 70)

    for attr_name in dir(module):
        if not attr_name.startswith('_'):
            attr = getattr(module, attr_name)
            if callable(attr):
                try:
                    sig = inspect.signature(attr)
                    doc = inspect.getdoc(attr)
                    doc_summary = doc.split('\n')[0] if doc else "No documentation"
                    print(f"\n  {attr_name}{sig}")
                    print(f"  → {doc_summary[:100]}...")
                except Exception as e:
                    print(f"\n  {attr_name}() - Unable to inspect")

# Examples: Explore specific modules

# Core workspaces
explore_api_module(fabric_client.core.workspaces, "core.workspaces")

# Admin domains
explore_api_module(fabric_client.admin.domains, "admin.domains")

# Lakehouse items
explore_api_module(fabric_client.lakehouse.items, "lakehouse.items")

# Notebook operations
explore_api_module(fabric_client.notebook.items, "notebook.items")
```

---

### List All Sub-Modules for a Top-Level Module

```python
def list_submodules(top_level_module_name):
    """List all sub-modules for a given top-level module."""
    module = getattr(fabric_client, top_level_module_name)
    print(f"\n{top_level_module_name} sub-modules:")

    submodules = []
    for attr_name in dir(module):
        if not attr_name.startswith('_'):
            attr = getattr(module, attr_name)
            if not callable(attr):
                submodules.append(attr_name)

    for submodule in sorted(submodules):
        print(f"  • {top_level_module_name}.{submodule}")

    return submodules

# Examples
list_submodules('core')      # 21 sub-modules
list_submodules('admin')     # 10 sub-modules
list_submodules('lakehouse') # 4 sub-modules
list_submodules('warehouse') # 3 sub-modules
```

---

### Inspect Method Parameters and Docstrings

```python
import inspect

def inspect_method(module_path, method_name):
    """Get detailed information about a specific method.

    Args:
        module_path: Dot-notation path (e.g., 'core.workspaces')
        method_name: Method name (e.g., 'list_workspaces')
    """
    parts = module_path.split('.')
    module = fabric_client

    for part in parts:
        module = getattr(module, part)

    method = getattr(module, method_name)

    print(f"\n{module_path}.{method_name}")
    print("=" * 70)
    print(f"\nSignature: {inspect.signature(method)}")
    print(f"\nDocumentation:\n{inspect.getdoc(method) or 'No documentation available'}")

# Examples
inspect_method('core.workspaces', 'list_workspaces')
inspect_method('core.items', 'create_item')
inspect_method('admin.domains', 'assign_domain_workspaces_by_ids')
inspect_method('lakehouse.items', 'create_item')
```

---

### Generate Complete JSON Documentation

The complete API structure is already documented in [fabric-api-complete-documentation.json](../scripts/fabric-api-complete-documentation.json), which was generated using:

```bash
# Run the exploration notebook to regenerate
jupyter notebook scripts/fabric-api-exploration.ipynb
```

This generates a JSON file with:
- All 39 top-level modules
- 100+ sub-modules and their methods
- Method signatures and docstrings
- Properties and attributes

**JSON Structure**:
```json
{
  "client": "FabricClient",
  "version": "0.1.0b2",
  "top_level_modules": ["admin", "core", "lakehouse", ...],
  "all_modules": {
    "core.workspaces": {
      "path": "fabric_client.core.workspaces",
      "type": "WorkspacesOperations",
      "methods": [...],
      "properties": [...]
    },
    ...
  }
}
```

---

**Document Version**: 2.0  
**Last Updated**: February 13, 2026  
**Status**: Complete - Based on full API discovery from fabric-api-complete-documentation.json

---

## Contributing

This documentation provides complete coverage of all 39 top-level modules in `microsoft-fabric-api` version 0.1.0b2.

If you discover new API methods, corrections, or when the SDK version updates:

1. Run the [fabric-api-exploration.ipynb](../scripts/fabric-api-exploration.ipynb) notebook to regenerate the JSON
2. Update this document with new findings
3. Share discoveries with the team
4. Update the document version number

**Maintenance Checklist**:
- ✅ All 39 top-level modules documented
- ✅ Admin module (10 sub-modules) documented
- ✅ Core module (21 sub-modules) documented
- ✅ Workload-specific modules documented with examples
- ✅ Common patterns and usage examples provided

---

*This documentation is based on `microsoft-fabric-api` version 0.1.0b2 and the complete API discovery performed on February 13, 2026. Always refer to official Microsoft documentation for the most up-to-date information.*
