"""The FalabellaAPIClient 0.2.0 shim warns and re-exports falabella_sdk."""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHIM_SRC = ROOT / "legacy-shim" / "src"


def _run(code: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([str(SHIM_SRC), str(ROOT / "src")])
    return subprocess.run(
        [sys.executable, "-W", "default", "-c", code],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_import_emits_future_warning_pointing_to_new_name():
    result = _run("import FalabellaAPIClient")
    assert result.returncode == 0, result.stderr
    assert "FutureWarning" in result.stderr
    assert "pip install falabella-sdk" in result.stderr
    assert "falabella_sdk" in result.stderr


def test_reexports_the_new_client():
    result = _run(
        "import warnings; warnings.simplefilter('ignore');"
        "import FalabellaAPIClient, falabella_sdk;"
        "assert FalabellaAPIClient.FalabellaClient is falabella_sdk.FalabellaClient;"
        "assert set(FalabellaAPIClient.__all__) == set(falabella_sdk.__all__)"
    )
    assert result.returncode == 0, result.stderr
