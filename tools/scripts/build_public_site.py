#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False


from campagna_paths import repo_root
from png_catalog import (
    META_AMBITO_RE,
    META_PROMEMORIA_RE,
    META_REGIONE_RE,
    region_bucket,
    region_sort_key,
    write_indice,
)

REPO_ROOT = repo_root()
TOOLS_PUBL = REPO_ROOT / "tools" / "pubblicazione"
DEFAULT_MANIFEST = TOOLS_PUBL / "manifest.json"
HOME_HERO_ASSET = "immagini/varie/gruppo-pg-carovana.jpg"
HOME_HERO_PUBLIC_PATH = "/immagini/varie/gruppo-pg-carovana.jpg"
PUBBLICAZIONE_ASSETS_DIR = TOOLS_PUBL / "assets"
PROMPT_PAGE_BODY_PATH = TOOLS_PUBL / "prompt-page-body.html"
HEADER_LOGO_PUBLIC_PATH = "/assets/header.png"
PROMPT_DATA_PUBLIC_PATH = "/assets/prompt-data.json"
PROMPT_SCRIPT_PUBLIC_PATH = "/assets/prompt-page.js"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((/immagini/[^)\s]+)\)")
OG_IMAGE_IN_PUBLIC_MD_RE = re.compile(
    r"!\[[^\]]*\]\(\{\{\s*'(/[^']+)'\s*\|\s*relative_url\s*\}\}\)"
)
SESSION_LINK_RE = re.compile(r"\[(Sessione (\d{3}))\](?!\()")
ENTITY_BULLET_RE = re.compile(r"^(\s*-\s+\*\*)([^*]+)(\*\*.*)$")

SESSION_H1_RE = re.compile(r"^#\s+Sessione\s+(\d+)\s*[—–-]\s*(.+)$", re.MULTILINE)
META_RAZZA_RE = re.compile(r"^\*\*Razza:\*\*\s*(.+)$", re.MULTILINE)
META_CLASSE_RE = re.compile(r"^\*\*Classe:\*\*\s*(.+)$", re.MULTILINE)
META_RUOLO_RE = re.compile(r"^\*\*Ruolo:\*\*\s*(.+)$", re.MULTILINE)
META_REGIONE_RE = re.compile(r"^\*\*Regione:\*\*\s*(.+)$", re.MULTILINE)
META_TIPO_RE = re.compile(r"^\*\*Tipo:\*\*\s*(.+)$", re.MULTILINE)

THUMB_MAX_EDGE = 320
THUMB_PORTRAIT_W = 280
THUMB_PORTRAIT_H = 373
THUMB_JPEG_QUALITY = 82
EXCERPT_MAX_LEN = 440

