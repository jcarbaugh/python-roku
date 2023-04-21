from setuptools import setup, find_packages
import os

f = open(os.path.join(os.path.dirname(__file__), "README.rst"))
readme = f.read()
f.close()

setup(
    name="roku",
    version="5.0",
    description="Client for the Roku media player",
    long_description=readme,
    author="Jeremy Carbaugh",
    author_email="jeremy@jcarbaugh.com",
    url="https://github.com/jcarbaugh/python-roku",
    packages=find_packages(),
    install_requires=[
        "requests<3",
    ],
    license="BSD License",
    platforms=["any"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
