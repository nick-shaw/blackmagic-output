#!/usr/bin/env python3
"""
Local Build Test Script

Simulates what GitHub Actions will do to build and test the package.
Run this before pushing to verify the build works locally.
"""

import subprocess
import sys
import shutil
from pathlib import Path


def run_command(cmd, description, check=True):
    """Run a shell command and report results."""
    print(f"\n{'=' * 70}")
    print(f"▶ {description}")
    print(f"  Command: {cmd}")
    print('=' * 70)

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:
        print(f"\n✗ FAILED with exit code {result.returncode}")
        if result.stderr:
            print("Error output:")
            print(result.stderr)
        if check:
            return False
    else:
        print(f"✓ SUCCESS")

    return True


def main():
    """Run local build tests."""
    print("=" * 70)
    print("LOCAL BUILD TEST")
    print("=" * 70)
    print("\nThis script simulates the GitHub Actions workflow locally.")
    print("It will test version consistency and build the package.\n")

    project_root = Path(__file__).parent
    dist_dir = project_root / "dist"

    # Step 1: Version check
    if not run_command(
        "python check_version.py",
        "Step 1/5: Check version consistency"
    ):
        print("\n✗ Build test failed at version check")
        return 1

    # Step 2: Clean previous builds
    print(f"\n{'=' * 70}")
    print("▶ Step 2/5: Clean previous build artifacts")
    print('=' * 70)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
        print("✓ Cleaned dist/ directory")
    else:
        print("✓ No previous build artifacts to clean")

    # Step 3: Install build dependencies
    if not run_command(
        f"{sys.executable} -m pip install --upgrade build",
        "Step 3/5: Install build dependencies"
    ):
        print("\n✗ Build test failed at dependency installation")
        return 1

    # Step 4: Build package
    if not run_command(
        f"{sys.executable} -m build",
        "Step 4/5: Build package (wheel + sdist)"
    ):
        print("\n✗ Build test failed at package build")
        return 1

    # Step 5: Test installation and import
    print(f"\n{'=' * 70}")
    print("▶ Step 5/5: Test package installation and import")
    print('=' * 70)

    # Find the wheel file
    wheel_files = list(dist_dir.glob("*.whl"))
    if not wheel_files:
        print("✗ No wheel file found in dist/")
        return 1

    wheel_file = wheel_files[0]
    print(f"Found wheel: {wheel_file.name}")

    # Install the wheel
    if not run_command(
        f"{sys.executable} -m pip install '{wheel_file}' --force-reinstall",
        "Installing wheel"
    ):
        print("\n✗ Build test failed at wheel installation")
        return 1

    # Test import
    if not run_command(
        f"{sys.executable} -c \"import blackmagic_io; print(f'Successfully imported blackmagic_io version {{blackmagic_io.__version__}}')\"",
        "Testing import"
    ):
        print("\n✗ Build test failed at import test")
        return 1

    # Success summary
    print(f"\n{'=' * 70}")
    print("✓ ALL TESTS PASSED!")
    print('=' * 70)
    print("\nBuild artifacts created:")
    for item in sorted(dist_dir.iterdir()):
        print(f"  - {item.name}")

    print("\nYour package is ready for GitHub Actions to build!")
    print("The workflows should work correctly when you push.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
