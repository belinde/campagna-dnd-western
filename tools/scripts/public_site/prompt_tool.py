from __future__ import annotations

import json
import re
from pathlib import Path

from png_catalog import region_bucket

from public_site.constants import (
    META_CLASSE_RE,
    META_POPOLAZIONE_RE,
    META_RAZZA_RE,
    META_REGIONE_RE,
    META_RUOLO_RE,
    META_TIPO_RE,
    PROMPT_PAGE_BODY_PATH,
    PROMPT_SCRIPT_PUBLIC_PATH,
)
from public_site.jekyll import front_matter
from public_site.manifest import liquid_rel_jekyll, natural_sort_key
from public_site.markdown import (
    extract_title,
    extract_visual_reference,
    meta_line_first,
    sanitize_heading_text,
)
from public_site.media import first_image_path_from_markdown, thumb_path_for_catalog
from public_site.models import PageEntry


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


_COMPACT_TIPO_MARKERS = (
    "fattoria",
    "cascina",
    "podere",
    "mulino",
    "homestead",
    "farmstead",
)
_COMPACT_TIPO_EXACT = ("casa", "famiglia")
_CITY_TIPO_MARKERS = ("città", "citta", "capitale", "metropoli")


def parse_population_number(popolazione: str) -> int | None:
    """Estrae il numero abitanti principale da **Popolazione:** (es. ~40.000)."""
    text = (popolazione or "").strip()
    if not text:
        return None
    family_match = re.search(
        r"\((\d+)\s*(?:persone|abitanti|people)\)", text, re.IGNORECASE
    )
    if family_match:
        return int(family_match.group(1))
    numbers: list[int] = []
    for raw in re.findall(r"[\d][\d.,]*", text):
        digits = re.sub(r"[^\d]", "", raw)
        if not digits:
            continue
        numbers.append(int(digits))
    if not numbers:
        return None
    return max(numbers)


def infer_location_scale(tipo: str, popolazione: str) -> str:
    """compact | settlement | city — per gerarchia Setting nel generatore prompt."""
    tipo_cf = (tipo or "").casefold()
    pop_cf = (popolazione or "").casefold()
    pop_num = parse_population_number(popolazione)

    if pop_num is not None and pop_num < 50:
        return "compact"
    for marker in _COMPACT_TIPO_MARKERS:
        if marker in tipo_cf:
            return "compact"
    for marker in _COMPACT_TIPO_EXACT:
        if re.search(rf"\b{re.escape(marker)}\b", tipo_cf):
            return "compact"
    if "famiglia" in pop_cf and (pop_num is None or pop_num < 50):
        return "compact"

    for marker in _CITY_TIPO_MARKERS:
        if marker in tipo_cf:
            return "city"
    if pop_num is not None and pop_num >= 5000:
        return "city"

    return "settlement"


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
    from png_catalog import META_AMBITO_RE, META_PROMEMORIA_RE

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
        tipo_luogo = ""
        popolazione = ""
        description = subtitle

        if kind == "png":
            regione_raw = meta_line_first(META_REGIONE_RE, raw_text)
            promemoria = meta_line_first(META_PROMEMORIA_RE, raw_text)
            ambito = meta_line_first(META_AMBITO_RE, raw_text)
            description = promemoria or subtitle
        elif kind == "luogo":
            regione_raw = meta_line_first(META_REGIONE_RE, raw_text)
            tipo_luogo = meta_line_first(META_TIPO_RE, raw_text)
            popolazione = meta_line_first(META_POPOLAZIONE_RE, raw_text)

        regione_bucket_val = region_bucket(regione_raw) if regione_raw.strip() else ""
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
        if regione_bucket_val:
            item["regione"] = regione_bucket_val
        if kind == "luogo":
            item["tipo"] = tipo_luogo
            item["popolazione"] = popolazione
            item["locationScale"] = infer_location_scale(tipo_luogo, popolazione)
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
