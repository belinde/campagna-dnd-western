#!/usr/bin/env python3
"""Genera un PDF player-safe da un file Markdown del repository.

Applica lo stile visivo del sito pubblico (`tools/pubblicazione/assets/site.css`:
fondo scuro, serif, accento oro) e la stessa sanificazione del manifest
(`stripSections`), cosi` che un documento nato come materiale DM possa essere
consegnato ai giocatori senza esporre sezioni private.

Il rendering usa Google Chrome in headless (`--print-to-pdf`) su un profilo
temporaneo dedicato: non tocca il profilo personale ne` quello «Agenti».

Esempio:
    python3 tools/scripts/build_player_pdf.py spunti/cosa-potevate-fare-meglio.md \
        --hero immagini/varie/cosa-potevate-fare-meglio.jpg \
        --sottotitolo "La corsa al Nuovo Mondo — Arco della Strage dei Branchi"
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST = REPO_ROOT / "tools" / "pubblicazione" / "manifest.json"
HEADER_LOGO = REPO_ROOT / "tools" / "pubblicazione" / "assets" / "header.png"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "tools" / "build" / "pdf"

# Righe di metadato interno da non pubblicare (prima di qualsiasi `##`).
META_LINE_RE = re.compile(r"^\*\*(Tipo|Stato|Priorita`?|Priorità):\*\*", re.IGNORECASE)


def strip_sections(markdown: str, titles: list[str]) -> str:
    """Rimuove le sezioni `## Titolo` (e tutto il loro contenuto) elencate nel manifest."""
    wanted = {t.strip().lower() for t in titles}
    out: list[str] = []
    skipping = False
    for line in markdown.splitlines():
        heading = re.match(r"^(#{2,6})\s+(.*)$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip().lower()
            if title in wanted:
                skipping = True
                skip_level = level
                continue
            if skipping and level <= skip_level:
                skipping = False
        if not skipping:
            out.append(line)
    return "\n".join(out)


def split_title(markdown: str) -> tuple[str, str]:
    """Estrae il primo `# Titolo` e restituisce (titolo, corpo senza titolo)."""
    lines = markdown.splitlines()
    title = ""
    body: list[str] = []
    for i, line in enumerate(lines):
        if not title and line.startswith("# "):
            title = line[2:].strip()
            body = lines[i + 1 :]
            break
    else:
        return "", markdown
    return title, "\n".join(body)


def drop_meta_lines(markdown: str) -> str:
    """Toglie le righe di metadato DM presenti nel preambolo (prima della prima `##`)."""
    out: list[str] = []
    in_preamble = True
    for line in markdown.splitlines():
        if line.startswith("## "):
            in_preamble = False
        if in_preamble and META_LINE_RE.match(line.strip()):
            continue
        out.append(line)
    return "\n".join(out)


def resolve_images(html: str) -> str:
    """Trasforma i path `/immagini/...` del repository in URL `file://` assoluti."""

    def repl(match: re.Match[str]) -> str:
        src = match.group(1)
        if src.startswith(("http://", "https://", "data:", "file://")):
            return match.group(0)
        path = (REPO_ROOT / src.lstrip("/")).resolve()
        return f'src="{path.as_uri()}"'

    return re.sub(r'src="([^"]+)"', repl, html)


def build_css() -> str:
    """Palette e tipografia derivate da tools/pubblicazione/assets/site.css, adattate alla stampa."""
    return """
:root {
  --bg: #12100d;
  --panel: #1a1713;
  --panel-border: #2f2a23;
  --text: #f5efe5;
  --muted: #c4b8a5;
  --accent: #d39c4a;
  --accent-soft: rgba(211, 156, 74, 0.16);
}

/* Margine di pagina a zero: e` l'unico modo per cui Chrome estende lo sfondo scuro
   fino ai bordi del foglio. I margini verticali sono simulati dalle fasce
   `thead`/`tfoot` di `.sheet`, che Chrome ripete e spazia su ogni pagina. */
@page {
  size: A4;
  margin: 0;
}

* { box-sizing: border-box; }

