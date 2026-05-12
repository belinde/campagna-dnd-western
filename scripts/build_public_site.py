#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = REPO_ROOT / "pubblicazione" / "manifest.json"
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((/immagini/[^)\s]+)\)")
OG_IMAGE_IN_PUBLIC_MD_RE = re.compile(
    r"!\[[^\]]*\]\(\{\{\s*'(/[^']+)'\s*\|\s*relative_url\s*\}\}\)"
)
SESSION_LINK_RE = re.compile(r"\[(Sessione (\d{3}))\](?!\()")
ENTITY_BULLET_RE = re.compile(r"^(\s*-\s+\*\*)([^*]+)(\*\*.*)$")


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
    manifest_output = manifest.get("outputDirectory", "build/public-site")
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


def render_section_hub_index(
    *,
    hub_title: str,
    hub_route: str,
    source_path: Path,
    section_key: str,
    built_pages: list[PageEntry],
) -> str:
    in_section = [p for p in built_pages if public_sidebar_section(p) == section_key]
    ordered = sort_pages_for_section(section_key, in_section)
    lines = [
        front_matter(
            title=hub_title,
            route=hub_route,
            collection_label="",
            source_path=source_path,
        ),
    ]
    for page in ordered:
        lines.append(f"- [{page.title}]({{{{ '{page.route}' | relative_url }}}})")
    lines.append("")
    return "\n".join(lines)


