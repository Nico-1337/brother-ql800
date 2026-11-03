# AGENTS.md — brother-ql800

## Purpose

Print the label of a medicine box (people, name, use, duration, dosage) on a Brother QL-800 driven by Home
Assistant. The JSON catalog that describes the medicines also serves as the inventory of the medicine cabinet.

## File map

| File | Role |
| --- | --- |
| `imprimer_medicament.py` | CLI: reads the catalog, picks the template, saves `<cle>.png`, checks the printer status, publishes the MQTT order through the HA REST API, waits for the report (60 × 1 s). |
| `gabarit_medicament.py` | Base template drawn at 991×306 (29 × 90 mm at 300 dpi): black band + vertical first names, name, use, duration, dosage in a column on the right, pictograms. `label(..., largeur=696)` scales it down to the compact 696×215 format. Also provides `F`, `fit`, `wrap`, the pictograms (`sunrise`, `sun`, `moon`, `repas`, `soleil_non`, `sablier`), `EXTRAS` and `depuis_fiche(m, largeur=696)`. |
| `gabarit_62_rouge.py` | 62 mm template drawn at 1063×696 on two layers (black, red), dosage at the bottom. `portrait=True` (default) → 696×456; `portrait=False` → 1063×696 (62 × 90 mm, rotated by the add-on). `rouge=False` → the red layer turns black. RGB output with 3 pure colors. |
| `exemples/medicaments.json` | Fictional catalog (ALEX, SAM): `exemple500` (dosage in boxes), `exemplegel` (text dosage), `inventaire` (non-printable entry). |
| `docs/exemple-compact.png`, `docs/exemple-grand.png` | Renders of the examples for the README. |
| `.gitignore` | Ignores `/*.png` (outputs at the root) and any `medicaments.json` outside `exemples/`. |

The HA add-on `local_brother_ql` (outside the repository) imports `gabarit_medicament.depuis_fiche` for its
"medicament" order: do not change its signature or behavior without flagging it.

## Data flow

```
JSON catalog["medicaments"][cle]
  → fields (personnes, nom, description, posologie, pictos, duree, posologie_detail)
  → template → PIL.Image → <cle>.png (always written)
  → [--apercu: stop]
  → GET /api/states/sensor.etiqueteuse_brother_ql_800_etat  (must be "pret")
  → GET /api/states/sensor.etiqueteuse_brother_ql_800_derniere_impression (last_updated before sending)
  → POST /api/services/mqtt/publish {topic: "brother_ql/cmd", retain: false,
        payload: {action: "print", job: "medicament <cle>", label: "62"|"62red"|"29x90",
                  copies, red, image: <PNG base64>}}
  → polling of the last-print sensor: last_updated changed AND attributes.job == job
  → shows state, imprime, copies, erreurs
```

Mapping options → template → MQTT `label`:

| Option | Template | Image size | `label` | `red` |
| --- | --- | --- | --- | --- |
| (none) | `gabarit_medicament.label(..., largeur=696)` | 696×215, mode `1` | `62` | false |
| `--grand` | `gabarit_62_rouge.label(..., rouge=False)` | 696×456, RGB black/white | `62` | false |
| `--62rouge` | `gabarit_62_rouge.label(..., rouge=True)` | 696×456, RGB black/red/white | `62red` | true |
| `--29x90` | `gabarit_medicament.label(...)` | 991×306, mode `1` | `29x90` | false |

## Commands

```sh
pip install pillow
python imprimer_medicament.py --liste
python imprimer_medicament.py <cle> [copies] [--apercu] [--grand | --62rouge | --29x90]
python gabarit_medicament.py     # writes exemple.png (generic example)
python gabarit_62_rouge.py       # writes exemple_62.png
```

## Environment variables

| Variable | Default | Role |
| --- | --- | --- |
| `HA_URL` | `http://homeassistant.local:8123` | Home Assistant base URL; `/api` is appended. |
| `HA_TOKEN` | — | Long-lived token. If unset, read from the Windows user variable through `powershell.exe`. |
| `ETIQUETTES_CATALOGUE` | `exemples/medicaments.json` | Path of the real catalog. |

## Catalog format

`{"medicaments": {<cle>: entry}}`. Fields of an entry: `nom` (str), `description` (str), `personnes` (list of
first names, empty = inventory entry), `posologie` (list of 3 integers morning/noon/evening, OR str, OR `null` = not
printable), `pictos` (subset of `["repas", "soleil"]`), `duree` (str or `null`; "a, b" is split after the
comma), `posologie_detail` (str or `null`, instructions separated by ` · `).

## Conventions

- Python 3, standard library + Pillow; no other dependency.
- Comments, docstrings and messages in French WITHOUT accents (existing choice, to be respected in these files).
- Compact code, short drawing functions; font sizes given as decreasing lists tried by
  `fit` / `wrap`.
- No house-specific setting hard-coded: everything goes through environment variables.

## Invariants not to break

- Width 696 px = 62 mm continuous tape at 300 dpi, for the 62 mm formats (compact, `--grand`, `--62rouge`).
- Compact = 696×215 (≈ 62 × 19 mm), **1-bit** image (`convert("1", dither=NONE)`), scaled down in grayscale BEFORE
  thresholding at 128.
- 29 × 90 = 991×306 landscape; the add-on rotates it for the 306-dot head.
- 62 template: each color on its own layer, scaled down then thresholded; output strictly black `(0,0,0)`, red
  `(220,0,0)`, white. No gray or pink (the black/red sorting in `brother_ql` would misclassify them). Red wins
  where they overlap.
- Fonts: Arial (`arialbd.ttf`, `arial.ttf`) then Liberation Sans (`/usr/share/fonts/truetype/liberation2/…`),
  same metrics: the layout must stay identical on the PC and in the add-on.
- An entry without `posologie` or without `personnes` is never printed (`sys.exit` in the CLI, `ValueError` in
  `depuis_fiche`).
- MQTT order not retained (`retain: False`): a retained order would replay.
- `<cle>.png` is written before any status check.

## Known pitfalls

- No automatic retry: a failure after sending may have already printed. Without a report within 60 s, check
  the label before running again (possible duplicate).
- HA entity IDs hard-coded (`sensor.etiqueteuse_brother_ql_800_etat`,
  `sensor.etiqueteuse_brother_ql_800_derniere_impression`); the ready state is the string `pret`.
- `--grand` and `--62rouge` share the 62 template; only `rouge` changes. `--29x90` and the compact format share
  `gabarit_medicament`.
- The PNG is written in the current folder, named after the key.
- `Image.Dither.NONE` requires a recent version of Pillow.

## Never commit

- The real catalog (`medicaments.json` outside `exemples/`): it is health data.
- Real first names, real medicines linked to people, generated labels (`*.png` at the root).
- Tokens (`HA_TOKEN`), IP addresses, host or domain names of a real house.
- Photos of people or of real labels.
- The examples only use the fictional first names ALEX and SAM.

## Check a change

```sh
python imprimer_medicament.py exemple500 --apercu              # → mockup exemple500.png (696x215)
python imprimer_medicament.py exemplegel --grand --apercu      # → 696x456
python imprimer_medicament.py exemplegel --62rouge --apercu    # check: black, red, white only
python imprimer_medicament.py exemple500 --29x90 --apercu      # → 991x306
python imprimer_medicament.py inventaire --apercu              # must refuse (inventory entry)
```

Open the PNGs, compare them with `docs/exemple-*.png`, then delete the PNGs produced at the root.
