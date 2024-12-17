from pathlib import Path

from setuptools import find_packages
from setuptools import setup


def read(fname: str) -> str:
    file_path = Path(__file__).parent / fname
    return file_path.read_text(encoding="UTF-8")


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
    long_description_content_type="text/x-rst",
    packages=find_packages("src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    package_data={
        "pytest_regressions": ["py.typed"],
    },
    extras_require={
        "dev": [
            "matplotlib",
            "mypy",
            "numpy",
            "pandas",
            "pillow",
            "pyarrow",
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
    install_requires=["pytest-datadir>=1.2.0", "pytest>=6.2.0", "pyyaml"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Pytest",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation :: CPython",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
    ],
    entry_points={"pytest11": ["regressions = pytest_regressions.plugin"]},
)
