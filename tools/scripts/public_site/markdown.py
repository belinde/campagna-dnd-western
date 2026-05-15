from __future__ import annotations

import html
import re
from pathlib import Path

from png_catalog import META_AMBITO_RE, META_PROMEMORIA_RE

from public_site.constants import (
    ENTITY_BULLET_RE,
    EXCERPT_MAX_LEN,
    HEADING_RE,
    IMAGE_RE,
    META_CLASSE_RE,
    META_RAZZA_RE,
    META_REGIONE_RE,
    META_RUOLO_RE,
    META_TIPO_RE,
    PUBLIC_IMAGE_MD_RE,
    SALIENT_IMAGE_SECTIONS,
    SESSION_H1_RE,
    SESSION_LINK_RE,
    VISUAL_REF_FENCE_RE,
    VISUAL_REF_HEADINGS,
)
from public_site.media import render_salient_media_card_html
from public_site.models import HubCardInfo, PageEntry, PreparedPage


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


def is_salient_image_caption_line(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped) and stripped.startswith("*") and stripped.endswith("*")


def wrap_salient_image_blocks(markdown_text: str) -> str:
    """Converte immagine + didascalia nelle sezioni salienti in card HTML full width."""
    lines = markdown_text.splitlines()
    output: list[str] = []
    current_h2: str | None = None
    index = 0

    while index < len(lines):
        line = lines[index]
        heading = HEADING_RE.match(line)
        if heading and len(heading.group(1)) == 2:
            current_h2 = sanitize_heading_text(heading.group(2))
            output.append(line)
            index += 1
            continue

        if current_h2 in SALIENT_IMAGE_SECTIONS:
            image_match = PUBLIC_IMAGE_MD_RE.match(line)
            if image_match:
                alt_text, asset_path = image_match.groups()
                next_index = index + 1
                if next_index < len(lines) and not lines[next_index].strip():
                    next_index += 1
                caption_line: str | None = None
                if next_index < len(lines) and is_salient_image_caption_line(lines[next_index]):
                    caption_line = lines[next_index]
                    next_index += 1
                output.append(render_salient_media_card_html(alt_text, asset_path, caption_line))
                index = next_index
                continue

        output.append(line)
        index += 1

    return "\n".join(output).strip() + "\n"


def meta_line_first(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return match.group(1).strip() if match else ""


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
