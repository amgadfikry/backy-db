# setup.py
from setuptools import setup, find_packages

setup(
    name="backydb",
    version="0.1.0",
    description="Modular backup and restore system for databases with encryption support",
    packages=find_packages(),
    install_requires=[
        "mysql-connector-python==9.4.0",
        "cryptography==45.0.5",
        "python-dotenv==1.1.1",
        "pydantic==2.11.7",
    ],
    extras_require={
        "dev": [
            "pytest==8.4.1",
            "pytest-cov==6.2.1",
            "pytest-mock==3.14.1",
            "coverage==7.10.1",
            "black",
            "isort",
            "mypy",
        ],
        "test": [
            "pytest==8.4.1",
            "pytest-cov==6.2.1",
            "pytest-mock==3.14.1",
            "coverage==7.10.1",
        ],
    },
    python_requires=">=3.8",
    include_package_data=True,
    zip_safe=False,
)
