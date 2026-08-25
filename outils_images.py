#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fabrique toutes les déclinaisons web des photos + le manifeste photos.json.

    python3 outils_images.py                 les niveaux manquants
    python3 outils_images.py --force         tout refaire
    python3 outils_images.py --sans-originaux    n'expose pas les fichiers source

Sources : originaux/   (jamais modifié)
Sortie  : site/photos/w600 w1200 w2000 w3200 original/ + photos.json
"""

import json, shutil, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

RACINE = Path(__file__).resolve().parent
SRC    = RACINE / "originaux"
SITE   = RACINE / "site"
PHOTOS = SITE / "photos"
MANIF  = RACINE / "photos.json"

# largeur maximale du côté long, qualité webp, doublon jpeg de secours
#
# Les trois premiers paliers servent les pages : ils sont réglés pour la
# légèreté, l'image y est toujours vue réduite. Le w3200 ne sert que la
# visionneuse, où la photo est regardée en grand : il garde sa qualité haute.
NIVEAUX = [
    ("w600",   600, 76, False),
    ("w1200", 1200, 76, True),
    ("w1600", 1600, 74, False),
    ("w3200", 3200, 84, False),
]

EXT_DIRECT = {".jpg", ".jpeg", ".png", ".tif", ".tiff"}
EXT_SIPS   = {".heic", ".heif", ".orf", ".cr2", ".nef", ".dng", ".arw"}

FORCE = "--force" in sys.argv
SANS_ORIG = "--sans-originaux" in sys.argv


def log(*a): print(*a, flush=True)


def ouvrir(chemin: Path) -> Image.Image:
    if chemin.suffix.lower() in EXT_SIPS:
        tmp = Path(tempfile.mkdtemp()) / (chemin.stem + ".jpg")
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "100",
                        str(chemin), "--out", str(tmp)], check=True, capture_output=True)
        im = Image.open(tmp)
    else:
        im = Image.open(chemin)
    im = ImageOps.exif_transpose(im)
    return im.convert("RGB") if im.mode != "RGB" else im


def date_prise(chemin: Path) -> datetime:
    if chemin.suffix.lower() in EXT_DIRECT:
        try:
            ex = Image.open(chemin).getexif()
            brut = ex.get(36867) or ex.get(306) or ex.get_ifd(0x8769).get(36867)
            if brut:
                return datetime.strptime(str(brut).strip(), "%Y:%m:%d %H:%M:%S")
        except Exception:
            pass
    return datetime.fromtimestamp(chemin.stat().st_mtime)


def couleur(im: Image.Image) -> str:
    p = im.copy(); p.thumbnail((24, 24), Image.Resampling.LANCZOS)
    px = list(p.getdata()); n = len(px)
    r, g, b = (sum(c[i] for c in px) // n for i in range(3))
    return "#%02x%02x%02x" % (int(r * .84), int(g * .84), int(b * .84))


def main():
    if not SRC.is_dir():
        sys.exit(f"Dossier source introuvable : {SRC}")

    sources = sorted(p for p in SRC.iterdir()
                     if p.suffix.lower() in EXT_DIRECT | EXT_SIPS and not p.name.startswith("."))
    log(f"{len(sources)} photos source\n")

    for nom, *_ in NIVEAUX:
        (PHOTOS / nom).mkdir(parents=True, exist_ok=True)
    if not SANS_ORIG:
        (PHOTOS / "original").mkdir(parents=True, exist_ok=True)

    anciens = {}
    if MANIF.exists() and not FORCE:
        try:
            anciens = {p["id"]: p for p in json.loads(MANIF.read_text(encoding="utf-8"))}
        except Exception:
            pass

    fiches = []
    for i, src in enumerate(sources, 1):
        base = src.stem

        # on ne refait que les paliers réellement absents : supprimer un dossier
        # suffit donc à le régénérer seul, sans toucher aux autres
        a_faire = [n for n in NIVEAUX
                   if FORCE or not (PHOTOS / n[0] / f"{base}.webp").exists()]

        if not a_faire and base in anciens:
            fiches.append(anciens[base])
            continue

        im = ouvrir(src)
        L, H = im.size
        c = couleur(im)

        for nom, maxi, q, avec_jpeg in a_faire:
            cp = im.copy()
            cp.thumbnail((maxi, maxi), Image.Resampling.LANCZOS)
            cp.save(PHOTOS / nom / f"{base}.webp", "WEBP", quality=q, method=6)
            if avec_jpeg:
                cp.save(PHOTOS / nom / f"{base}.jpg", "JPEG", quality=q + 4,
                        optimize=True, progressive=True)

        # fichier téléchargeable : l'original tel quel, ou sa conversion pleine résolution
        orig_nom = ""
        if not SANS_ORIG:
            if src.suffix.lower() in EXT_DIRECT:
                orig_nom = base + src.suffix.lower()
                cible = PHOTOS / "original" / orig_nom
                if not cible.exists() or FORCE:
                    shutil.copy2(src, cible)
            else:
                orig_nom = base + ".jpg"
                cible = PHOTOS / "original" / orig_nom
                if not cible.exists() or FORCE:
                    im.save(cible, "JPEG", quality=97, optimize=True,
                            subsampling=0, progressive=True)

        quand = date_prise(src)
        im.close()

        fiches.append(dict(id=base, l=L, h=H, c=c, orig=orig_nom,
                           jour=quand.strftime("%Y-%m-%d"),
                           heure=quand.strftime("%H:%M"),
                           ts=quand.strftime("%Y-%m-%d %H:%M:%S")))
        log(f"  [{i:>2}/{len(sources)}] {base}  {L}x{H}  {c}")

    fiches.sort(key=lambda p: p["ts"])
    MANIF.write_text(json.dumps(fiches, ensure_ascii=False, indent=1), encoding="utf-8")

    log(f"\n✓ {len(fiches)} photos · manifeste photos.json écrit")
    for nom, *_ in NIVEAUX:
        d = PHOTOS / nom
        taille = sum(f.stat().st_size for f in d.iterdir()) / 1048576
        log(f"   {nom:<9} {len(list(d.iterdir())):>3} fichiers  {taille:7.1f} Mo")
    if not SANS_ORIG:
        d = PHOTOS / "original"
        taille = sum(f.stat().st_size for f in d.iterdir()) / 1048576
        log(f"   original  {len(list(d.iterdir())):>3} fichiers  {taille:7.1f} Mo")


if __name__ == "__main__":
    main()
