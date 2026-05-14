"""Percorsi canonici del repository Campagna (root = directory che contiene `ambientazione/`)."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Risale da questo file fino alla root del repo (presenza di `ambientazione/`)."""
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "ambientazione").is_dir():
            return parent
    msg = f"Directory ambientazione/ non trovata risalendo da {here}"
    raise RuntimeError(msg)
