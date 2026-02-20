# Frequently Asked Questions (FAQ)

## General Questions

### What is this project?

This is a reference architecture for implementing CI/CD pipelines for Microsoft Fabric workspaces using GitHub Actions and the `fabric-cicd` Python library. It demonstrates best practices for deploying multiple workspaces from a single repository using a medallion architecture (Bronze → Silver → Gold).

### Do I need to be a Fabric expert to use this?

No, but basic familiarity with Microsoft Fabric workspaces and GitHub Actions is helpful. The [Setup Guide](Setup-Guide) provides step-by-step instructions for getting started.

### Can I use this with Azure DevOps instead of GitHub Actions?

This reference architecture is designed for GitHub Actions. However, the core concepts and scripts can be adapted for Azure DevOps Pipelines with modifications to the workflow files.

## Setup and Configuration

### How long does initial setup take?

Approximately 30-45 minutes for first-time setup, including:
- Creating Service Principal (10 minutes)
- Granting workspace permissions (10 minutes)
- Configuring GitHub secrets (5 minutes)
- Testing deployment (15-20 minutes)

### Do I need separate Service Principals for each environment?

No. You can use a single Service Principal with access to all workspaces (Dev, Test, Prod), or create separate Service Principals per environment for better security isolation.

### What permissions does the Service Principal need?

The Service Principal needs **Workspace Contributor** or **Workspace Admin** role on each target workspace. Admin role is required if you need to manage workspace settings or user access. Terraform grants this automatically when creating the workspace (the creating identity becomes Admin).

### Do workspaces need to be created before running the deployment pipeline?

Yes. Workspace lifecycle is managed by Terraform (`terraform.yml`), not by the Python deployment scripts. Run Terraform first, then run the item deployment pipeline (`fabric-deploy.yml`).

## Workspace Management

### How many workspaces can I deploy from one repository?

There's no hard limit. The deployment script automatically discovers all workspace folders containing `config.yml` and `parameter.yml` files. Each workspace deploys independently.

### Can I have different medallion layers (Bronze/Silver/Gold) in different workspaces?

Yes. Each workspace folder can have its own structure. The "Fabric Blueprint" workspace demonstrates the medallion architecture, but you can customize the folder structure for each workspace.

### What happens if I delete a workspace folder from the repository?

By default, orphan cleanup is enabled, so items not present in the repository will be removed from the Fabric workspace during deployment. You can disable this by setting `unpublish.skip` to `true` in `config.yml`.

### How do I add a new workspace?

1. Add Terraform resources for the new workspace in `terraform/main.tf`
2. Add variable values in each `terraform/environments/*.tfvars`
3. Create a workspace folder: `workspaces/<Workspace Name>/`
4. Create `config.yml` with workspace names (must match the Terraform `workspace_name_*` values)
5. Create `parameter.yml` with transformation rules
6. Add workspace items (Lakehouses, Notebooks, etc.)
7. Run (or trigger) `terraform.yml` to provision the workspace
8. Commit and push to trigger item deployment

## Deployment

### When does deployment happen automatically?

Deployment to **Dev** happens automatically when a PR is merged to `main` branch with changes in `workspaces/**` paths. Test and Prod deployments are manual via workflow dispatch.

### Why didn't my merge trigger a deployment?

Automatic deployment only triggers when changes are made to files in `workspaces/**` paths. Changes to `.github/`, `scripts/`, or documentation files do NOT trigger automatic deployment.

### Can I deploy to Prod directly?

Technically yes, but it's not recommended. The workflow supports deploying to any environment, but best practice is to deploy Dev → Test → Prod in sequence for validation.

### What is atomic rollback?

Atomic rollback means if any workspace deployment fails, all previously deployed workspaces in that run are automatically rolled back to their previous state. This keeps environments consistent.

**Note**: Atomic rollback is a planned feature. Currently, deployments stop on first failure without automatic rollback.

### How long does a deployment take?

- **Single workspace**: 2-5 minutes
- **Multiple workspaces**: 5-15 minutes (depends on number of items)
- **Large workspaces**: 10-20 minutes (hundreds of items)

## ID Transformation

### What are ID transformations?

ID transformations replace environment-specific values (like Dev lakehouse IDs) with target environment values (like Prod lakehouse IDs) during deployment. This is configured in `parameter.yml`.

### How do I find my Dev workspace IDs?

