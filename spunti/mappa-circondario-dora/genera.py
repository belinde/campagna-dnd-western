# Mappa del circondario di Silverado come taccuino di rilievo di Dora.
# Contiene solo luoghi visitati in gioco o riferiti ai PG (sessioni 013-014).
# La geometria viene dalla carta DM della conca (stesse coordinate), ingrandita sul corridoio percorso.
import html, re
W, H = 1500, 1060
INK = "#3b2a1a"; FADE = "#7a5c3e"; WATER = "#4f6f7f"; RED = "#8c2f22"
S, OX, OY = 1.4, 180, 360          # scala e origine del ritaglio sulla carta DM
DX, DY = 40, 150                   # dove cade l'origine sulla pagina
def P(x, y): return (DX + (x - OX) * S, DY + (y - OY) * S)
def tp(d):
    nums = re.findall(r"-?\d+(?:\.\d+)?", d)
    it = iter(nums); pairs = []
    for x in it:
        y = next(it); pairs.append(P(float(x), float(y)))
    it2 = iter(pairs); buf = []
    def rep(m):
        return ""
    toks = re.split(r"(-?\d+(?:\.\d+)?)", d)
    res, k, i = [], 0, 0
    flat = [c for p in pairs for c in p]
    for tok in toks:
        if re.fullmatch(r"-?\d+(?:\.\d+)?", tok):
            res.append(f"{flat[k]:.1f}"); k += 1
        else:
            res.append(tok)
    return "".join(res)

