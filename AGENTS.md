# AGENTS.md — brother-ql800

## But

Imprimer l'étiquette d'une boîte de médicament (personnes, nom, usage, durée, posologie) sur une Brother QL-800
pilotée par Home Assistant. Le catalogue JSON qui décrit les médicaments sert aussi d'inventaire d'armoire à pharmacie.

## Carte des fichiers

| Fichier | Rôle |
| --- | --- |
| `imprimer_medicament.py` | CLI : lit le catalogue, choisit le gabarit, sauve `<cle>.png`, vérifie l'état de l'imprimante, publie l'ordre MQTT via l'API REST HA, attend le compte rendu (60 × 1 s). |
| `gabarit_medicament.py` | Gabarit de base dessiné en 991×306 (29 × 90 mm à 300 dpi) : bandeau noir + prénoms verticaux, nom, usage, durée, posologie en colonne à droite, pictos. `label(..., largeur=696)` le réduit au format compact 696×215. Fournit aussi `F`, `fit`, `wrap`, les pictos (`sunrise`, `sun`, `moon`, `repas`, `soleil_non`, `sablier`), `EXTRAS` et `depuis_fiche(m, largeur=696)`. |
| `gabarit_62_rouge.py` | Gabarit 62 mm dessiné en 1063×696 sur deux calques (noir, rouge), posologie en bas. `portrait=True` (défaut) → 696×456 ; `portrait=False` → 1063×696 (62 × 90 mm, tourné par l'add-on). `rouge=False` → le calque rouge passe en noir. Sortie RGB à 3 couleurs pures. |
| `exemples/medicaments.json` | Catalogue fictif (ALEX, SAM) : `exemple500` (posologie en cases), `exemplegel` (posologie texte), `inventaire` (fiche non imprimable). |
| `docs/exemple-compact.png`, `docs/exemple-grand.png` | Rendus des exemples pour le README. |
| `.gitignore` | Ignore `/*.png` (sorties à la racine) et tout `medicaments.json` hors `exemples/`. |

L'add-on HA `local_brother_ql` (hors dépôt) importe `gabarit_medicament.depuis_fiche` pour son ordre « medicament » :
ne pas changer sa signature ni son comportement sans le signaler.

## Flux de données

```
catalogue JSON["medicaments"][cle]
  → champs (personnes, nom, description, posologie, pictos, duree, posologie_detail)
  → gabarit → PIL.Image → <cle>.png (toujours écrit)
  → [--apercu : fin]
  → GET /api/states/sensor.etiqueteuse_brother_ql_800_etat  (doit valoir "pret")
  → GET /api/states/sensor.etiqueteuse_brother_ql_800_derniere_impression (last_updated avant envoi)
  → POST /api/services/mqtt/publish {topic: "brother_ql/cmd", retain: false,
        payload: {action: "print", job: "medicament <cle>", label: "62"|"62red"|"29x90",
                  copies, red, image: <PNG base64>}}
  → sondage du capteur de dernière impression : last_updated changé ET attributes.job == job
  → affiche state, imprime, copies, erreurs
```

Correspondance options → gabarit → `label` MQTT :

| Option | Gabarit | Taille image | `label` | `red` |
| --- | --- | --- | --- | --- |
| (aucune) | `gabarit_medicament.label(..., largeur=696)` | 696×215, mode `1` | `62` | false |
| `--grand` | `gabarit_62_rouge.label(..., rouge=False)` | 696×456, RGB noir/blanc | `62` | false |
| `--62rouge` | `gabarit_62_rouge.label(..., rouge=True)` | 696×456, RGB noir/rouge/blanc | `62red` | true |
| `--29x90` | `gabarit_medicament.label(...)` | 991×306, mode `1` | `29x90` | false |

## Commandes

```sh
pip install pillow
python imprimer_medicament.py --liste
python imprimer_medicament.py <cle> [copies] [--apercu] [--grand | --62rouge | --29x90]
python gabarit_medicament.py     # écrit exemple.png (exemple générique)
python gabarit_62_rouge.py       # écrit exemple_62.png
```

## Variables d'environnement

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `HA_URL` | `http://homeassistant.local:8123` | Base de Home Assistant ; `/api` est ajouté. |
| `HA_TOKEN` | — | Jeton longue durée. À défaut, lu dans la variable utilisateur Windows via `powershell.exe`. |
| `ETIQUETTES_CATALOGUE` | `exemples/medicaments.json` | Chemin du catalogue réel. |

## Format du catalogue

`{"medicaments": {<cle>: fiche}}`. Champs d'une fiche : `nom` (str), `description` (str), `personnes` (liste de
prénoms, vide = fiche d'inventaire), `posologie` (liste de 3 entiers matin/midi/soir, OU str, OU `null` = non
imprimable), `pictos` (sous-ensemble de `["repas", "soleil"]`), `duree` (str ou `null` ; « a, b » se coupe après la
virgule), `posologie_detail` (str ou `null`, consignes séparées par ` · `).

