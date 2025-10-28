from __future__ import annotations

from pathlib import Path
from typing import Any
import importlib
import sys

# Import the module object explicitly to avoid grabbing the Click command
make_test = importlib.import_module(
    "execution_testing.cli.eest.make.commands.test"
)


def test_ruff_called_with_project_config(
    monkeypatch: Any, tmp_path: Path
) -> None:
    called: dict[str, list[str]] = {}

    # Force a predictable Ruff invocation
    monkeypatch.setattr(
        make_test, "_ruff_cmd", lambda: [sys.executable, "-m", "ruff"]
    )

    # Capture the subprocess invocation
    def fake_run(cmd: list[str], check: bool = True) -> int:
        called["cmd"] = cmd
        return 0

    monkeypatch.setattr(make_test.subprocess, "run", fake_run)

    # Point to a dummy pyproject.toml
    dummy_cfg = tmp_path / "pyproject.toml"
    dummy_cfg.write_text("")

    monkeypatch.setattr(make_test, "_project_pyproject", lambda: dummy_cfg)

    target = tmp_path / "sample.py"
    target.write_text("x='1'\n")

    make_test._ruff_format_file(target)

    cmd = called["cmd"]
    assert cmd[:3] == [sys.executable, "-m", "ruff"]
    assert "format" in cmd
    idx = cmd.index("--config")
    assert cmd[idx + 1] == str(dummy_cfg)
    assert cmd[-1] == str(target)