out = []
def a(s): out.append(s)
def t(x, y, s, size=20, fill=INK, anchor="start", rot=None, weight="normal"):
    tr = f' transform="rotate({rot} {x:.1f} {y:.1f})"' if rot is not None else ""
    lines = s.split("\n")
    a(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" font-weight="{weight}"{tr}>')
    for i, l in enumerate(lines):
        a(f'<tspan x="{x:.1f}" dy="{0 if i == 0 else size * 1.15:.1f}">{html.escape(l)}</tspan>')
    a('</text>')
def path(d, stroke, w, dash=None, extra=""):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    a(f'<path d="{tp(d)}" fill="none" stroke="{stroke}" stroke-width="{w}"{da} stroke-linecap="round"{extra}/>')
def leader(x1, y1, x2, y2, col=FADE):
    a(f'<path d="M{x1:.1f} {y1:.1f} Q {(x1+x2)/2+15:.1f} {(y1+y2)/2-15:.1f}, {x2:.1f} {y2:.1f}" fill="none" stroke="{col}" stroke-width="1.2" stroke-dasharray="3 4"/>')

a(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Z003, \'URW Chancery L\', cursive">')
a('''<defs>
  <radialGradient id="carta" cx="50%" cy="45%" r="75%">
    <stop offset="0" stop-color="#efe1c1"/><stop offset="0.7" stop-color="#e3cfa4"/><stop offset="1" stop-color="#c9ad7c"/>
  </radialGradient>
  <radialGradient id="macchia" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#b58e57" stop-opacity="0.25"/><stop offset="1" stop-color="#b58e57" stop-opacity="0"/>
  </radialGradient>
  <marker id="freccia" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0 L10 5 L0 10 z" fill="#3b2a1a"/>
  </marker>
</defs>''')
a(f'<rect width="{W}" height="{H}" fill="url(#carta)"/>')
for cx, cy, r in [(1320, 180, 120), (230, 960, 140), (760, 120, 70), (1400, 700, 90)]:
    a(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#macchia)"/>')
a(f'<line x1="750" y1="20" x2="750" y2="{H-20}" stroke="#b89a6a" stroke-width="1.5" stroke-dasharray="2 6" opacity="0.6"/>')

# --- cartiglio
t(40, 62, "Circondario di Silverado", 40, INK, weight="bold")
t(42, 94, "rilievo provvisorio — da ripassare a china. D.", 20, FADE)
t(42, 120, "commissione Brannagh: 4–5 giornate di rilievo ancora da fare", 17, FADE)

# --- colline a ovest (riferite da Bea, viste da lontano)
for i, y in enumerate(range(600, 760, 48)):
    x = 22 + (i % 2) * 14
    a(f'<path d="M{x} {y+20} q 20 -30 40 0 q 13 -18 26 0" fill="none" stroke="{FADE}" stroke-width="2"/>')
t(26, 590, "colline a ovest", 18, FADE, rot=-90)

# --- acque
path("M200 385 C 260 405, 320 430, 420 468", WATER, 2.5, "10 7")          # a monte: non visto
path("M420 468 S 620 545, 700 590 C 810 650, 930 760, 1035 885", WATER, 4)  # visto
x, y = P(640, 548); t(x, y, "rio dell'Acquaferra", 26, WATER, rot=27)
sx, sy = P(200, 385); a(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="none" stroke="{WATER}" stroke-width="2"/>')
t(sx - 10, sy + 34, "sorgenti?", 17, WATER)
path("M222 622 C 300 596, 400 578, 468 560", WATER, 2.2, "8 7")            # torrente a monte: non visto
path("M468 560 S 506 528, 514 500", WATER, 3)                              # visto al guado
x, y = P(300, 598); t(x, y, "torrente — nome? da dove scende?", 17, WATER, rot=-13)

# --- piste percorse
path("M430 500 S 640 640, 760 720 C 860 790, 950 860, 1020 918", INK, 2.5, "16 6")
x, y = P(840, 790); t(x + 10, y + 34, "riva sud: un'ora abbondante a piedi\ndal paese al podere", 18, INK, rot=37)
a(f'<path d="{tp("M1050 910 C 1100 885, 1130 870, 1170 852")}" fill="none" stroke="{INK}" stroke-width="2.5" stroke-dasharray="16 6" marker-end="url(#freccia)"/>')
x, y = P(1170, 852); t(x - 120, y - 22, "a Tre Pali: 4 giorni di pista", 19, INK)

# --- Silverado
cx, cy = P(1040, 920)
a(f'<rect x="{cx-75:.1f}" y="{cy-22:.1f}" width="150" height="54" fill="none" stroke="{INK}" stroke-width="2"/>')
for i in range(6):
    a(f'<rect x="{cx-66+i*23:.1f}" y="{cy-14:.1f}" width="15" height="13" fill="{INK}" opacity="0.75"/>')
    a(f'<rect x="{cx-66+i*23:.1f}" y="{cy+8:.1f}" width="15" height="13" fill="{INK}" opacity="0.5"/>')
rx, ry = cx + 30, cy + 34
a(f'<path d="M{rx:.1f} {ry:.1f} L{W-40} {ry+30:.1f}" stroke="{INK}" stroke-width="3"/>')
a(f'<line x1="{rx:.1f}" y1="{ry-10:.1f}" x2="{rx:.1f}" y2="{ry+10:.1f}" stroke="{INK}" stroke-width="5"/>')
xx = rx + 22
while xx < W - 45:
    yy = ry + (xx - rx) * 30 / (W - 40 - rx)
    a(f'<line x1="{xx:.1f}" y1="{yy-6:.1f}" x2="{xx:.1f}" y2="{yy+6:.1f}" stroke="{INK}" stroke-width="2"/>'); xx += 22
t(cx - 10, cy + 74, "SILVERADO", 34, INK, "middle", weight="bold")
t(cx - 82, cy + 4, "i binari finiscono qui", 16, INK, "end")
t(W - 190, ry + 60, "binari e telegrafo, a est", 15, INK)

t(1110, 220, ("Silverado\n"
              "· Capolinea: 3 $ a notte, colazione compresa\n"
              "  (Bea; biada e stalla a parte)\n"
              "· Casa dei Registri: Quist, onesto\n"
              "· sceriffo Hale: senza carta non si muove\n"
              "· altre osterie: Filone Magro, Pozzo Profondo"), 18, INK)
t(1110, 400, ("La ferrovia, dove proseguirà?\n"
              "a NE verso la Fossa Bianca,\n"
              "o a sud, dove ci sono meno salite?\n"
              "(chiacchiere al Capolinea)"), 18, FADE)
t(1110, 520, ("Colonia halfling chiusa nel filo\n"
              "spinato di qualcuno: dove?"), 18, FADE)
t(1110, 600, ("Miniera di ferro, verso le colline:\n"
              "una vena sola, «va sempre peggio»"), 18, FADE)

# --- vicini
hx, hy = P(552, 612)
a(f'<path d="M{hx-12:.1f} {hy+6:.1f} l12 -12 l12 12 v10 h-24 z" fill="none" stroke="{INK}" stroke-width="2"/>')
t(340, 640, ("Carmody, 16 SE: Tom, Nora e cinque figli\n"
                     "fucile puntato a terra = «buongiorno»\n"
                     "il lotto è vuoto da 4–5 anni (i Phillips)\n"
                     "«Garrity vuole solo i soldi»"), 18, INK)
leader(470, 636, hx - 6, hy + 18, INK)
fx, fy = P(372, 432); fy += 14
a(f'<path d="M{fx-11:.1f} {fy+6:.1f} l11 -11 l11 11 v9 h-22 z" fill="none" stroke="{FADE}" stroke-width="1.6" stroke-dasharray="3 3"/>')
t(400, 186, ("Pattinson, 8 SE: la famiglia in regola all'angolo NO\n"
              "(Quist). Casa di legno, il vecchio lavora il legname\n"
              "(Carmody). Non ancora visitati"), 17, FADE)
leader(410, 236, fx + 8, fy - 8)
# --- guado e podere
gx, gy = P(500, 548)
a(f'<path d="M{gx-14:.1f} {gy-6:.1f} h28 M{gx-14:.1f} {gy+7:.1f} h28" stroke="{INK}" stroke-width="2.5"/>')
t(530, 292, "guado sul torrente: largo una decina\ndi metri, bassissimo, si passa", 17, INK)
leader(560, 318, gx + 6, gy - 8, INK)
hx, hy = P(465, 522)
a(f'<path d="M{hx-14:.1f} {hy+6:.1f} l14 -14 l14 14 v13 h-28 z" fill="{INK}" opacity="0.85"/>')
a(f'<ellipse cx="{hx:.1f}" cy="{hy:.1f}" rx="58" ry="38" fill="none" stroke="{RED}" stroke-width="2"/>')
t(hx - 250, hy - 60, "16 NO: Halverson", 24, RED, weight="bold")
t(hx - 250, hy - 38, "baracca dei Phillips, ora occupata", 16, RED)

# --- il Pelato, riferito da Bea (posizione stimata)
lx, ly = P(285, 525)
a(f'<path d="M{lx-45:.1f} {ly+14:.1f} q 45 -60 90 0" fill="none" stroke="{FADE}" stroke-width="2" stroke-dasharray="6 4"/>')
for dx in (-20, 0, 20):
    a(f'<circle cx="{lx+dx:.1f}" cy="{ly-4:.1f}" r="3.5" fill="#f6efe0" stroke="{FADE}" stroke-width="1"/>')
t(lx - 40, ly + 44, "il Pelato?", 22, FADE, weight="bold")
t(70, 560, ("Bea: oltre il guado, sulle colline a ovest.\n"
            "Collina pelata, piena di sassi bianchi\n"
            "come i suoi fermaporta. «Vuota»: da lì\n"
            "partirono le prime ricerche. Il vecchio Sam\n"
            "li portò al mineralogista di allora."), 16, FADE)
leader(200, 556, lx - 30, ly + 50)

# --- riquadro: il podere visto dal canneto
bx, by = 60, 760
a(f'<rect x="{bx}" y="{by}" width="560" height="260" fill="#efe3c6" stroke="{INK}" stroke-width="2"/>')
t(bx + 14, by + 30, "Il podere, visto dal canneto", 22, INK, weight="bold")
t(bx + 14, by + 54, "Garrity (mezzelfo, cappello rosso, giacca frangiata) + un'elfa + due umani", 14, INK)
a(f'<path d="M{bx+40} {by+215} Q {bx+280} {by+95}, {bx+520} {by+215}" fill="none" stroke="{INK}" stroke-width="2"/>')
a(f'<rect x="{bx+250}" y="{by+130}" width="60" height="32" fill="none" stroke="{INK}" stroke-width="2"/>')
a(f'<path d="M{bx+246} {by+130} L{bx+314} {by+130}" stroke="{INK}" stroke-width="4"/>')
a(f'<line x1="{bx+276}" y1="{by+124}" x2="{bx+306}" y2="{by+116}" stroke="{RED}" stroke-width="2.5"/>')
t(bx + 320, by + 104, "tiratore sdraiato sulla falda\nnascosta del tetto, col fucile!", 15, RED)
t(bx + 322, by + 160, "due solchi freschi:\naltro che «mesi»", 14, INK)
for i in range(3):
    a(f'<ellipse cx="{bx+450+i*18}" cy="{by+196}" rx="8" ry="6" fill="none" stroke="{INK}" stroke-width="1.5"/>')
t(bx + 448, by + 182, "massi", 14, INK)
a(f'<line x1="{bx+150}" y1="{by+185}" x2="{bx+150}" y2="{by+150}" stroke="{INK}" stroke-width="2"/><circle cx="{bx+150}" cy="{by+140}" r="16" fill="none" stroke="{INK}" stroke-width="1.5"/>')
t(bx + 128, by + 114, "pioppo", 14, INK)
for i in range(10):
    a(f'<line x1="{bx+30+i*7}" y1="{by+248}" x2="{bx+34+i*7}" y2="{by+222}" stroke="{FADE}" stroke-width="1.5"/>')
t(bx + 110, by + 246, "canneto; ghiaia sotto la riva scavata", 14, FADE)
t(bx + 380, by + 246, "fosso asciutto fin dietro", 14, FADE)

# --- rosa dei venti e scala
a(f'<g transform="translate(1440 110)"><path d="M0 -40 L8 0 L0 40 L-8 0 Z" fill="none" stroke="{INK}" stroke-width="2"/><path d="M0 -40 L8 0 L-8 0 Z" fill="{INK}"/></g>')
t(1440, 60, "N", 22, INK, "middle")
mx, my, L = 700, 1030, 180 * S
a(f'<path d="M{mx} {my} h{L:.1f} M{mx} {my-8} v16 M{mx+L/2:.1f} {my-6} v12 M{mx+L:.1f} {my-8} v16" stroke="{INK}" stroke-width="2"/>')
t(mx + L / 2, my - 14, "un miglio, a passi (stima)", 16, INK, "middle")
a('</svg>')
open(__file__.replace("genera.py", "circondario-dora.svg"), "w").write("\n".join(out))
