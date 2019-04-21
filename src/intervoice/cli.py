"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mintervoice` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``intervoice.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``intervoice.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import sys
import types

import click


from intervoice import app
from intervoice import listen
from intervoice import manager
from intervoice import worker


@click.group()
@click.option("--log/--no-log", "should_log", is_flag=True, default=True)
@click.pass_context
def cli(ctx, **kwargs):
    ctx.obj = kwargs.copy()
    app.main(**kwargs)


@cli.command("mic")
def _detect_mic(**kwargs):
    del sys.argv[1]
    import intervoice.mic


@cli.command("listen")
@click.option("--server", "-s", default="127.0.0.1")
@click.option("--port", "-p", default=8019, type=int)
@click.option("--device", "-d", default=7, type=int)
@click.option("--hypotheses", type=bool, default=True)
@click.option("--save-adaptation-state", type=bool)
@click.option("--send-adaptation-state", type=bool)
@click.option("--audio-gate", default=0, type=int)
def _listen(**kwargs):
    content_type = "audio/x-raw, layout=(string)interleaved, rate=(int)16000, format=(string)S16LE, channels=(int)1"
    path = "client/ws/speech"

    listen.run(
        args=types.SimpleNamespace(**kwargs), path=path, content_type=content_type
    )


@cli.command("manage")
@click.option("--import-path", "-i", "module_names", multiple=True, default=None)
@click.option("--num-workers", type=int, default=5)
@click.pass_obj
def _manage(obj, **kwargs):
    manager.main(**obj, **kwargs)


@cli.command("worker")
@click.option("import_paths", "-i", multiple=True)
@click.pass_obj
def _worker(obj, **kwargs):
    worker.main(**kwargs)
