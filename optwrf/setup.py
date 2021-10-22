"""
Build and install the project.
"""
from setuptools import setup, find_packages


NAME = "optwrf"
FULLNAME = "optwrf"
AUTHOR = "Jeffrey Sward"
AUTHOR_EMAIL = "jas983@cornell.edu"
MAINTAINER = "Jeffrey Sward"
MAINTAINER_EMAIL = AUTHOR_EMAIL
LICENSE = "BSD License"
URL = "https://github.com/jeffreysward/met4ene"
DESCRIPTION = "Set up and run the WRF model from scratch"
KEYWORDS = "WRF"
# with open("README.rst") as f:
#     LONG_DESCRIPTION = "".join(f.readlines())

CLASSIFIERS = [
    "Development Status :: 2 - Pre-Alpha",
    "Intended Audience :: Science/Research",
    "Topic :: Scientific/Engineering",
    "Programming Language :: Python :: 3 :: Only",
]
PLATFORMS = "Any"
PACKAGES = find_packages()
# PACKAGES = find_packages(exclude=["old", "log_and_err"])
SCRIPTS = []
PACKAGE_DATA = {
    "optwrf": ["data/*.yml"],
}
INSTALL_REQUIRES = [
    "numpy",
    "scipy",
    "pandas",
    "xarray",
    "pyyaml",
    "requests",
]
PYTHON_REQUIRES = ">=3.6"

if __name__ == "__main__":
    setup(
        name=NAME,
        fullname=FULLNAME,
        description=DESCRIPTION,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        license=LICENSE,
        url=URL,
        platforms=PLATFORMS,
        scripts=SCRIPTS,
        packages=PACKAGES,
        include_package_data=True,
        package_data=PACKAGE_DATA,
        classifiers=CLASSIFIERS,
        keywords=KEYWORDS,
        install_requires=INSTALL_REQUIRES,
        python_requires=PYTHON_REQUIRES,
    )
