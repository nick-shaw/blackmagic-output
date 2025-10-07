"""
Setup script for Blackmagic DeckLink Python Output Library
"""

from pybind11.setup_helpers import Pybind11Extension, build_ext
import pybind11
from setuptools import setup, find_packages
import platform
import os

# Determine platform-specific settings
system = platform.system()
is_windows = system == "Windows"
is_macos = system == "Darwin"
is_linux = system == "Linux"

# DeckLink SDK paths - platform-specific SDK files included in repo
if is_windows:
    local_sdk_path_rel = os.path.join("decklink_sdk", "Win", "include")
    local_sdk_path_abs = os.path.join(os.path.dirname(__file__), local_sdk_path_rel)
    decklink_include = [
        local_sdk_path_abs,
        "C:/Program Files/Blackmagic Design/DeckLink SDK/Win/include",
        "C:/Program Files (x86)/Blackmagic Design/DeckLink SDK/Win/include"
    ]
    decklink_libs = []
    extra_compile_args = ["/std:c++17"]
    extra_link_args = []

elif is_macos:
    local_sdk_path_rel = os.path.join("decklink_sdk", "Mac", "include")
    local_sdk_path_abs = os.path.join(os.path.dirname(__file__), local_sdk_path_rel)
    decklink_include = [
        local_sdk_path_abs,
        "/Applications/Blackmagic DeckLink SDK/Mac/include",
        "/usr/local/include/decklink"
    ]
    decklink_libs = []
    extra_compile_args = ["-std=c++17", "-framework", "CoreFoundation"]
    extra_link_args = ["-framework", "CoreFoundation"]

elif is_linux:
    local_sdk_path_rel = os.path.join("decklink_sdk", "Linux", "include")
    local_sdk_path_abs = os.path.join(os.path.dirname(__file__), local_sdk_path_rel)
    decklink_include = [
        local_sdk_path_abs,
        "/usr/include/decklink",
        "/usr/local/include/decklink"
    ]
    decklink_libs = ["dl", "pthread"]
    extra_compile_args = ["-std=c++17"]
    extra_link_args = ["-ldl", "-lpthread"]

else:
    raise RuntimeError(f"Unsupported platform: {system}")

# Filter existing include paths (use absolute paths for checking)
existing_include_dirs = []
for inc_dir in decklink_include:
    if os.path.exists(inc_dir):
        existing_include_dirs.append(inc_dir)
        print(f"Found DeckLink SDK at: {inc_dir}")

if not existing_include_dirs:
    print("WARNING: DeckLink SDK include directories not found.")
    print("Please ensure the decklink_sdk directory exists with platform-specific SDK headers")
    print(f"Searched paths: {decklink_include}")
else:
    print(f"Using DeckLink SDK from: {existing_include_dirs[0]}")

# Define the extension module
ext_modules = [
    Pybind11Extension(
        "decklink_output",
        sources=[
            "python_bindings.cpp",
            "decklink_wrapper_mac.cpp" if is_macos else "decklink_wrapper.cpp",
            "decklink_hdr_frame.cpp",
            os.path.join(local_sdk_path_rel, "DeckLinkAPIDispatch.cpp"),
        ],
        include_dirs=[
            pybind11.get_include(),
        ] + existing_include_dirs,
        libraries=decklink_libs,
        language="c++",
        cxx_std=17,
    ),
]

# Compiler arguments
for ext in ext_modules:
    ext.extra_compile_args.extend(extra_compile_args)
    ext.extra_link_args.extend(extra_link_args)

setup(
    # Use pyproject.toml for metadata, but keep setup.py for build configuration
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    zip_safe=False,
)
