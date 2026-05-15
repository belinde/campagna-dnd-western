#!/usr/bin/env python3
"""Entry point: genera la sorgente Jekyll player-safe (logica in public_site/)."""

from __future__ import annotations

from public_site.manifest import load_manifest, parse_args, resolve_output_directory
from public_site.pipeline import build_site


def main() -> None:
    args = parse_args()
    manifest = load_manifest(args.manifest)
    output_dir = resolve_output_directory(manifest, args.output)
    page_count, asset_count = build_site(manifest, output_dir)
    print(f"Sito pubblico generato in: {output_dir}")
    print(f"Pagine esportate: {page_count}")
    print(f"Asset copiati: {asset_count}")


if __name__ == "__main__":
    main()
