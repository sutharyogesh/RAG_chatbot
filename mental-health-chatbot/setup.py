#!/usr/bin/env python3
"""
Setup script for Mental Health ChatBot
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mental-health-chatbot",
    version="1.0.0",
    author="Mental Health ChatBot Team",
    author_email="team@mentalhealthchatbot.com",
    description="AI-powered mental health support chatbot with assessment and recommendation features",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/mental-health-chatbot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Healthcare Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-cov>=4.1.0",
            "black>=23.11.0",
            "flake8>=6.1.0",
            "isort>=5.12.0",
        ],
        "prod": [
            "gunicorn>=21.2.0",
            "whitenoise>=6.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mental-health-chatbot=run:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.html", "*.css", "*.js", "*.json", "*.md"],
    },
    zip_safe=False,
)