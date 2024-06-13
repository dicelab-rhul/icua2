from setuptools import setup, find_packages

setup(
    name="icua2",
    version="0.0.1",
    author="Benedict Wilkins",
    author_email="benrjw@gmail.com",
    description="Integrated Cognitive User Assistance v2 - a platform supporting research in human attention guidance.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/dicelab-rhul/icua2",
    packages=find_packages(),
    install_requires=[
        "star_ray[xml,pygame]",
        "pyfuncschedule",
        "aiostream",
    ],
    extras_require={
        "tobii": ["tobii_research"],
    },
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.10",
    ],
)
