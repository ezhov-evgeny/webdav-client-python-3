#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Setup script; project metadata is in pyproject.toml."""
import sys

from setuptools import setup
from setuptools.command.install import install as InstallCommand
from setuptools.command.test import test as TestCommand


class Install(InstallCommand):
    def run(self):
        InstallCommand.run(self)


class Test(TestCommand):
    user_options = [("pytest-args=", "a", "")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    scripts=["wdc"],
    cmdclass={"install": Install, "test": Test},
)
