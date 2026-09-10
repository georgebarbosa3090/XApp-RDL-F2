from setuptools import setup, find_packages

setup(
    name="xapp-rdl-f2",
    version="2.0.0",
    description="O-RAN Near-RT RIC Conflict Mitigation xApp — Phase 2: Context-Aware MARL (CA-RDL)",
    author="George Barbosa",
    author_email="georgebarbosa3090@gmail.com",
    packages=find_packages(include=["src", "src.*"]),
    python_requires=">=3.10",
    install_requires=[
        "pydantic>=2.0.0",
        "structlog>=23.1.0",
        "prometheus-client>=0.17.0",
        "pycrate>=0.5.0",
        "requests>=2.31.0",
        "numpy>=1.24.0",
        "scipy>=1.10.0",
        "torch>=2.0.0"
    ],
    entry_points={
        "console_scripts": [
            "xapp-rdl=src.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Networking",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Intended Audience :: Science/Research",
    ],
)
