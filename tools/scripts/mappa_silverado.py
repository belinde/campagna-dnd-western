#!/usr/bin/env python3
"""Genera il disegno tecnico SVG della mappa di Silverado.

Pianta con leggero rilievo: tetti a due falde, ombre a sud-est, tratto
irregolare per simulare l'inchiostro a mano. L'invecchiamento (pergamena,
macchie, pieghe, vignettatura) si applica dopo, sul raster.

Catena completa:

    python3 tools/scripts/mappa_silverado.py immagini/luoghi/silverado-mappa.svg
    inkscape --export-type=png --export-filename=/tmp/ink.png --export-width=3600 \\
        immagini/luoghi/silverado-mappa.svg
    python3 tools/scripts/invecchia_mappa.py /tmp/ink.png /tmp/anticata.png 2400

L'ultimo passaggio va poi ridotto a tavolozza per contenere il peso del PNG.
Il seme casuale e` fisso: rigenerando si ottiene la stessa mappa.
"""
import math
import random

random.seed(1889)

W, H = 2400, 1600
out = []


# ---------------------------------------------------------------- utilita`
def jit(a=2.2):
    return random.uniform(-a, a)


def pt(x, y, a=2.2):
    return f"{x + jit(a):.1f},{y + jit(a):.1f}"


def poly(points, cls, a=2.0, extra=""):
    d = " ".join(pt(x, y, a) for x, y in points)
    out.append(f'<polygon class="{cls}" points="{d}" {extra}/>')


def line(x1, y1, x2, y2, cls, a=1.6):
    out.append(f'<line class="{cls}" x1="{x1 + jit(a):.1f}" y1="{y1 + jit(a):.1f}" '
               f'x2="{x2 + jit(a):.1f}" y2="{y2 + jit(a):.1f}"/>')


def rot(px, py, cx, cy, ang):
    r = math.radians(ang)
    dx, dy = px - cx, py - cy
    return cx + dx * math.cos(r) - dy * math.sin(r), cy + dx * math.sin(r) + dy * math.cos(r)


def rect_pts(x, y, w, h, ang=0):
    cx, cy = x + w / 2, y + h / 2
    return [rot(px, py, cx, cy, ang) for px, py in
            [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]]


