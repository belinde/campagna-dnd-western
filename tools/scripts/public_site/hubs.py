from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path

from png_catalog import region_bucket, region_sort_key

from public_site.jekyll import front_matter
from public_site.manifest import (
    liquid_rel_jekyll,
    public_sidebar_section,
    session_number_from_path,
    sort_pages_for_section,
)
from public_site.media import og_path_to_thumb_route, thumb_file_exists
from public_site.models import HubCardInfo, PageEntry, SessionNavLink


def session_badge_number(page: PageEntry, meta: HubCardInfo) -> int | None:
    if meta.session_num is not None:
        return meta.session_num
    m = re.match(r"sessione-(\d+)", page.relative_path.stem, re.IGNORECASE)
    return int(m.group(1)) if m else None


def build_session_chapter_nav(
    built_pages: list[PageEntry],
) -> dict[int, tuple[SessionNavLink | None, SessionNavLink | None]]:
    """Per ogni numero sessione pubblicata, link a precedente e successiva (se esistono)."""
    ordered: list[tuple[int, PageEntry]] = []
    for page in built_pages:
        session_num = session_number_from_path(page.relative_path)
        if session_num is not None:
            ordered.append((session_num, page))
    ordered.sort(key=lambda item: item[0])

    navigation: dict[int, tuple[SessionNavLink | None, SessionNavLink | None]] = {}
    for index, (session_num, page) in enumerate(ordered):
        prev_link: SessionNavLink | None = None
        next_link: SessionNavLink | None = None
        if index > 0:
            _, prev_page = ordered[index - 1]
            prev_link = SessionNavLink(route=prev_page.route)
        if index + 1 < len(ordered):
            _, next_page = ordered[index + 1]
            next_link = SessionNavLink(route=next_page.route)
        navigation[session_num] = (prev_link, next_link)
    return navigation


def png_card_search_blob(page: PageEntry, meta: HubCardInfo) -> str:
    parts = (page.title, meta.subtitle, meta.promemoria, meta.ambito, meta.regione)
    return " ".join(p for p in parts if p).casefold()


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
    start_reading_route = "/resoconti/sessione-001/" if section_key == "resoconti" else None
    lines = [
        front_matter(
            title=hub_title,
            route=hub_route,
            collection_label="",
            source_path=source_path,
            start_reading_route=start_reading_route,
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