1. **Fabric UI**: Open item in Dev workspace, check URL for GUID
2. **Fabric API**: Use `az rest --method get --url "https://api.fabric.microsoft.com/v1/workspaces/<workspace-id>/items"`
3. **Deployment logs**: After first deployment, IDs are shown in GitHub Actions logs

### Why aren't my IDs transforming?

Common causes:
- `find_value` doesn't match Dev ID exactly (check case and format)
- Regex pattern is incorrect (test at [regex101.com](https://regex101.com/))
- `item_type` filter doesn't match (case-sensitive: "Notebook" not "notebook")
- Missing `is_regex: "true"` for regex patterns

### Can I use the same parameter.yml for all workspaces?

No. Each workspace folder needs its own `parameter.yml` with that workspace's specific Dev IDs. IDs are unique per workspace.

## Security

### Are my GitHub secrets secure?

Yes. GitHub Secrets are encrypted and never exposed in logs. The workflow uses `***` masking for secret values. Never print secrets with `echo ${{ secrets.* }}`.

### How often should I rotate Service Principal secrets?

Microsoft recommends rotating client secrets every 90 days for production environments. You can configure secrets with up to 2 years expiration in Azure AD.

### Can I use Managed Identity instead of Service Principal?

Not directly with GitHub Actions. Service Principal with client secret is the standard authentication method for external CI/CD systems. Managed Identity works for Azure-hosted runners only.

## Troubleshooting

### Deployment failed with "Workspace not found"

1. Verify workspace exists in Fabric portal
2. Check `config.yml` workspace name matches exactly (case-sensitive)
3. Ensure Service Principal has access to the workspace
4. Confirm workspace name includes environment prefix (e.g., `[D]`, `[T]`, `[P]`)

### Authentication failed errors

1. Verify GitHub secrets are set correctly (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`)
2. Check Service Principal exists in correct Azure AD tenant
3. Ensure client secret hasn't expired
4. Verify Service Principal has Fabric workspace permissions

### Items are deploying but with wrong IDs

This indicates ID transformation rules in `parameter.yml` aren't working:
1. Check `find_value` matches your Dev workspace IDs exactly
2. Verify `replace_value` uses correct variable syntax (e.g., `$items.Lakehouse.lakehouse_name.id`)
3. Ensure `item_type` matches the item you're transforming
4. Test regex patterns if using `is_regex: "true"`

### Old items aren't being removed

Orphan cleanup may be disabled. Check `config.yml`:
```yaml
unpublish:
  skip:
    dev: false  # Should be false to enable cleanup
```

## Advanced Topics

### Can I customize the deployment script?

Yes! The deployment scripts are in `scripts/` directory:
- `deploy_to_fabric.py` — Main deployment orchestration
- `deployment_config.py` — Configuration constants

Follow the [GitHub workflow](https://github.com/dc-floriangaerner/dc-fabric-cicd/blob/main/.github/copilot-instructions.md#making-changes-to-this-repository) for making changes.

### How do I test changes locally before deploying?

```bash
# Install dependencies
pip install fabric-cicd azure-identity

# Deploy to Dev locally (requires Azure CLI authentication)
python -m scripts.deploy_to_fabric \
  --workspaces_directory workspaces \
  --environment dev
```

### Can I exclude certain items from deployment?

Currently, the `fabric-cicd` library deploys all items in the workspace folder. To exclude items, either:
1. Move them outside the workspace folder structure
2. Use `.gitignore` to prevent them from being committed (they won't be deployed)

### How do I handle sensitive data in notebooks?

Never commit sensitive data. Instead:
1. Use environment variables in notebooks
2. Reference Azure Key Vault secrets
3. Use parameter cells in notebooks with values passed at runtime
4. Store connection strings in Fabric workspace settings (not in code)

## Getting More Help

Still have questions?

- **Troubleshooting Guide**: [Troubleshooting](Troubleshooting)
- **Setup Guide**: [Setup Guide](Setup-Guide)
- **Microsoft Fabric Docs**: [learn.microsoft.com/fabric/](https://learn.microsoft.com/fabric/)
- **fabric-cicd Library**: [microsoft.github.io/fabric-cicd/](https://microsoft.github.io/fabric-cicd/)
- **GitHub Issues**: [Create an issue](https://github.com/dc-floriangaerner/dc-fabric-cicd/issues/new)
- **Email Support**: [florian.gaerner@dataciders.com](mailto:florian.gaerner@dataciders.com)
