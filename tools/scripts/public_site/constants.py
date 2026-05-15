from __future__ import annotations

import re

from campagna_paths import repo_root

try:
    from PIL import Image  # noqa: F401

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

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
OG_IMAGE_IN_SALIENT_HTML_RE = re.compile(
    r'<img\s+[^>]*\bsrc="\{\{\s*\'(/[^\'"]+)\'\s*\|\s*relative_url\s*\}\}"',
    re.IGNORECASE,
)
PUBLIC_IMAGE_MD_RE = re.compile(
    r"^!\[([^\]]*)\]\(\{\{\s*'(/[^']+)'\s*\|\s*relative_url\s*\}\}\)\s*$"
)
SALIENT_IMAGE_SECTIONS = frozenset({"Immagine", "Immagini salienti"})
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
