#!/usr/bin/env python
import codecs
import os

from setuptools import find_packages
from setuptools import setup


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
    python_requires=">=3.6",
    extras_require={
        "dev": [
            "matplotlib",
            "numpy",
            "pandas",
            "pillow",
            "pre-commit",
            "restructuredtext-lint",
            "tox",
        ],
        "num": [
            "numpy",
            "pandas",
        ],
        "image": ["pillow", "numpy"],
        "dataframe": ["numpy", "pandas"],
    },
    install_requires=["pytest-datadir>=1.2.0", "pytest>=3.5.0", "pyyaml"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["regressions = pytest_regressions.plugin"]},
)
