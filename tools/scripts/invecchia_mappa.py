#!/usr/bin/env python3
"""Invecchia il disegno tecnico: fibra della carta, macchie, pieghe, vignettatura."""
import sys
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

rng = np.random.default_rng(1859)
src = sys.argv[1]
dst = sys.argv[2]
LARG = int(sys.argv[3]) if len(sys.argv) > 3 else 2400

img = Image.open(src).convert("RGB")
img = img.resize((LARG, int(LARG * img.height / img.width)), Image.LANCZOS)
W, H = img.size
a = np.asarray(img).astype(np.float32) / 255.0


def rumore(scala, sigma=1.0):
    """Rumore gaussiano sfocato a una data scala, normalizzato in [0,1]."""
    h, w = max(2, H // scala), max(2, W // scala)
    n = rng.normal(0, 1, (h, w)).astype(np.float32)
    im = Image.fromarray(((n * 0.15 + 0.5).clip(0, 1) * 255).astype(np.uint8))
    im = im.resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(sigma))
    v = np.asarray(im).astype(np.float32) / 255.0
    return (v - v.min()) / (v.max() - v.min() + 1e-6)


# ---------------------------------------------------------------- pergamena
fibra = (0.45 * rumore(2, 0.6) + 0.30 * rumore(7, 1.2) +
         0.25 * rumore(28, 2.0))
nuvole = 0.55 * rumore(60, 3.0) + 0.45 * rumore(160, 6.0)

# tinta base della carta: sabbia calda con variazioni
carta = np.empty((H, W, 3), np.float32)
carta[..., 0] = 0.918 - 0.085 * nuvole
carta[..., 1] = 0.855 - 0.105 * nuvole
carta[..., 2] = 0.722 - 0.135 * nuvole
carta *= (0.955 + 0.075 * fibra)[..., None]

# ---------------------------------------------------------------- macchie
macchie = Image.new("L", (W, H), 255)
d = ImageDraw.Draw(macchie)
for _ in range(34):
    cx, cy = rng.uniform(0, W), rng.uniform(0, H)
    r = rng.uniform(W * 0.02, W * 0.13)
    d.ellipse([cx - r, cy - r * rng.uniform(0.5, 1.1),
               cx + r * rng.uniform(0.7, 1.3), cy + r], fill=int(rng.uniform(170, 225)))
# aloni concentrati sui bordi
for _ in range(22):
    lato = rng.integers(0, 4)
    cx = rng.uniform(0, W) if lato < 2 else (0 if lato == 2 else W)
    cy = (0 if lato == 0 else H) if lato < 2 else rng.uniform(0, H)
    r = rng.uniform(W * 0.04, W * 0.16)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=int(rng.uniform(150, 205)))
macchie = macchie.filter(ImageFilter.GaussianBlur(W / 120))
m = np.asarray(macchie).astype(np.float32) / 255.0
m = 0.88 + 0.12 * m
carta *= m[..., None] ** 0.7
carta[..., 0] *= (0.995 + 0.02 * (1 - m))
carta[..., 2] *= (0.93 + 0.07 * m)

# ---------------------------------------------------------------- pieghe
pieghe = np.ones((H, W), np.float32)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
for fx in (W * 0.335, W * 0.668):
    pieghe *= 1.0 - 0.10 * np.exp(-((xx - fx) ** 2) / (2 * (W * 0.0022) ** 2))
    pieghe += 0.05 * np.exp(-((xx - fx - W * 0.004) ** 2) / (2 * (W * 0.0035) ** 2))
for fy in (H * 0.5,):
    pieghe *= 1.0 - 0.09 * np.exp(-((yy - fy) ** 2) / (2 * (H * 0.0028) ** 2))
    pieghe += 0.045 * np.exp(-((yy - fy - H * 0.005) ** 2) / (2 * (H * 0.0045) ** 2))
carta *= pieghe[..., None]

# ---------------------------------------------------------------- inchiostro
# il disegno viene moltiplicato sulla carta: le zone chiare lasciano passare
# la texture, il tratto scuro resta scuro.
ink = np.clip(a * 1.04, 0, 1)        # il disegno resta il padrone dell'immagine
fuso = np.clip(carta * ink * 1.10, 0, 1)

# leggera diffusione dell'inchiostro nella carta
sfum = Image.fromarray((fuso * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(W / 2000))
fuso = 0.86 * fuso + 0.14 * (np.asarray(sfum).astype(np.float32) / 255.0)

# ---------------------------------------------------------------- vignettatura
cx, cy = W / 2, H / 2
r = np.sqrt(((xx - cx) / (W / 2)) ** 2 + ((yy - cy) / (H / 2)) ** 2)
vign = np.clip(1.03 - 0.17 * np.clip(r - 0.62, 0, None) ** 1.4 * 2.2, 0, 1.03)
bordo = np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy]) / (W * 0.045)
vign *= np.clip(0.72 + 0.28 * bordo, 0, 1) ** 0.6
fuso *= vign[..., None]

# ---------------------------------------------------------------- grana finale
grana = rng.normal(0, 0.007, (H, W, 1)).astype(np.float32)
fuso = np.clip(fuso + grana, 0, 1)

# virata seppia leggera
fuso[..., 0] = np.clip(fuso[..., 0] * 1.030, 0, 1)
fuso[..., 2] = np.clip(fuso[..., 2] * 0.955, 0, 1)

Image.fromarray((fuso * 255).astype(np.uint8)).save(dst, optimize=True)
print("scritto", dst, Image.open(dst).size)
