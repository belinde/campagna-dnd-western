from __future__ import annotations

import html
import shutil
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore[misc, assignment]

from public_site.constants import (
    HAS_PILLOW,
    IMAGE_RE,
    OG_IMAGE_IN_PUBLIC_MD_RE,
    OG_IMAGE_IN_SALIENT_HTML_RE,
    PUBBLICAZIONE_ASSETS_DIR,
    REPO_ROOT,
    THUMB_JPEG_QUALITY,
    THUMB_MAX_EDGE,
    THUMB_PORTRAIT_H,
    THUMB_PORTRAIT_W,
)


def thumb_file_exists(output_dir: Path, og_image: str | None) -> bool:
    if not og_image or not HAS_PILLOW:
        return False
    try:
        rel = og_image.lstrip("/")
        thumb_rel = thumb_relative_path_jpeg(rel)
        return (output_dir / thumb_rel).is_file()
    except ValueError:
        return False


def first_image_path_from_markdown(markdown_text: str) -> str | None:
    match = IMAGE_RE.search(markdown_text)
    return match.group(2) if match else None


def thumb_path_for_catalog(og_path: str | None, output_dir: Path) -> str | None:
    if not og_path or not thumb_file_exists(output_dir, og_path):
        return None
    return og_path_to_thumb_route(og_path)


def is_personaggi_portrait_image(asset_relative_path: str) -> bool:
    parts = Path(asset_relative_path).parts
    return len(parts) >= 2 and parts[0] == "immagini" and parts[1] == "personaggi"


