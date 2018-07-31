#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import codecs
from setuptools import setup, find_packages


def read(fname):
    file_path = os.path.join(os.path.dirname(__file__), fname)
    return codecs.open(file_path, encoding="utf-8").read()


setup(
    name="pytest-regressions",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    author="ESSS",
    author_email="foss@esss.co",
    maintainer="Bruno Oliveira",
    maintainer_email="bruno@esss.co",
    license="MIT",
    url="https://github.com/ESSS/pytest-regressions",
    description="Easy to use fixtures to write regression tests.",
    long_description=read("README.rst"),
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*",
    extras_require={
        "dev": [
            "matplotlib",
            "numpy",
            "pandas",
            "pillow",
            "pre-commit",
            "restructuredtext-lint",
            "tox",
        ]
    },
    install_requires=[
        "pathlib2;python_version<'3.0'",
        "pytest-datadir>=1.2.0",
        "pytest>=3.5.0",
        "pyyaml",
        "six",
    ],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["regressions = pytest_regressions.plugin"]},
)
