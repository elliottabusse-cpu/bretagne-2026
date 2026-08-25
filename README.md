# Une semaine en Bretagne — album photo

Site statique, sans framework ni dépendance : HTML, CSS et JavaScript à la main.
90 photos réparties sur 6 journées, du 14 au 20 août 2026.

## Organisation

```
originaux/            les 90 fichiers sources, jamais modifiés (436 Mo, dont 2 RAW .ORF et 1 .heic)
jours.json            TOUS les textes du site : titres, lieux, légendes, couvertures, sélections
build.py              génère les images web et les pages HTML
site/                 ← le dossier à mettre en ligne
  index.html            accueil : couverture + sommaire + un chapitre par journée
  jour-1.html … jour-6.html   une page par journée
  style.css / script.js
  photos/thumbs/        700 px  · webp + jpg — mosaïques
  photos/full/         2400 px  · webp + jpg — visionneuse, affichée aussitôt
  photos/hd/           3840 px  · webp      — pleine qualité, chargée à la demande
```

## Modifier les textes

Tout est dans `jours.json` : titre de l'album, sous-titre, intro, et pour chaque
journée son lieu, sa légende, sa photo de couverture et la sélection montrée sur
l'accueil. Ensuite :

```bash
python3 build.py --pages
```

C'est instantané : les images ne sont pas retouchées.

## Regénérer les images

```bash
python3 build.py            # ne traite que les images manquantes
python3 build.py --force    # refait les 90 photos (environ 6 minutes)
```

Ajouter des photos : les déposer dans `originaux/`, puis `python3 build.py`.
Elles sont classées automatiquement par date de prise de vue (EXIF) ; une
nouvelle journée apparaît toute seule et peut être décrite dans `jours.json`.

Formats lus : jpg, png, tif, ainsi que heic et les RAW (orf, cr2, nef, dng, arw)
via `sips`, l'outil intégré à macOS.

## Voir le site en local

```bash
python3 -m http.server 4173 --directory site
```

Puis http://localhost:4173

## Mettre en ligne

**Netlify** — le plus simple : glisser le dossier `site/` sur
[app.netlify.com/drop](https://app.netlify.com/drop). Rien d'autre à faire.
En reliant plutôt un dépôt Git, `netlify.toml` est déjà configuré (`publish = "site"`,
cache long sur les images).

**GitHub Pages** — pousser le dépôt, puis dans *Settings → Pages* choisir la
branche et le dossier `/site`. Le fichier `.nojekyll` est déjà présent, il évite
que GitHub ignore certains fichiers.

Le site pèse environ 180 Mo. Pour l'alléger si besoin :

```bash
rm site/photos/hd/*.webp     # −84 Mo : la visionneuse reste en 2400 px
rm site/photos/full/*.jpg    # −51 Mo : abandonne le repli JPEG (WebP seul)
```

## Détails d'implémentation

- **Chargement progressif** : les miniatures sont en `loading="lazy"`, et chaque
  vignette affiche d'abord la couleur dominante de sa photo — pas de saut de
  mise en page pendant le chargement.
- **Qualité au clic** : la visionneuse montre immédiatement le 2400 px, puis
  bascule sur le 3840 px dès qu'il est téléchargé, et seulement pour la photo
  réellement regardée. Le voisinage est préchargé en 2400 px.
- **Mosaïques** : les rangées sont calculées en JavaScript à partir des
  proportions réelles. Le nombre de photos par rangée suit un motif (3, puis 2,
  puis 4…) pour éviter l'effet grille. Aucune photo n'est recadrée ; les
  panoramiques occupent une rangée entière.
- **Sans JavaScript** : les pages restent lisibles, seule la mise en page
  justifiée devient une grille simple.
- **Confort** : `prefers-reduced-motion` désactive animations et parallaxe ;
  la visionneuse se ferme au bouton retour du téléphone ; navigation au clavier
  (← → Échap Début Fin) et au doigt (glisser).
- **Vie privée** : `robots.txt` et `noindex` empêchent le référencement, et les
  métadonnées EXIF (dont la géolocalisation) sont retirées des images publiées.
