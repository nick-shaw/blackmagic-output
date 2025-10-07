"""
Setup script for Blackmagic DeckLink Python Output Library
"""

from pybind11.setup_helpers import Pybind11Extension, build_ext
from pybind11 import get_cmake_dir
import pybind11
from setuptools import setup, Extension
import platform
import os

# Determine platform-specific settings
system = platform.system()
is_windows = system == "Windows"
is_macos = system == "Darwin"
is_linux = system == "Linux"

# DeckLink SDK paths - use local downloaded SDK files
local_sdk_path = os.path.join(os.path.dirname(__file__), "decklink_sdk", "include")

# Platform-specific SDK paths (fallback if local SDK not available)
if is_windows:
    decklink_include = [
        local_sdk_path,
        "C:/Program Files/Blackmagic Design/DeckLink SDK/Win/include",
        "C:/Program Files (x86)/Blackmagic Design/DeckLink SDK/Win/include"
    ]
    decklink_libs = []
    extra_compile_args = ["/std:c++17"]
    extra_link_args = []
    
elif is_macos:
    decklink_include = [
        local_sdk_path,
        "/Applications/Blackmagic DeckLink SDK/Mac/include",
        "/usr/local/include/decklink"
    ]
    decklink_libs = []
    extra_compile_args = ["-std=c++17", "-framework", "CoreFoundation"]
    extra_link_args = ["-framework", "CoreFoundation"]
    
elif is_linux:
    decklink_include = [
        local_sdk_path,
        "/usr/include/decklink",
        "/usr/local/include/decklink",
        "./decklink_sdk/Linux/include"
    ]
    decklink_libs = ["dl", "pthread"]
    extra_compile_args = ["-std=c++17"]
    extra_link_args = ["-ldl", "-lpthread"]

else:
    raise RuntimeError(f"Unsupported platform: {system}")

# Filter existing include paths
existing_include_dirs = []
for inc_dir in decklink_include:
    if os.path.exists(inc_dir):
        existing_include_dirs.append(inc_dir)
        print(f"Found DeckLink SDK at: {inc_dir}")

if not existing_include_dirs:
    print("WARNING: DeckLink SDK include directories not found.")
    print("Please ensure the decklink_sdk/include directory exists with SDK headers")
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
            "decklink_sdk/include/DeckLinkAPIDispatch.cpp",
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
    name="blackmagic-output",
    version="1.0.0",
    description="Python library for Blackmagic DeckLink video output",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/blackmagic-output",
    
    # Python modules
    py_modules=["blackmagic_output"],
    
    # C++ extensions
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
    
    # Requirements
    install_requires=[
        "numpy>=1.19.0",
        "pybind11>=2.6.0",
    ],
    
    # Optional dependencies for development/examples
    extras_require={
        "examples": ["opencv-python", "pillow"],
        "dev": ["pytest", "black", "mypy"],
    },
    
    # Python version requirement
    python_requires=">=3.7",
    
    # Package classification
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: C++",
    ],
    
    # Keywords for package discovery
    keywords="blackmagic decklink video output sdi hdmi",
    
    # Package data
    zip_safe=False,
)