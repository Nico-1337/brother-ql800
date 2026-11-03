"""Imprime l'etiquette d'une boite de medicament sur la Brother QL-800 (add-on local_brother_ql).

Usage :  python imprimer_medicament.py <cle> [copies] [--apercu] [--grand | --62rouge | --29x90]
         python imprimer_medicament.py --liste
Catalogue : fichier JSON (variable ETIQUETTES_CATALOGUE, exemple fictif dans exemples/medicaments.json). Il sert aussi
d'inventaire de l'armoire a pharmacie : une fiche sans posologie n'est pas imprimable.
Rouleaux : DK-22205 62 mm papier blanc continu, noir seul (rouleau par defaut). Format par defaut =
COMPACT 62 x 19 mm (gabarit_medicament reduit a 696x215 ; 62 x 39 se revele trop grand) ;
--grand = ancien 62 x 39 mm (gabarit_62_rouge en portrait 696x456, rouge=False) ; --62rouge = ruban DK-22251 62 mm noir+rouge (red=true) ;
--29x90 = DK-11201 predecoupe (gabarit_medicament, 991x306).
Chaine : catalogue -> gabarit -> mqtt.publish brother_ql/cmd (NON retenu) -> compte rendu lu
dans sensor.etiqueteuse_brother_ql_800_derniere_impression. --apercu : PNG seulement, rien n'est envoye.
Aucune reprise automatique : un echec apres l'envoi peut deja avoir sorti l'etiquette.
"""
import base64, io, json, os, subprocess, sys, time, urllib.request
import gabarit_62_rouge
import gabarit_medicament

# Reglages locaux : rien de propre a une maison n'est ecrit en dur.
CATALOGUE = os.environ.get("ETIQUETTES_CATALOGUE", os.path.join(os.path.dirname(__file__), "exemples", "medicaments.json"))
HA = os.environ.get("HA_URL", "http://homeassistant.local:8123").rstrip("/") + "/api"
RESULT = "sensor.etiqueteuse_brother_ql_800_derniere_impression"


def token():
    if os.environ.get("HA_TOKEN"):
        return os.environ["HA_TOKEN"]
    return subprocess.run(["powershell.exe", "-NoProfile", "-Command",
        '[Environment]::GetEnvironmentVariable("HA_TOKEN","User")'], capture_output=True, text=True).stdout.strip()


def api(path, body=None):
    req = urllib.request.Request(HA + path, data=json.dumps(body).encode() if body is not None else None,
        method="POST" if body is not None else "GET",
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read() or b"null")


def main():
    cat = json.load(open(CATALOGUE, encoding="utf-8"))["medicaments"]
    if "--liste" in sys.argv:
        for k, m in cat.items(): print(f"{k:16} {m['nom']:20} {'/'.join(m['personnes']) or '(armoire, a dicter)'}")
        return
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cle, copies = args[0], int(args[1]) if len(args) > 1 else 1
    rouge, petit, grand = "--62rouge" in sys.argv, "--29x90" in sys.argv, "--grand" in sys.argv
    m = cat[cle]
    if m.get("posologie") is None or not m.get("personnes"):
        sys.exit(f"{cle} : fiche d'inventaire de l'armoire, posologie ou personne pas encore renseignee")
    pos = m["posologie"] if isinstance(m["posologie"], str) else tuple(m["posologie"])
    champs = (m["personnes"], m["nom"], m["description"], pos, m.get("pictos", []), m.get("duree"),
              m.get("posologie_detail"))
    if petit:
        png = gabarit_medicament.label(*champs)
    elif rouge or grand:
        png = gabarit_62_rouge.label(*champs, rouge=rouge)
    else:
        png = gabarit_medicament.label(*champs, largeur=696)
    png.save(f"{cle}.png")
    print(f"maquette {cle}.png ({png.size[0]}x{png.size[1]})")
    if "--apercu" in sys.argv:
        return
    etat = api("/states/sensor.etiqueteuse_brother_ql_800_etat")
    if etat["state"] != "pret":
        sys.exit(f"imprimante {etat['state']} : {etat['attributes'].get('erreurs')} — rien n'est envoye")
    avant = api(f"/states/{RESULT}").get("last_updated")
    buf = io.BytesIO(); png.save(buf, "PNG")
    job = f"medicament {cle}"
    payload = {"action": "print", "job": job, "label": "29x90" if petit else "62red" if rouge else "62", "copies": copies,
               "red": rouge,
               "image": base64.b64encode(buf.getvalue()).decode()}
    api("/services/mqtt/publish", {"topic": "brother_ql/cmd", "payload": json.dumps(payload), "retain": False})
    print("ordre envoye, attente du compte rendu...")
    for _ in range(60):
        time.sleep(1)
        r = api(f"/states/{RESULT}")
        if r.get("last_updated") != avant and r["attributes"].get("job") == job:
            a = r["attributes"]
            print(f"impression : {r['state']} (imprime={a.get('imprime')}, copies={a.get('copies')}, "
                  f"erreurs={a.get('erreurs')})")
            return
    print("pas de compte rendu en 60 s : verifier l'etiquette AVANT de relancer (doublon possible)")


if __name__ == "__main__":
    main()
