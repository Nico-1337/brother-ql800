"""Gabarit etiquette medicament Brother QL-800, rouleau DK-11201 (29 x 90 mm) : 991 x 306 points a 300 dpi.

Meme contenu que la variante A de la D110 : bandeau noir a gauche avec le(s)
prenom(s) a la verticale, nom + dosage, usage, duree (sablier), posologie. Le format etant 3 fois plus long
que haut, la posologie passe dans une colonne a droite au lieu d'une bande en bas.
L'image est paysage : l'add-on la tourne seul (rotate auto) pour la tete de 306 points.
"""
import math
from PIL import Image, ImageDraw, ImageFont

W, H = 991, 306


# Arial sur le PC (Windows) ; Liberation Sans dans l'add-on local_brother_ql (Debian, fonts-liberation2) :
# memes metriques qu'Arial, donc meme mise en page des deux cotes.
POLICES = {True: ("arialbd.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
           False: ("arial.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf")}


def F(sz, bold=True):
    for nom in POLICES[bold]:
        try:
            return ImageFont.truetype(nom, sz)
        except OSError:
            pass
    raise OSError("ni Arial ni Liberation Sans")


def fit(d, t, maxw, sizes, bold=True):
    for sz in sizes:
        f = F(sz, bold)
        if d.textlength(t, font=f) <= maxw:
            return f
    return F(sizes[-1], bold)


def wrap(d, t, maxw, sizes, bold=True, max_lines=2):
    """Plus grande police qui tient en au plus max_lines lignes (coupure aux espaces)."""
    for sz in sizes:
        f = F(sz, bold)
        lines, cur = [], ""
        for w in t.split():
            test = f"{cur} {w}".strip()
            if d.textlength(test, font=f) <= maxw:
                cur = test
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
        if len(lines) <= max_lines and all(d.textlength(ln, font=f) <= maxw for ln in lines):
            return f, lines
    return f, lines


# --- Pictos (dessines a l'echelle s, 1 = taille D110) ---------------------------------------------------

def sunrise(d, cx, cy, s):
    r = 6 * s
    d.pieslice((cx - r, cy - r + 2 * s, cx + r, cy + r + 2 * s), 180, 360, fill=0)
    d.line((cx - r - 3 * s, cy + 2 * s, cx + r + 3 * s, cy + 2 * s), fill=0, width=int(2 * s))
    for a in (210, 250, 290, 330):
        x, y = math.cos(math.radians(a)), math.sin(math.radians(a))
        d.line((cx + x * (r + 2 * s), cy + 2 * s + y * (r + 2 * s), cx + x * (r + 4 * s), cy + 2 * s + y * (r + 4 * s)),
               fill=0, width=int(s))


def sun(d, cx, cy, s):
    r = 4 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=0)
    for a in range(0, 360, 45):
        x, y = math.cos(math.radians(a)), math.sin(math.radians(a))
        d.line((cx + x * (r + 2 * s), cy + y * (r + 2 * s), cx + x * (r + 4 * s), cy + y * (r + 4 * s)), fill=0, width=int(s))


def moon(d, cx, cy, s):
    r = 6 * s
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=0)
    d.ellipse((cx - r + 4 * s, cy - r - 2 * s, cx + r + 4 * s, cy + r - 2 * s), fill=255)


def repas(d, cx, cy, s):
    d.line((cx - 4 * s, cy - 8 * s, cx - 4 * s, cy + 8 * s), fill=0, width=int(2 * s))
    for dx in (-6, -4, -2):
        d.line((cx + dx * s, cy - 8 * s, cx + dx * s, cy - 4 * s), fill=0, width=int(s))
    d.line((cx - 6 * s, cy - 4 * s, cx - 2 * s, cy - 4 * s), fill=0, width=int(s))
    d.polygon([(cx + 3 * s, cy - 8 * s), (cx + 6 * s, cy - 4 * s), (cx + 6 * s, cy + s), (cx + 3 * s, cy + s)], fill=0)
    d.line((cx + 4 * s, cy + s, cx + 4 * s, cy + 8 * s), fill=0, width=int(2 * s))


def soleil_non(d, cx, cy, s):
    d.ellipse((cx - 3 * s, cy - 3 * s, cx + 3 * s, cy + 3 * s), outline=0, width=int(2 * s))
    for a in range(0, 360, 60):
        x, y = math.cos(math.radians(a)), math.sin(math.radians(a))
        d.line((cx + x * 5 * s, cy + y * 5 * s, cx + x * 8 * s, cy + y * 8 * s), fill=0, width=int(s))
    d.line((cx - 8 * s, cy + 8 * s, cx + 8 * s, cy - 8 * s), fill=255, width=int(4 * s))
    d.line((cx - 8 * s, cy + 8 * s, cx + 8 * s, cy - 8 * s), fill=0, width=int(2 * s))


def sablier(d, x, y, s):
    d.polygon([(x, y), (x + 7 * s, y), (x + 3.5 * s, y + 4 * s)], fill=0)
    d.polygon([(x + 3.5 * s, y + 5 * s), (x, y + 9 * s), (x + 7 * s, y + 9 * s)], outline=0, width=int(s))
    d.line((x - s, y, x + 8 * s, y), fill=0, width=int(s))
    d.line((x - s, y + 9 * s, x + 8 * s, y + 9 * s), fill=0, width=int(s))


EXTRAS = {"repas": repas, "soleil": soleil_non}


