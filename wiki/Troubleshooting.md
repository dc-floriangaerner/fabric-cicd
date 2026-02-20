# Troubleshooting

Common issues and solutions for Fabric CI/CD deployments.

## Authentication Issues

### ClientSecretCredential Authentication Failed

**Error**: `ClientSecretCredential authentication failed` or `DefaultAzureCredential failed to retrieve a token`

**Causes**:
- Incorrect GitHub secrets (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID)
- Service Principal doesn't have Fabric workspace access
- Service Principal created in wrong Microsoft Entra ID tenant
- Client secret expired

**Solutions**:
1. Verify GitHub secrets are correctly configured:
   - Go to Settings → Secrets and variables → Actions
   - Check AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_TENANT_ID
2. Verify Service Principal has workspace access:
   - Open Fabric workspace → Workspace settings → Manage access
   - Ensure Service Principal has Admin or Contributor role
3. Check Service Principal tenant:
   - Azure Portal → Microsoft Entra ID → App registrations
   - Verify tenant ID matches AZURE_TENANT_ID secret
4. Check client secret expiration:
   - Azure Portal → App registrations → Your app → Certificates & secrets
   - Create new secret if expired (max 2 years)

## Workspace Issues

### Workspace Not Found

**Error**: `Workspace '[D] Fabric Blueprint' not found`

**Causes**:
- Workspace was not provisioned by Terraform yet
- Workspace name in `config.yml` doesn’t match the Terraform-created name
- Service Principal doesn’t have access to workspace
- Workspace name is case-sensitive

**Solutions**:
1. Confirm the workspace was provisioned by Terraform:
   - Check the `terraform.yml` workflow run completed successfully for the target environment
   - Run `terraform show` locally to inspect current state
2. Check `config.yml` workspace name matches exactly:
   - Open `workspaces/<workspace-name>/config.yml`
   - Verify it matches the `workspace_name_*` value in `terraform/environments/<env>.tfvars`
3. Re-run Terraform if the workspace is missing:
   - Go to **Actions** → **Terraform — Fabric Infrastructure** → **Run workflow**
   - Select the target environment

### No Workspaces Detected

**Error**: `No workspace folders found to deploy`

**Causes**:
- Workspace folders missing `config.yml` or `parameter.yml`
- Incorrect folder structure
- Files named incorrectly

**Solutions**:
1. Verify folder structure:
   ```
   workspaces/
   ├── <Workspace Name>/
   │   ├── config.yml         # Required
   │   ├── parameter.yml      # Required
   │   └── <items>/
   ```
2. Check file names (case-sensitive):
   - `config.yml` (not Config.yml or config.yaml)
   - `parameter.yml` (not Parameter.yml or parameter.yaml)
3. Validate file contents:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yml'))"
   ```

## Deployment Issues

### Item Deployment Failed

**Error**: `Failed to publish item: <item-name>`

**Causes**:
- Invalid item definition (malformed JSON/Python)
- Missing metadata files
- Item name violates Fabric naming restrictions
- Incorrect ID transformations

**Solutions**:
1. Validate JSON files:
   ```bash
   python -m json.tool item-content.json
   ```
2. Check required metadata files:
   - `<item-type>-content.json/py` - Main definition
   - `<item-type>.metadata.json` - Metadata
   - `alm.settings.json` - ALM config (lakehouses only)
3. Verify item name follows restrictions:
   - Max 256 characters
   - Cannot end with `.` or space
   - Forbidden characters: `" / : < > \ * ? |`
4. Review `parameter.yml` transformations:
   - Check Dev IDs are correct
   - Verify replacement variables are valid

### ID Transformation Not Working

**Error**: Item references wrong workspace/lakehouse ID after deployment

**Causes**:
- `find_value` doesn't match Dev workspace ID
- Regex pattern is incorrect
- Item type filter is wrong
- Case-sensitive mismatch

**Solutions**:
1. Verify `find_value` matches Dev ID exactly:
   ```yaml
   - find_value: "12345678-1234-1234-1234-123456789abc"  # Must match Dev ID
   ```
2. Test regex patterns:
   - Use https://regex101.com/ to test patterns
   - Ensure proper escaping of special characters
3. Check item type matches:
   ```yaml
   item_type: "Notebook"  # Case-sensitive
   ```
4. Review deployment logs:
   - Look for "ID Transformation" section
   - Check which transformations were applied

### Orphan Items Not Removed

**Error**: Old items remain in workspace after removal from repository

**Causes**:
- Orphan cleanup is disabled in `config.yml`
- Item type not in scope for deployment
- Service Principal lacks delete permissions

**Solutions**:
1. Check `config.yml` for cleanup settings:
   ```yaml
   unpublish:
     skip:
       dev: false  # Should be false to enable cleanup
   ```
2. Verify item type is supported:
   - Lakehouse, Notebook, DataPipeline, SemanticModel, etc.
3. Check Service Principal permissions:
   - Must have Admin or Contributor role
   - Verify can delete items manually in Fabric

