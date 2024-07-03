from setuptools import setup, find_packages

ICUA2_VERSION = "0.0.2"
setup(
    name="matbii",
    version="0.0.2",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="A configurable implementation of the MATB-II: Multi-Attribute Task Battery.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/dicelab-rhul/icua2/tree/main/example/matbii",
    packages=find_packages(),
    install_requires=[f"icua2=={ICUA2_VERSION}"],
    extras_require={
        "tobii": [f"icua2[tobii]=={ICUA2_VERSION}"],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.10",
    ],
    package_data={
        "matbii.tasks": ["**/*.sch", "**/*.schema.json", "**/*.svg.jinja"],
    },
)
