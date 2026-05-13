#!/usr/bin/env python3
"""Normalizza asset sotto immagini/ a JPEG .jpg con lato lungo <= 1920 px e aggiorna i riferimenti nei Markdown."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

REPO_ROOT = Path(__file__).resolve().parent.parent
MAX_LONGEST_SIDE = 1920
JPEG_QUALITY = 85
RASTER_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp"})
EXCLUDE_DIR_NAMES = frozenset({"build", ".git", "node_modules", "__pycache__", ".cursor"})
MD_IMAGE_REF_RE = re.compile(r'(/immagini/[^\s)]+?)\.(png|jpeg|webp)\b', re.IGNORECASE)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Converte/rinomina immagini raster in JPEG .jpg (lato lungo <= 1920) e aggiorna i link nei Markdown."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("immagini")],
        help="File o directory da processare (default: immagini/).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra le azioni senza modificare file.",
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Non aggiornare i riferimenti nei file .md.",
    )
    return parser.parse_args()


def resolve_paths(paths: list[Path]) -> list[Path]:
    resolved: list[Path] = []
    for p in paths:
        rp = (REPO_ROOT / p).resolve() if not p.is_absolute() else p.resolve()
        if not rp.exists():
            raise FileNotFoundError(f"Percorso non trovato: {p}")
        resolved.append(rp)
    return resolved


def iter_raster_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for base in paths:
        if base.is_file():
            if base.suffix.lower() in RASTER_SUFFIXES:
                files.append(base)
        else:
            for p in base.rglob("*"):
                if p.is_file() and p.suffix.lower() in RASTER_SUFFIXES:
                    files.append(p)
    return sorted(set(files), key=lambda x: x.as_posix())


def is_under_repo(path: Path) -> bool:
    try:
        path.relative_to(REPO_ROOT)
        return True
    except ValueError:
        return False


def should_skip_markdown(path: Path) -> bool:
    return any(part in EXCLUDE_DIR_NAMES for part in path.parts)


def to_rgb_white_background(im: Image.Image) -> Image.Image:
    if im.mode in ("RGBA", "LA"):
        rgba = im.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if im.mode == "P":
        rgba = im.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if im.mode != "RGB":
        return im.convert("RGB")
    return im


def process_one_image(path: Path, *, dry_run: bool) -> str:
    """
    Ritorna una etichetta di esito: ok_skip, renamed_jpeg, converted, reencoded_jpeg.
    """
    if not is_under_repo(path):
        raise ValueError(f"File fuori dal repository: {path}")

    suffix = path.suffix.lower()
    dest_jpg = path.with_suffix(".jpg")

    with Image.open(path) as im:
        im.load()
        w, h = im.size
        longest = max(w, h)

        if suffix == ".jpg" and longest <= MAX_LONGEST_SIDE:
            return "ok_skip"

        if suffix == ".jpeg" and longest <= MAX_LONGEST_SIDE:
            if dry_run:
                return "renamed_jpeg"
            dest_jpg.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(path), str(dest_jpg))
            return "renamed_jpeg"

        im_rgb = to_rgb_white_background(im)
        im_work = im_rgb.copy()
        if longest > MAX_LONGEST_SIDE:
            im_work.thumbnail((MAX_LONGEST_SIDE, MAX_LONGEST_SIDE), Image.Resampling.LANCZOS)

        if dry_run:
            if suffix in (".jpg", ".jpeg") and longest > MAX_LONGEST_SIDE:
                return "reencoded_jpeg"
            return "converted"

        dest_jpg.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(suffix=".jpg", dir=dest_jpg.parent)
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
            os.replace(tmp_path, dest_jpg)
        except BaseException:
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        if path.resolve() != dest_jpg.resolve() and path.exists():
            path.unlink()

        if suffix in (".jpg", ".jpeg") and longest > MAX_LONGEST_SIDE:
            return "reencoded_jpeg"
        return "converted"


def update_markdown_refs(*, dry_run: bool) -> int:
    """Sostituisce /immagini/... .png|.jpeg|.webp con .jpg. Ritorna il numero di file .md modificati."""
    changed_files = 0
    for md_path in sorted(REPO_ROOT.rglob("*.md"), key=lambda p: p.as_posix()):
        if not is_under_repo(md_path) or should_skip_markdown(md_path):
            continue
        try:
            text = md_path.read_text(encoding="utf-8")
        except OSError:
            continue

        def repl(m: re.Match[str]) -> str:
            return f"{m.group(1)}.jpg"

        new_text, n = MD_IMAGE_REF_RE.subn(repl, text)
        if n == 0 or new_text == text:
            continue
        if dry_run:
            print(f"  [dry-run] aggiornerebbe {n} riferimento/i in {md_path.relative_to(REPO_ROOT)}")
        else:
            md_path.write_text(new_text, encoding="utf-8")
        changed_files += 1
    return changed_files


def main() -> None:
    args = parse_args()
    if not HAS_PILLOW:
        print("Errore: Pillow non installato. pip install -r scripts/requirements-public-site.txt", file=sys.stderr)
        sys.exit(1)

    try:
        bases = resolve_paths(list(args.paths))
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)

    raster_files = iter_raster_files(bases)
    stats = {
        "ok_skip": 0,
        "renamed_jpeg": 0,
        "converted": 0,
        "reencoded_jpeg": 0,
    }

    if args.dry_run:
        print("Modalità dry-run: nessun file verrà modificato.\n")

    for img_path in raster_files:
        rel = img_path.relative_to(REPO_ROOT)
        try:
            outcome = process_one_image(img_path, dry_run=args.dry_run)
        except Exception as exc:
            print(f"Errore su {rel}: {exc}", file=sys.stderr)
            sys.exit(1)
        stats[outcome] = stats.get(outcome, 0) + 1
        if args.dry_run and outcome != "ok_skip":
            print(f"  {rel}: {outcome}")
        elif not args.dry_run and outcome != "ok_skip":
            print(f"  {rel} -> {outcome}")

    md_changed = 0
    if not args.no_markdown:
        md_changed = update_markdown_refs(dry_run=args.dry_run)

    print("\nRiepilogo:")
    print(f"  gia` JPEG .jpg conformi (skip): {stats['ok_skip']}")
    print(f"  rinominati .jpeg -> .jpg (senza ricompressione): {stats['renamed_jpeg']}")
    print(f"  convertiti da PNG/WebP (o simili): {stats['converted']}")
    print(f"  JPEG ricodificati (lato lungo > {MAX_LONGEST_SIDE}): {stats['reencoded_jpeg']}")
    print(f"  file Markdown aggiornati: {md_changed}")


if __name__ == "__main__":
    main()
