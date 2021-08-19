# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="Py-OWNPT",
    version="1.0.0",
    description="Python utilities for OpenWordnet-PT (OWN-PT)",
    long_description=open('README.md').read(),
    # author="",
    # author_email="",
    # url="",
    license=open('LICENSE').read(),
    packages=[
        "pyownpt",
        "pyownpt.cli"],
    install_requires=open("requirements").readlines()
)

