# Une semaine en Bretagne — album photo

Site statique, HTML/CSS/JS pur. Aucun framework, aucune dépendance, aucun backend.

## Organisation

```
originaux/          les 90 fichiers d'origine — jamais modifiés
photos.json         manifeste généré (dimensions, couleurs, dates EXIF)
jours.json          ← LES TEXTES SE MODIFIENT ICI
outils_images.py    fabrique les déclinaisons d'images
build.py            assemble les pages HTML
site/               ← LE DOSSIER À DÉPLOYER
```

## Modifier les textes

Tout se règle dans `jours.json` : titre de l'album, sous-titre, intro, photo de
couverture, et pour chaque journée le lieu, la légende et sa photo d'ouverture.

```bash
python3 build.py
```

Regénère `index.html` et les six pages de journée en une seconde. Les images ne
sont pas retouchées.

## Refabriquer les images

```bash
python3 outils_images.py
```

Ne recalcule que ce qui manque. `--force` refait tout, `--sans-originaux`
n'expose pas les fichiers source.

## Les niveaux d'image

| dossier | côté long | usage |
|---|---|---|
| `w600` | 600 px | mobile, vignettes du sommaire |
| `w1200` | 1200 px | affichage courant (+ JPEG de secours) |
| `w2000` | 2000 px | **plafond des pages** |
| `w3200` | 3200 px | visionneuse uniquement |
| `original` | natif 5184 px | bouton de téléchargement |

Le navigateur choisit tout seul via `srcset`/`sizes` : il ne télécharge jamais
plus gros que nécessaire.

**Les pages s'arrêtent à 2000 px.** Au-delà le gain visuel est nul — l'image y
est toujours vue réduite — alors que le poids double. Les trois premiers
paliers sont compressés en qualité 76 pour la légèreté ; le `w3200`, lui,
garde la qualité 84 car il est regardé en grand.

Dans la visionneuse, la photo s'affiche d'abord en 1200 px puis se remplace par
le palier adapté à l'écran, jusqu'à 3200 px — la mention « pleine qualité »
apparaît quand c'est fait. Le bouton de téléchargement sert l'original.

Régénérer un seul palier : supprimer son dossier et relancer
`python3 outils_images.py` — les autres ne sont pas retouchés.

## Déploiement

### Netlify

Glisser-déposer le dossier `site/` sur https://app.netlify.com/drop.
Ou, en ligne de commande :

```bash
npx netlify-cli deploy --dir=site --prod
```

### GitHub Pages

```bash
git init && git add . && git commit -m "Album Bretagne"
git branch -M main && git remote add origin <URL-de-votre-dépôt>
git push -u origin main
```

Puis, dans *Settings → Pages*, choisir la branche `main` et le dossier `/site`.

> GitHub Pages plafonne à 1 Go par site. Avec les originaux (419 Mo) on reste
> dessous, mais les envois sont lents. Pour un dépôt léger, relancer
> `python3 outils_images.py --sans-originaux` et supprimer `site/photos/original`
> — le bouton de téléchargement disparaît alors de la visionneuse.

## Ce que fait le site

- **Accueil** : les 90 photos, dans l'ordre chronologique, réparties en six
  journées. Six rythmes de mise en page alternent (pleine largeur, duo,
  photo décalée, rail typographique, panoramique à fond perdu, paire de
  portraits) — aucune photo n'est recadrée, chacune garde son format exact.
- **Une page par journée** : accessible depuis le sommaire (flèche ↗ à droite),
  depuis chaque ouverture de journée et depuis le pied de page.
- **Sommaire** : cliquer sur une ligne descend jusqu'à la journée dans la page.
- **Visionneuse** : clavier (← → Échap Début Fin), glissement du doigt,
  bouton retour du téléphone, téléchargement de l'original.
- Chargement paresseux, révélation progressive au défilement, parallaxe,
  transitions entre pages, respect de `prefers-reduced-motion`.

## Aperçu local

```bash
python3 -m http.server 4173 --directory site
```

Puis ouvrir http://localhost:4173
