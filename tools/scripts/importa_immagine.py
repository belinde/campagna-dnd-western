#!/usr/bin/env python3
"""Importa un asset immagine nel repository: converte in JPEG .jpg, ridimensiona se necessario, sposta e rimuove la sorgente.

Uso:
    python3 tools/scripts/importa_immagine.py path/origine.png path/destinazione.jpg

Il file sorgente viene convertito in JPEG (qualità 85, progressive), ridimensionato se il lato
lungo supera 1920 px, salvato nella destinazione e la sorgente viene eliminata.

Se la destinazione esiste già, lo script si interrompe con errore (modalità additiva: non
sovrascrivere asset esistenti senza conferma esplicita).
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from campagna_paths import repo_root

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

REPO_ROOT = repo_root()
MAX_LONGEST_SIDE = 1920
JPEG_QUALITY = 85


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Importa un'immagine nel repository: converte in JPEG, ridimensiona e sposta."
    )
    parser.add_argument(
        "origine",
        type=Path,
        help="Path del file immagine sorgente (PNG, JPEG, WebP).",
    )
    parser.add_argument(
        "destinazione",
        type=Path,
        help="Path di destinazione nel repository (deve terminare in .jpg).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sovrascrive la destinazione se esiste già (modalità sostituzione).",
    )
    parser.add_argument(
        "--keep-source",
        action="store_true",
        help="Non eliminare il file sorgente dopo l'import.",
    )
    return parser.parse_args()


def resolve_path(p: Path) -> Path:
    """Risolve un path relativo rispetto alla root del repo."""
    if p.is_absolute():
        return p.resolve()
    return (REPO_ROOT / p).resolve()


def to_rgb_white_background(im: Image.Image) -> Image.Image:
    """Converte in RGB appiattendo eventuale trasparenza su fondo bianco."""
    if im.mode in ("RGBA", "LA", "P"):
        rgba = im.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if im.mode != "RGB":
        return im.convert("RGB")
    return im


def main() -> None:
    args = parse_args()

    if not HAS_PILLOW:
        print(
            "Errore: Pillow non installato. pip install Pillow",
            file=sys.stderr,
        )
        sys.exit(1)

    origine = resolve_path(args.origine)
    destinazione = resolve_path(args.destinazione)

    # --- Validazioni ---
    if not origine.exists():
        print(f"Errore: file sorgente non trovato: {origine}", file=sys.stderr)
        sys.exit(1)

    if not origine.is_file():
        print(f"Errore: il percorso sorgente non è un file: {origine}", file=sys.stderr)
        sys.exit(1)

    if destinazione.suffix.lower() != ".jpg":
        print(
            f"Errore: la destinazione deve terminare in .jpg (ricevuto: {destinazione.suffix})",
            file=sys.stderr,
        )
        sys.exit(1)

    if destinazione.exists() and not args.force:
        print(
            f"Errore: la destinazione esiste già: {destinazione}\n"
            "Usa --force per sovrascrivere (modalità sostituzione).",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Apertura e conversione ---
    try:
        with Image.open(origine) as im:
            im.load()
            w, h = im.size
            longest = max(w, h)

            # Caso speciale: JPEG già conforme, solo rinomina/sposta
            is_jpeg_source = origine.suffix.lower() in (".jpg", ".jpeg")
            if is_jpeg_source and longest <= MAX_LONGEST_SIDE and im.mode == "RGB":
                # Sposta senza ricompressione
                destinazione.parent.mkdir(parents=True, exist_ok=True)
                if origine.resolve() != destinazione.resolve():
                    import shutil
                    shutil.copy2(str(origine), str(destinazione))
                    if not args.keep_source:
                        origine.unlink()
                print(f"OK: {origine.name} -> {destinazione.relative_to(REPO_ROOT)} (spostato senza ricompressione)")
                print(f"   Dimensioni: {w}x{h} px")
                return

            # Conversione completa
            im_rgb = to_rgb_white_background(im)
            im_work = im_rgb.copy()

            resized = False
            if longest > MAX_LONGEST_SIDE:
                im_work.thumbnail((MAX_LONGEST_SIDE, MAX_LONGEST_SIDE), Image.Resampling.LANCZOS)
                resized = True

    except Exception as exc:
        print(f"Errore nell'apertura dell'immagine: {exc}", file=sys.stderr)
        sys.exit(1)

    # --- Salvataggio ---
    destinazione.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(suffix=".jpg", dir=destinazione.parent)
    os.close(tmp_fd)
    tmp_path = Path(tmp_name)

    try:
        im_work.save(
            tmp_path,
            format="JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
            progressive=True,
        )
        os.replace(tmp_path, destinazione)
    except BaseException:
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    # --- Pulizia sorgente ---
    if not args.keep_source and origine.resolve() != destinazione.resolve():
        origine.unlink()

    # --- Report ---
    final_w, final_h = im_work.size
    rel_dest = destinazione.relative_to(REPO_ROOT)
    actions = []
    if origine.suffix.lower() != ".jpg":
        actions.append(f"convertito da {origine.suffix.upper()}")
    if resized:
        actions.append(f"ridimensionato da {w}x{h} a {final_w}x{final_h}")
    if not args.keep_source:
        actions.append("sorgente eliminata")

    print(f"OK: {origine.name} -> {rel_dest}")
    print(f"   Dimensioni finali: {final_w}x{final_h} px | JPEG q{JPEG_QUALITY} progressive")
    if actions:
        print(f"   Azioni: {'; '.join(actions)}")


if __name__ == "__main__":
    main()
