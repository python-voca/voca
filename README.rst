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

.. |docs| image:: https://readthedocs.org/projects/python-voca/badge/?style=flat
    :target: https://readthedocs.org/projects/python-voca
    :alt: Documentation Status


.. |travis| image:: https://travis-ci.org/githubuser/python-voca.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/githubuser/python-voca

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/githubuser/python-voca?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/githubuser/python-voca

.. |version| image:: https://img.shields.io/pypi/v/voca.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/voca

.. |commits-since| image:: https://img.shields.io/github/commits-since/githubuser/python-voca/v0.1.4.svg
    :alt: Commits since latest release
    :target: https://github.com/githubuser/python-voca/compare/v0.1.4...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/voca.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/voca

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/voca.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/voca

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/voca.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/voca


.. end-badges

Control your computer by voice!

Features
========


- Write your own commands using a simple syntax, or use the existing ones.
- Different commands are available for each app.
- When editing a command file, your new commands are immediately available as soon as you save. No need to fiddle with reloading.
- If there's a fatal error in a command file, don't worry -- Voca simply uses a backup from the last time that file worked.
- Your commands are executed asynchronously, so you never need to wait for one to finish before executing the next.
- Voca uses a modern parser, so your grammar can be arbitrarily complex.
- Use any speech engine you like -- Voca takes its input as newline-separated json on stdin.
- Voca provides adapters for current Caster and Dragonfly commands, so you can keep using commands you like -- just install Voca alongside Caster. More plugins and adapters for other systems can be added.
- Voca has a pluggable architecture. Install independent plugins for controlling your apps, without needing to fork the main repository.
- Voca uses Python 3.7+, so all the newest Python features are available.
- Voca is continuously tested in CI, and maintains test coverage checks.
- Free and open source, licensed GPLv3.

Limitations
===========


- Nobody has used it at all, so I don't know if it's useful.
- Voca does not provide a speech engine; it requires input from an existing one like Dragon, Kaldi, or DeepSpeech.
- Multiple platforms are planned, and the basic outline is there, but tests are not currently passing on OSX or Windows. Linux is working.


Installation
============

::

    pip install voca


Documentation
=============

Prerequisites:

- A speech engine, e.g. kaldi/silvius server via included docker script or on its website
- Microphone
- Python 3



Development
===========

- git clone this repo and cd inside
- To start the kaldi server and workers in docker, plus a client listening to your mic, run ``./run-kaldi-server.sh``
- ``./pycli init`` will create a virtualenv and install the package into it
- ``./venv/bin/voca manage`` to start the manager process which accepts commands on stdin. The manager will start its workers.


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