def bandeau(im, d, who):
    """Prenom(s) a la VERTICALE (lecture de bas en haut), colles au bord droit du bandeau noir."""
    cols = []
    for nom in who:
        f = fit(d, nom, H - 24, (60,) if len(who) == 1 else (52, 48, 44), True)
        tw = int(d.textlength(nom, font=f)) + 12
        t = Image.new("L", (tw, f.size + 12), 0)
        ImageDraw.Draw(t).text((tw // 2, (f.size + 12) // 2), nom, font=f, fill=255, anchor="mm")
        cols.append(t.rotate(90, expand=True))
    largeur = sum(c.width for c in cols) + 6 * (len(cols) - 1)
    B = 14 + largeur
    d.rectangle((0, 0, B, H), fill=0)
    xc = B - largeur
    for c in cols:
        im.paste(c, (xc, (H - c.height) // 2))
        xc += c.width + 6
    return B


def label(who, name, use, pos, extras=(), duree=None, detail=None, largeur=None):
    """largeur : reduit l'etiquette (niveaux de gris, AVANT le seuillage) a cette largeur en points ;
    696 = ruban continu 62 mm, soit 62 x 19 mm (format compact, format par defaut)."""
    im = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(im)
    B = bandeau(im, d, who)

    # Colonne posologie a droite
    col_extras = 70 if extras else 0
    bw = 300
    bx1 = W - 6 - col_extras
    bx0 = bx1 - bw
    top, bot = 8, H - 8

    # Colonne texte
    x = B + 22
    maxw = bx0 - 18 - x
    y = 6
    f = fit(d, name, maxw, (80, 74, 68, 62, 56, 52, 48, 44), True)
    d.text((x, y), name, font=f, fill=0)
    y += f.size + 14
    f, lines = wrap(d, use, maxw, (44, 40, 36, 32), False)
    for ln in lines:
        d.text((x, y), ln, font=f, fill=0)
        y += f.size + 4
    if duree:
        y += 10
        s = 4
        f, lines = wrap(d, duree, maxw - 12 * s, (36, 33, 30, 27), True)
        if len(lines) > 1 and ", " in duree:
            # couper apres la virgule plutot qu'au hasard (« 3 j fievre, / 5 j douleur »)
            a, b = duree.split(", ", 1)
            lines = [a + ",", b]
            f = fit(d, max(lines, key=len), maxw - 12 * s, (36, 33, 30, 27), True)
        sablier(d, x + s, y + 4, s)
        for ln in lines:
            d.text((x + 12 * s, y), ln, font=f, fill=0)
            y += f.size + 4

    if isinstance(pos, str):
        d.rounded_rectangle((bx0, top, bx1, bot), radius=20, outline=0, width=6)
        cx = (bx0 + bx1) // 2
        # une seule ligne si elle reste grande, sinon deux
        f, plines = wrap(d, pos, bw - 30, (60, 56, 52), True, max_lines=1)
        if d.textlength(plines[0], font=f) > bw - 30 or len(plines) > 1:
            f, plines = wrap(d, pos, bw - 30, (64, 58, 52, 46), True)
        dlines = []
        if detail:
            fd, dlines = wrap(d, detail.replace(" · ", " — "), bw - 30, (32, 30, 28, 26), True, max_lines=3)
            # une consigne par ligne quand elle est faite de morceaux « a · b »
            if " · " in detail:
                parts = detail.split(" · ")
                fd = fit(d, max(parts, key=len), bw - 30, (32, 30, 28, 26), True)
                dlines = parts
        bloc = len(plines) * (f.size + 6) + (18 + len(dlines) * (fd.size + 8) if dlines else 0)
        yy = (top + bot - bloc) // 2
        for ln in plines:
            d.text((cx, yy + f.size // 2), ln, font=f, fill=0, anchor="mm")
            yy += f.size + 6
        if dlines:
            yy += 8
            d.line((bx0 + 30, yy, bx1 - 30, yy), fill=0, width=3)
            yy += 10
            for ln in dlines:
                d.text((cx, yy + fd.size // 2), ln, font=fd, fill=0, anchor="mm")
                yy += fd.size + 8
    else:
        cw = (bw - 2 * 12) // 3
        for i, (ico, n) in enumerate(zip((sunrise, sun, moon), pos)):
            cx0 = bx0 + i * (cw + 12)
            d.rounded_rectangle((cx0, top, cx0 + cw, bot), radius=16, outline=0, width=6)
            ico(d, cx0 + cw // 2, top + 70, 4)
            d.text((cx0 + cw // 2, top + 200), str(n) if n else "–", font=F(96), fill=0, anchor="mm")
    ex = W - 4 - col_extras // 2
    for j, e in enumerate(extras):
        EXTRAS[e](d, ex, top + 60 + j * 110, 3)
    if largeur:
        im = im.resize((largeur, round(H * largeur / W)), Image.LANCZOS).point(lambda v: 0 if v < 128 else 255)
    return im.convert("1", dither=Image.Dither.NONE)


def depuis_fiche(m, largeur=696):
    """Etiquette d'une fiche du catalogue (medicaments.json) ; 696 = format compact 62 x 19 mm.
    Utilise par imprimer_medicament.py (PC) et par l'add-on local_brother_ql (ordre « medicament »)."""
    if m.get("posologie") is None or not m.get("personnes"):
        raise ValueError(f"{m.get('nom')} : fiche d'inventaire, posologie ou personne pas encore dictee")
    pos = m["posologie"] if isinstance(m["posologie"], str) else tuple(m["posologie"])
    return label(m["personnes"], m["nom"], m.get("description", ""), pos, m.get("pictos", []),
                 m.get("duree"), m.get("posologie_detail"), largeur=largeur)


if __name__ == "__main__":
    # Exemple GENERIQUE : les vraies fiches (donnees de sante) restent hors du depot.
    label(["ALEX"], "EXEMPLE 500", "Description courte", (1, 0, 1), ["repas"], "7 jours").save("exemple.png")
    print("ok")
