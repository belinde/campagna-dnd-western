from __future__ import annotations

import shutil
import sys
from pathlib import Path

from png_catalog import META_AMBITO_RE, META_PROMEMORIA_RE, write_indice

from public_site.constants import HAS_PILLOW, HOME_HERO_ASSET, META_REGIONE_RE, REPO_ROOT
from public_site.hubs import build_session_chapter_nav, write_section_hub_pages
from public_site.jekyll import (
    front_matter,
    render_index,
    write_jekyll_config,
    write_layout,
)
from public_site.manifest import resolve_pages, session_number_from_path
from public_site.markdown import (
    build_entity_route_lookup,
    collect_hub_card_metadata,
    demote_remaining_h1,
    extract_title,
    meta_line_first,
    sanitize_heading_text,
    render_png_public_header_html,
    rewrite_image_links,
    rewrite_section_entity_links,
    rewrite_session_links,
    strip_h2_section,
    strip_sensitive_sections,
    transform_body_for_profile,
    wrap_salient_image_blocks,
)
from public_site.media import (
    copy_asset,
    copy_pubblicazione_assets,
    first_og_image_path_from_body,
    write_thumbnail_for_asset,
)
from public_site.models import PageEntry, PreparedPage, SessionNavLink
from public_site.prompt_tool import collect_prompt_catalog, write_prompt_tool_assets


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
    pending_page_writes: list[tuple[Path, PageEntry, str, str, str | None]] = []

    for prepared in prepared_pages:
        entry = prepared.entry
        title = prepared.title
        body = prepared.body
        body = rewrite_session_links(body)
        body = rewrite_section_entity_links(body, entity_route_lookup)
        body, assets = rewrite_image_links(body)
        og_image = first_og_image_path_from_body(body)
        body = wrap_salient_image_blocks(body)
        referenced_assets.update(assets)

        if entry.relative_path.parts[0] == "resoconti" and entry.relative_path.name.lower().startswith(
            "sessione-"
        ):
            body = strip_h2_section(body, "Riassunto")

        destination = output_dir / entry.relative_path
        pending_page_writes.append((destination, entry, title, body, og_image))

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
    session_chapter_nav = build_session_chapter_nav(built_pages, hub_cards)

    for asset in sorted(referenced_assets):
        copy_asset(asset, output_dir)
        write_thumbnail_for_asset(asset, output_dir)

    for destination, entry, title, body, og_image in pending_page_writes:
        body_pub = body
        session_num = session_number_from_path(entry.relative_path)
        session_nav_prev: SessionNavLink | None = None
        session_nav_next: SessionNavLink | None = None
        if session_num is not None:
            session_nav_prev, session_nav_next = session_chapter_nav.get(
                session_num, (None, None)
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            front_matter(
                title=title,
                route=entry.route,
                collection_label=entry.label,
                source_path=entry.relative_path,
                og_image=og_image,
                session_num=session_num,
                session_nav_prev=session_nav_prev,
                session_nav_next=session_nav_next,
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
