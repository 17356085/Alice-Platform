"""Run command implementations.

The legacy one-file ``commands/run.py`` module was moved to
``commands/legacy_run.py`` so this package can expose the resource commands
(``create``, ``list`` and ``show``) without an import collision.
"""

from aitest.cli.commands.legacy_run import run_command

__all__ = ["run_command"]
