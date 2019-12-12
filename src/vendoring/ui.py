"""Maintains state and output of the user interface.
"""

import traceback
from contextlib import contextmanager
from itertools import cycle
from textwrap import indent

import click as _click  # because click has useful utilities

from vendoring.errors import VendoringError


class _UserInterface:
    _spinner_frames = [
        "◴",
        "◷",
        "◶",
        "◵",
    ]

    def __init__(self):
        self.verbose = False

        # Internal state
        self._indentation = 0
        self._current_task = None
        self._logged_messages = []

        self._spinner = None

    def _log(self, text, nl=True, erase=False):
        if erase:
            assert nl is False
            text += "\b" * len(text)
        _click.echo(text, nl=nl)

    def warn(self, message):
        self.log(_click.style(f"WARN: {message}", fg="yellow"))

    def log(self, message):
        if self._indentation:
            message = indent(message, "  " * self._indentation)

        if self._current_task is not None and not self.verbose:
            if self._spinner is None:
                self._spinner = cycle(self._spinner_frames)
            self._logged_messages.append(message)
            self._log(next(self._spinner), nl=False, erase=True)
            return

        self._log(message)

    @contextmanager
    def indent(self):
        self._indentation += 1
        try:
            yield
        finally:
            self._indentation -= 1

    @contextmanager
    def task(self, task):
        if self._current_task is not None:
            raise Exception("Only 1 task at a time.")

        self._log(f"{task}... ", nl=self.verbose)

        self._current_task = task
        try:
            with self.indent():
                yield
        except VendoringError as e:
            self._current_task = None
            self._task_failed(e)
            raise
        else:
            self._current_task = None
            self._task_success()
        finally:
            self._logged_messages = []
            self._spinner = None

    def _task_failed(self, error):
        if self.verbose:
            # There's nothing that was "hidden", so no action needed.
            return

        self._log(" ")  # clear the spinner
        # We were in "silent" mode, print the "hidden" messages.
        with self.indent():
            for message in self._logged_messages:
                self._log(message)

    def _task_success(self):
        message = _click.style("Done!", fg="green")
        if self.verbose:
            with self.indent():
                self.log(message)
        else:
            self._log(message)

    def show_error(self, e):
        if self.verbose:
            parts = traceback.format_exception(e.__class__, e, e.__traceback__)
            message = "".join(parts)
        else:
            message = str(e)

        with self.indent():
            self.log(_click.style(message, fg="red"))


UI = _UserInterface()