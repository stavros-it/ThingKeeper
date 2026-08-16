"""Tests for the CLI entry point: python -m thingkeeper --report PATH."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run_cli(*args, env_extra=None):
    cmd = [sys.executable, "-m", "thingkeeper", *args]
    env = {
        "PYTHONPATH": str(Path(__file__).resolve().parent.parent),
        **dict(__import__("os").environ),
    }
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        cmd, capture_output=True, text=True, env=env, timeout=60,
    )


def test_cli_generates_pdf_report(db, tmp_path):
    out = tmp_path / "cli_report.pdf"
    result = _run_cli("--report", str(out),
                     env_extra={"THINGKEEPER_DATA": str(tmp_path)})
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert out.exists()
    assert out.read_bytes()[:5] == b"%PDF-"


def test_cli_no_args_prints_usage(db, tmp_path):
    """Running with no args would launch the GUI, which we can't do in CI.

    Instead, test that --help works and shows the --report option.
    """
    result = _run_cli("--help", env_extra={"THINGKEEPER_DATA": str(tmp_path)})
    assert result.returncode == 0
    assert "--report" in result.stdout


def test_cli_report_to_nonexistent_dir_fails(db, tmp_path):
    out = tmp_path / "nonexistent_subdir" / "report.pdf"
    result = _run_cli("--report", str(out),
                     env_extra={"THINGKEEPER_DATA": str(tmp_path)})
    assert result.returncode != 0