VISUAL_REF_HEADINGS: tuple[tuple[str, str], ...] = (
    ("imagePrompt", "Image prompt:"),
    ("constraints", "Constraints to preserve:"),
    ("avoids", "Details to avoid:"),
)
VISUAL_REF_FENCE_RE = re.compile(r"```text\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class PageEntry:
    source_path: Path
    relative_path: Path
    route: str
    title: str
    label: str
    kind: str
    profile: str | None = None
    aliases: tuple[str, ...] = ()
    featured: bool = False


@dataclass(frozen=True)
class PreparedPage:
    entry: PageEntry
    title: str
    body: str


@dataclass
class HubCardInfo:
    """Metadati per le card delle pagine indice (export pubblico)."""

    subtitle: str = ""
    session_num: int | None = None
    episode_title: str = ""
    excerpt: str = ""
    regione: str = ""
    ambito: str = ""
    promemoria: str = ""


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


def route_for(relative_path: Path) -> str:
    path_without_suffix = relative_path.with_suffix("").as_posix()
    return f"/{path_without_suffix}/"


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


def thumb_file_exists(output_dir: Path, og_image: str | None) -> bool:
    if not og_image or not HAS_PILLOW:
        return False
    try:
        rel = og_image.lstrip("/")
        thumb_rel = thumb_relative_path_jpeg(rel)
        return (output_dir / thumb_rel).is_file()
    except ValueError:
        return False


def session_badge_number(page: PageEntry, meta: HubCardInfo) -> int | None:
    if meta.session_num is not None:
        return meta.session_num
    m = re.match(r"sessione-(\d+)", page.relative_path.stem, re.IGNORECASE)
    return int(m.group(1)) if m else None


def png_card_search_blob(page: PageEntry, meta: HubCardInfo) -> str:
    parts = (page.title, meta.subtitle, meta.promemoria, meta.ambito, meta.regione)
    return " ".join(p for p in parts if p).casefold()


def render_png_public_header_html(regione: str, ambito: str, promemoria: str) -> str:
    if not any((regione.strip(), ambito.strip(), promemoria.strip())):
        return ""
    meta_bits = [html.escape(b) for b in (regione.strip(), ambito.strip()) if b.strip()]
    meta_line = ""
    if meta_bits:
        meta_line = f'<p class="png-public-meta">{" · ".join(meta_bits)}</p>'
    prom_html = ""
    if promemoria.strip():
        prom_html = f'<p class="png-promemoria">{html.escape(promemoria.strip())}</p>'
    return f'<div class="png-public-header">{meta_line}{prom_html}</div>\n\n'


def render_entity_card_html(
    page: PageEntry,
    meta: HubCardInfo,
    og_image: str | None,
    output_dir: Path,
    *,
    portrait_thumb: bool = False,
    png_hub: bool = False,
) -> str:
    href = liquid_rel_jekyll(page.route)
    title_esc = html.escape(page.title)
    meta_esc = html.escape(meta.subtitle) if meta.subtitle else ""
    if thumb_file_exists(output_dir, og_image):
        thumb_route = og_path_to_thumb_route(og_image or "")
        img_src = liquid_rel_jekyll(thumb_route)
        media = f'<img class="card-thumb" src="{img_src}" alt="" loading="lazy">'
    else:
        media = '<div class="card-thumb-placeholder" aria-hidden="true"></div>'
    meta_html = f'<p class="card-meta">{meta_esc}</p>' if meta_esc else ""
    excerpt_html = ""
    if png_hub and meta.promemoria.strip():
        excerpt_html = f'<p class="card-excerpt">{html.escape(meta.promemoria.strip())}</p>'
    data_attrs = ""
    if png_hub:
        reg = html.escape(region_bucket(meta.regione) if meta.regione.strip() else "Altro")
        ambito_attr = html.escape(meta.ambito.strip())
        search_attr = html.escape(png_card_search_blob(page, meta))
        data_attrs = (
            f' data-regione="{reg}" data-ambito="{ambito_attr}" data-search="{search_attr}"'
        )
    media_class = "entity-card-media entity-card-media--portrait" if portrait_thumb else "entity-card-media"
    card_class = "entity-card entity-card--portrait" if portrait_thumb else "entity-card"
    return textwrap.dedent(
        f"""\
        <article class="{card_class}"{data_attrs}>
          <a class="entity-card-link" href="{href}">
            <div class="{media_class}">{media}</div>
            <div class="entity-card-body">
              <h2 class="card-title">{title_esc}</h2>
              {meta_html}
              {excerpt_html}
            </div>
          </a>
        </article>
        """
    ).strip()


def render_session_card_html(page: PageEntry, meta: HubCardInfo, og_image: str | None, output_dir: Path) -> str:
    href = liquid_rel_jekyll(page.route)
    num = session_badge_number(page, meta)
    if num is not None:
        badge_inner = html.escape(f"Sessione {num}")
    else:
        badge_inner = html.escape(page.title)
    episode = meta.episode_title or page.title
    title_esc = html.escape(episode)
    excerpt_esc = html.escape(meta.excerpt) if meta.excerpt else ""
    if thumb_file_exists(output_dir, og_image):
        thumb_route = og_path_to_thumb_route(og_image or "")
        img_src = liquid_rel_jekyll(thumb_route)
        media = f'<img class="card-thumb" src="{img_src}" alt="" loading="lazy">'
    else:
        media = '<div class="card-thumb-placeholder" aria-hidden="true"></div>'
    excerpt_html = f'<p class="card-excerpt">{excerpt_esc}</p>' if excerpt_esc else ""
    badge_html = f'<span class="session-card-badge">{badge_inner}</span>'
    return textwrap.dedent(
        f"""\
        <article class="session-card">
          <a class="session-card-link" href="{href}">
            <div class="session-card-top">{badge_html}</div>
            <div class="session-card-media">{media}</div>
            <div class="session-card-body">
              <h2 class="card-title">{title_esc}</h2>
              {excerpt_html}
            </div>
          </a>
        </article>
        """
    ).strip()


def render_png_hub_index(
    *,
    hub_title: str,
    hub_route: str,
    source_path: Path,
    built_pages: list[PageEntry],
    hub_cards: dict[Path, HubCardInfo],
    page_og_images: dict[Path, str | None],
    output_dir: Path,
) -> str:
    in_section = [p for p in built_pages if public_sidebar_section(p) == "png"]
    ordered = sort_pages_for_section("png", in_section)
    by_region: dict[str, list[PageEntry]] = {}
    for page in ordered:
        meta = hub_cards.get(page.relative_path, HubCardInfo())
        reg = region_bucket(meta.regione) if meta.regione.strip() else "Altro"
        by_region.setdefault(reg, []).append(page)
    regions = sorted(by_region.keys(), key=region_sort_key)
    region_options = "".join(
        f'<option value="{html.escape(region)}">{html.escape(region)}</option>'
        for region in regions
    )
    lines = [
        front_matter(
            title=hub_title,
            route=hub_route,
            collection_label="",
            source_path=source_path,
            png_hub=True,
        ),
        '<div class="png-hub" data-png-hub>',
        '<div class="png-hub-toolbar">',
        '<label class="png-hub-search-label" for="png-hub-search">Cerca</label>',
        '<input type="search" id="png-hub-search" class="png-hub-search" '
        'placeholder="Nome, promemoria, ambito…" autocomplete="off">',
        '<label class="png-hub-region-label" for="png-hub-region">Regione</label>',
        '<select id="png-hub-region" class="png-hub-region">',
        '<option value="__all__">Tutte</option>',
        region_options,
        "</select>",
        "</div>",
        '<p class="png-hub-empty" hidden>Nessun personaggio corrisponde ai filtri.</p>',
    ]
    for region in regions:
        region_esc = html.escape(region)
        lines.append(f'<section class="png-region-block" data-regione="{region_esc}">')
        lines.append(f'<h2 class="png-region-title">{region_esc}</h2>')
        lines.append('<div class="card-grid">')
        for page in by_region[region]:
            meta = hub_cards.get(page.relative_path, HubCardInfo())
            og = page_og_images.get(page.relative_path)
            lines.append(
                render_entity_card_html(page, meta, og, output_dir, png_hub=True)
            )
        lines.extend(["</div>", "</section>"])
    lines.extend(["</div>", ""])
    return "\n".join(lines)


def render_section_hub_index(
    *,
    hub_title: str,
    hub_route: str,
    source_path: Path,
    section_key: str,
    built_pages: list[PageEntry],
    hub_cards: dict[Path, HubCardInfo],
    page_og_images: dict[Path, str | None],
    output_dir: Path,
) -> str:
    if section_key == "png":
        return render_png_hub_index(
            hub_title=hub_title,
            hub_route=hub_route,
            source_path=source_path,
            built_pages=built_pages,
            hub_cards=hub_cards,
            page_og_images=page_og_images,
            output_dir=output_dir,
        )
    in_section = [p for p in built_pages if public_sidebar_section(p) == section_key]
    ordered = sort_pages_for_section(section_key, in_section)
    grid_class = "card-grid card-grid--personaggi" if section_key == "personaggi" else "card-grid"
    lines = [
        front_matter(
            title=hub_title,
            route=hub_route,
            collection_label="",
            source_path=source_path,
        ),
        f'<div class="{grid_class}">',
    ]
    for page in ordered:
        meta = hub_cards.get(page.relative_path, HubCardInfo())
        og = page_og_images.get(page.relative_path)
        if section_key == "resoconti":
            lines.append(render_session_card_html(page, meta, og, output_dir))
        elif section_key == "personaggi":
            lines.append(render_entity_card_html(page, meta, og, output_dir, portrait_thumb=True))
        else:
            lines.append(render_entity_card_html(page, meta, og, output_dir))
    lines.extend(["</div>", ""])
    return "\n".join(lines)


def write_section_hub_pages(
    output_dir: Path,
    built_pages: list[PageEntry],
    hub_cards: dict[Path, HubCardInfo],
    page_og_images: dict[Path, str | None],
) -> int:
    hubs: list[tuple[str, str, str, Path, str]] = [
        ("Personaggi", "/personaggi/", output_dir / "personaggi" / "index.md", Path("tools/pubblicazione/_generated/index-personaggi.md"), "personaggi"),
        ("Resoconti", "/resoconti/", output_dir / "resoconti" / "index.md", Path("tools/pubblicazione/_generated/index-resoconti.md"), "resoconti"),
        ("PNG", "/png/", output_dir / "png" / "index.md", Path("tools/pubblicazione/_generated/index-png.md"), "png"),
        ("Luoghi", "/luoghi/", output_dir / "luoghi" / "index.md", Path("tools/pubblicazione/_generated/index-luoghi.md"), "luoghi"),
    ]
    for hub_title, hub_route, dest, source_stub, section_key in hubs:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(
            render_section_hub_index(
                hub_title=hub_title,
                hub_route=hub_route,
                source_path=source_stub,
                section_key=section_key,
                built_pages=built_pages,
                hub_cards=hub_cards,
                page_og_images=page_og_images,
                output_dir=output_dir,
            ),
            encoding="utf-8",
        )
    return len(hubs)


def sanitize_heading_text(value: str) -> str:
    cleaned = value.strip().strip("#").strip()
    cleaned = re.sub(r"[*_`]+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def strip_sensitive_sections(markdown_text: str, blocked_headings: set[str]) -> str:
    output_lines: list[str] = []
    skip_level: int | None = None

    for line in markdown_text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = sanitize_heading_text(heading.group(2))

            if skip_level is not None and level <= skip_level:
                skip_level = None

            if skip_level is None and title in blocked_headings:
                skip_level = level
                continue

        if skip_level is None:
            output_lines.append(line)

    compacted_lines: list[str] = []
    previous_blank = False
    for line in output_lines:
        is_blank = line.strip() == ""
        if is_blank and previous_blank:
            continue
        compacted_lines.append(line)
        previous_blank = is_blank

    return "\n".join(compacted_lines).strip() + "\n"


def extract_title(markdown_text: str, fallback: str) -> tuple[str, str]:
    lines = markdown_text.splitlines()
    for index, line in enumerate(lines):
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 1:
            title = sanitize_heading_text(heading.group(2))
            remaining = lines[:index] + lines[index + 1 :]
            while remaining and remaining[0].strip() == "":
                remaining.pop(0)
            body = "\n".join(remaining).strip() + "\n"
            return title or fallback, body
    return fallback, markdown_text.strip() + "\n"


def demote_remaining_h1(markdown_text: str) -> str:
    adjusted_lines: list[str] = []
    for line in markdown_text.splitlines():
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 1:
            adjusted_lines.append(f"## {heading.group(2)}")
            continue
        adjusted_lines.append(line)
    return "\n".join(adjusted_lines).strip() + "\n"


def split_h2_sections(markdown_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_title: str | None = None
    current_lines: list[str] = []

    for line in markdown_text.splitlines():
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 2:
            if current_title is not None:
                sections[current_title] = "\n".join(current_lines).strip()
            current_title = sanitize_heading_text(heading.group(2))
            current_lines = []
            continue

        if current_title is not None:
            current_lines.append(line)

    if current_title is not None:
        sections[current_title] = "\n".join(current_lines).strip()

    return sections


def parse_visual_ref_block(block: str) -> dict[str, str]:
    text = block.strip()
    result = {key: "" for key, _ in VISUAL_REF_HEADINGS}
    positions: list[tuple[int, str, str]] = []
    for key, heading in VISUAL_REF_HEADINGS:
        idx = text.find(heading)
        if idx >= 0:
            positions.append((idx, key, heading))
    positions.sort(key=lambda item: item[0])
    for index, (idx, key, heading) in enumerate(positions):
        start = idx + len(heading)
        end = positions[index + 1][0] if index + 1 < len(positions) else len(text)
        result[key] = text[start:end].strip()
    if not any(result.values()):
        return {"imagePrompt": text, "constraints": "_None._", "avoids": "_None._"}
    return result


def extract_visual_reference(markdown_text: str) -> dict[str, str] | None:
    sections = split_h2_sections(markdown_text)
    body = sections.get("Riferimento visivo", "")
    if not body.strip():
        return None
    match = VISUAL_REF_FENCE_RE.search(body)
    if not match:
        return None
    parsed = parse_visual_ref_block(match.group(1))
    if not parsed.get("imagePrompt", "").strip():
        return None
    return parsed


def first_image_path_from_markdown(markdown_text: str) -> str | None:
    match = IMAGE_RE.search(markdown_text)
    return match.group(2) if match else None


def thumb_path_for_catalog(og_path: str | None, output_dir: Path) -> str | None:
    if not og_path or not thumb_file_exists(output_dir, og_path):
        return None
    return og_path_to_thumb_route(og_path)


def prompt_search_blob(
    *,
    label: str,
    subtitle: str,
    description: str,
    promemoria: str = "",
    ambito: str = "",
    regione_raw: str = "",
) -> str:
    parts = (label, subtitle, description, promemoria, ambito, regione_raw)
    return " ".join(p for p in parts if p).casefold()


def prompt_subtitle_for_entry(relative_path: Path, raw_text: str) -> str:
    parts = relative_path.parts
    if parts[0] == "personaggi":
        razza = meta_line_first(META_RAZZA_RE, raw_text)
        classe = meta_line_first(META_CLASSE_RE, raw_text)
        bits = [b for b in (razza, classe) if b]
        return " · ".join(bits)
    if parts[0] == "png":
        return meta_line_first(META_RUOLO_RE, raw_text)
    if len(parts) >= 3 and parts[0] == "ambientazione" and parts[1] == "luoghi":
        reg = meta_line_first(META_REGIONE_RE, raw_text)
        tipo = meta_line_first(META_TIPO_RE, raw_text)
        bits = [b for b in (reg, tipo) if b]
        return " · ".join(bits)
    return ""


def collect_prompt_catalog(entries: list[PageEntry], output_dir: Path) -> dict[str, list[dict]]:
    luoghi: list[dict] = []
    personaggi: list[dict] = []
    png: list[dict] = []

    for entry in entries:
        rp = entry.relative_path
        parts = rp.parts
        bucket: list[dict] | None
        kind: str
        if parts[0] == "personaggi":
            bucket = personaggi
            kind = "pg"
        elif parts[0] == "png":
            bucket = png
            kind = "png"
        elif len(parts) >= 3 and parts[0] == "ambientazione" and parts[1] == "luoghi":
            bucket = luoghi
            kind = "luogo"
        else:
            continue

        raw_text = entry.source_path.read_text(encoding="utf-8")
        visual_ref = extract_visual_reference(raw_text)
        if visual_ref is None:
            continue

        fallback_title = sanitize_heading_text(rp.stem.replace("-", " "))
        title, _ = extract_title(raw_text, fallback_title)
        subtitle = prompt_subtitle_for_entry(rp, raw_text)
        regione_raw = ""
        promemoria = ""
        ambito = ""
        description = subtitle

        if kind == "png":
            regione_raw = meta_line_first(META_REGIONE_RE, raw_text)
            promemoria = meta_line_first(META_PROMEMORIA_RE, raw_text)
            ambito = meta_line_first(META_AMBITO_RE, raw_text)
            description = promemoria or subtitle
        elif kind == "luogo":
            regione_raw = meta_line_first(META_REGIONE_RE, raw_text)

        regione_bucket = region_bucket(regione_raw) if regione_raw.strip() else ""
        og_path = first_image_path_from_markdown(raw_text)
        item: dict = {
            "id": rp.stem,
            "label": title,
            "subtitle": subtitle,
            "description": description,
            "kind": kind,
            "visualRef": visual_ref,
            "search": prompt_search_blob(
                label=title,
                subtitle=subtitle,
                description=description,
                promemoria=promemoria,
                ambito=ambito,
                regione_raw=regione_raw,
            ),
        }
        thumb = thumb_path_for_catalog(og_path, output_dir)
        if thumb:
            item["thumbPath"] = thumb
        if regione_bucket:
            item["regione"] = regione_bucket
        bucket.append(item)

    label_key = lambda item: item["label"].lower()
    return {
        "luoghi": sorted(luoghi, key=label_key),
        "personaggi": sorted(
            personaggi, key=lambda item: natural_sort_key(item["label"])
        ),
        "png": sorted(png, key=label_key),
    }


def write_prompt_tool_assets(output_dir: Path, catalog: dict[str, list[dict]]) -> None:
    if not PROMPT_PAGE_BODY_PATH.is_file():
        raise FileNotFoundError(
            f"Manca {PROMPT_PAGE_BODY_PATH}: corpo HTML della pagina Generatore prompt."
        )

    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (assets_dir / "prompt-data.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    body_html = PROMPT_PAGE_BODY_PATH.read_text(encoding="utf-8").strip() + "\n"
    script_tag = (
        f'<script src="{liquid_rel_jekyll(PROMPT_SCRIPT_PUBLIC_PATH)}" defer></script>\n'
    )
    prompt_index = output_dir / "prompt" / "index.md"
    prompt_index.parent.mkdir(parents=True, exist_ok=True)
    prompt_index.write_text(
        front_matter(
            title="Generatore prompt per immagini",
            route="/prompt/",
            collection_label="",
            source_path=Path("tools/pubblicazione/prompt-page-body.html"),
        )
        + body_html
        + "\n"
        + script_tag,
        encoding="utf-8",
    )


def format_section(title: str, body: str) -> str:
    clean_body = body.strip()
    return f"## {title}\n\n{clean_body}\n"


def render_public_png_body(markdown_text: str) -> str:
    """Export player-safe PNG body: Immagine, Aspetto (as Descrizione), Eventi only."""
    sections = split_h2_sections(markdown_text)
    image_body = sections.get("Immagine", "_Nessuna immagine ancora associata._")
    description_body = sections.get("Aspetto", "_Descrizione non ancora pubblicata._")
    events_body = sections.get("Eventi interessanti", "_Nessun evento interessante ancora pubblicato._")

    rendered_sections = [
        format_section("Immagine", image_body),
        format_section("Descrizione", description_body),
        format_section("Eventi interessanti", events_body),
    ]
    return "\n".join(rendered_sections).strip() + "\n"


def transform_body_for_profile(markdown_text: str, profile: str | None) -> str:
    if profile == "public-png":
        return render_public_png_body(markdown_text)
    return markdown_text


def rewrite_session_links(markdown_text: str) -> str:
    def replacer(match: re.Match[str]) -> str:
        session_label, session_number = match.groups()
        return f"[{session_label}]({{{{ '/resoconti/sessione-{session_number}/' | relative_url }}}})"

    return SESSION_LINK_RE.sub(replacer, markdown_text)


def build_entity_route_lookup(pages: list[PreparedPage]) -> dict[str, str]:
    route_lookup: dict[str, str] = {}
    for page in pages:
        route_lookup[page.title] = page.entry.route
        for alias in page.entry.aliases:
            route_lookup[alias] = page.entry.route
    return route_lookup


def rewrite_section_entity_links(markdown_text: str, route_lookup: dict[str, str]) -> str:
    target_sections = {"Personaggi non giocanti incontrati", "Luoghi visitati"}
    rewritten_lines: list[str] = []
    current_section: str | None = None

    for line in markdown_text.splitlines():
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 2:
            current_section = sanitize_heading_text(heading.group(2))
            rewritten_lines.append(line)
            continue

        bullet_match = ENTITY_BULLET_RE.match(line)
        if current_section in target_sections and bullet_match:
            prefix, entity_name, suffix = bullet_match.groups()
            route = route_lookup.get(entity_name.strip())
            if route:
                rewritten_lines.append(f"{prefix}[{entity_name}]({{{{ '{route}' | relative_url }}}}){suffix}")
                continue

        rewritten_lines.append(line)

    return "\n".join(rewritten_lines).strip() + "\n"


def rewrite_image_links(markdown_text: str) -> tuple[str, set[str]]:
    images: set[str] = set()

    def replacer(match: re.Match[str]) -> str:
        alt_text, image_path = match.groups()
        normalized = image_path.lstrip("/")
        images.add(normalized)
        return f"![{alt_text}]({{{{ '/{normalized}' | relative_url }}}})"

    return IMAGE_RE.sub(replacer, markdown_text), images


def first_og_image_path_from_body(markdown_text: str) -> str | None:
    """Primo path immagine nel markdown dopo rewrite_image_links (URL path con / iniziale)."""
    match = OG_IMAGE_IN_PUBLIC_MD_RE.search(markdown_text)
    return match.group(1) if match else None


def meta_line_first(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


def is_personaggi_portrait_image(asset_relative_path: str) -> bool:
    parts = Path(asset_relative_path).parts
    return len(parts) >= 2 and parts[0] == "immagini" and parts[1] == "personaggi"


def thumb_resize_cover_portrait(im_rgb: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Ridimensiona e ritaglia in un riquadro verticale target_w x target_h (in alto: scarta il basso)."""
    w, h = im_rgb.size
    tr = target_w / target_h
    sr = w / h
    if sr > tr:
        new_h = target_h
        new_w = max(1, int(round(w * target_h / h)))
        resized = im_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max(0, (new_w - target_w) // 2)
        return resized.crop((left, 0, left + target_w, target_h))
    new_w = target_w
    new_h = max(1, int(round(h * target_w / w)))
    resized = im_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return resized.crop((0, 0, target_w, target_h))


def thumb_cover_square_top(im_rgb: Image.Image, size: int) -> Image.Image:
    """Copre un quadrato size×size ritagliando dall'alto (per sorgenti verticali h > w)."""
    w, h = im_rgb.size
    new_w = size
    new_h = max(1, int(round(h * size / w)))
    resized = im_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
    if new_h < size:
        new_h = size
        new_w = max(1, int(round(w * size / h)))
        resized = im_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max(0, (new_w - size) // 2)
        return resized.crop((left, 0, left + size, size))
    return resized.crop((0, 0, size, size))


def thumb_relative_path_jpeg(asset_relative_path: str) -> str:
    """immagini/foo/bar.png -> immagini/thumbs/foo/bar.jpg"""
    path = Path(asset_relative_path)
    if not path.parts or path.parts[0] != "immagini":
        raise ValueError(f"Path immagine non valido: {asset_relative_path}")
    rest = Path(*path.parts[1:]).with_suffix(".jpg")
    return (Path("immagini") / "thumbs" / rest).as_posix()


def og_path_to_thumb_route(og_image: str) -> str:
    rel = og_image.lstrip("/")
    return "/" + thumb_relative_path_jpeg(rel)


def write_thumbnail_for_asset(asset_relative_path: str, output_dir: Path) -> bool:
    """Genera JPEG thumb sotto immagini/thumbs/... Ritorna False se Pillow assente o errore."""
    if not HAS_PILLOW:
        return False
    source_file = REPO_ROOT / asset_relative_path
    if not source_file.exists():
        return False
    thumb_rel = thumb_relative_path_jpeg(asset_relative_path)
    dest = output_dir / thumb_rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(source_file) as im:
            if im.mode in ("RGBA", "P"):
                rgba = im.convert("RGBA")
                background = Image.new("RGB", rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.split()[3])
                im_rgb = background
            elif im.mode != "RGB":
                im_rgb = im.convert("RGB")
            else:
                im_rgb = im
            if is_personaggi_portrait_image(asset_relative_path):
                im_rgb = thumb_resize_cover_portrait(im_rgb, THUMB_PORTRAIT_W, THUMB_PORTRAIT_H)
            else:
                pw, ph = im_rgb.size
                if ph > pw:
                    im_rgb = thumb_cover_square_top(im_rgb, THUMB_MAX_EDGE)
                else:
                    im_rgb.thumbnail((THUMB_MAX_EDGE, THUMB_MAX_EDGE), Image.Resampling.LANCZOS)
            im_rgb.save(dest, format="JPEG", quality=THUMB_JPEG_QUALITY, optimize=True)
        return True
    except OSError:
        return False


def excerpt_plain(markdown_fragment: str, max_len: int = EXCERPT_MAX_LEN) -> str:
    text = markdown_fragment.strip()
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.replace("**", "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "…"


def strip_h2_section(markdown_text: str, heading_title: str) -> str:
    """Rimuove la sezione che inizia con ## heading_title (H2) fino alla prossima heading di livello <= 2."""
    output_lines: list[str] = []
    skip_level: int | None = None
    target = heading_title

    for line in markdown_text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            title = sanitize_heading_text(heading.group(2))

            if skip_level is not None and level <= skip_level:
                skip_level = None

            if skip_level is None and level == 2 and title == target:
                skip_level = level
                continue

        if skip_level is None:
            output_lines.append(line)

    compacted_lines: list[str] = []
    previous_blank = False
    for line in output_lines:
        is_blank = line.strip() == ""
        if is_blank and previous_blank:
            continue
        compacted_lines.append(line)
        previous_blank = is_blank

    return "\n".join(compacted_lines).strip() + "\n"


def collect_hub_card_metadata(
    entries: list[PageEntry], blocked_headings: set[str]
) -> dict[Path, HubCardInfo]:
    """Estrae metadati per le card indice dal markdown sanificato (stesso perimetro dell'export)."""
    result: dict[Path, HubCardInfo] = {}
    for entry in entries:
        raw_text = entry.source_path.read_text(encoding="utf-8")
        sanitized = strip_sensitive_sections(raw_text, blocked_headings)
        rp = entry.relative_path
        parts = rp.parts

        if parts[0] == "resoconti" and rp.name.startswith("sessione-"):
            match = SESSION_H1_RE.search(sanitized)
            sections = split_h2_sections(sanitized)
            riassunto_body = sections.get("Riassunto", "")
            excerpt = excerpt_plain(riassunto_body) if riassunto_body else ""
            if match:
                result[rp] = HubCardInfo(
                    session_num=int(match.group(1)),
                    episode_title=match.group(2).strip(),
                    excerpt=excerpt,
                )
            else:
                result[rp] = HubCardInfo(excerpt=excerpt)
        elif parts[0] == "personaggi":
            razza = meta_line_first(META_RAZZA_RE, sanitized)
            classe = meta_line_first(META_CLASSE_RE, sanitized)
            bits = [b for b in (razza, classe) if b]
            result[rp] = HubCardInfo(subtitle=" · ".join(bits))
        elif parts[0] == "png":
            result[rp] = HubCardInfo(
                subtitle=meta_line_first(META_RUOLO_RE, sanitized),
                regione=meta_line_first(META_REGIONE_RE, sanitized),
                ambito=meta_line_first(META_AMBITO_RE, sanitized),
                promemoria=meta_line_first(META_PROMEMORIA_RE, sanitized),
            )
        elif len(parts) >= 3 and parts[0] == "ambientazione" and parts[1] == "luoghi":
            reg = meta_line_first(META_REGIONE_RE, sanitized)
            tipo = meta_line_first(META_TIPO_RE, sanitized)
            bits = [b for b in (reg, tipo) if b]
            result[rp] = HubCardInfo(subtitle=" · ".join(bits))
    return result


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_jekyll_config(output_dir: Path, manifest: dict) -> None:
    site = manifest["site"]
    config_text = textwrap.dedent(
        f"""\
        title: {yaml_string(site['title'])}
        description: {yaml_string(site['description'])}
        lang: "it"
        url: {yaml_string(site.get('url', ''))}
        baseurl: {yaml_string(site.get('baseurl', ''))}
        tagline: {yaml_string(site.get('tagline', ''))}
        defaults:
          - scope:
              path: ""
            values:
              layout: default
        markdown: kramdown
        kramdown:
          input: GFM
          hard_wrap: false
        """
    )
    (output_dir / "_config.yml").write_text(config_text, encoding="utf-8")


def write_layout(output_dir: Path) -> None:
    layout_dir = output_dir / "_layouts"
    layout_dir.mkdir(parents=True, exist_ok=True)
    layout_text = textwrap.dedent(
        """\
        <!doctype html>
        <html lang="it">
          <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta name="color-scheme" content="dark">
            <meta name="theme-color" content="#12100d">
            <meta name="apple-mobile-web-app-status-bar-style" content="black">
            <title>{% if page.title %}{{ page.title }} | {{ site.title }}{% else %}{{ site.title }}{% endif %}</title>
            <meta name="description" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.description | escape }}{% endif %}">
            {% if page.og_image %}
            <meta property="og:type" content="website">
            <meta property="og:site_name" content="{{ site.title | escape }}">
            <meta property="og:title" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.title | escape }}{% endif %}">
            <meta property="og:description" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.description | escape }}{% endif %}">
            <meta property="og:url" content="{{ page.url | absolute_url }}">
            <meta property="og:image" content="{{ page.og_image | absolute_url }}">
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:title" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.title | escape }}{% endif %}">
            <meta name="twitter:description" content="{% if page.title %}{{ page.title | strip_html | strip_newlines | escape }}{% else %}{{ site.description | escape }}{% endif %}">
            <meta name="twitter:image" content="{{ page.og_image | absolute_url }}">
            {% endif %}
            <link rel="stylesheet" href="{{ '/assets/site.css' | relative_url }}">
            <link rel="icon" type="image/png" href="/assets/favicon-96x96.png" sizes="96x96" />
            <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg" />
            <link rel="shortcut icon" href="/assets/favicon.ico" />
            <link rel="apple-touch-icon" sizes="180x180" href="/assets/apple-touch-icon.png" />
            <link rel="manifest" href="/assets/site.webmanifest" />
          </head>
          <body{% if page.home_full_bleed and page.hero_image %} class="home-full-bleed" style="--home-hero-image: url('{{ page.hero_image | relative_url }}')"{% endif %}>
            <header class="site-header">
              <div class="site-header-inner">
                <div class="site-header-brand">
                  <a class="site-title site-title-logo" href="{{ '/' | relative_url }}">
                    <img src="@HEADER_LOGO_LIQUID@" alt="{{ site.title | escape }}" decoding="async">
                  </a>
                  {% if site.tagline and site.tagline != "" %}
                  <p class="site-tagline">{{ site.tagline }}</p>
                  {% endif %}
                </div>
              </div>
            </header>
            <div class="site-shell">
              <aside class="site-sidebar">
                <nav class="site-sidebar-nav" aria-label="Sezioni">
                  <a href="{{ '/personaggi/' | relative_url }}">Personaggi</a>
                  <a href="{{ '/resoconti/' | relative_url }}">Resoconti</a>
                  <a href="{{ '/png/' | relative_url }}">PNG</a>
                  <a href="{{ '/luoghi/' | relative_url }}">Luoghi</a>
                  <a href="{{ '/prompt/' | relative_url }}">Generatore</a>
                </nav>
              </aside>
              <div class="site-content">
                <main class="site-main">
                  <div class="content-wrap">
                    <article class="page-card">
                      {% if page.show_title != false %}
                      <header class="page-header">
                        {% if page.collection_label %}
                        <p class="eyebrow">{{ page.collection_label }}</p>
                        {% endif %}
                        <h1>{{ page.title }}</h1>
                      </header>
                      {% endif %}
                      <div class="page-content">
                        {{ content }}
                      </div>
                    </article>
                  </div>
                </main>
              </div>
            </div>
            <script src="{{ '/assets/site.js' | relative_url }}" defer></script>
          </body>
        </html>
        """
    ).replace(
        "@HEADER_LOGO_LIQUID@",
        "{{ '" + HEADER_LOGO_PUBLIC_PATH + "' | relative_url }}",
    )
    (layout_dir / "default.html").write_text(layout_text, encoding="utf-8")


def front_matter(
    title: str,
    route: str,
    collection_label: str,
    source_path: Path,
    *,
    show_title: bool = True,
    og_image: str | None = None,
    hero_image: str | None = None,
    home_full_bleed: bool = False,
    png_hub: bool = False,
) -> str:
    lines = [
        "---",
        f"title: {yaml_string(title)}",
        'layout: "default"',
        f"permalink: {yaml_string(route)}",
        f"collection_label: {yaml_string(collection_label)}",
        f"source_path: {yaml_string(source_path.as_posix())}",
    ]
    if png_hub:
        lines.append("png_hub: true")
    if not show_title:
        lines.append("show_title: false")
    if og_image:
        lines.append(f"og_image: {yaml_string(og_image)}")
    if hero_image:
        lines.append(f"hero_image: {yaml_string(hero_image)}")
    if home_full_bleed:
        lines.append("home_full_bleed: true")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def render_index(manifest: dict, pages: list[PageEntry]) -> str:
    home_pages = [page for page in pages if public_sidebar_section(page) is None]
    featured_pages = [page for page in home_pages if page.featured]
    other_pages = [page for page in home_pages if not page.featured]

    hero_img = "{{ '" + HOME_HERO_PUBLIC_PATH + "' | relative_url }}"
    lines = [
        front_matter(
            title=manifest["site"]["title"],
            route="/",
            collection_label="Archivio pubblico",
            source_path=Path("tools/pubblicazione/manifest.json"),
            show_title=False,
            og_image=HOME_HERO_PUBLIC_PATH,
        ),
        "",
        f'<h1 class="home-tagline">{html.escape(manifest["site"]["tagline"])}</h1>',
        "",
        f'<figure class="home-hero"><img src="{hero_img}" alt="Il gruppo di avventurieri in carovana" loading="eager" decoding="async"></figure>',
        '<div class="hero">',
        f"{manifest['site']['description']}",
        "</div>",
    ]

    if featured_pages:
        lines.extend(["", "## Percorsi consigliati", ""])
        for page in featured_pages:
            lines.append(f"- [{page.label}]({{{{ '{page.route}' | relative_url }}}})")

    if other_pages:
        lines.extend(["", "## Altri contenuti player-safe", ""])
        for page in other_pages:
            lines.append(f"- [{page.title}]({{{{ '{page.route}' | relative_url }}}})")

    return "\n".join(lines).strip() + "\n"


def copy_asset(relative_asset_path: str, output_dir: Path) -> None:
    source_path = REPO_ROOT / relative_asset_path
    if not source_path.exists():
        raise FileNotFoundError(f"Asset referenziato ma non trovato: {relative_asset_path}")
    destination = output_dir / relative_asset_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)


def copy_pubblicazione_assets(output_dir: Path) -> None:
    """Copia byte-per-byte i file in tools/pubblicazione/assets/ (PNG con alpha, ecc.) senza generare thumbnail."""
    if not PUBBLICAZIONE_ASSETS_DIR.is_dir():
        raise FileNotFoundError(
            "Manca la cartella tools/pubblicazione/assets/: contiene gli asset statici del sito pubblico "
            "che non devono essere processati dalla pipeline immagini/."
        )
    if not (PUBBLICAZIONE_ASSETS_DIR / "header.png").is_file():
        raise FileNotFoundError(
            "Manca tools/pubblicazione/assets/header.png (logo intestazione del sito, PNG con trasparenza)."
        )
    if not (PUBBLICAZIONE_ASSETS_DIR / "site.css").is_file():
        raise FileNotFoundError(
            "Manca tools/pubblicazione/assets/site.css (foglio di stile del sito pubblico)."
        )
    if not (PUBBLICAZIONE_ASSETS_DIR / "site.js").is_file():
        raise FileNotFoundError(
            "Manca tools/pubblicazione/assets/site.js (filtri hub PNG del sito pubblico)."
        )
    if not (PUBBLICAZIONE_ASSETS_DIR / "prompt-page.js").is_file():
        raise FileNotFoundError(
            "Manca tools/pubblicazione/assets/prompt-page.js (Generatore prompt del sito pubblico)."
        )
    dest_root = output_dir / "assets"
    dest_root.mkdir(parents=True, exist_ok=True)
    for path in sorted(PUBBLICAZIONE_ASSETS_DIR.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(PUBBLICAZIONE_ASSETS_DIR)
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def prepare_pages(entries: list[PageEntry], blocked_headings: set[str]) -> list[PreparedPage]:
    prepared_pages: list[PreparedPage] = []

    for entry in entries:
        raw_text = entry.source_path.read_text(encoding="utf-8")
        sanitized_text = strip_sensitive_sections(raw_text, blocked_headings)
        fallback_title = sanitize_heading_text(entry.relative_path.stem.replace("-", " "))
        title, body = extract_title(sanitized_text, fallback_title)
        body = transform_body_for_profile(body, entry.profile)
        body = demote_remaining_h1(body)
        if entry.profile == "public-png":
            header = render_png_public_header_html(
                meta_line_first(META_REGIONE_RE, raw_text),
                meta_line_first(META_AMBITO_RE, raw_text),
                meta_line_first(META_PROMEMORIA_RE, raw_text),
            )
            if header:
                body = header + body
        prepared_pages.append(PreparedPage(entry=entry, title=title, body=body))

    return prepared_pages


def build_site(manifest: dict, output_dir: Path) -> tuple[int, int]:
    write_indice(REPO_ROOT)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    blocked_headings = set(manifest.get("stripSections", []))
    resolved_entries = resolve_pages(manifest)
    hub_cards = collect_hub_card_metadata(resolved_entries, blocked_headings)
    prepared_pages = prepare_pages(resolved_entries, blocked_headings)
    entity_route_lookup = build_entity_route_lookup(prepared_pages)
    built_pages: list[PageEntry] = []
    referenced_assets: set[str] = set()
    page_og_images: dict[Path, str | None] = {}
    pending_page_writes: list[tuple[Path, PageEntry, str, str]] = []

    for prepared in prepared_pages:
        entry = prepared.entry
        title = prepared.title
        body = prepared.body
        body = rewrite_session_links(body)
        body = rewrite_section_entity_links(body, entity_route_lookup)
        body, assets = rewrite_image_links(body)
        referenced_assets.update(assets)

        if entry.relative_path.parts[0] == "resoconti" and entry.relative_path.name.lower().startswith(
            "sessione-"
        ):
            body = strip_h2_section(body, "Riassunto")

        destination = output_dir / entry.relative_path
        pending_page_writes.append((destination, entry, title, body))

        built_pages.append(
            PageEntry(
                source_path=entry.source_path,
                relative_path=entry.relative_path,
                route=entry.route,
                title=title,
                label=entry.label,
                kind=entry.kind,
                profile=entry.profile,
                aliases=entry.aliases,
                featured=entry.featured,
            )
        )

    if not HAS_PILLOW:
        print(
            "Avviso: Pillow non installato (pip install -r tools/scripts/requirements-public-site.txt); "
            "nessuna thumbnail generata; le card useranno il segnaposto.",
            file=sys.stderr,
        )

    referenced_assets.add(HOME_HERO_ASSET)

    for asset in sorted(referenced_assets):
        copy_asset(asset, output_dir)
        write_thumbnail_for_asset(asset, output_dir)

    for destination, entry, title, body in pending_page_writes:
        body_pub = body
        og_image = first_og_image_path_from_body(body_pub)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            front_matter(
                title=title,
                route=entry.route,
                collection_label=entry.label,
                source_path=entry.relative_path,
                og_image=og_image,
            )
            + body_pub,
            encoding="utf-8",
        )
        page_og_images[entry.relative_path] = og_image

    hub_page_count = write_section_hub_pages(output_dir, built_pages, hub_cards, page_og_images)

    prompt_catalog = collect_prompt_catalog(resolved_entries, output_dir)
    write_prompt_tool_assets(output_dir, prompt_catalog)
    prompt_page_count = 1

    write_jekyll_config(output_dir, manifest)
    write_layout(output_dir)
    copy_pubblicazione_assets(output_dir)
    (output_dir / "index.md").write_text(render_index(manifest, built_pages), encoding="utf-8")

    return len(built_pages) + hub_page_count + prompt_page_count, len(referenced_assets)


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
