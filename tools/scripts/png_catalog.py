#!/usr/bin/env python3
"""Lettura metadati PNG, ordinamento per regione e generazione di png/INDICE.md."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from campagna_paths import repo_root

INDICE_FILENAME = "INDICE.md"
PNG_DIRNAME = "png"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
META_REGIONE_RE = re.compile(r"^\*\*Regione:\*\*\s*(.+)$", re.MULTILINE)
META_AMBITO_RE = re.compile(r"^\*\*Ambito:\*\*\s*(.+)$", re.MULTILINE)
META_PROMEMORIA_RE = re.compile(r"^\*\*Promemoria:\*\*\s*(.+)$", re.MULTILINE)
META_RUOLO_RE = re.compile(r"^\*\*Ruolo:\*\*\s*(.+)$", re.MULTILINE)
META_RAZZA_CLASSE_RE = re.compile(r"^\*\*Razza/Classe:\*\*\s*(.+)$", re.MULTILINE)
IMAGE_PATH_RE = re.compile(r"!\[[^\]]*\]\((/immagini/[^)\s]+)\)")

REGION_OTHER = "Altro"
INDICE_THUMB_WIDTH_PX = 80

# Ordine preferito (case-insensitive match sul valore in scheda).
PREFERRED_REGION_ORDER: tuple[str, ...] = (
    "La East Coast",
    "Gli Appalacchi",
    "Il Middle West",
    "Le Pianure del Sud",
    "La Frontiera",
    "Le Montagne Rocciose",
    "Le Terre Selvagge",
    "Itinerante",
    "Varie",
)

REQUIRED_META_FIELDS = ("regione", "ambito", "promemoria")


@dataclass(frozen=True)
class PngEntry:
    slug: str
    path: Path
    title: str
    regione: str
    ambito: str
    promemoria: str
    ruolo: str = ""
    portrait_path: str = ""


def meta_line_first(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def extract_title(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 1:
            title = heading.group(2).strip().strip("#").strip()
            title = re.sub(r"[*_`]+", "", title)
            return title or fallback
    return fallback


def extract_portrait_path(markdown_text: str) -> str:
    """Primo path assoluto /immagini/... in sintassi immagine Markdown."""
    match = IMAGE_PATH_RE.search(markdown_text)
    return match.group(1) if match else ""


def parse_png_sheet(path: Path) -> PngEntry:
    text = path.read_text(encoding="utf-8")
    slug = path.stem
    return PngEntry(
        slug=slug,
        path=path,
        title=extract_title(text, slug.replace("-", " ").title()),
        regione=meta_line_first(META_REGIONE_RE, text),
        ambito=meta_line_first(META_AMBITO_RE, text),
        promemoria=meta_line_first(META_PROMEMORIA_RE, text),
        ruolo=meta_line_first(META_RUOLO_RE, text),
        portrait_path=extract_portrait_path(text),
    )


def png_dir(root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    return base / PNG_DIRNAME


def scan_png_sheets(root: Path | None = None) -> list[PngEntry]:
    directory = png_dir(root)
    if not directory.is_dir():
        return []
    entries: list[PngEntry] = []
    for path in sorted(directory.glob("*.md"), key=lambda p: p.name.lower()):
        if path.name == INDICE_FILENAME:
            continue
        entries.append(parse_png_sheet(path))
    return entries


def _normalized_region_key(region: str) -> str:
    return region.strip().casefold()


def _preferred_region_index(region: str) -> int | None:
    key = _normalized_region_key(region)
    for index, preferred in enumerate(PREFERRED_REGION_ORDER):
        if key == preferred.casefold():
            return index
    return None


def region_bucket(region: str) -> str:
    cleaned = region.strip()
    if not cleaned:
        return REGION_OTHER
    if _preferred_region_index(cleaned) is not None:
        return cleaned
    return REGION_OTHER


def region_sort_key(region: str) -> tuple[int, str]:
    cleaned = region.strip()
    if not cleaned:
        return (len(PREFERRED_REGION_ORDER) + 1, "")
    preferred_index = _preferred_region_index(cleaned)
    if preferred_index is not None:
        return (preferred_index, cleaned.casefold())
    return (len(PREFERRED_REGION_ORDER), cleaned.casefold())


def portrait_path_for_indice(portrait_path: str) -> str:
    """Path relativo da png/INDICE.md: /immagini/... -> ../immagini/..."""
    cleaned = portrait_path.strip()
    if cleaned.startswith("/"):
        return f"../{cleaned.lstrip('/')}"
    if cleaned.startswith("immagini/"):
        return f"../{cleaned}"
    return cleaned


def format_indice_list_item(entry: PngEntry) -> str:
    prom = entry.promemoria.strip() or "—"
    title = entry.title
    slug_link = f"[{title}]({entry.slug}.md)"
    if entry.portrait_path:
        src = portrait_path_for_indice(entry.portrait_path)
        alt = title.replace('"', "'")
        thumb = (
            f'<a href="{entry.slug}.md">'
            f'<img src="{src}" width="{INDICE_THUMB_WIDTH_PX}" alt="{alt}"></a>'
        )
        return f"- {thumb} {slug_link} — {prom}"
    return f"- {slug_link} — {prom}"


def known_region_values(entries: list[PngEntry]) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for entry in entries:
        reg = entry.regione.strip()
        if not reg or reg in seen:
            continue
        seen.add(reg)
        values.append(reg)
    values.sort(key=lambda r: region_sort_key(r))
    return values


def group_entries_by_region(entries: list[PngEntry]) -> list[tuple[str, list[PngEntry]]]:
    buckets: dict[str, list[PngEntry]] = {}
    for entry in entries:
        bucket = region_bucket(entry.regione)
        buckets.setdefault(bucket, []).append(entry)

    def entry_sort_key(e: PngEntry) -> tuple[str, str]:
        return (e.title.casefold(), e.slug)

    grouped: list[tuple[str, list[PngEntry]]] = []
    for region in sorted(buckets.keys(), key=region_sort_key):
        grouped.append((region, sorted(buckets[region], key=entry_sort_key)))
    return grouped


def render_indice_md(entries: list[PngEntry]) -> str:
    lines = [
        "# Indice PNG",
        "",
        "> Generato automaticamente da `tools/scripts/rebuild_png_index.py`. "
        "Non modificare manualmente le voci sottostanti: aggiornare **Regione**, "
        "**Ambito** e **Promemoria** nelle schede in `png/` (e `## Immagine` per la "
        "miniatura), poi rigenerare l'indice.",
        "",
    ]
    if not entries:
        lines.append("_Nessuna scheda PNG ancora presente._")
        lines.append("")
        return "\n".join(lines)

    known = known_region_values(entries)
    if known:
        lines.append("## Regioni in uso")
        lines.append("")
        for reg in known:
            lines.append(f"- {reg}")
        lines.append("")

    for region, group in group_entries_by_region(entries):
        lines.append(f"## {region}")
        lines.append("")
        for entry in group:
            lines.append(format_indice_list_item(entry))
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def missing_required_fields(entry: PngEntry) -> list[str]:
    missing: list[str] = []
    if not entry.regione.strip():
        missing.append("Regione")
    if not entry.ambito.strip():
        missing.append("Ambito")
    if not entry.promemoria.strip():
        missing.append("Promemoria")
    return missing


def validate_entries(entries: list[PngEntry]) -> list[tuple[PngEntry, list[str]]]:
    problems: list[tuple[PngEntry, list[str]]] = []
    for entry in entries:
        missing = missing_required_fields(entry)
        if missing:
            problems.append((entry, missing))
    return problems


def write_indice(root: Path | None = None) -> Path:
    base = root if root is not None else repo_root()
    entries = scan_png_sheets(base)
    destination = png_dir(base) / INDICE_FILENAME
    destination.write_text(render_indice_md(entries), encoding="utf-8")
    return destination