html, body {
  background: #12100d;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

body {
  margin: 0;
  padding: 0 14mm;
  font-family: Georgia, "Liberation Serif", "Noto Serif", "Times New Roman", serif;
  font-size: 11.5pt;
  line-height: 1.6;
  color: var(--text);
}

.sheet {
  width: 100%;
  border-collapse: collapse;
}

.sheet > thead > tr > td,
.sheet > tfoot > tr > td,
.sheet > tbody > tr > td {
  padding: 0;
  border: 0;
  background: transparent;
}

.sheet-margin { height: 14mm; }

p { margin: 0 0 0.85em; orphans: 2; widows: 2; }
strong { color: #ffe9c6; }
a { color: var(--accent); text-decoration: none; }

/* ---- Copertina ---- */

.cover {
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 265mm;
  text-align: center;
  page-break-after: always;
}

.cover-logo {
  width: 100%;
  max-width: 150mm;
  margin: 0 auto 10mm;
  display: block;
}

.cover h1 {
  margin: 0 0 4mm;
  font-size: 30pt;
  line-height: 1.12;
  color: var(--accent);
  letter-spacing: 0.01em;
}

.cover .tagline {
  margin: 0 auto 9mm;
  max-width: 130mm;
  font-size: 12.5pt;
  font-style: italic;
  color: var(--muted);
}

.cover-rule {
  width: 60mm;
  height: 1px;
  margin: 0 auto 9mm;
  background: linear-gradient(90deg, transparent, var(--accent), transparent);
}

.cover-figure {
  margin: 0;
  border: 1px solid var(--panel-border);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.25);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.28);
}

.cover-figure img { display: block; width: 100%; height: auto; }

.cover-figure figcaption {
  padding: 3.5mm 5mm 4mm;
  font-size: 10pt;
  line-height: 1.5;
  color: var(--muted);
}

/* ---- Corpo ---- */

h2 {
  margin: 9mm 0 3mm;
  padding-bottom: 2mm;
  border-bottom: 1px solid var(--panel-border);
  font-size: 17pt;
  line-height: 1.2;
  color: var(--accent);
  page-break-after: avoid;
}

h2:first-child { margin-top: 0; }

h3 {
  margin: 6mm 0 2.5mm;
  font-size: 13.5pt;
  line-height: 1.25;
  color: #e7c48a;
  page-break-after: avoid;
}

ul, ol { margin: 0 0 0.9em; padding-left: 1.25em; }
li { margin-bottom: 0.45em; }

blockquote {
  margin: 5mm 0;
  padding: 4mm 5mm;
  border: 1px solid rgba(211, 156, 74, 0.28);
  border-left: 3px solid var(--accent);
  border-radius: 10px;
  background: var(--accent-soft);
  color: var(--muted);
  page-break-inside: avoid;
}

blockquote p { margin: 0 0 0.5em; }
blockquote p:last-child { margin-bottom: 0; }
blockquote strong { color: var(--accent); }

code {
  padding: 0.1em 0.3em;
  border-radius: 5px;
  background: rgba(255, 255, 255, 0.06);
  font-size: 0.92em;
}

hr {
  margin: 8mm 0;
  border: 0;
  height: 1px;
  background: var(--panel-border);
}

main table {
  width: 100%;
  margin: 4mm 0 6mm;
  border-collapse: collapse;
  font-size: 10.5pt;
  line-height: 1.5;
}

main thead { display: table-header-group; }

main th {
  padding: 2.5mm 3mm;
  text-align: left;
  vertical-align: bottom;
  background: rgba(211, 156, 74, 0.14);
  border-bottom: 1px solid rgba(211, 156, 74, 0.35);
  color: var(--accent);
  font-size: 10.5pt;
  letter-spacing: 0.02em;
}

main td {
  padding: 2.5mm 3mm;
  vertical-align: top;
  border-bottom: 1px solid var(--panel-border);
}

main tbody tr { page-break-inside: avoid; }
main tbody tr:nth-child(even) td { background: rgba(255, 255, 255, 0.025); }

