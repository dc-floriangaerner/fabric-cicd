# Contributing to Fabric CI/CD Reference Architecture

Thank you for your interest in contributing to this reference architecture! This document provides guidelines for contributing to the project.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Pull Request Process](#pull-request-process)

## Code of Conduct

This project follows standard open-source collaboration practices:
- Be respectful and constructive
- Focus on what's best for the community
- Show empathy towards other contributors

## How Can I Contribute?

### Reporting Bugs
- Use the [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) template
- Check existing issues to avoid duplicates
- Include detailed reproduction steps
- Provide environment information

### Suggesting Features
- Use the [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) template
- Clearly describe the use case
- Consider implementation complexity
- Discuss alternatives

### Contributing Code
1. **Fork the repository** (for external contributors)
2. **Create an issue** documenting your proposed changes
3. **Create a feature branch** from `main`
4. **Make your changes** following our coding standards
5. **Write tests** for new functionality
6. **Update documentation** as needed
7. **Submit a Pull Request**

## Development Workflow

### Required GitHub Workflow

**All changes must follow this process:**

1. **Create a GitHub Issue**
   - Document what you're changing and why
   - Include acceptance criteria
   - Apply appropriate labels (`bug`, `enhancement`, `documentation`)

2. **Create a Feature Branch**
   - Use descriptive names: `feature/<issue-number>-brief-description`
   - Example: `feature/42-add-platinum-lakehouse`
   - Branch from latest `main`:
     ```powershell
     git checkout main
     git pull
     git checkout -b feature/42-add-platinum-lakehouse
     ```

3. **Make Changes**
   - Commit frequently with clear messages referencing the issue
   - Example: `git commit -m "Add platinum lakehouse structure #42"`
   - Keep commits focused and atomic

4. **Test Locally**
   - Run `ruff check scripts/` (linting)
   - Run `ruff format scripts/` (formatting)
   - Run `pytest tests/` (tests)
   - Run `pre-commit run --all-files` (all hooks)

5. **Create Pull Request**
   - Push branch: `git push -u origin feature/42-add-platinum-lakehouse`
   - Create PR from your branch to `main`
   - Reference the issue: "Closes #42"
   - Add reviewers
   - Ensure CI checks pass

6. **Review and Merge**
   - Address review feedback
   - Squash commits for clean history
   - Delete branch after merge

## Coding Standards

### Python Code

**Style Guide:**
- Follow PEP 8 conventions
- Use type hints for function arguments and return values
- Line length: 120 characters max
- Use Ruff for linting and formatting

**Example:**
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
        logger.info(f"Starting deployment to {workspace_name}")
        # deployment logic here
        return True
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        return False
```

**Error Handling:**
- Catch specific exceptions, not bare `except:`
- Use `sys.exit(1)` for fatal errors
- Log errors with context

**Logging:**
- Use the `logging` module, not `print()`
- Use appropriate log levels: `debug`, `info`, `warning`, `error`
- Include context in log messages

### Fabric Item Definitions

**Naming Conventions:**
- Item prefixes: `cp_` (Copy jobs), `nb_` (Notebooks), `lakehouse_` (Lakehouses), `da_` (Data agents)
- Layer prefixes: `br_` (Bronze), `sl_` (Silver), `gd_` (Gold)
- Max 256 characters for display names
- No forbidden characters: `" / : < > \ * ? |`

**File Structure:**
```
<item-name>.<ItemType>/
  ├── <item-type>-content.json/py
  ├── <item-type>.metadata.json
  ├── alm.settings.json (for lakehouses)
  └── shortcuts.metadata.json (for lakehouses)
```

**JSON Formatting:**
- All JSON files must be valid
- Use 2-space indentation
- Validate with `python -m json.tool <file>.json`

**Notebooks:**
- Preserve `# METADATA` and `# CELL` comment structure
- Use `synapse_pyspark` kernel
- Include cell boundaries

### YAML Configuration

**Style:**
- Use 2-space indentation (not tabs)
- Add descriptive comments for complex transformations
- Escape special characters in regex patterns

**Example:**
```yaml
find_replace:
  - find_value: 'database\s*=\s*Sql\.Database\s*\(\s*"([^"]+)"'
    replace_value:
      _ALL_: "$items.Lakehouse.lakehouse_silver.sqlendpoint"
    is_regex: "true"
    item_type: "SemanticModel"
    # Transforms SQL Database references to Silver lakehouse endpoint
```

## Testing Guidelines

### Test Structure
```
tests/
├── __init__.py
├── conftest.py               # Shared fixtures
├── test_deployment_config.py # Configuration tests
├── test_deploy_to_fabric.py  # Main deployment script tests
└── test_fabric_workspace_manager.py  # Workspace manager tests
```

### Writing Tests

**Focus on pure logic:**
- Configuration loading and validation
- Argument parsing
- Workspace discovery
- ID transformation logic

**Mock external dependencies:**
- Fabric API calls
- Azure authentication
- File system operations (when appropriate)

**Example:**
```python
def test_load_workspace_config(tmp_path):
    """Test loading valid workspace configuration."""
    config_file = tmp_path / "config.yml"
    config_file.write_text("""
core:
  workspace:
    dev: "[D] Test Workspace"
    test: "[T] Test Workspace"
    prod: "[P] Test Workspace"
""")

    config = load_config(str(config_file))
    assert config["core"]["workspace"]["dev"] == "[D] Test Workspace"
```

### Running Tests

```powershell
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=scripts --cov-report=html

# Run specific test file
pytest tests/test_deployment_config.py
```

## Documentation

### Code Documentation

**Docstrings:**
- Use Google-style docstrings
- Include Args, Returns, Raises sections
- Provide examples for complex functions

**Comments:**
- Explain why, not what
- Use inline comments sparingly
- Keep comments up-to-date with code changes

### User Documentation

**README.md:**
- Keep concise as primary entry point
- Focus on Quick Start and essential information
- Link to Wiki for detailed guidance

**Wiki:**
- Comprehensive reference for all functionality
- Step-by-step guides with screenshots
- Troubleshooting section with common issues

**Code Examples:**
- Provide working examples
- Include both PowerShell and Bash variants (when applicable)
- Test examples before committing

## Pull Request Process

### Before Submitting

- [ ] Code passes all linting checks (`ruff check scripts/`)
- [ ] Code is properly formatted (`ruff format scripts/`)
- [ ] All tests pass (`pytest tests/`)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] Documentation is updated
- [ ] Commit messages are clear and reference the issue

### PR Description Template

```markdown
## Description
Brief description of changes

## Related Issue
Closes #<issue-number>

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing Performed
- [ ] Local testing completed
- [ ] Unit tests added/updated
- [ ] Manual testing in Dev environment

## Deployment Considerations
Any special considerations for deployment (database migrations, config changes, etc.)

## Screenshots (if applicable)
Add screenshots for UI changes or documentation updates
```

### Review Process

1. **Automated Checks**: All CI/CD checks must pass
2. **Code Review**: At least one approval required
3. **Testing**: Verify changes work as expected
4. **Documentation**: Ensure documentation is clear and complete
5. **Merge**: Squash commits for clean history

### After Merge

- Feature branch is automatically deleted
- Changes deploy to Dev environment (if in `workspaces/**` paths)
- Monitor GitHub Actions for deployment success
- Verify deployment in Fabric workspace

## Questions or Problems?

- Check the [GitHub Wiki](https://github.com/dc-floriangaerner/dc-fabric-cicd/wiki) for detailed guidance
- Search [existing issues](https://github.com/dc-floriangaerner/dc-fabric-cicd/issues)
- Create a new issue with your question
- Reach out to project maintainers

Thank you for contributing! 🎉
