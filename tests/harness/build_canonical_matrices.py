"""Shim — delegates to caid.matrices. Config: matrix_config.toml."""

from pathlib import Path
import sys

# Workspace-sibling caid-agent — preferred so changes to the engine flow
# without re-publishing a package.
_SIBLING_CAID_SRC = Path(__file__).resolve().parents[3] / "caid-agent" / "src"
if _SIBLING_CAID_SRC.exists() and str(_SIBLING_CAID_SRC) not in sys.path:
    sys.path.insert(0, str(_SIBLING_CAID_SRC))

from caid.matrices import build_canonical_matrices, load_config

ROOT = Path(__file__).resolve().parents[2]
if __name__ == "__main__":
    build_canonical_matrices(
        ROOT, load_config(Path(__file__).parent / "matrix_config.toml")
    )
