# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="",
    version="",
    # description="",
    long_description=open('README.org').read(),
    # author="",
    # author_email="",
    # url="",
    license=open('LICENSE').read(),
    packages=["py-ownpt"],
    install_requires=open("requrements").readlines()
)

