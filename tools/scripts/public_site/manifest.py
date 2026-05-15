from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

from public_site.constants import DEFAULT_MANIFEST, REPO_ROOT
from public_site.models import PageEntry


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Genera una sorgente Jekyll player-safe dal repository privato."
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Percorso del manifest JSON di pubblicazione.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Directory di output. Se omessa, usa outputDirectory dal manifest.",
    )
    return parser.parse_args()


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Manifest non trovato: {path}")
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def natural_sort_key(value: str) -> list[object]:
    parts = re.split(r"(\d+)", value)
    key: list[object] = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.lower())
    return key


def sort_paths(paths: Iterable[Path], order: str) -> list[Path]:
    sorted_paths = sorted(paths, key=lambda item: natural_sort_key(item.as_posix()))
    if order == "desc":
        sorted_paths.reverse()
    return sorted_paths


def resolve_output_directory(manifest: dict, requested_output: Path | None) -> Path:
    if requested_output is not None:
        return (REPO_ROOT / requested_output).resolve()
    manifest_output = manifest.get("outputDirectory", "tools/build/public-site")
    return (REPO_ROOT / manifest_output).resolve()


def route_for(relative_path: Path) -> str:
    path_without_suffix = relative_path.with_suffix("").as_posix()
    return f"/{path_without_suffix}/"


def resolve_pages(manifest: dict) -> list[PageEntry]:
    entries: list[PageEntry] = []
    seen: set[Path] = set()

    for page_config in manifest.get("pages", []):
        relative_path = Path(page_config["path"])
        source_path = REPO_ROOT / relative_path
        if not source_path.exists():
            raise FileNotFoundError(f"Pagina pubblica non trovata: {relative_path}")
        entries.append(
            PageEntry(
                source_path=source_path,
                relative_path=relative_path,
                route=route_for(relative_path),
                title="",
                label=page_config.get("label", "Pagina pubblica"),
                kind="page",
                profile=page_config.get("profile"),
                aliases=tuple(page_config.get("aliases", [])),
                featured=bool(page_config.get("featured", False)),
            )
        )
        seen.add(relative_path)

    for page_config in manifest.get("allowlist", {}).get("entries", []):
        relative_path = Path(page_config["path"])
        source_path = REPO_ROOT / relative_path
        if not source_path.exists():
            raise FileNotFoundError(f"Materiale allowlist non trovato: {relative_path}")
        if relative_path in seen:
            continue
        entries.append(
            PageEntry(
                source_path=source_path,
                relative_path=relative_path,
                route=route_for(relative_path),
                title="",
                label=page_config.get("label", "Materiali conosciuti"),
                kind="allowlist",
                profile=page_config.get("profile"),
                aliases=tuple(page_config.get("aliases", [])),
                featured=False,
            )
        )
        seen.add(relative_path)

    for collection in manifest.get("collections", []):
        source_dir = REPO_ROOT / collection["source"]
        if not source_dir.exists():
            raise FileNotFoundError(f"Collection non trovata: {collection['source']}")
        include_pattern = collection.get("include", "*.md")
        for source_path in sort_paths(source_dir.glob(include_pattern), collection.get("sort", "asc")):
            relative_path = source_path.relative_to(REPO_ROOT)
            if relative_path in seen:
                continue
            entries.append(
                PageEntry(
                    source_path=source_path,
                    relative_path=relative_path,
                    route=route_for(relative_path),
                    title="",
                    label=collection["name"],
                    kind="collection",
                    profile=collection.get("profile"),
                    aliases=tuple(collection.get("aliases", [])),
                    featured=False,
                )
            )
            seen.add(relative_path)

    return entries


def public_sidebar_section(entry: PageEntry) -> str | None:
    """Ritorna la chiave sezione sidebar o None per il bucket Home."""
    parts = entry.relative_path.parts
    if entry.kind == "collection":
        if parts and parts[0] == "personaggi":
            return "personaggi"
        if parts and parts[0] == "resoconti":
            return "resoconti"
        return None
    if entry.kind == "allowlist":
        if parts and parts[0] == "png":
            return "png"
        if len(parts) >= 3 and parts[0] == "ambientazione" and parts[1] == "luoghi":
            return "luoghi"
        return None
    return None


def sort_pages_for_section(section: str, pages: list[PageEntry]) -> list[PageEntry]:
    if section == "personaggi":
        return sorted(pages, key=lambda p: natural_sort_key(p.relative_path.as_posix()))
    if section == "resoconti":
        return sorted(pages, key=lambda p: natural_sort_key(p.relative_path.as_posix()), reverse=True)
    return sorted(pages, key=lambda p: (p.title.lower(), p.relative_path.as_posix()))


def liquid_rel_jekyll(path: str) -> str:
    return "{{ '" + path + "' | relative_url }}"


def session_number_from_path(relative_path: Path) -> int | None:
    if relative_path.parts[0] != "resoconti":
        return None
    match = re.match(r"sessione-(\d+)", relative_path.stem, re.IGNORECASE)
    return int(match.group(1)) if match else None
