#!/usr/bin/env python3
"""
Version Consistency Checker

Checks that version numbers are consistent across all project files.
Run this before committing version changes to ensure nothing is missed.
"""

import re
import sys
from pathlib import Path

VERSION_FILE_PATTERNS = {
    "pyproject.toml": (
        r'version\s*=\s*"([^"]+)"',
        "pyproject.toml version"
    ),
    "CMakeLists.txt": (
        r'project\([^)]+VERSION\s+(\d+\.\d+\.\d+)',
        "CMakeLists.txt version (base only, no beta suffix)"
    ),
    "src/blackmagic_io/__init__.py": (
        r'__version__\s*=\s*"([^"]+)"',
        "__init__.py version"
    ),
    "src/python_bindings.cpp": (
        r'm\.attr\("__version__"\)\s*=\s*"([^"]+)"',
        "python_bindings.cpp version"
    ),
}

CHANGELOG_PATTERN = r'##\s+\[([^\]]+)\]\s+-\s+\d{4}-\d{2}-\d{2}'


def extract_version(file_path, pattern):
    """Extract version string from a file using regex pattern."""
    try:
        content = Path(file_path).read_text()
        match = re.search(pattern, content)
        if match:
            return match.group(1)
        return None
    except FileNotFoundError:
        return None


def extract_base_version(version_string):
    """Extract base version (X.Y.Z) from version string, removing beta suffixes."""
    match = re.match(r'(\d+\.\d+\.\d+)', version_string)
    return match.group(1) if match else version_string


def check_versions():
    """Check version consistency across all files."""
    project_root = Path(__file__).parent
    versions = {}
    errors = []

    print("Checking version consistency...\n")

    for file_path, (pattern, description) in VERSION_FILE_PATTERNS.items():
        full_path = project_root / file_path
        version = extract_version(full_path, pattern)

        if version:
            versions[file_path] = version
            print(f"✓ {description:50s} {version}")
        else:
            error_msg = f"✗ Could not find version in {file_path}"
            print(error_msg)
            errors.append(error_msg)

    changelog_path = project_root / "CHANGELOG.md"
    if changelog_path.exists():
        content = changelog_path.read_text()
        match = re.search(CHANGELOG_PATTERN, content)
        if match:
            changelog_version = match.group(1)
            versions["CHANGELOG.md"] = changelog_version
            print(f"✓ {'CHANGELOG.md latest version':50s} {changelog_version}")
        else:
            error_msg = "✗ Could not find latest version in CHANGELOG.md"
            print(error_msg)
            errors.append(error_msg)

    print("\n" + "=" * 70)

    if not versions:
        print("ERROR: No versions found!")
        return 1

    pyproject_version = versions.get("pyproject.toml")
    if not pyproject_version:
        print("ERROR: Could not find version in pyproject.toml (canonical source)")
        return 1

    base_version = extract_base_version(pyproject_version)
    cmake_version = versions.get("CMakeLists.txt")

    print(f"\nCanonical version (pyproject.toml): {pyproject_version}")
    print(f"Base version (X.Y.Z): {base_version}")

    inconsistencies = []

    for file_path, version in versions.items():
        if file_path == "CMakeLists.txt":
            if version != base_version:
                inconsistencies.append(
                    f"  ✗ {file_path}: {version} (expected base version: {base_version})"
                )
        elif file_path != "pyproject.toml":
            if version != pyproject_version:
                inconsistencies.append(
                    f"  ✗ {file_path}: {version} (expected: {pyproject_version})"
                )

    if inconsistencies:
        print("\nINCONSISTENCIES FOUND:")
        for inconsistency in inconsistencies:
            print(inconsistency)
        print("\nPlease update all version numbers to match pyproject.toml")
        return 1

    if errors:
        print("\nERRORS:")
        for error in errors:
            print(f"  {error}")
        return 1

    print("\n✓ All versions are consistent!")
    return 0


if __name__ == "__main__":
    sys.exit(check_versions())
