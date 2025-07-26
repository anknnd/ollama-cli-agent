#!/usr/bin/env python3
"""
Setup script for Ollama CLI Agent
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="ollama-cli-agent",
    version="1.0.0",
    description="A powerful, extensible command-line interface for interacting with Ollama LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ollama CLI Team",
    author_email="support@ollama-cli.dev",
    url="https://github.com/your-org/ollama-cli",
    license="MIT",
    
    # Package discovery
    packages=find_packages(where="."),
    package_dir={"": "."},
    include_package_data=True,
    
    # Dependencies
    install_requires=requirements,
    python_requires=">=3.8",
    
    # Optional dependencies
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "testing": [
            "pytest>=7.0.0",
            "pytest-mock>=3.10.0",
            "pytest-asyncio>=0.21.0",
        ],
    },
    
    # Entry points
    entry_points={
        "console_scripts": [
            "ollama-cli=main:main",
            "ollama-agent=main:main",
        ],
    },
    
    # Package data
    package_data={
        "": [
            "*.md",
            "*.txt",
            "*.yml",
            "*.yaml",
            ".agentrc.example",
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
    ],
    
    # Keywords
    keywords=[
        "ollama",
        "llm",
        "cli",
        "agent",
        "chatbot",
        "ai",
        "assistant",
        "tools",
        "automation"
    ],
    
    # Project URLs
    project_urls={
        "Documentation": "https://github.com/your-org/ollama-cli/blob/main/README.md",
        "Source": "https://github.com/your-org/ollama-cli",
        "Tracker": "https://github.com/your-org/ollama-cli/issues",
        "Changelog": "https://github.com/your-org/ollama-cli/blob/main/docs/",
    },
    
    # Zip safety
    zip_safe=False,
)
