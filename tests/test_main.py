"""Smoke tests del CLI minimo."""

from __future__ import annotations

import pytest

from bolsa_sim.__main__ import cli


def test_version() -> None:
    assert cli(["--version"]) == 0


def test_demo() -> None:
    assert cli(["--demo"]) == 0


def test_argumento_invalido() -> None:
    with pytest.raises(SystemExit):
        cli(["--nope"])