/* Prima colonna stretta (Leva / Sessione) nelle tabelle del documento */
main table td:first-child, main table th:first-child { width: 17%; }
main table.cols-2 td:first-child, main table.cols-2 th:first-child { width: 26%; }
"""


def render_html(title: str, subtitle: str, body_md: str, hero: Path | None,
                hero_caption: str) -> str:
    md = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    body_html = resolve_images(md.render(body_md))

    # Marca le tabelle a due colonne, che vogliono una prima colonna piu` larga.
    def mark_two_columns(match: re.Match[str]) -> str:
        block = match.group(0)
        head = re.search(r"<thead>.*?</thead>", block, re.S)
        if head and len(re.findall(r"<th[ >]", head.group(0))) == 2:
            return block.replace("<table>", '<table class="cols-2">', 1)
        return block

    body_html = re.sub(r"<table>.*?</table>", mark_two_columns, body_html, flags=re.S)

    cover_figure = ""
    if hero is not None:
        caption = f"<figcaption>{hero_caption}</figcaption>" if hero_caption else ""
        cover_figure = (
            f'<figure class="cover-figure"><img src="{hero.resolve().as_uri()}" alt="">'
            f"{caption}</figure>"
        )

    logo = (
        f'<img class="cover-logo" src="{HEADER_LOGO.as_uri()}" alt="La corsa al Nuovo Mondo">'
        if HEADER_LOGO.exists()
        else ""
    )
    tagline = f'<p class="tagline">{subtitle}</p>' if subtitle else ""

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{build_css()}</style>
</head>
<body>
<table class="sheet">
<thead><tr><td><div class="sheet-margin"></div></td></tr></thead>
<tfoot><tr><td><div class="sheet-margin"></div></td></tr></tfoot>
<tbody><tr><td>
<section class="cover">
  {logo}
  <h1>{title}</h1>
  {tagline}
  <div class="cover-rule"></div>
  {cover_figure}
</section>
<main>
{body_html}
</main>
</td></tr></tbody>
</table>
</body>
</html>
"""


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    chrome = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which(
        "chromium-browser"
    )
    if chrome is None:
        sys.exit("Serve Google Chrome o Chromium per generare il PDF.")

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="chrome-pdf-") as profile:
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--no-default-browser-check",
                f"--user-data-dir={profile}",
                "--no-pdf-header-footer",
                f"--print-to-pdf={pdf_path}",
                html_path.as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sorgente", help="File Markdown nel repository (path relativo o assoluto)")
    parser.add_argument("--hero", help="Immagine di copertina (path nel repository)")
    parser.add_argument("--didascalia", default="", help="Didascalia dell'immagine di copertina")
    parser.add_argument("--sottotitolo", default="", help="Sottotitolo in copertina")
    parser.add_argument("--output", help="PDF di destinazione (default: tools/build/pdf/<slug>.pdf)")
    parser.add_argument(
        "--keep-html", action="store_true", help="Conserva l'HTML intermedio accanto al PDF"
    )
    args = parser.parse_args()

    source = Path(args.sorgente)
    if not source.is_absolute():
        source = (REPO_ROOT / source).resolve()
    if not source.is_file():
        sys.exit(f"Sorgente non trovata: {source}")

    strip = json.loads(MANIFEST.read_text(encoding="utf-8")).get("stripSections", [])
    markdown = source.read_text(encoding="utf-8")
    markdown = strip_sections(markdown, strip)
    title, body = split_title(markdown)
    body = drop_meta_lines(body).strip()

    hero = None
    if args.hero:
        hero = Path(args.hero)
        if not hero.is_absolute():
            hero = (REPO_ROOT / hero).resolve()
        if not hero.is_file():
            sys.exit(f"Immagine di copertina non trovata: {hero}")

    html = render_html(title or source.stem, args.sottotitolo, body, hero, args.didascalia)

    output = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR / f"{source.stem}.pdf"
    if not output.is_absolute():
        output = (REPO_ROOT / output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    html_path = output.with_suffix(".html")
    html_path.write_text(html, encoding="utf-8")
    html_to_pdf(html_path, output)
    if not args.keep_html:
        html_path.unlink()

    print(f"PDF generato: {output.relative_to(REPO_ROOT)}")
    print(f"Sezioni rimosse: {', '.join(strip)}")


if __name__ == "__main__":
    main()