### Rollback Failed

**Error**: Some workspaces did not deploy correctly after a failure

**Causes**:
- Service Principal lacks permissions on some workspaces
- Items locked or in use

**Solutions**:
1. Review deployment logs:
   - Identify which workspace failed
   - Check specific error messages
2. Verify Service Principal permissions:
   - All workspaces need Admin or Contributor role (granted via Terraform)
   - Re-run `terraform.yml` for the affected environment to restore expected role assignments

## Terraform Issues

### Terraform Plan Fails

**Error**: `Error: could not configure provider...` or authentication errors in `terraform.yml`

**Causes**:
- GitHub secrets `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` missing or incorrect
- `ARM_SUBSCRIPTION_ID` secret missing (required for state storage access)

**Solutions**:
1. Verify all four required secrets are set in the GitHub repository:
   - `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `ARM_SUBSCRIPTION_ID`
2. Confirm Service Principal has `Storage Blob Data Contributor` on the Terraform state storage account

### Terraform State Drift

**Symptom**: Workspace exists in Fabric but Terraform wants to recreate it

**Causes**:
- Workspace was created outside Terraform (manually)
- State file was deleted or corrupted

**Solutions**:
1. Import the existing workspace into Terraform state:
   ```bash
   terraform import fabric_workspace.fabric_blueprint <workspace-id>
   ```
2. Run `terraform plan` to confirm no destructive changes before applying

## Workflow Issues

### Deployment Not Triggered

**Error**: Pipeline doesn't run after merge to main

**Causes**:
- Changes not in `workspaces/**` paths
- Workflow file is disabled
- Branch protection rules preventing workflow

**Solutions**:
1. Check changed files:
   - Automatic deployment only triggers on `workspaces/**` changes
   - Changes to `.github/`, `scripts/`, docs DO NOT trigger
2. Verify workflow is enabled:
   - Go to Actions → Deploy to Microsoft Fabric
   - Check if workflow is enabled
3. Use manual workflow dispatch:
   - Actions → Deploy to Microsoft Fabric → Run workflow
   - Select environment and trigger manually

### Workflow Permission Denied

**Error**: `Resource not accessible by integration` or workflow permission errors

**Causes**:
- GitHub Actions permissions not configured
- GITHUB_TOKEN lacks necessary permissions
- Environment protection rules blocking deployment

**Solutions**:
1. Check Actions permissions:
   - Settings → Actions → General
   - Workflow permissions: "Read and write permissions"
2. Verify environment settings:
   - Settings → Environments → Select environment
   - Check deployment branch rules
3. Review protection rules:
   - Required reviewers (needs GitHub Team/Enterprise)
   - Deployment branches configuration

## Configuration Issues

### Invalid YAML Syntax

**Error**: `yaml.scanner.ScannerError` or YAML parsing failed

**Causes**:
- Incorrect indentation (must use spaces, not tabs)
- Missing colons or quotes
- Invalid characters in string values

**Solutions**:
1. Validate YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yml'))"
   ```
2. Check indentation:
   - Use 2 spaces (not tabs)
   - Consistent indentation throughout file
3. Quote string values with special characters:
   ```yaml
   find_value: 'regex\s*pattern\s*here'  # Quote regex patterns
   ```

### Missing Required Fields

**Error**: `KeyError` or missing configuration values

**Causes**:
- Required fields not specified in `config.yml`
- Incorrect field names (case-sensitive)
- Missing nested structure

**Solutions**:
1. Verify required fields in `config.yml`:
   ```yaml
   core:
     workspace:
       dev: "[D] Workspace Name"    # Required
       test: "[T] Workspace Name"   # Required
       prod: "[P] Workspace Name"   # Required
     repository_directory: "."       # Required
     parameter: "parameter.yml"      # Required
   ```
2. Check field names (case-sensitive):
   - `workspace` not `Workspace`
   - `parameter` not `parameters`

## Debug Mode

Enable debug logging for more detailed information:

1. Add GitHub secret:
   - Name: `ACTIONS_RUNNER_DEBUG`
   - Value: `true`
2. Re-run failed workflow
3. Review expanded debug output in Actions logs

## Getting Help

If issues persist after trying these solutions:

1. **Check workflow logs** - Review full logs for specific error messages
2. **Verify configuration** - Double-check all `config.yml` and `parameter.yml` files
3. **Test locally** - Try deploying to a test workspace first
4. **Review documentation** - Check [Setup Guide](Setup-Guide) and [Workspace Configuration](Workspace-Configuration)
5. **Contact support** - Email [florian.gaerner@dataciders.com](mailto:florian.gaerner@dataciders.com) for assistance

## Additional Resources

- [Microsoft Fabric Documentation](https://learn.microsoft.com/fabric/)
- [fabric-cicd Library](https://pypi.org/project/fabric-cicd/)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Azure Service Principal Setup](https://learn.microsoft.com/azure/active-directory/develop/howto-create-service-principal-portal)