# ------------------------------------------------------------- primitive
def edificio(x, y, w, h, ang=0, tipo="grezzo", camino=False):
    """Casa vista dall'alto: ombra, due falde, assi del tetto, cornicione."""
    p = rect_pts(x, y, w, h, ang)
    # ombra verso sud-est
    poly([(px + 9, py + 9) for px, py in p], "ombra", 1.2)
    falda_a = "tetto-a" if tipo != "verniciato" else "tetto-a-v"
    falda_b = "tetto-b" if tipo != "verniciato" else "tetto-b-v"
    lungo_x = w >= h
    cx, cy = x + w / 2, y + h / 2
    if lungo_x:  # colmo orizzontale
        m1 = rot(x, cy, cx, cy, ang)
        m2 = rot(x + w, cy, cx, cy, ang)
        poly([p[0], p[1], m2, m1], falda_a, 1.4)
        poly([m1, m2, p[2], p[3]], falda_b, 1.4)
        n = max(2, int(w // 13))
        for i in range(1, n):
            t = x + w * i / n
            a1 = rot(t, y, cx, cy, ang)
            a2 = rot(t, y + h, cx, cy, ang)
            line(a1[0], a1[1], a2[0], a2[1], "assi", 0.7)
    else:  # colmo verticale
        m1 = rot(cx, y, cx, cy, ang)
        m2 = rot(cx, y + h, cx, cy, ang)
        poly([p[0], m1, m2, p[3]], falda_a, 1.4)
        poly([m1, p[1], p[2], m2], falda_b, 1.4)
        n = max(2, int(h // 13))
        for i in range(1, n):
            t = y + h * i / n
            a1 = rot(x, t, cx, cy, ang)
            a2 = rot(x + w, t, cx, cy, ang)
            line(a1[0], a1[1], a2[0], a2[1], "assi", 0.7)
    line(m1[0], m1[1], m2[0], m2[1], "colmo", 1.0)
    poly(p, "muro", 1.4)
    if camino:
        c = rot(x + w * 0.72, y + h * 0.28, cx, cy, ang)
        poly([(c[0] - 4, c[1] - 4), (c[0] + 4, c[1] - 4),
              (c[0] + 4, c[1] + 4), (c[0] - 4, c[1] + 4)], "camino", 0.8)


def tenda(x, y, s=22, ang=0):
    p = [rot(px, py, x, y, ang) for px, py in
         [(x - s * 0.62, y + s * 0.42), (x, y - s * 0.45),
          (x + s * 0.62, y + s * 0.42)]]
    poly([(px + 6, py + 6) for px, py in p], "ombra", 1.0)
    poly(p, "tenda", 1.0)
    line(p[1][0], p[1][1], (p[0][0] + p[2][0]) / 2, (p[0][1] + p[2][1]) / 2, "assi", 0.6)


def carro(x, y, ang=0, telo=True):
    w, h = 34, 17
    p = rect_pts(x - w / 2, y - h / 2, w, h, ang)
    poly([(px + 5, py + 5) for px, py in p], "ombra", 1.0)
    poly(p, "carro-telo" if telo else "carro", 1.0)
    for f in (0.18, 0.82):
        a = rot(x - w / 2 + w * f, y - h / 2 - 3, x, y, ang)
        b = rot(x - w / 2 + w * f, y + h / 2 + 3, x, y, ang)
        out.append(f'<circle class="ruota" cx="{a[0]:.1f}" cy="{a[1]:.1f}" r="4"/>')
        out.append(f'<circle class="ruota" cx="{b[0]:.1f}" cy="{b[1]:.1f}" r="4"/>')


def recinto(points, chiuso=True):
    pts = points + [points[0]] if chiuso else points
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        line(x1, y1, x2, y2, "staccionata", 1.2)
        d = math.hypot(x2 - x1, y2 - y1)
        n = max(1, int(d // 26))
        for k in range(n + 1):
            t = k / n
            px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            out.append(f'<circle class="palo" cx="{px + jit(1):.1f}" cy="{py + jit(1):.1f}" r="2.4"/>')


def strada(points, larg=90, cls="strada"):
    """Banda di terra battuta con solchi di ruota."""
    left, right = [], []
    for i, (x, y) in enumerate(points):
        if i == 0:
            dx, dy = points[1][0] - x, points[1][1] - y
        elif i == len(points) - 1:
            dx, dy = x - points[i - 1][0], y - points[i - 1][1]
        else:
            dx, dy = points[i + 1][0] - points[i - 1][0], points[i + 1][1] - points[i - 1][1]
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        left.append((x + nx * larg / 2, y + ny * larg / 2))
        right.append((x - nx * larg / 2, y - ny * larg / 2))
    poly(left + right[::-1], cls, 3.0)
    # solchi di ruota
    for off in (-0.55, -0.2, 0.2, 0.55):
        pts = []
        for i, (x, y) in enumerate(points):
            lx, ly = left[i]
            rx, ry = right[i]
            mx, my = (lx + rx) / 2, (ly + ry) / 2
            pts.append((mx + (lx - mx) * off * 2 * 0.5 * 2, my + (ly - my) * off * 2 * 0.5 * 2))
        d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        out.append(f'<path class="solco" d="{d}"/>')


def ferrovia(points):
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    out.append(f'<path class="massicciata" d="{d}"/>')
    # traversine
    tot = 0
    for i in range(len(points) - 1):
        (x1, y1), (x2, y2) = points[i], points[i + 1]
        seg = math.hypot(x2 - x1, y2 - y1)
        n = int(seg // 17)
        for k in range(n):
            t = k / n
            px, py = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
            dx, dy = (x2 - x1) / seg, (y2 - y1) / seg
            nx, ny = -dy, dx
            line(px + nx * 11, py + ny * 11, px - nx * 11, py - ny * 11, "traversina", 0.8)
        tot += seg
    out.append(f'<path class="rotaia" d="{d}" transform="translate(0,-5)"/>')
    out.append(f'<path class="rotaia" d="{d}" transform="translate(0,5)"/>')


def palo_telegrafo(x, y):
    line(x, y, x, y - 14, "palo-tel", 0.6)
    line(x - 7, y - 12, x + 7, y - 12, "palo-tel", 0.6)


def etichetta(x, y, testo, cls="et", anchor="middle", dy=0):
    out.append(f'<text class="{cls}" x="{x}" y="{y + dy}" text-anchor="{anchor}">{testo}</text>')


# ============================================================ TERRENO
out.append('<rect class="suolo" x="0" y="0" width="2400" height="1600"/>')

# macchie di terreno piu` chiaro / cespugli
for _ in range(190):
    x, y = random.uniform(40, 2360), random.uniform(40, 1560)
    r = random.uniform(9, 34)
    out.append(f'<ellipse class="chiazza" cx="{x:.0f}" cy="{y:.0f}" '
               f'rx="{r:.0f}" ry="{r * random.uniform(0.4, 0.8):.0f}"/>')
for _ in range(240):
    x, y = random.uniform(40, 2360), random.uniform(40, 1560)
    out.append(f'<path class="sterpo" d="M{x:.0f},{y:.0f} l-4,-7 M{x:.0f},{y:.0f} l2,-8 '
               f'M{x:.0f},{y:.0f} l6,-6"/>')

# ---- colline d'argento, bordo occidentale
collina = [(0, 120), (110, 150), (185, 230), (150, 340), (205, 430), (160, 560),
           (215, 690), (150, 820), (205, 950), (140, 1090), (200, 1220),
           (130, 1360), (175, 1480), (0, 1560)]
poly(collina + [(0, 1560), (0, 120)], "collina", 2.5)
for cy in range(200, 1500, 118):
    line(50, cy, 96, cy - 26, "crinale", 1.2)
    line(96, cy - 26, 140, cy + 4, "crinale", 1.2)
for sx, sy in [(92, 300), (118, 640), (86, 980), (128, 1290)]:
    poly([(sx - 11, sy + 8), (sx, sy - 11), (sx + 11, sy + 8)], "scavo", 1.0)
    line(sx - 11, sy + 8, sx + 11, sy + 8, "crinale", 0.8)
etichetta(112, 760, "COLLINE D'ARGENTO", "et-regione",
          anchor="middle")
out[-1] = out[-1].replace('<text', '<text transform="rotate(-90 112 760)"', 1)

# ============================================================ STRADE
via_maestra = [(150, 858), (430, 846), (760, 838), (1080, 862), (1340, 908), (1560, 962)]
strada(via_maestra, 96)

via_nord = [(470, 842), (430, 700), (352, 520), (268, 350), (196, 210), (150, 90)]
strada(via_nord, 58)

via_recinti = [(1196, 894), (1236, 1056), (1330, 1196), (1452, 1258)]
strada(via_recinti, 52)

via_sud = [(360, 900), (420, 1070), (470, 1250), (520, 1420)]
strada(via_sud, 44)

vicolo = [(1156, 872), (1176, 990), (1196, 1104)]
strada(vicolo, 36)

# ============================================================ FERROVIA
bin_pts = [(2400, 1010), (2130, 1000), (1900, 996), (1700, 1000), (1596, 1006)]
ferrovia(bin_pts)
for i in range(9):
    palo_telegrafo(1700 + i * 78, 946 + i * 2)
# fine corsa: respingente
line(1590, 988, 1590, 1026, "respingente", 0.8)
line(1596, 988, 1596, 1026, "respingente", 0.8)

# ============================================================ PIAZZALE E SCALO
recinto([(1430, 900), (1800, 888), (1812, 1150), (1436, 1162)])
# cataste di traversine
for i in range(5):
    x = 1470 + i * 26
    for k in range(4):
        line(x, 1078 + k * 5, x + 20, 1078 + k * 5, "catasta", 0.6)
for i in range(4):
    x = 1620 + i * 24
    for k in range(3):
        line(x, 1110 + k * 5, x + 18, 1110 + k * 5, "catasta", 0.6)
# gru a mano
out.append('<circle class="gru" cx="1720" cy="1042" r="15"/>')
line(1720, 1042, 1772, 1006, "gru-braccio", 0.7)
line(1772, 1006, 1772, 1034, "assi", 0.7)
# magazzini dello scalo
edificio(1452, 906, 118, 52, 0, "magazzino")
edificio(1600, 900, 92, 46, 0, "magazzino")
edificio(1710, 898, 86, 44, 0, "magazzino")
edificio(1448, 1058, 0.1, 0.1)  # no-op per mantenere ordine casuale stabile

# ============================================================ RECINTI DEL BESTIAME
recinto([(1470, 1218), (1830, 1198), (1856, 1392), (1492, 1414)])
recinto([(1560, 1232), (1690, 1226), (1698, 1330), (1568, 1336)])
recinto([(1256, 1250), (1420, 1240), (1432, 1392), (1268, 1402)])
for _ in range(9):
    x = random.uniform(1500, 1820)
    y = random.uniform(1240, 1380)
    out.append(f'<ellipse class="bestia" cx="{x:.0f}" cy="{y:.0f}" rx="9" ry="5"/>')
    line(x - 7, y + 4, x - 7, y + 10, "assi", 0.5)
    line(x + 7, y + 4, x + 7, y + 10, "assi", 0.5)
edificio(1548, 1466, 130, 54, -2, "magazzino")  # fienile
edificio(1462, 1440, 96, 44, 1, "grezzo")       # scuderia sud

# ============================================================ I TRE ISOLATI VERNICIATI
# fila nord della via maestra, centro citta`
isolati = [
    # (x, y, w, h, ang, etichetta, dy_label)
    (742, 690, 104, 74, 0, "Ufficio dello\nSceriffo"),
    (876, 676, 150, 96, 0, "Casa dei Registri"),
    (1052, 672, 96, 78, 0, "Banca Federale"),
    (1176, 676, 76, 62, 0, "Telegrafo"),
    (1278, 690, 82, 58, 1, "Compagnia\ndelle Cinghie"),
    (884, 556, 118, 58, 0, "Albergo del\nCapolinea"),
    (1032, 552, 74, 52, 0, "Stamperia"),
    (1128, 556, 62, 46, 0, "Avv."),
    (1206, 554, 62, 46, 0, "Avv."),
    (1288, 552, 84, 52, 0, "Medico"),
    (760, 556, 92, 54, 0, "Gilda dei\nMinatori"),
]
for x, y, w, h, a, lab in isolati:
    edificio(x, y, w, h, a, "verniciato", camino=True)

# Albo della Casa dei Registri
line(944, 782, 944, 806, "assi", 0.6)
line(966, 782, 966, 806, "assi", 0.6)
poly([(936, 764), (974, 764), (974, 786), (936, 786)], "albo", 0.8)

# ============================================================ OSTERIE
osterie = [
    (1376, 906, 128, 76, 0, "Osteria del Capolinea"),
    (640, 690, 88, 58, 0, None),
    (486, 692, 78, 54, -1, None),
    (952, 930, 96, 60, 0, None),
    (700, 936, 82, 56, 1, None),
    (330, 700, 76, 52, 0, None),
]
for x, y, w, h, a, lab in osterie:
    edificio(x, y, w, h, a, "verniciato", camino=True)
    out.append(f'<circle class="segno-osteria" cx="{x + w / 2:.0f}" cy="{y + h / 2:.0f}" r="9"/>')
    line(x + w / 2, y + h / 2 - 9, x + w / 2, y + h / 2 + 9, "segno-l", 0.5)

# ============================================================ CITTA` DI LEGNO CRUDO
random.seed(4411)
grezzi = []
# fila nord ovest
for i in range(9):
    grezzi.append((200 + i * 62, 700 + random.uniform(-14, 14),
                   random.uniform(40, 56), random.uniform(32, 44), random.uniform(-4, 4)))
# fila sud della via maestra (lato citta`)
for i in range(13):
    grezzi.append((190 + i * 74, 946 + random.uniform(-18, 22),
                   random.uniform(42, 62), random.uniform(32, 46), random.uniform(-5, 5)))
# seconda fila sud
for i in range(11):
    grezzi.append((240 + i * 78, 1046 + random.uniform(-16, 20),
                   random.uniform(38, 58), random.uniform(30, 42), random.uniform(-6, 6)))
# grappolo est, dietro i saloon
for i in range(7):
    grezzi.append((1080 + i * 66, 1006 + random.uniform(-20, 24),
                   random.uniform(40, 56), random.uniform(30, 42), random.uniform(-5, 5)))
# grappolo nord est
for i in range(6):
    grezzi.append((1400 + i * 70, 748 + random.uniform(-22, 18),
                   random.uniform(42, 60), random.uniform(30, 44), random.uniform(-4, 4)))
for x, y, w, h, a in grezzi:
    edificio(x, y, w, h, a, "grezzo", camino=random.random() < 0.35)

# dormitori (edifici lunghi e stretti) presso lo scalo
for i in range(4):
    edificio(1520 + i * 8, 700 + i * 46, 176, 34, -1, "lungo")
etichetta(1608, 690, "Dormitori delle squadre", "et-piccola")

# baracche halfling e gnome, margine nord est
for i in range(9):
    edificio(1860 + (i % 3) * 58, 700 + (i // 3) * 48, 44, 30,
             random.uniform(-6, 6), "grezzo")
etichetta(1928, 688, "Baracche delle squadre", "et-piccola")

# fucina
edificio(628, 962, 74, 52, 0, "grezzo", camino=True)
out.append('<path class="fumo" d="M676,952 c-10,-22 12,-30 2,-52 c-8,-18 10,-26 4,-44"/>')

# scuderie e maniscalco
edificio(1004, 1042, 132, 56, -1, "lungo")
recinto([(986, 1112), (1160, 1102), (1168, 1178), (994, 1188)])

# magazzini e depositi del minerale, lato ovest
edificio(330, 614, 128, 46, 2, "magazzino")
edificio(346, 522, 110, 44, -1, "magazzino")
etichetta(470, 512, "Depositi del minerale", "et-piccola")

# ============================================================ TENDOPOLI E PIAZZALE DEI CARRI
random.seed(77)
for i in range(16):
    tenda(220 + (i % 4) * 74 + random.uniform(-12, 12),
          1140 + (i // 4) * 84 + random.uniform(-14, 14),
          random.uniform(20, 28), random.uniform(-8, 8))
for i in range(11):
    carro(560 + (i % 3) * 78 + random.uniform(-16, 16),
          1120 + (i // 3) * 82 + random.uniform(-14, 14),
          random.uniform(-25, 25), telo=random.random() < 0.6)
etichetta(400, 1112, "Tendopoli", "et")
etichetta(660, 1104, "Piazzale dei Carri", "et")

# carri del minerale sulla via maestra, in discesa dalle colline
for i, (cx, cy) in enumerate([(268, 848), (352, 842), (452, 838)]):
    carro(cx, cy, random.uniform(-4, 4), telo=False)

# margine sud: capanne sparse e recinto dei cavalli
random.seed(909)
for bx, by in [(620, 1320), (712, 1398), (546, 1452), (836, 1352),
               (930, 1440), (1046, 1330), (1180, 1452)]:
    edificio(bx, by, random.uniform(38, 52), random.uniform(28, 38),
             random.uniform(-8, 8), "grezzo", camino=random.random() < 0.4)
recinto([(700, 1180), (900, 1170), (912, 1282), (712, 1292)])
for _ in range(4):
    x = random.uniform(730, 880)
    y = random.uniform(1198, 1266)
    out.append(f'<ellipse class="bestia" cx="{x:.0f}" cy="{y:.0f}" rx="9" ry="5"/>')
etichetta(806, 1160, "Recinto dei cavalli", "et-piccola")

# ============================================================ POZZO E CAMPOSANTO
out.append('<circle class="pozzo" cx="586" cy="846" r="17"/>')
out.append('<circle class="pozzo-i" cx="586" cy="846" r="9"/>')
line(572, 832, 600, 860, "assi", 0.7)
etichetta(586, 806, "Pozzo Profondo", "et-piccola")

for i in range(7):
    x = 262 + (i % 4) * 26 + random.uniform(-4, 4)
    y = 288 + (i // 4) * 30
    line(x, y - 9, x, y + 9, "croce", 0.6)
    line(x - 6, y - 3, x + 6, y - 3, "croce", 0.6)
etichetta(310, 256, "Camposanto", "et-piccola")

# ============================================================ QUARTIERE STABILE
# le tre dozzine di famiglie che vivono della citta`, non delle colline
random.seed(2026)
for i in range(11):
    bx = 690 + i * 68 + random.uniform(-8, 8)
    by = 404 + (i % 2) * 34 + random.uniform(-8, 8)
    edificio(bx, by, random.uniform(44, 58), random.uniform(34, 44),
             random.uniform(-3, 3), "verniciato", camino=True)
    if i % 3 == 0:
        recinto([(bx - 8, by - 10), (bx + 62, by - 12),
                 (bx + 64, by + 58), (bx - 6, by + 60)])
etichetta(1040, 380, "Case dei residenti", "et-piccola")

# capanne isolate a est e nord-est
for bx, by in [(1620, 448), (1748, 500), (1560, 336), (2040, 560),
               (2170, 700), (2244, 900), (1980, 1220), (2126, 1108)]:
    edificio(bx, by, random.uniform(40, 54), random.uniform(30, 40),
             random.uniform(-7, 7), "grezzo", camino=random.random() < 0.5)

# falegnameria e deposito del sale, lato sud della via maestra
edificio(1318, 986, 104, 48, 1, "magazzino")
etichetta(1398, 958, "Deposito del sale", "et-piccola")
edificio(856, 1014, 92, 46, -2, "magazzino")
etichetta(902, 1004, "Falegnameria", "et-piccola")
for i in range(4):
    for k in range(5):
        line(806 + k * 4, 1052 + i * 6, 806 + k * 4, 1076 + i * 6, "catasta", 0.6)

# ============================================================ SERBATOIO E BINARIO MORTO
out.append('<circle class="serbatoio" cx="1876" cy="1098" r="30"/>')
out.append('<circle class="serbatoio-i" cx="1876" cy="1098" r="19"/>')
for a_ in (35, 145, 215, 325):
    ax = 1876 + 30 * math.cos(math.radians(a_))
    ay = 1098 + 30 * math.sin(math.radians(a_))
    line(1876, 1098, ax, ay, "assi", 0.5)
line(1876, 1068, 1876, 1040, "palo-tel", 0.6)
etichetta(1876, 1152, "Serbatoio dell'acqua", "et-piccola")
ferrovia([(2214, 1002), (2080, 1038), (1940, 1052), (1830, 1046), (1756, 1032)])
line(1750, 1016, 1750, 1048, "respingente", 0.8)

# ============================================================ MARCIAPIEDI DI ASSI
for bx, by, bw in [(736, 774, 300), (1046, 762, 320), (1370, 782, 140)]:
    poly([(bx, by), (bx + bw, by - 6), (bx + bw, by + 10), (bx, by + 16)], "marciapiede", 1.2)
    for k in range(int(bw // 18)):
        line(bx + k * 18, by, bx + k * 18, by + 14, "assi", 0.5)
# pali per legare i cavalli
for hx in range(770, 1420, 46):
    line(hx, 800, hx + 26, 798, "staccionata", 0.8)
    out.append(f'<circle class="palo" cx="{hx}" cy="800" r="2.2"/>')
    out.append(f'<circle class="palo" cx="{hx + 26}" cy="798" r="2.2"/>')

# ============================================================ ETICHETTE PRINCIPALI
for x, y, w, h, a, lab in isolati:
    if not lab:
        continue
    righe = lab.split("\n")
    base = y - 10 - (len(righe) - 1) * 15
    for k, r in enumerate(righe):
        etichetta(x + w / 2, base + k * 15, r, "et-edificio")

etichetta(1440, 894, "Osteria del Capolinea", "et-edificio")
etichetta(1498, 1158, "Piazzale del Capolinea", "et")
etichetta(1778, 1362, "Recinti del Bestiame", "et")
etichetta(1070, 1200, "Scuderie e Maniscalco", "et-piccola")
etichetta(628, 1024, "Fucina", "et-piccola")
etichetta(900, 830, "STRADA MAESTRA", "et-strada")
etichetta(196, 806, "\u25c0 verso le colline e le concessioni", "et-piccola", anchor="start")
etichetta(250, 190, "Pista dei Coloni", "et-piccola")
out[-1] = out[-1].replace('<text', '<text transform="rotate(-58 250 190)"', 1)
etichetta(150, 74, "▲ verso la conca di Acquaferra", "et-piccola")
etichetta(2180, 946, "verso il guado e Tre Pali ▶", "et-piccola")
etichetta(2020, 1128, "Capolinea della Ferrovia", "et-piccola")

# ============================================================ CORNICE
out.append('<rect class="cornice-e" x="26" y="26" width="2348" height="1548"/>')
out.append('<rect class="cornice-i" x="40" y="40" width="2320" height="1520"/>')

# ============================================================ CARTIGLIO
out.append('<g id="cartiglio">')
out.append('<rect class="carta" x="1700" y="70" width="600" height="250"/>')
out.append('<rect class="carta-b" x="1712" y="82" width="576" height="226"/>')
etichetta(2000, 168, "SILVERADO", "titolo")
etichetta(2000, 206, "Capolinea occidentale della ferrovia", "sottotitolo")
etichetta(2000, 240, "Popolazione dichiarata: 3.000 anime", "didascalia")
etichetta(2000, 264, "Rilevata per la Casa dei Registri", "didascalia")
etichetta(2000, 288, "Mese di Alto Sole, Anno 159", "didascalia")
out.append('</g>')

# ============================================================ LEGENDA
lx, ly = 1880, 1180
out.append(f'<rect class="carta" x="{lx}" y="{ly}" width="440" height="340"/>')
out.append(f'<rect class="carta-b" x="{lx + 10}" y="{ly + 10}" width="420" height="320"/>')
etichetta(lx + 220, ly + 46, "LEGENDA", "legenda-t")
voci = [
    ("verniciato", "Edifici di assi verniciate"),
    ("grezzo", "Baracche e legno crudo"),
    ("osteria", "Osteria (sei registrate)"),
    ("tenda", "Tende e dormitori"),
    ("ferrovia", "Ferrovia in esercizio"),
    ("strada", "Strada di terra battuta"),
    ("recinto", "Recinzioni"),
    ("telegrafo", "Pali del telegrafo"),
]
for i, (sym, txt) in enumerate(voci):
    yy = ly + 82 + i * 31
    sx = lx + 36
    if sym == "verniciato":
        poly([(sx - 14, yy - 9), (sx + 14, yy - 9), (sx + 14, yy + 7), (sx - 14, yy + 7)], "tetto-a-v", 0.4)
        poly([(sx - 14, yy - 9), (sx + 14, yy - 9), (sx + 14, yy + 7), (sx - 14, yy + 7)], "muro", 0.4)
    elif sym == "grezzo":
        poly([(sx - 13, yy - 8), (sx + 13, yy - 8), (sx + 13, yy + 6), (sx - 13, yy + 6)], "tetto-a", 0.4)
        poly([(sx - 13, yy - 8), (sx + 13, yy - 8), (sx + 13, yy + 6), (sx - 13, yy + 6)], "muro", 0.4)
    elif sym == "osteria":
        out.append(f'<circle class="segno-osteria" cx="{sx}" cy="{yy}" r="9"/>')
        line(sx, yy - 9, sx, yy + 9, "segno-l", 0.3)
    elif sym == "tenda":
        poly([(sx - 13, yy + 8), (sx, yy - 9), (sx + 13, yy + 8)], "tenda", 0.4)
    elif sym == "ferrovia":
        line(sx - 16, yy, sx + 16, yy, "rotaia-l", 0.3)
        for k in range(-2, 3):
            line(sx + k * 8, yy - 6, sx + k * 8, yy + 6, "traversina", 0.3)
    elif sym == "strada":
        poly([(sx - 16, yy - 7), (sx + 16, yy - 7), (sx + 16, yy + 7), (sx - 16, yy + 7)], "strada", 0.4)
    elif sym == "recinto":
        line(sx - 16, yy, sx + 16, yy, "staccionata", 0.3)
        for k in (-16, -5, 6, 16):
            out.append(f'<circle class="palo" cx="{sx + k}" cy="{yy}" r="2.4"/>')
    elif sym == "telegrafo":
        palo_telegrafo(sx, yy + 8)
    etichetta(lx + 70, yy + 6, txt, "legenda-v", anchor="start")

# ============================================================ SCALA E ROSA DEI VENTI
sx0, sy0 = 900, 1500
for i in range(4):
    cls = "scala-p" if i % 2 == 0 else "scala-d"
    out.append(f'<rect class="{cls}" x="{sx0 + i * 70}" y="{sy0}" width="70" height="14"/>')
for i in range(5):
    etichetta(sx0 + i * 70, sy0 + 34, str(i * 50), "didascalia")
etichetta(sx0 + 140, sy0 - 10, "Passi", "didascalia")

out.append('<g transform="translate(180,1420)">')
out.append('<circle class="bussola" r="46"/>')
out.append('<path class="ago-n" d="M0,-40 L11,0 L0,40 L-11,0 Z"/>')
out.append('<path class="ago-s" d="M0,-40 L-11,0 L0,0 Z"/>')
etichetta(0, -54, "N", "didascalia")
out.append('</g>')

# ============================================================ SVG
STYLE = """
  .suolo      { fill:#ddccaa; }
  .chiazza    { fill:#d3c098; opacity:.5; }
  .sterpo     { fill:none; stroke:#8b7a53; stroke-width:1.1; opacity:.55; }
  .collina    { fill:#cdb68d; stroke:#7a6741; stroke-width:2; }
  .crinale    { stroke:#7a6741; stroke-width:1.6; fill:none; stroke-linecap:round; }
  .scavo      { fill:#bda87e; stroke:#6b5a36; stroke-width:1.6; }
  .strada     { fill:#cbb68e; stroke:#8b7649; stroke-width:1.6; }
  .solco      { fill:none; stroke:#9c8657; stroke-width:1.2; opacity:.65; }
  .massicciata{ fill:none; stroke:#bda67c; stroke-width:30; stroke-linecap:round; }
  .traversina { stroke:#6b5836; stroke-width:2.6; stroke-linecap:round; }
  .rotaia     { fill:none; stroke:#3f3222; stroke-width:2.2; }
  .rotaia-l   { stroke:#3f3222; stroke-width:2.2; }
  .respingente{ stroke:#3f3222; stroke-width:4; stroke-linecap:round; }
  .ombra      { fill:#8a7550; opacity:.32; }
  .tetto-a    { fill:#c9b083; }
  .tetto-b    { fill:#9a8055; }
  .tetto-a-v  { fill:#d6bd92; }
  .tetto-b-v  { fill:#a0855a; }
  .muro       { fill:none; stroke:#3b2d1c; stroke-width:2.2; stroke-linejoin:round; }
  .colmo      { stroke:#3b2d1c; stroke-width:1.8; }
  .assi       { stroke:#6d5a39; stroke-width:.9; }
  .camino     { fill:#9c8355; stroke:#3b2d1c; stroke-width:1.2; }
  .tenda      { fill:#cdb992; stroke:#3b2d1c; stroke-width:1.8; stroke-linejoin:round; }
  .carro      { fill:#b59a6d; stroke:#3b2d1c; stroke-width:1.6; }
  .carro-telo { fill:#d8c8a4; stroke:#3b2d1c; stroke-width:1.6; }
  .ruota      { fill:none; stroke:#3b2d1c; stroke-width:1.3; }
  .staccionata{ stroke:#5a4828; stroke-width:1.7; }
  .palo       { fill:#4a3a20; }
  .catasta    { stroke:#5a4828; stroke-width:1.8; stroke-linecap:round; }
  .gru        { fill:none; stroke:#3b2d1c; stroke-width:2; }
  .gru-braccio{ stroke:#3b2d1c; stroke-width:2.4; }
  .bestia     { fill:#b39a6d; stroke:#4a3a20; stroke-width:1.2; }
  .pozzo      { fill:#c6b087; stroke:#3b2d1c; stroke-width:2.2; }
  .pozzo-i    { fill:#8d7a53; stroke:#3b2d1c; stroke-width:1.4; }
  .croce      { stroke:#4a3a20; stroke-width:1.8; stroke-linecap:round; }
  .albo       { fill:#d8c8a4; stroke:#3b2d1c; stroke-width:1.6; }
  .fumo       { fill:none; stroke:#7a6741; stroke-width:1.6; opacity:.6; }
  .palo-tel   { stroke:#4a3a20; stroke-width:1.5; stroke-linecap:round; }
  .segno-osteria { fill:none; stroke:#3b2d1c; stroke-width:1.6; }
  .segno-l    { stroke:#3b2d1c; stroke-width:1.4; }
  .marciapiede{ fill:#d2bd93; stroke:#5a4828; stroke-width:1.4; }
  .serbatoio  { fill:#c6b087; stroke:#3b2d1c; stroke-width:2.4; }
  .serbatoio-i{ fill:none; stroke:#3b2d1c; stroke-width:1.2; }
  .cornice-e  { fill:none; stroke:#4a3a20; stroke-width:5; }
  .cornice-i  { fill:none; stroke:#4a3a20; stroke-width:1.6; }
  .carta      { fill:#e2d3b0; stroke:#4a3a20; stroke-width:3; }
  .carta-b    { fill:none; stroke:#4a3a20; stroke-width:1.2; }
  .scala-p    { fill:#3b2d1c; stroke:#3b2d1c; stroke-width:1.2; }
  .scala-d    { fill:#e2d3b0; stroke:#3b2d1c; stroke-width:1.2; }
  .bussola    { fill:#e2d3b0; stroke:#4a3a20; stroke-width:2; }
  .ago-n      { fill:#3b2d1c; }
  .ago-s      { fill:#8a7550; }
  text        { font-family:'Liberation Serif','Times New Roman',serif; fill:#3b2d1c; }
  .titolo     { font-size:62px; letter-spacing:10px; }
  .sottotitolo{ font-size:22px; font-style:italic; }
  .didascalia { font-size:17px; }
  .legenda-t  { font-size:22px; letter-spacing:4px; }
  .legenda-v  { font-size:18px; }
  .et         { font-size:22px; }
  .et-edificio{ font-size:17px; }
  .et-piccola { font-size:15px; font-style:italic; }
  .et-strada  { font-size:26px; letter-spacing:7px; fill:#6b5836; }
  .et-regione { font-size:26px; letter-spacing:8px; fill:#7a6741; }
"""

svg = (f'<?xml version="1.0" encoding="UTF-8"?>\n'
       f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
       f'viewBox="0 0 {W} {H}">\n<defs><style>{STYLE}</style></defs>\n'
       + "\n".join(out) + "\n</svg>\n")

import sys
open(sys.argv[1] if len(sys.argv) > 1 else "silverado.svg", "w", encoding="utf-8").write(svg)
print("scritto", len(svg), "byte")