## Conventions

- Python 3, bibliothèque standard + Pillow ; aucune autre dépendance.
- Commentaires, docstrings et messages en français SANS accents (choix existant, à respecter dans ces fichiers).
- Code compact, fonctions de dessin courtes ; tailles de police données en listes décroissantes essayées par
  `fit` / `wrap`.
- Aucun réglage propre à une maison en dur : tout passe par les variables d'environnement.

## Invariants à ne pas casser

- Largeur 696 px = ruban continu 62 mm à 300 dpi, pour les formats 62 mm (compact, `--grand`, `--62rouge`).
- Compact = 696×215 (≈ 62 × 19 mm), image **1 bit** (`convert("1", dither=NONE)`), réduite en niveaux de gris AVANT
  seuillage à 128.
- 29 × 90 = 991×306 paysage ; l'add-on le tourne pour la tête de 306 points.
- Gabarit 62 : chaque couleur sur son calque, réduite puis seuillée ; sortie strictement noir `(0,0,0)`, rouge
  `(220,0,0)`, blanc. Aucun gris ni rose (le tri noir/rouge de `brother_ql` les classerait mal). Le rouge l'emporte en
  cas de recouvrement.
- Polices : Arial (`arialbd.ttf`, `arial.ttf`) puis Liberation Sans (`/usr/share/fonts/truetype/liberation2/…`),
  mêmes métriques : la mise en page doit rester identique sur le PC et dans l'add-on.
- Une fiche sans `posologie` ou sans `personnes` n'est jamais imprimée (`sys.exit` dans le CLI, `ValueError` dans
  `depuis_fiche`).
- Ordre MQTT non retenu (`retain: False`) : un ordre retenu se rejouerait.
- `<cle>.png` est écrit avant toute vérification d'état.

## Pièges connus

- Pas de reprise automatique : un échec après l'envoi peut avoir déjà imprimé. Sans compte rendu en 60 s, vérifier
  l'étiquette avant de relancer (doublon possible).
- Identifiants d'entités HA codés en dur (`sensor.etiqueteuse_brother_ql_800_etat`,
  `sensor.etiqueteuse_brother_ql_800_derniere_impression`) ; l'état prêt est la chaîne `pret`.
- `--grand` et `--62rouge` partagent le gabarit 62 ; seul `rouge` change. `--29x90` et le compact partagent
  `gabarit_medicament`.
- Le PNG est écrit dans le dossier courant, sous le nom de la clé.
- `Image.Dither.NONE` exige une version récente de Pillow.

## Ne jamais commiter

- Le vrai catalogue (`medicaments.json` hors `exemples/`) : ce sont des données de santé.
- Prénoms réels, vrais médicaments associés à des personnes, étiquettes générées (`*.png` à la racine).
- Jetons (`HA_TOKEN`), adresses IP, noms d'hôte ou de domaine d'une maison réelle.
- Photos de personnes ou d'étiquettes réelles.
- Les exemples utilisent uniquement les prénoms fictifs ALEX et SAM.

## Vérifier un changement

```sh
python imprimer_medicament.py exemple500 --apercu              # → maquette exemple500.png (696x215)
python imprimer_medicament.py exemplegel --grand --apercu      # → 696x456
python imprimer_medicament.py exemplegel --62rouge --apercu    # contrôler : noir, rouge, blanc seulement
python imprimer_medicament.py exemple500 --29x90 --apercu      # → 991x306
python imprimer_medicament.py inventaire --apercu              # doit refuser (fiche d'inventaire)
```

Ouvrir les PNG, comparer à `docs/exemple-*.png`, puis supprimer les PNG produits à la racine.
