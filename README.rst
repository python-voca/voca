========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor|
        |
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/python-intervoice/badge/?style=flat
    :target: https://readthedocs.org/projects/python-intervoice
    :alt: Documentation Status


.. |travis| image:: https://travis-ci.org/githubuser/python-intervoice.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/githubuser/python-intervoice

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/githubuser/python-intervoice?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/githubuser/python-intervoice

.. |version| image:: https://img.shields.io/pypi/v/intervoice.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/intervoice

.. |commits-since| image:: https://img.shields.io/github/commits-since/githubuser/python-intervoice/v0.1.0.svg
    :alt: Commits since latest release
    :target: https://github.com/githubuser/python-intervoice/compare/v0.1.0...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/intervoice.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/intervoice

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/intervoice.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/intervoice

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/intervoice.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/intervoice


.. end-badges

An example package. Generated with cookiecutter-pylibrary.

* Free software: BSD 2-Clause License

Installation
============

::

    pip install intervoice


Documentation
=============

* Prerequisites:
  - kaldi/silvius server. Also available online.
  - Python 3



Development
===========

- git clone this repo and cd inside
- ./run-kaldi-server.sh
- pip install intervoice
- intervoice mic &
- intervoice manage


To run the all tests run::

    tox

Note, to combine the coverage data from all the tox environments run:

.. list-table::
    :widths: 10 90
    :stub-columns: 1

    - - Windows
      - ::

            set PYTEST_ADDOPTS=--cov-append
            tox

    - - Other
      - ::

            PYTEST_ADDOPTS=--cov-append tox
