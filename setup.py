# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="Py-OWN",
    version="1.0.0",
    description="Python utilities for OpenWordnets",
    long_description=open('README.md').read(),
    # author="",
    # author_email="",
    # url="",
    license=open('LICENSE').read(),
    packages=[
        "pyown",
        "pyown.cli"],
    install_requires=open("requirements").readlines()
)

