#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import io
import re
import sys
from glob import glob
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext
import pathlib


from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    with io.open(
        join(dirname(__file__), *names), encoding=kwargs.get("encoding", "utf8")
    ) as fh:
        return fh.read()


PROJECT_ROOT = pathlib.Path(__file__).parent

try:
    with open(PROJECT_ROOT / "requirements.in") as f:
        INSTALL_REQUIRES = [line for line in f.read().splitlines() if line[0].isalpha()]
except FileNotFoundError:
    print(sys.exc_info())
    INSTALL_REQUIRES = []


NAME = "voca"

setup(
    name=NAME,
    version="0.1.3",
    license="GNU General Public License v3 (GPLv3)",
    description="Control your computer by voice!",
    long_description="%s\n%s"
    % (
        re.compile("^.. start-badges.*^.. end-badges", re.M | re.S).sub(
            "", read("README.rst")
        ),
        re.sub(":[a-z]+:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst")),
    ),
    long_description_content_type="text/x-rst",
    author="Full Name",
    author_email="email@example.com",
    url="https://github.com/githubuser/python-voca",
    packages=list(find_packages("src")),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        "Topic :: Utilities",
    ],
    keywords=[
        # eg: 'keyword1', 'keyword2', 'keyword3',
    ],
    python_requires=">=3.6",
    install_requires=INSTALL_REQUIRES
    # eg: 'aspectlib==1.1.1', 'six>=1.7',
    ,
    extras_require={
        # eg:
        #   'rst': ['docutils>=0.11'],
        #   ':python_version=="2.6"': ['argparse'],
    },
    entry_points={
        "console_scripts": ["voca = voca.cli:cli"],
        "voca_plugins": [
            "basic = voca.plugins:basic",
            "math = voca.plugins:math",
            "python = voca.plugins:python",
            "yes = voca.plugins:yes",
            "no = voca.plugins:no",
            "turtle_context = voca.plugins:turtle_context",
            "vscode = voca.plugins:vscode",
        ],
    },
)
