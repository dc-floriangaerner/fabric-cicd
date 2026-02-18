# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Scan workspace item files for GUIDs that have no matching find_replace rule in
parameter.yml. Any unmatched GUID will be deployed verbatim, causing the file to
reference a Dev-only ID in Test or Production environments.

Scanned contexts:
  Notebooks  (notebook-content.py)
    - # META  "default_lakehouse": "GUID"
    - # META  "default_lakehouse_workspace_id": "GUID"
    - # META  "default_lakehouse_sql_endpoint": "GUID"
    - # META containing known_lakehouses GUID references
  JSON item content files (e.g. copyjob-content.json, pipeline-content.json)
    - "workspaceId", "artifactId", "lakehouseId", "connectionId" field values

Usage:
    python -m scripts.check_unmapped_ids --workspaces_directory workspaces
    python -m scripts.check_unmapped_ids --workspaces_directory workspaces \\
        --workspace_filter "Fabric Blueprint"
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .deployment_config import (
    CONFIG_FILE,
    EXIT_FAILURE,
    EXIT_SUCCESS,
    SEPARATOR_LONG,
    SEPARATOR_SHORT,
)
from .logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")

# # META fields in notebook-content.py that embed environment-specific GUIDs.
# Checked individually by field name to keep false-positive rate low.
NOTEBOOK_SENSITIVE_FIELDS = {
    "default_lakehouse",
    "default_lakehouse_workspace_id",
    "default_lakehouse_sql_endpoint",
}

# Additional # META context keyword that may embed multiple GUIDs inline
NOTEBOOK_KNOWN_LAKEHOUSES_KEY = "known_lakehouses"

# JSON fields in item content files that typically carry env-specific GUIDs
JSON_SENSITIVE_FIELDS = {
    "workspaceId",
    "artifactId",
    "lakehouseId",
    "connectionId",
}

# Files that never require parameterisation — skip entirely
SKIP_FILENAMES = {
    "alm.settings.json",
    "shortcuts.metadata.json",
    "stage_config.json",
}

# Suffixes that are metadata, not deployable content
SKIP_SUFFIXES = {".metadata.json"}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class FindReplaceRule:
    """Parsed representation of one find_replace entry in parameter.yml."""

    find_value: str
    is_regex: bool
    item_types: list[str]  # empty list = applies to all types
    file_paths: list[str]  # empty list = applies to all files
    source_file: str = ""
    _compiled: re.Pattern | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.is_regex:
            try:
                self._compiled = re.compile(self.find_value)
            except re.error as exc:
                logger.warning(f"  [WARN] Could not compile regex in {self.source_file}: {exc}")
                self._compiled = None


@dataclass
class UnmappedGuid:
    """A GUID found in an item file that has no covering rule."""

    workspace_folder: str
    relative_file: str  # relative to repo root
    item_type: str
    field_name: str
    guid: str
    context: str  # the source line (trimmed) where the GUID was found


# ---------------------------------------------------------------------------
# Parameter file loading
# ---------------------------------------------------------------------------


