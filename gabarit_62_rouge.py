"""Gabarit etiquette medicament Brother QL-800, ruban continu 62 mm : DK-22251 (noir + rouge) ou DK-22205
(papier blanc, noir seul ; rouleau par defaut : rouge=False, l'accent rouge
passe en noir).

Dessinee en 1063 x 696 puis, par defaut (portrait=True, 62 x 90 en portrait),
reduite a 696 x 456 = 62 mm de large x 39 mm de long : le texte court EN TRAVERS du ruban, aucune rotation.
portrait=False : 62 x 90 mm, paysage, tourne de 90 par l'add-on.
Meme contenu que la variante A ; la largeur de 62 mm permet de revenir a la disposition d'origine (posologie
en bas). Le rouge sert d'accent : bandeau des prenoms, duree, cadre de posologie, maximum par jour.
Chaque couleur est dessinee sur son propre calque puis seuillee : l'image finale ne contient que du noir pur,
du rouge pur et du blanc, sans bord gris ou rose que le tri noir/rouge de brother_ql classerait mal.
"""
from PIL import Image, ImageDraw
from gabarit_medicament import F, fit, wrap, sablier, sunrise, sun, moon, EXTRAS

W, H = 1063, 696
NOIR, ROUGE = (0, 0, 0), (220, 0, 0)


def bandeau(red, rd, who):
    """Bandeau ROUGE plein, prenoms en blanc (reserve) a la verticale, lecture de bas en haut."""
    cols = []
    for nom in who:
        f = fit(rd, nom, H - 60, (110,) if len(who) == 1 else (96, 88, 80), True)
        tw = int(rd.textlength(nom, font=f)) + 20
        t = Image.new("L", (tw, f.size + 20), 0)
        ImageDraw.Draw(t).text((tw // 2, (f.size + 20) // 2), nom, font=f, fill=255, anchor="mm")
        cols.append(t.rotate(90, expand=True))
    largeur = sum(c.width for c in cols) + 12 * (len(cols) - 1)
    B = 24 + largeur
    rd.rectangle((0, 0, B, H), fill=0)
    xc = B - largeur
    for c in cols:
        red.paste(c, (xc, (H - c.height) // 2))
        xc += c.width + 12
    return B


def label(who, name, use, pos, extras=(), duree=None, detail=None, portrait=True, rouge=True):
    blk = Image.new("L", (W, H), 255)
    red = Image.new("L", (W, H), 255)
    bd, rd = ImageDraw.Draw(blk), ImageDraw.Draw(red)
    B = bandeau(red, rd, who)

    x = B + 40
    maxw = W - 24 - x
    col_extras = 110 if extras else 0
    y = 14
    f = fit(bd, name, maxw, (116, 108, 100, 92, 84), True)
    bd.text((x, y), name, font=f, fill=0)
    y += f.size + 22
    f, lines = wrap(bd, use, maxw, (64, 58, 52, 46), False)
    for ln in lines:
        bd.text((x, y), ln, font=f, fill=0)
        y += f.size + 6
    if duree:
        y += 14
        s = 6
        f, lines = wrap(rd, duree, maxw - 12 * s, (54, 50, 46, 42), True)
        if len(lines) > 1 and ", " in duree:
            a, b = duree.split(", ", 1)
            lines = [a + ",", b]
            f = fit(rd, max(lines, key=len), maxw - 12 * s, (54, 50, 46, 42), True)
        sablier(rd, x + s, y + 6, s)
        for ln in lines:
            rd.text((x + 12 * s, y), ln, font=f, fill=0)
            y += f.size + 6

    top, bot = max(y + 20, H - 262), H - 14
    bx0, bx1 = x, W - 18 - col_extras
    zone = bx1 - bx0
    if isinstance(pos, str):
        rd.rounded_rectangle((bx0, top, bx1, bot), radius=34, outline=0, width=10)
        cx = (bx0 + bx1) // 2
        f = fit(bd, pos, zone - 60, (80, 72, 64), True)
        if detail:
            parts = detail.split(" · ")
            fd = fit(bd, max(parts, key=len), zone - 60, (44, 40, 36, 32), True)
            pas = fd.size + 10
            bloc = f.size + 20 + pas * len(parts)
            yy = (top + bot - bloc) // 2
            bd.text((cx, yy + f.size // 2), pos, font=f, fill=0, anchor="mm")
            yy += f.size + 20
            # une consigne par ligne ; la derniere (le maximum par jour) en rouge
            for i, p in enumerate(parts):
                d = rd if i == len(parts) - 1 else bd
                d.text((cx, yy + pas // 2), p, font=fd, fill=0, anchor="mm")
                yy += pas
        else:
            bd.text((cx, (top + bot) // 2), pos, font=f, fill=0, anchor="mm")
    else:
        cw = (zone - 2 * 20) // 3
        for i, (ico, n) in enumerate(zip((sunrise, sun, moon), pos)):
            cx0 = bx0 + i * (cw + 20)
            rd.rounded_rectangle((cx0, top, cx0 + cw, bot), radius=28, outline=0, width=10)
            ico(bd, cx0 + cw // 2, top + 60, 5)
            bd.text((cx0 + cw // 2, top + 160), str(n) if n else "–", font=F(110), fill=0, anchor="mm")
    ex = W - 14 - col_extras // 2
    for j, e in enumerate(extras):
        EXTRAS[e](bd, ex, top + 60 + j * 120, 5)

    if portrait:
        # reduire les CALQUES (niveaux de gris) avant le seuillage : l'image finale reste a 3 couleurs pures
        taille = (696, round(H * 696 / W))
        blk, red = blk.resize(taille, Image.LANCZOS), red.resize(taille, Image.LANCZOS)
    # Calques -> image a 3 couleurs pures (le rouge l'emporte s'ils se recouvrent)
    out = Image.new("RGB", blk.size, (255, 255, 255))
    out.paste(NOIR, mask=blk.point(lambda v: 255 if v < 128 else 0, mode="1"))
    out.paste(ROUGE if rouge else NOIR, mask=red.point(lambda v: 255 if v < 128 else 0, mode="1"))
    return out


if __name__ == "__main__":
    label(["ALEX"], "EXEMPLE 500", "Description courte", (1, 0, 1), ["repas"], "7 jours").save("exemple_62.png")
    print("ok")
