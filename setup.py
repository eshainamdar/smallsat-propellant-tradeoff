from setuptools import setup, find_packages

setup(
    name="propellant_tradeoff",
    version="0.1.0",
    description=(
        "Open, hardware-validated thermochemical performance modeling for "
        "comparing candidate propulsion technologies for small-satellite "
        "upper-stage / kick-stage applications."
    ),
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "rocketcea>=1.2.3",
        "numpy",
        "scipy",
        "matplotlib",
    ],
    python_requires=">=3.9",
)
