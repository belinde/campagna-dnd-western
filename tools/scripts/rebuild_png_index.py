#!/usr/bin/env python3
"""Rigenera png/INDICE.md dalle schede in png/*.md."""

from __future__ import annotations

import argparse
import sys

from png_catalog import scan_png_sheets, validate_entries, write_indice
from campagna_paths import repo_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rigenera png/INDICE.md dai metadati delle schede PNG."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Esce con codice 1 se una scheda manca di Regione, Ambito o Promemoria.",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Root del repository (default: auto).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = repo_root() if args.repo_root is None else __import__("pathlib").Path(args.repo_root)

    entries = scan_png_sheets(root)
    if args.check:
        problems = validate_entries(entries)
        if problems:
            for entry, missing in problems:
                rel = entry.path.relative_to(root)
                print(
                    f"ERRORE {rel}: mancano {', '.join(missing)}",
                    file=sys.stderr,
                )
            sys.exit(1)

    destination = write_indice(root)
    print(f"Indice PNG aggiornato: {destination}")
    print(f"Schede indicizzate: {len(entries)}")


if __name__ == "__main__":
    main()