def _normalise_to_list(value: object) -> list[str]:
    """Return a list[str] regardless of whether value is str, list, or None."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def load_rules(param_file: Path, _seen: set[Path] | None = None) -> list[FindReplaceRule]:
    """Recursively load find_replace rules from a parameter.yml (and its extends)."""
    if _seen is None:
        _seen = set()

    resolved = param_file.resolve()
    if resolved in _seen or not param_file.exists():
        return []
    _seen.add(resolved)

    try:
        raw = yaml.safe_load(param_file.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning(f"  [WARN] Could not parse {param_file}: {exc}")
        return []

    if not isinstance(raw, dict):
        return []

    rules: list[FindReplaceRule] = []

    # Process extended template files first
    for rel in _normalise_to_list(raw.get("extend")):
        extended = (param_file.parent / rel).resolve()
        rules.extend(load_rules(extended, _seen))

    # Process find_replace entries in this file
    for entry in raw.get("find_replace") or []:
        if not isinstance(entry, dict):
            continue
        find_value = str(entry.get("find_value", "")).strip()
        if not find_value:
            continue

        is_regex = str(entry.get("is_regex", "false")).lower() in ("true",)
        item_types = _normalise_to_list(entry.get("item_type"))
        file_paths = _normalise_to_list(entry.get("file_path"))

        rules.append(
            FindReplaceRule(
                find_value=find_value,
                is_regex=is_regex,
                item_types=item_types,
                file_paths=file_paths,
                source_file=str(param_file),
            )
        )

    return rules


# ---------------------------------------------------------------------------
# Path / item-type helpers
# ---------------------------------------------------------------------------


def item_type_from_path(path: Path) -> str:
    """Derive the Fabric item type from its containing folder name.

    Folder names follow the pattern  ``<DisplayName>.<ItemType>``.
    Returns ``"Unknown"`` when the pattern cannot be matched.
    """
    for part in path.parts:
        if "." in part:
            candidate = part.rsplit(".", 1)[-1]
            # Valid item types are CamelCase and at least 3 chars long
            if len(candidate) >= 3 and candidate[0].isupper() and candidate.isalpha():
                return candidate
    return "Unknown"


def _glob_to_regex(pattern: str) -> re.Pattern:
    """Convert a glob pattern (supporting ``**``) to a compiled regex.

    The match is checked against the forward-slash-normalised relative path
    from the workspace root (e.g. ``2_Silver/transformation/nb.Notebook/notebook-content.py``).
    """
    pattern = pattern.replace("\\", "/").lstrip("/").lstrip("./")
    buf: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern[i : i + 2] == "**":
            buf.append(".*")
            i += 2
            # consume optional trailing slash
            if i < len(pattern) and pattern[i] == "/":
                i += 1
        elif pattern[i] == "*":
            buf.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            buf.append("[^/]")
            i += 1
        elif pattern[i] in r"\.^$+{}[]|()":
            buf.append(re.escape(pattern[i]))
            i += 1
        else:
            buf.append(pattern[i])
            i += 1
    return re.compile("".join(buf) + "$")


def _file_matches_path_filters(file_rel_from_workspace: Path, filter_patterns: list[str]) -> bool:
    """Return True if the file matches at least one of the glob filter patterns."""
    if not filter_patterns:
        return True
    norm = str(file_rel_from_workspace).replace("\\", "/")
    for pat in filter_patterns:
        try:
            if _glob_to_regex(pat).search(norm):
                return True
        except re.error:
            pass
    return False


# ---------------------------------------------------------------------------
# Coverage check
# ---------------------------------------------------------------------------


def is_covered(
    guid: str,
    context_line: str,
    file_rel_from_workspace: Path,
    item_type: str,
    rules: list[FindReplaceRule],
) -> bool:
    """Return True if at least one rule covers this GUID occurrence."""
    for rule in rules:
        # item_type filter
        if rule.item_types and item_type not in rule.item_types:
            continue
        # file_path filter
        if rule.file_paths and not _file_matches_path_filters(file_rel_from_workspace, rule.file_paths):
            continue

        if rule.is_regex:
            if rule._compiled is None:
                continue
            m = rule._compiled.search(context_line)
            if m:
                try:
                    if m.group(1) == guid:
                        return True
                except IndexError:
                    # Pattern has no capture group — treat full match as hit
                    if guid in m.group(0):
                        return True
        else:
            if rule.find_value == guid:
                return True

    return False


# ---------------------------------------------------------------------------
# GUID extraction
# ---------------------------------------------------------------------------


def _extract_from_notebook(file_path: Path) -> list[tuple[str, str, str]]:
    """Yield (field_name, guid, context_line) tuples from a notebook-content.py file.

    Only inspects ``# META`` lines to avoid false-positives from cell code.
    Cell code that hardcodes lakehouse GUIDs is the developer's responsibility
    to parameterise via literal rules; those are flagged separately through the
    JSON extraction path when a dataset-settings file exists.
    """
    results: list[tuple[str, str, str]] = []
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return results

    for line in lines:
        if "# META" not in line:
            continue
        guids = GUID_RE.findall(line)
        if not guids:
            continue

        # Check for a named field: "field_name": "GUID"
        field_match = re.search(r'"([^"]+)":\s*"([0-9a-fA-F]{8}-[0-9a-fA-F-]{27})"', line)
        if field_match:
            field_name = field_match.group(1)
            guid = field_match.group(2)
            if field_name in NOTEBOOK_SENSITIVE_FIELDS:
                results.append((field_name, guid, line.strip()))
            continue

        # known_lakehouses: may contain multiple GUIDs inline
        if NOTEBOOK_KNOWN_LAKEHOUSES_KEY in line:
            for guid in guids:
                results.append((NOTEBOOK_KNOWN_LAKEHOUSES_KEY, guid, line.strip()))

    return results


def _extract_from_json(file_path: Path) -> list[tuple[str, str, str]]:
    """Yield (field_name, guid, context_line) tuples from a JSON item content file.

    Parses line-by-line (not DOM) so it works even with large / nested files and
    avoids pulling in a JSON parser just to walk keys.
    """
    results: list[tuple[str, str, str]] = []
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return results

    for line in lines:
        for sensitive_field in JSON_SENSITIVE_FIELDS:
            if f'"{sensitive_field}"' not in line:
                continue
            guids = GUID_RE.findall(line)
            for guid in guids:
                results.append((sensitive_field, guid, line.strip()))

    return results


# ---------------------------------------------------------------------------
# Workspace scanner
# ---------------------------------------------------------------------------


def scan_workspace(workspace_folder: str, workspaces_dir: Path, repo_root: Path) -> list[UnmappedGuid]:
    """Scan all item files in one workspace folder and return unmapped GUIDs."""
    workspace_dir = workspaces_dir / workspace_folder
    rules = load_rules(workspace_dir / "parameter.yml")

    logger.debug(f"  Loaded {len(rules)} find_replace rule(s) from parameter.yml " f"(incl. templates)")

    unmapped: list[UnmappedGuid] = []

    for file_path in workspace_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.name in SKIP_FILENAMES:
            continue
        if any(file_path.name.endswith(s) for s in SKIP_SUFFIXES):
            continue

        item_type = item_type_from_path(file_path)
        if item_type == "Unknown":
            continue

        # Determine which extractor to use
        if file_path.name == "notebook-content.py":
            guid_entries = _extract_from_notebook(file_path)
        elif file_path.suffix == ".json":
            guid_entries = _extract_from_json(file_path)
        else:
            continue

        if not guid_entries:
            continue

        # Path relative to workspace root for filter matching
        try:
            file_rel_ws = file_path.relative_to(workspace_dir)
        except ValueError:
            file_rel_ws = file_path

        # Path relative to repo root for reporting
        try:
            file_rel_repo = file_path.relative_to(repo_root)
        except ValueError:
            file_rel_repo = file_path

        for field_name, guid, context in guid_entries:
            if not is_covered(guid, context, file_rel_ws, item_type, rules):
                unmapped.append(
                    UnmappedGuid(
                        workspace_folder=workspace_folder,
                        relative_file=str(file_rel_repo).replace("\\", "/"),
                        item_type=item_type,
                        field_name=field_name,
                        guid=guid,
                        context=context[:120],  # truncate for readability
                    )
                )

    return unmapped


# ---------------------------------------------------------------------------
# Workspace discovery
# ---------------------------------------------------------------------------


def discover_workspaces(workspaces_dir: Path) -> list[str]:
    """Return workspace folder names that contain a config.yml."""
    folders = []
    for child in sorted(workspaces_dir.iterdir()):
        if child.is_dir() and (child / CONFIG_FILE).exists():
            folders.append(child.name)
    return folders


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _github_error(file: str, title: str, message: str) -> None:
    """Emit a GitHub Actions error annotation if running in CI."""
    logger.info("::error file=%s,title=%s::%s", file, title, message)


def report_results(all_unmapped: list[UnmappedGuid], is_github_actions: bool) -> None:
    """Print a human-readable (and optionally annotated) report."""
    if not all_unmapped:
        logger.info("✓ No unmapped IDs found. All GUIDs are covered by parameter rules.")
        return

    logger.info(f"\nFound {len(all_unmapped)} unmapped GUID(s):\n")

    by_file: dict[str, list[UnmappedGuid]] = {}
    for u in all_unmapped:
        by_file.setdefault(u.relative_file, []).append(u)

    for rel_file, items in sorted(by_file.items()):
        logger.info(f"  {rel_file}")
        for u in items:
            msg = f'GUID {u.guid} in field "{u.field_name}" has no matching ' f"find_replace rule in parameter.yml"
            logger.info(f"    ✗ {msg}")
            logger.info(f"      context: {u.context}")
            if is_github_actions:
                _github_error(
                    file=u.relative_file,
                    title="Unmapped GUID",
                    message=msg,
                )
        logger.info("")

    logger.info(SEPARATOR_SHORT)
    logger.info("These GUIDs will be deployed verbatim (as Dev IDs) to Test/Production.")
    logger.info("Add a find_replace rule to the workspace parameter.yml (or a template) for each GUID above.")
    logger.info("See workspaces/<workspace>/parameter_templates/ for examples.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run the unmapped-ID scan.

    Returns EXIT_SUCCESS (0) when all GUIDs are covered, EXIT_FAILURE (1) otherwise.
    """
    parser = argparse.ArgumentParser(
        description=("Scan workspace item files for GUIDs that have no matching " "find_replace rule in parameter.yml.")
    )
    parser.add_argument(
        "--workspaces_directory",
        required=True,
        help="Path to the workspaces directory (e.g. 'workspaces')",
    )
    parser.add_argument(
        "--workspace_filter",
        default=None,
        help="Only scan this workspace folder name (optional)",
    )
    args = parser.parse_args(argv)

    workspaces_dir = Path(args.workspaces_directory).resolve()
    if not workspaces_dir.is_dir():
        logger.error(f"ERROR: workspaces directory not found: {workspaces_dir}")
        return EXIT_FAILURE

    repo_root = workspaces_dir.parent

    import os

    is_github_actions = os.environ.get("GITHUB_ACTIONS", "").lower() == "true"

    logger.info(SEPARATOR_LONG)
    logger.info("Fabric CI/CD — Unmapped ID Scanner")
    logger.info(SEPARATOR_LONG)

    # Discover workspaces
    all_workspaces = discover_workspaces(workspaces_dir)
    if args.workspace_filter:
        all_workspaces = [w for w in all_workspaces if w == args.workspace_filter]
        if not all_workspaces:
            logger.error(f"ERROR: No workspace named '{args.workspace_filter}' found in {workspaces_dir}")
            return EXIT_FAILURE

    if not all_workspaces:
        logger.warning("No workspaces with config.yml found — nothing to scan.")
        return EXIT_SUCCESS

    logger.info(f"Scanning {len(all_workspaces)} workspace(s)...\n")

    all_unmapped: list[UnmappedGuid] = []
    for workspace_folder in all_workspaces:
        logger.info(f"{SEPARATOR_SHORT}")
        logger.info(f"Workspace: {workspace_folder}")
        unmapped = scan_workspace(workspace_folder, workspaces_dir, repo_root)
        if unmapped:
            logger.info(f"  ✗ {len(unmapped)} unmapped GUID(s) detected")
        else:
            logger.info("  ✓ All GUIDs are covered")
        all_unmapped.extend(unmapped)

    logger.info(f"\n{SEPARATOR_LONG}")
    report_results(all_unmapped, is_github_actions)

    return EXIT_FAILURE if all_unmapped else EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
