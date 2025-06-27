# Copyright (c) 2025, Williams.Wang. All rights reserved. Use restricted under LICENSE terms.

"""
Setup script for Voice Recording and Transcription Tool
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

# 读取requirements
requirements = []
requirements_file = this_directory / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() for line in f 
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="voice-transcription-tool",
    version="1.0.0",
    author="Williams.Wang",
    author_email="your-email@example.com",
    description="A macOS voice recording and transcription CLI tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/voice-transcription-tool",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Capture/Recording",
        "Topic :: Text Processing :: Markup",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "voice=src.cli.main:app",
        ],
    },
    include_package_data=True,
    zip_safe=False,
) 