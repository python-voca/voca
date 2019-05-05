========
Overview
========

.. start-badges

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests
      - | |travis| |appveyor| |codecov|
        |
    * - package
      - | |version| |wheel| |supported-versions| |supported-implementations|
        | |commits-since|

.. |docs| image:: https://readthedocs.org/projects/voca/badge/?style=flat
    :target: https://readthedocs.org/projects/voca
    :alt: Documentation Status


.. |travis| image:: https://travis-ci.com/python-voca/voca.svg?branch=master
    :alt: Travis-CI Build Status
    :target: https://travis-ci.com/python-voca/voca

.. |appveyor| image:: https://ci.appveyor.com/api/projects/status/github/python-voca/voca?branch=master&svg=true
    :alt: AppVeyor Build Status
    :target: https://ci.appveyor.com/project/python-voca/voca

.. |version| image:: https://img.shields.io/pypi/v/voca.svg
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/voca

.. |commits-since| image:: https://img.shields.io/github/commits-since/python-voca/voca/v0.1.5.svg
    :alt: Commits since latest release
    :target: https://github.com/python-voca/voca/compare/v0.1.5...master

.. |wheel| image:: https://img.shields.io/pypi/wheel/voca.svg
    :alt: PyPI Wheel
    :target: https://pypi.python.org/pypi/voca

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/voca.svg
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/voca

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/voca.svg
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/voca

.. |codecov| image:: https://img.shields.io/codecov/c/github/python-voca/voca.svg
      :alt: Code coverage
      :target: https://codecov.io/gh/python-voca/voca

.. end-badges

Control your computer by voice!

Features
========


- Define your own personal commands in your home directory (outside the Voca source tree).
- Different commands are available for each app, in addition to globally available commands.
- When editing a command file, your new commands are immediately available as soon as you save. No need to fiddle with reloading.
- If there's a fatal error in a command file, don't worry -- Voca simply uses a backup from the last time that file worked.
- Your commands are executed asynchronously, so you never need to wait for one to finish before executing the next.
- Get immediate visual feedback during an utterance -- Voca's *eager mode* can start acting on your commands as soon as the first word in your utterance. Switch to *strict mode* and Voca will wait until the end of your utterance.
- Voca uses a modern parser, so your grammar can be arbitrarily complex.
- Use any speech engine you like -- Voca takes its input as newline-separated json on stdin.
- Voca generates detailed structured logs you can use for debugging or analyzing your command history.
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
- The documentation is minimal.


Installation
============

::

    pip install voca


Usage
=====

- Start the server with Docker by running ``./run-kaldi-server.sh`` or use another, such as the online servers at http://voxhub.io/silvius. (Voca is not affiliated with Silvius, but is compatible.)
- Detect which audio device you're using as the microphone by running ``voca --mic`` with different ``--device`` numbers until one of them shows output.
- Send audio to the server and receive transcripts on stdout by running ``voca --listen -d 2``, replacing ``2`` with your microphone's device number from the previous step. Try saying something and check that you get json output. Cancel this process with ``control-c``.
- Check that the manager is working by sending it a transcript. The ``-i`` option says which command module you want to load.

  ::

    voca manage -i voca.plugins.basic   <<EOF
    {"status": 0, "segment": 0, "result": {"hypotheses": [{"transcript": "say bravo"}], "final": true}, "id": "eec37b79-f55e-4bf8-9afe-01f278902599"}
    EOF


  It should type the letter ``b`` on your screen. Cancel this process with ``control-c``.


- Start the listener and manager, piping the listener's transcripts into the manager.

  ::

     voca listen -d <device_number>  | voca manage -i voca.plugins.basic


  Speak into your microphone ``say charlie``. It should type the letter ``c`` on your screen. Cancel this process with ``control-c``.


- See the location of your config directory in ``voca --help``, and add new commands in any ``.py`` file at ``{config_dir}/user_modules/*.py``. Run ``voca manage -i user_modules.my_module`` (replacing ``my_module`` with the name of your file, excluding the ``.py`` suffix.)

- Try using the Caster commands.

  ::

   voca listen -d <device_number>  | VOCA_PATCH_CASTER=1 voca manage


For example, in Visual Studio Code, say ``new file``. It should open new file in the editor by automatically pressing ``control-n``.

- Structured logs are stored in ``{config_dir}/logs/``. Examine them with ``eliot-tree --color=always -l0 {filepath} | less -SR``. They'll show how your commands flowed through the program, and will display the full grammar that was active during each command.


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
