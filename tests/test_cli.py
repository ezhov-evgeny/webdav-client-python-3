import re
import runpy
import subprocess
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock

import pytest


WDC = Path(__file__).resolve().parents[1] / "wdc"


@pytest.mark.parametrize("option", ["--help", "-h", "--version", "-v"])
@pytest.mark.parametrize("completion_available", [False, True])
def test_cli_startup(option, completion_available, monkeypatch, capsys):
    completion = ModuleType("argcomplete")
    completion.autocomplete = Mock()
    monkeypatch.setitem(
        sys.modules, "argcomplete", completion if completion_available else None
    )
    monkeypatch.setattr(sys, "argv", [str(WDC), option])

    with pytest.raises(SystemExit) as result:
        runpy.run_path(str(WDC), run_name="__main__")

    assert result.value.code == 0
    output = capsys.readouterr()
    assert output.err == ""
    if option in ("--help", "-h"):
        assert "usage:" in output.out
        assert "wdc" in output.out
    else:
        assert re.fullmatch(r"wdc \d+\.\d+\.\d+\n", output.out)
    if completion_available:
        completion.autocomplete.assert_called_once()


@pytest.mark.parametrize("option", ["--help", "--version"])
def test_installed_cli(option):
    result = subprocess.run(
        ["wdc", option],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "wdc" in result.stdout


@pytest.fixture
def strtobool():
    return runpy.run_path(str(WDC))["strtobool"]


@pytest.mark.parametrize(
    "value,expected",
    [(value, 1) for value in ("y", "yes", "t", "true", "on", "1")]
    + [(value, 0) for value in ("n", "no", "f", "false", "off", "0")],
)
def test_strtobool(value, expected, strtobool):
    assert strtobool(value) == expected
    assert strtobool(value.upper()) == expected


@pytest.mark.parametrize("value", ["", "invalid", " yes "])
def test_strtobool_invalid(value, strtobool):
    with pytest.raises(ValueError):
        strtobool(value)
