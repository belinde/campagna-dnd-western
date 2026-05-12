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


@dataclass(frozen=True)
class PageEntry:
    source_path: Path
    relative_path: Path
    route: str
    title: str
    label: str
    kind: str
    profile: str | None = None
    featured: bool = False


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
                    featured=False,
                )
            )
            seen.add(relative_path)

    return entries


def route_for(relative_path: Path) -> str:
    path_without_suffix = relative_path.with_suffix("").as_posix()
    return f"/{path_without_suffix}/"


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


def rewrite_image_links(markdown_text: str) -> tuple[str, set[str]]:
    images: set[str] = set()

    def replacer(match: re.Match[str]) -> str:
        alt_text, image_path = match.groups()
        normalized = image_path.lstrip("/")
        images.add(normalized)
        return f"![{alt_text}]({{{{ '/{normalized}' | relative_url }}}})"

    return IMAGE_RE.sub(replacer, markdown_text), images


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_jekyll_config(output_dir: Path, manifest: dict, player_guide_path: str) -> None:
    site = manifest["site"]
    config_text = textwrap.dedent(
        f"""\
        title: {yaml_string(site['title'])}
        description: {yaml_string(site['description'])}
        lang: "it"
        url: {yaml_string(site.get('url', ''))}
        baseurl: {yaml_string(site.get('baseurl', ''))}
        tagline: {yaml_string(site.get('tagline', ''))}
        player_guide_path: {yaml_string(player_guide_path)}
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
            <link rel="stylesheet" href="{{ '/assets/site.css' | relative_url }}">
          </head>
          <body>
            <header class="site-header">
              <div class="wrap">
                <a class="site-title" href="{{ '/' | relative_url }}">{{ site.title }}</a>
                <nav class="site-nav" aria-label="Navigazione principale">
                  <a href="{{ '/' | relative_url }}">Home</a>
                  {% if site.player_guide_path != "" %}
                  <a href="{{ site.player_guide_path | relative_url }}">Guida giocatori</a>
                  {% endif %}
                </nav>
              </div>
            </header>

            <main class="wrap">
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

            <footer class="site-footer">
              <div class="wrap">
                <p>Sorgente privata del DM, export pubblico player-safe generato automaticamente.</p>
              </div>
            </footer>
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
          --max-width: 860px;
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
          width: min(calc(100% - 2rem), var(--max-width));
          margin: 0 auto;
        }

        .site-header,
        .site-footer {
          background: rgba(10, 8, 6, 0.92);
          border-bottom: 1px solid var(--panel-border);
        }

        .site-footer {
          border-top: 1px solid var(--panel-border);
          border-bottom: 0;
          margin-top: 3rem;
        }

        .site-header .wrap,
        .site-footer .wrap {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
          padding: 1rem 0;
        }

        .site-title {
          font-size: 1.15rem;
          font-weight: 700;
          text-decoration: none;
          color: var(--text);
        }

        .site-nav {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .site-nav a {
          text-decoration: none;
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
          .site-header .wrap,
          .site-footer .wrap {
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
    lines.append("---")
    return "\n".join(lines) + "\n\n"


def render_index(manifest: dict, pages: list[PageEntry]) -> str:
    featured_pages = [page for page in pages if page.kind == "page" and page.featured]
    other_pages = [page for page in pages if page.kind == "page" and not page.featured]
    collections: dict[str, list[PageEntry]] = {}
    allowlist_groups: dict[str, list[PageEntry]] = {}
    for page in pages:
        if page.kind == "collection":
            collections.setdefault(page.label, []).append(page)
            continue
        if page.kind == "allowlist":
            allowlist_groups.setdefault(page.label, []).append(page)

    lines = [
        front_matter(
            title=manifest["site"]["title"],
            route="/",
            collection_label="Archivio pubblico",
            source_path=Path("pubblicazione/manifest.json"),
            show_title=False,
        ),
        f"# {manifest['site']['title']}",
        "",
        '<div class="hero">',
        "",
        f"**{manifest['site']['tagline']}**",
        "",
        "Questo sito contiene solo materiale **player-safe** estratto dal repository privato della campagna. Le sezioni riservate al DM vengono rimosse automaticamente in fase di export.",
        "",
        "</div>",
    ]

    if featured_pages:
        lines.extend(["", "## Percorsi consigliati", ""])
        for page in featured_pages:
            lines.append(f"- [{page.label}]({{{{ '{page.route}' | relative_url }}}})")

    for collection_name, collection_pages in collections.items():
        lines.extend(["", f"## {collection_name}", ""])
        for page in collection_pages:
            lines.append(f"- [{page.title}]({{{{ '{page.route}' | relative_url }}}})")

    for group_name, grouped_pages in allowlist_groups.items():
        lines.extend(["", f"## {group_name}", ""])
        for page in grouped_pages:
            lines.append(f"- [{page.title}]({{{{ '{page.route}' | relative_url }}}})")

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


def build_site(manifest: dict, output_dir: Path) -> tuple[int, int]:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    blocked_headings = set(manifest.get("stripSections", []))
    resolved_entries = resolve_pages(manifest)
    built_pages: list[PageEntry] = []
    referenced_assets: set[str] = set()

    for entry in resolved_entries:
        raw_text = entry.source_path.read_text(encoding="utf-8")
        sanitized_text = strip_sensitive_sections(raw_text, blocked_headings)
        fallback_title = sanitize_heading_text(entry.relative_path.stem.replace("-", " "))
        title, body = extract_title(sanitized_text, fallback_title)
        body = transform_body_for_profile(body, entry.profile)
        body = demote_remaining_h1(body)
        body, assets = rewrite_image_links(body)
        referenced_assets.update(assets)

        destination = output_dir / entry.relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            front_matter(
                title=title,
                route=entry.route,
                collection_label=entry.label,
                source_path=entry.relative_path,
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
                featured=entry.featured,
            )
        )

    for asset in sorted(referenced_assets):
        copy_asset(asset, output_dir)

    write_jekyll_config(
        output_dir,
        manifest,
        next((page.route for page in built_pages if page.kind == "page" and page.featured), ""),
    )
    write_layout(output_dir)
    write_styles(output_dir)
    (output_dir / "index.md").write_text(render_index(manifest, built_pages), encoding="utf-8")

    return len(built_pages), len(referenced_assets)


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