def thumb_resize_cover_portrait(im_rgb: Image.Image, target_w: int, target_h: int) -> Image.Image:
    """Ridimensiona e ritaglia in un riquadro verticale target_w x target_h (in alto: scarta il basso)."""
    w, h = im_rgb.size
    tr = target_w / target_h
    sr = w / h
    if sr > tr:
        new_h = target_h
        new_w = max(1, int(round(w * target_h / h)))
        resized = im_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max(0, (new_w - target_w) // 2)
        return resized.crop((left, 0, left + target_w, target_h))
    new_w = target_w
    new_h = max(1, int(round(h * target_w / w)))
    resized = im_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return resized.crop((0, 0, target_w, target_h))


def thumb_cover_square_top(im_rgb: Image.Image, size: int) -> Image.Image:
    """Copre un quadrato size×size ritagliando dall'alto (per sorgenti verticali h > w)."""
    w, h = im_rgb.size
    new_w = size
    new_h = max(1, int(round(h * size / w)))
    resized = im_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
    if new_h < size:
        new_h = size
        new_w = max(1, int(round(w * size / h)))
        resized = im_rgb.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max(0, (new_w - size) // 2)
        return resized.crop((left, 0, left + size, size))
    return resized.crop((0, 0, size, size))


def thumb_relative_path_jpeg(asset_relative_path: str) -> str:
    """immagini/foo/bar.png -> immagini/thumbs/foo/bar.jpg"""
    path = Path(asset_relative_path)
    if not path.parts or path.parts[0] != "immagini":
        raise ValueError(f"Path immagine non valido: {asset_relative_path}")
    rest = Path(*path.parts[1:]).with_suffix(".jpg")
    return (Path("immagini") / "thumbs" / rest).as_posix()


def og_path_to_thumb_route(og_image: str) -> str:
    rel = og_image.lstrip("/")
    return "/" + thumb_relative_path_jpeg(rel)


def write_thumbnail_for_asset(asset_relative_path: str, output_dir: Path) -> bool:
    """Genera JPEG thumb sotto immagini/thumbs/... Ritorna False se Pillow assente o errore."""
    if not HAS_PILLOW:
        return False
    source_file = REPO_ROOT / asset_relative_path
    if not source_file.exists():
        return False
    thumb_rel = thumb_relative_path_jpeg(asset_relative_path)
    dest = output_dir / thumb_rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(source_file) as im:
            if im.mode in ("RGBA", "P"):
                rgba = im.convert("RGBA")
                background = Image.new("RGB", rgba.size, (255, 255, 255))
                background.paste(rgba, mask=rgba.split()[3])
                im_rgb = background
            elif im.mode != "RGB":
                im_rgb = im.convert("RGB")
            else:
                im_rgb = im
            if is_personaggi_portrait_image(asset_relative_path):
                im_rgb = thumb_resize_cover_portrait(im_rgb, THUMB_PORTRAIT_W, THUMB_PORTRAIT_H)
            else:
                pw, ph = im_rgb.size
                if ph > pw:
                    im_rgb = thumb_cover_square_top(im_rgb, THUMB_MAX_EDGE)
                else:
                    im_rgb.thumbnail((THUMB_MAX_EDGE, THUMB_MAX_EDGE), Image.Resampling.LANCZOS)
            im_rgb.save(dest, format="JPEG", quality=THUMB_JPEG_QUALITY, optimize=True)
        return True
    except OSError:
        return False


def render_salient_media_card_html(alt: str, asset_path: str, caption_md: str | None) -> str:
    alt_esc = html.escape(alt)
    src_liquid = f"{{{{ '{asset_path}' | relative_url }}}}"
    caption_block = ""
    if caption_md:
        caption_block = (
            f'\n  <figcaption class="salient-media-card__caption" markdown="1">\n\n'
            f"{caption_md.strip()}\n\n"
            f"  </figcaption>"
        )
    return (
        f'<figure class="salient-media-card">\n'
        f'  <div class="salient-media-card__media card-media-zoomable">\n'
        f'    <img src="{src_liquid}" alt="{alt_esc}" loading="lazy" decoding="async">\n'
        f"  </div>{caption_block}\n"
        f"</figure>"
    )


def first_og_image_path_from_body(markdown_text: str) -> str | None:
    """Primo path immagine nel corpo pubblicato (markdown o card salient HTML)."""
    match = OG_IMAGE_IN_PUBLIC_MD_RE.search(markdown_text)
    if match:
        return match.group(1)
    match = OG_IMAGE_IN_SALIENT_HTML_RE.search(markdown_text)
    return match.group(1) if match else None


def copy_asset(relative_asset_path: str, output_dir: Path) -> None:
    source_path = REPO_ROOT / relative_asset_path
    if not source_path.exists():
        raise FileNotFoundError(f"Asset referenziato ma non trovato: {relative_asset_path}")
    destination = output_dir / relative_asset_path
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_path, destination)


def copy_pubblicazione_assets(output_dir: Path) -> None:
    """Copia byte-per-byte i file in tools/pubblicazione/assets/ senza generare thumbnail."""
    if not PUBBLICAZIONE_ASSETS_DIR.is_dir():
        raise FileNotFoundError(
            "Manca la cartella tools/pubblicazione/assets/: contiene gli asset statici del sito pubblico "
            "che non devono essere processati dalla pipeline immagini/."
        )
    if not (PUBBLICAZIONE_ASSETS_DIR / "header.png").is_file():
        raise FileNotFoundError(
            "Manca tools/pubblicazione/assets/header.png (logo intestazione del sito, PNG con trasparenza)."
        )
    if not (PUBBLICAZIONE_ASSETS_DIR / "site.css").is_file():
        raise FileNotFoundError(
            "Manca tools/pubblicazione/assets/site.css (foglio di stile del sito pubblico)."
        )
    if not (PUBBLICAZIONE_ASSETS_DIR / "site.js").is_file():
        raise FileNotFoundError(
            "Manca tools/pubblicazione/assets/site.js (filtri hub PNG del sito pubblico)."
        )
    if not (PUBBLICAZIONE_ASSETS_DIR / "prompt-page.js").is_file():
        raise FileNotFoundError(
            "Manca tools/pubblicazione/assets/prompt-page.js (Generatore prompt del sito pubblico)."
        )
    dest_root = output_dir / "assets"
    dest_root.mkdir(parents=True, exist_ok=True)
    for path in sorted(PUBBLICAZIONE_ASSETS_DIR.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file():
            continue
        rel = path.relative_to(PUBBLICAZIONE_ASSETS_DIR)
        dest = dest_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