def write_section_hub_pages(output_dir: Path, built_pages: list[PageEntry]) -> int:
    hubs: list[tuple[str, str, str, Path, str]] = [
        ("Personaggi", "/personaggi/", output_dir / "personaggi" / "index.md", Path("pubblicazione/_generated/index-personaggi.md"), "personaggi"),
        ("Resoconti", "/resoconti/", output_dir / "resoconti" / "index.md", Path("pubblicazione/_generated/index-resoconti.md"), "resoconti"),
        ("PNG", "/png/", output_dir / "png" / "index.md", Path("pubblicazione/_generated/index-png.md"), "png"),
        ("Luoghi", "/luoghi/", output_dir / "luoghi" / "index.md", Path("pubblicazione/_generated/index-luoghi.md"), "luoghi"),
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


def format_section(title: str, body: str) -> str:
    clean_body = body.strip()
    return f"## {title}\n\n{clean_body}\n"


def render_public_png_body(markdown_text: str) -> str:
    sections = split_h2_sections(markdown_text)
    image_body = sections.get("Immagine canonica", "_Nessuna immagine canonica ancora associata._")
    description_body = sections.get("Aspetto", "_Descrizione non ancora pubblicata._")
    events_body = sections.get("Eventi interessanti", "_Nessun evento interessante ancora pubblicato._")

    rendered_sections = [
        format_section("Immagine canonica", image_body),
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
          </head>
          <body>
            <div class="site-shell">
              <aside class="site-sidebar">
                <nav class="site-sidebar-nav" aria-label="Sezioni">
                  <a href="{{ '/' | relative_url }}">Home</a>
                  <a href="{{ '/personaggi/' | relative_url }}">Personaggi</a>
                  <a href="{{ '/resoconti/' | relative_url }}">Resoconti</a>
                  <a href="{{ '/png/' | relative_url }}">PNG</a>
                  <a href="{{ '/luoghi/' | relative_url }}">Luoghi</a>
                </nav>
              </aside>
              <div class="site-content">
                <header class="site-header">
                  <div class="wrap">
                    <a class="site-title" href="{{ '/' | relative_url }}">{{ site.title }}</a>
                  </div>
                </header>

                <main class="wrap site-main">
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
                </main>
              </div>
            </div>
          </body>
        </html>
        """
    )
    (layout_dir / "default.html").write_text(layout_text, encoding="utf-8")


def write_styles(output_dir: Path) -> None:
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    styles = textwrap.dedent(
        """\
        :root {
          color-scheme: dark;
          --bg: #12100d;
          --panel: #1a1713;
          --panel-border: #2f2a23;
          --text: #f5efe5;
          --muted: #c4b8a5;
          --accent: #d39c4a;
          --accent-soft: rgba(211, 156, 74, 0.16);
          --shadow: rgba(0, 0, 0, 0.28);
        }

        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          font-family: Georgia, "Times New Roman", serif;
          line-height: 1.7;
          background: linear-gradient(180deg, #16120e 0%, #0f0d0b 100%);
          color: var(--text);
        }

        a {
          color: var(--accent);
        }

        a:hover {
          color: #efb867;
        }

        .wrap {
          width: 100%;
          max-width: none;
          margin: 0;
          padding-left: 1.25rem;
          padding-right: 1.25rem;
          box-sizing: border-box;
        }

        .site-main {
          flex: 1;
          min-width: 0;
        }

        .site-shell {
          display: flex;
          align-items: flex-start;
          min-height: 100vh;
        }

        .site-sidebar {
          flex: 0 0 220px;
          position: sticky;
          top: 0;
          align-self: flex-start;
          min-height: 100vh;
          padding: 1.25rem 1rem;
          background: rgba(10, 8, 6, 0.96);
          border-right: 1px solid var(--panel-border);
        }

        .site-sidebar-nav {
          display: flex;
          flex-direction: column;
          gap: 0.65rem;
        }

        .site-sidebar-nav a {
          text-decoration: none;
          font-size: 1rem;
          color: var(--muted);
        }

        .site-sidebar-nav a:hover {
          color: var(--accent);
        }

        .site-content {
          flex: 1;
          min-width: 0;
          display: flex;
          flex-direction: column;
        }

        .site-header {
          background: rgba(10, 8, 6, 0.92);
          border-bottom: 1px solid var(--panel-border);
        }

        .site-header .wrap {
          display: flex;
          align-items: center;
          justify-content: flex-start;
          gap: 1rem;
          padding: 1rem 0;
        }

        .site-title {
          font-size: 1.15rem;
          font-weight: 700;
          text-decoration: none;
          color: var(--text);
        }

        .page-card {
          margin: 2rem 0;
          padding: 1.8rem;
          background: var(--panel);
          border: 1px solid var(--panel-border);
          border-radius: 18px;
          box-shadow: 0 20px 48px var(--shadow);
        }

        .page-header {
          margin-bottom: 1.6rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid var(--panel-border);
        }

        .page-header h1 {
          margin: 0;
          line-height: 1.15;
        }

        .eyebrow {
          margin: 0 0 0.35rem;
          color: var(--muted);
          font-size: 0.95rem;
          letter-spacing: 0.03em;
          text-transform: uppercase;
        }

        .hero {
          margin-bottom: 2rem;
          padding: 1.2rem 1.4rem;
          background: var(--accent-soft);
          border: 1px solid rgba(211, 156, 74, 0.28);
          border-radius: 14px;
        }

        h2,
        h3 {
          line-height: 1.2;
          margin-top: 2rem;
        }

        img {
          display: block;
          max-width: 100%;
          height: auto;
          margin: 1.25rem auto;
          border-radius: 12px;
          border: 1px solid var(--panel-border);
        }

        code {
          padding: 0.15rem 0.35rem;
          border-radius: 6px;
          background: rgba(255, 255, 255, 0.06);
          font-size: 0.95em;
        }

        blockquote {
          margin: 1.5rem 0;
          padding-left: 1rem;
          border-left: 3px solid var(--accent);
          color: var(--muted);
        }

        @media (max-width: 720px) {
          .site-shell {
            flex-direction: column;
          }

          .site-sidebar {
            position: relative;
            min-height: 0;
            width: 100%;
            border-right: 0;
            border-bottom: 1px solid var(--panel-border);
          }

          .site-sidebar-nav {
            flex-direction: row;
            flex-wrap: wrap;
            gap: 0.75rem 1.25rem;
          }

          .site-header .wrap {
            flex-direction: column;
            align-items: flex-start;
          }

          .page-card {
            padding: 1.2rem;
          }
        }
        """
    )
    (assets_dir / "site.css").write_text(styles, encoding="utf-8")


def front_matter(
    title: str,
    route: str,
    collection_label: str,
    source_path: Path,
    *,
    show_title: bool = True,
    og_image: str | None = None,
) -> str:
    lines = [
        "---",
        f"title: {yaml_string(title)}",
        'layout: "default"',
        f"permalink: {yaml_string(route)}",
        f"collection_label: {yaml_string(collection_label)}",
        f"source_path: {yaml_string(source_path.as_posix())}",
    ]
    if not show_title:
        lines.append("show_title: false")
    if og_image:
        lines.append(f"og_image: {yaml_string(og_image)}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def render_index(manifest: dict, pages: list[PageEntry]) -> str:
    home_pages = [page for page in pages if public_sidebar_section(page) is None]
    featured_pages = [page for page in home_pages if page.featured]
    other_pages = [page for page in home_pages if not page.featured]

    lines = [
        front_matter(
            title=manifest["site"]["title"],
            route="/",
            collection_label="Archivio pubblico",
            source_path=Path("pubblicazione/manifest.json"),
            show_title=False,
        ),
        f"# {manifest['site']['tagline']}",
        "",
        '<div class="hero">',
        "",
        f"**{manifest['site']['description']}**",
        "",
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


def prepare_pages(entries: list[PageEntry], blocked_headings: set[str]) -> list[PreparedPage]:
    prepared_pages: list[PreparedPage] = []

    for entry in entries:
        raw_text = entry.source_path.read_text(encoding="utf-8")
        sanitized_text = strip_sensitive_sections(raw_text, blocked_headings)
        fallback_title = sanitize_heading_text(entry.relative_path.stem.replace("-", " "))
        title, body = extract_title(sanitized_text, fallback_title)
        body = transform_body_for_profile(body, entry.profile)
        body = demote_remaining_h1(body)
        prepared_pages.append(PreparedPage(entry=entry, title=title, body=body))

    return prepared_pages


def build_site(manifest: dict, output_dir: Path) -> tuple[int, int]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    blocked_headings = set(manifest.get("stripSections", []))
    resolved_entries = resolve_pages(manifest)
    prepared_pages = prepare_pages(resolved_entries, blocked_headings)
    entity_route_lookup = build_entity_route_lookup(prepared_pages)
    built_pages: list[PageEntry] = []
    referenced_assets: set[str] = set()

    for prepared in prepared_pages:
        entry = prepared.entry
        title = prepared.title
        body = prepared.body
        body = rewrite_session_links(body)
        body = rewrite_section_entity_links(body, entity_route_lookup)
        body, assets = rewrite_image_links(body)
        referenced_assets.update(assets)
        og_image = first_og_image_path_from_body(body)

        destination = output_dir / entry.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            front_matter(
                title=title,
                route=entry.route,
                collection_label=entry.label,
                source_path=entry.relative_path,
                og_image=og_image,
            )
            + body,
            encoding="utf-8",
        )

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

    for asset in sorted(referenced_assets):
        copy_asset(asset, output_dir)

    hub_page_count = write_section_hub_pages(output_dir, built_pages)

    write_jekyll_config(output_dir, manifest)
    write_layout(output_dir)
    write_styles(output_dir)
    (output_dir / "index.md").write_text(render_index(manifest, built_pages), encoding="utf-8")

    return len(built_pages) + hub_page_count, len(referenced_assets)


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
