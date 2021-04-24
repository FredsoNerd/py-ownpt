# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="Py-OWN-PT",
    version="0.0.0",
    description="Python utilities for OpenWordnet-PT (OWN-PT)",
    long_description=open('README.org').read(),
    # author="",
    # author_email="",
    # url="",
    license=open('LICENSE').read(),
    packages=["pyownpt"],
    install_requires=open("requirements").readlines()
)

