#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Assemble les pages de l'album « Une semaine en Bretagne ».

    python3 outils_images.py      (une fois : fabrique les images + photos.json)
    python3 build.py              (assemble index.html et les pages de journée)

Textes, couvertures et lieux : jours.json
"""

import html, json, sys
from datetime import datetime
from pathlib import Path

RACINE = Path(__file__).resolve().parent
SITE   = RACINE / "site"
MANIF  = RACINE / "photos.json"
JOURS  = RACINE / "jours.json"

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
SEMAINE = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]

PANO    = 2.35     # au-delà : panoramique, il passe à fond perdu
PORTRAIT = 0.95    # en deçà : format vertical

# --sans-originaux : les fichiers pleine résolution ne sont pas publiés.
# Le bouton de téléchargement sert alors la version 3200 px.
SANS_ORIG = "--sans-originaux" in sys.argv


LEGENDES = {}          # id de photo -> légende, rempli depuis jours.json


def e(t): return html.escape(str(t), quote=True)
def log(*a): print(*a, flush=True)
def r(p): return p["l"] / p["h"]


# =========================================================================
#  Images : un jeu de largeurs, le navigateur choisit
# =========================================================================

# Les pages s'arrêtent à 1600 px. Sur la plus grande mise en page (≈1270 px
# affichés) cela laisse encore 1,26 fois la densité d'un écran retina, pour un
# tiers de poids en moins. Le 3200 px reste réservé à la visionneuse.
SRCSET = ("photos/w600/{i}.webp 600w, photos/w1200/{i}.webp 1200w, "
          "photos/w1600/{i}.webp 1600w")


def image(p, tailles, prioritaire=False):
    return (
        f'<picture>'
        f'<source type="image/webp" srcset="{SRCSET.format(i=p["id"])}" sizes="{tailles}">'
        f'<img src="photos/w1200/{p["id"]}.jpg" alt="" width="{p["l"]}" height="{p["h"]}"'
        f'{" fetchpriority=\"high\"" if prioritaire else " loading=\"lazy\""} decoding="async">'
        f'</picture>'
    )


def telechargement(p):
    """Adresse et nom du fichier proposé au téléchargement dans la visionneuse."""
    if not SANS_ORIG and p.get("orig"):
        return "photos/original/" + p["orig"], p["orig"]
    return "photos/w3200/" + p["id"] + ".webp", p["id"] + "-3200px.webp"


def cadre(p, tailles, classe="", legende=None, prioritaire=False):
    """Un cadre cliquable au format exact de la photo : aucun recadrage.

    La vue (boîte au format de l'image, débordement masqué) est séparée de la
    légende, qui se pose sous la photo et ne doit donc pas être rognée.
    """
    leg = (f'<figcaption class="cadre__leg">{e(legende)}</figcaption>' if legende else "")
    dl, nom = telechargement(p)
    return (
        f'<figure class="cadre {classe}" style="--r:{round(r(p), 4)}">'
        f'<span class="cadre__vue" style="background-color:{p["c"]}">'
        f'<button class="cadre__zone" type="button" data-id="{p["id"]}" data-heure="{p["heure"]}"'
        f' data-dl="{dl}" data-dlnom="{nom}" aria-label="Agrandir la photo de {p["heure"]}">'
        + image(p, tailles, prioritaire) +
        f'</button></span>'
        f'<span class="cadre__heure">{p["heure"]}</span>'
        f'{leg}</figure>'
    )


# =========================================================================
#  Moteur de composition : des blocs de rythmes différents
# =========================================================================

T_PLEINE   = "(max-width:820px) 92vw, min(1560px, 88vw)"
T_BLEED    = "100vw"
T_PANO     = "150vw"
T_DUO      = "(max-width:820px) 92vw, min(760px, 43vw)"
T_GRANDE   = "(max-width:820px) 92vw, min(900px, 51vw)"
T_PETITE   = "(max-width:820px) 68vw, min(590px, 33vw)"
T_RAIL     = "(max-width:820px) 92vw, min(1000px, 57vw)"
T_PORTRAIT = "(max-width:820px) 46vw, min(520px, 29vw)"
T_TRIPT    = "(max-width:820px) 46vw, min(520px, 30vw)"
T_TEXTE    = "(max-width:820px) 92vw, min(860px, 48vw)"

# Chaque bloc porte une animation d'apparition différente, pour que le
# défilement ne se réduise pas à la répétition d'un même volet.
REVEAL = {
    "pleine":    "rev--voile",
    "immersif":  "rev--fondu",
    "duo":       "rev--cote",
    "decale":    "rev--voile",
    "rail":      "rev--cote",
    "triptyque": "rev--zoom",
    "texte":     "rev--voile",
    "portraits": "rev--zoom",
    "pano":      "rev--fondu",
}


def bloc_pano(p, legende=None):
    """Panoramique : la photo, plus large que l'écran, dérive au défilement."""
    leg = (f'<figcaption class="pano__leg">{e(legende)}</figcaption>' if legende else "")
    dl, nom = telechargement(p)
    return (
        f'<div class="bloc bloc--pano" data-pano style="--r:{round(r(p), 4)}">'
        f'<figure class="pano" style="background-color:{p["c"]}">'
        f'<button class="pano__zone" type="button" data-id="{p["id"]}" data-heure="{p["heure"]}"'
        f' data-dl="{dl}" data-dlnom="{nom}" aria-label="Agrandir le panorama de {p["heure"]}">'
        f'<span class="pano__piste">' + image(p, T_PANO) + '</span>'
        f'</button>'
        f'<span class="pano__marque"><span class="pano__fleche"></span>panorama</span>'
        f'{leg}</figure></div>'
    )


def bloc_immersif(p, legende=None):
    """Photo pleine fenêtre, plus haute, avec sa légende posée dessus."""
    leg = (f'<figcaption class="immersif__leg"><span>{e(legende)}</span></figcaption>'
           if legende else "")
    dl, nom = telechargement(p)
    return (
        f'<div class="bloc bloc--immersif">'
        f'<figure class="immersif" style="background-color:{p["c"]}">'
        f'<button class="immersif__zone" type="button" data-id="{p["id"]}" data-heure="{p["heure"]}"'
        f' data-dl="{dl}" data-dlnom="{nom}" aria-label="Agrandir la photo de {p["heure"]}">'
        f'<span class="immersif__media">' + image(p, T_BLEED) + '</span>'
        f'<span class="immersif__ombre"></span>'
        f'</button>{leg}</figure></div>'
    )


def bloc_exergue(texte, heure=None):
    """Interlude de récit : une phrase seule, respiration dans le flux."""
    h = f'<span class="exergue__heure">{e(heure)}</span>' if heure else ""
    return (f'<div class="bloc bloc--exergue reveler">'
            f'<p class="exergue">{h}<span class="exergue__texte">{e(texte)}</span></p>'
            f'</div>')


def bloc_texte(p, legende, a_gauche):
    """Une photo et sa légende côte à côte, en vis-à-vis."""
    cote = "gauche" if a_gauche else "droite"
    return (f'<div class="bloc bloc--texte bloc--{cote}">'
            f'<div class="bloc__photo">' + cadre(p, T_TEXTE) + '</div>'
            f'<div class="bloc__mot"><span class="mot__heure">{p["heure"]}</span>'
            f'<p class="mot__texte">{e(legende)}</p></div>'
            f'</div>')


def bloc_triptyque(trois):
    parts = "".join(
        f'<div class="bloc__part" style="--poids:{round(r(x), 4)}">' + cadre(x, T_TRIPT) + '</div>'
        for x in trois)
    somme = round(sum(r(x) for x in trois), 4)
    return f'<div class="bloc bloc--triptyque" style="--somme:{somme}">{parts}</div>'


def bloc_bleed(p):
    return '<div class="bloc bloc--bleed">' + cadre(p, T_BLEED) + '</div>'


def bloc_pleine(p, legende=None):
    return ('<div class="bloc bloc--pleine">' + cadre(p, T_PLEINE, legende=legende) + '</div>')


def bloc_duo(a, b, legendes):
    somme = round(r(a) + r(b), 4)
    return (f'<div class="bloc bloc--duo" style="--somme:{somme}">'
            f'<div class="bloc__part" style="--poids:{round(r(a),4)}">'
            + cadre(a, T_DUO, legende=legendes.get(a["id"])) + '</div>'
            f'<div class="bloc__part" style="--poids:{round(r(b),4)}">'
            + cadre(b, T_DUO, legende=legendes.get(b["id"])) + '</div>'
            f'</div>')


def bloc_decale(a, b, a_gauche, legendes):
    grande, petite = (a, b) if r(a) >= r(b) else (b, a)
    cote = "gauche" if a_gauche else "droite"
    return (f'<div class="bloc bloc--decale bloc--{cote}">'
            f'<div class="bloc__grande">'
            + cadre(grande, T_GRANDE, legende=legendes.get(grande["id"])) + '</div>'
            f'<div class="bloc__petite">' + cadre(petite, T_PETITE) + '</div>'
            f'</div>')


def bloc_rail(p, jour, n, a_gauche, legende=None):
    cote = "gauche" if a_gauche else "droite"
    mot = f'<span class="rail__mot">{e(legende)}</span>' if legende else ""
    rail = (f'<div class="bloc__rail">'
            f'<span class="rail__n">{n:02d}</span>'
            f'<span class="rail__trait"></span>'
            f'<span class="rail__heure">{p["heure"]}</span>'
            f'<span class="rail__lieu">{e(jour["lieu"])}</span>'
            f'{mot}</div>')
    return (f'<div class="bloc bloc--rail bloc--{cote}">'
            f'<div class="bloc__photo">' + cadre(p, T_RAIL) + '</div>' + rail + '</div>')


def bloc_portraits(a, b, legendes):
    return ('<div class="bloc bloc--portraits">'
            + cadre(a, T_PORTRAIT, legende=legendes.get(a["id"]))
            + cadre(b, T_PORTRAIT, legende=legendes.get(b["id"])) + '</div>')


# Rythmes : aucun motif ne revient deux fois de suite, et « pleine » n'est
# plus le motif par défaut — il alterne avec « immersif », « rail », « texte ».
CYCLE_ACCUEIL = ["immersif", "duo", "rail", "triptyque", "decale",
                 "texte", "duo", "pleine", "rail", "triptyque"]
CYCLE_JOUR    = ["immersif", "rail", "duo", "texte", "triptyque",
                 "pleine", "decale", "rail", "duo", "immersif", "triptyque", "texte"]

SOLO = ["immersif", "pleine", "rail", "texte"]      # replis quand il ne reste qu'une photo


def composer(photos, jour, cycle, legendes=None, recit=None):
    """Parcourt les photos dans l'ordre et alterne les rythmes de mise en page.

    Les interludes de récit sont insérés après la photo qu'ils désignent.
    """
    legendes = legendes or {}
    apres = {x["apres"]: x for x in (recit or []) if x.get("apres")}
    out, i, k, solo, cote = [], 0, 0, 0, 0
    precedent = None
    n = len(photos)

    def poser(html, utilisees, motif):
        out.append(html.replace('class="bloc ', f'class="bloc {REVEAL.get(motif, "")} ', 1))
        for x in utilisees:
            if x["id"] in apres:
                out.append(bloc_exergue(apres[x["id"]]["texte"], x["heure"]))

    while i < n:
        p = photos[i]
        leg = legendes.get(p["id"])

        if r(p) >= PANO:                                   # panoramique : traitement à part
            poser(bloc_pano(p, leg), [p], "pano"); i += 1; precedent = "pano"; continue

        suiv  = photos[i + 1] if i + 1 < n else None
        suiv2 = photos[i + 2] if i + 2 < n else None
        paire = suiv is not None and r(suiv) < PANO
        trio  = paire and suiv2 is not None and r(suiv2) < PANO

        if r(p) < PORTRAIT and suiv is not None and r(suiv) < PORTRAIT:
            poser(bloc_portraits(p, suiv, legendes), [p, suiv], "portraits"); i += 2; k += 1; precedent = "portraits"; continue

        motif = cycle[k % len(cycle)]
        if motif == "triptyque" and not trio:
            motif = "duo" if paire else None
        if motif in ("duo", "decale") and not paire:
            motif = None
        if motif == "texte" and not leg:
            motif = None
        if motif is None:                                  # repli : on tourne, jamais deux fois pareil
            motif = SOLO[solo % len(SOLO)]
            if motif == "texte" and not leg:
                motif = "immersif" if solo % 2 else "pleine"
            solo += 1

        if motif == precedent:              # jamais deux blocs identiques de suite
            secours = [m for m in SOLO if m != precedent and (m != "texte" or leg)]
            if secours:
                motif = secours[solo % len(secours)]
                solo += 1

        if motif == "duo":
            poser(bloc_duo(p, suiv, legendes), [p, suiv], motif); i += 2
        elif motif == "triptyque":
            poser(bloc_triptyque([p, suiv, suiv2]), [p, suiv, suiv2], motif); i += 3
        elif motif == "decale":
            poser(bloc_decale(p, suiv, cote % 2 == 0, legendes), [p, suiv], motif); i += 2; cote += 1
        elif motif == "rail":
            poser(bloc_rail(p, jour, i + 1, cote % 2 == 0, leg), [p], motif); i += 1; cote += 1
        elif motif == "texte":
            poser(bloc_texte(p, leg, cote % 2 == 0), [p], motif); i += 1; cote += 1
        elif motif == "immersif":
            poser(bloc_immersif(p, leg), [p], motif); i += 1
        else:
            poser(bloc_pleine(p, leg), [p], motif); i += 1
        precedent = motif
        k += 1

    return "".join(out)


# =========================================================================
#  Fragments de page
# =========================================================================

def tete(titre, description, couv, corps_classe):
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<script>document.documentElement.className+=" js";</script>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(titre)}</title>
<meta name="description" content="{e(description)}">
<meta name="theme-color" content="#f6f3ee">
<meta name="robots" content="noindex, nofollow">
<meta property="og:title" content="{e(titre)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:image" content="photos/w1200/{couv}.jpg">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="preload" as="image" href="photos/w1600/{couv}.webp" type="image/webp" fetchpriority="high">
<link rel="stylesheet" href="style.css">
</head>
<body class="{corps_classe}">
<div class="grain" aria-hidden="true"></div>
<div class="progres" id="progres" aria-hidden="true"><span></span></div>
<a class="saut" href="#contenu">Aller au contenu</a>
"""


def barre(jours, accueil, courant=None):
    liens = "".join(
        f'<a class="onglet{" actif" if j["id"] == courant else ""}" '
        f'href="{("#" + j["id"]) if accueil else ("index.html#" + j["id"])}" data-jour="{j["id"]}">'
        f'<span class="onglet__n">{j["n"]}</span><span class="onglet__t">{e(j["court"])}</span></a>'
        for j in jours
    )
    accueil_lien = "#haut" if accueil else "index.html"
    return f"""<header class="barre" id="barre">
  <div class="barre__int">
    <a class="barre__titre" href="{accueil_lien}">
      {"" if accueil else '<span class="barre__ret" aria-hidden="true"></span>'}
      <span class="barre__titre-p">Une semaine en</span><span class="barre__titre-g">Bretagne</span>
    </a>
    <nav class="onglets" id="onglets" aria-label="Journées">{liens}</nav>
  </div>
</header>
"""


def ouvrir_jour(j, texte="Voir cette journée seule"):
    return (f'<a class="ouvrir" href="{j["fichier"]}">'
            f'<span class="ouvrir__txt">{e(texte)}</span>'
            f'<span class="ouvrir__rond"><svg viewBox="0 0 24 24" aria-hidden="true">'
            f'<path d="M7 17L17 7M9 7h8v8"/></svg></span></a>')


def couverture_jour(j, prioritaire):
    c = j["couverture"]
    return f"""
  <div class="entree" style="view-transition-name:couv{j['n']};background-color:{c['c']}">
    <picture class="entree__media">
      <source type="image/webp" srcset="{SRCSET.format(i=c['id'])}" sizes="100vw">
      <img src="photos/w1200/{c['id']}.jpg" alt="{e(j['lieu'])}"
           {'fetchpriority="high"' if prioritaire else 'loading="lazy"'} decoding="async">
    </picture>
    <span class="entree__voile"></span>
    <div class="entree__texte">
      <p class="entree__n"><span class="masque"><span class="monte">Jour {j['n']:02d}</span></span></p>
      <h2 class="entree__lieu"><span class="masque"><span class="monte">{e(j['lieu'])}</span></span></h2>
      <p class="entree__meta"><span class="masque"><span class="monte">{e(j['libelle'])}
         <span class="pastille"></span> {len(j['photos'])} photos</span></span></p>
      {f'<p class="entree__leg">{e(j["legende"])}</p>' if j["legende"] else ''}
    </div>
    {ouvrir_jour(j)}
  </div>"""


def pied(album, total, njours, jours):
    plan = "".join(f'<a href="{j["fichier"]}">{e(j["lieu"])}</a>' for j in jours)
    return f"""
<footer class="pied">
  <div class="pied__int">
    <p class="pied__titre">{e(album.get('titre',''))}</p>
    <p class="pied__sous">{total} photos <span class="pastille"></span> {njours} journées
       <span class="pastille"></span> {e(album.get('sousTitre',''))}</p>
    <nav class="pied__plan" aria-label="Pages par journée">{plan}</nav>
    <a class="pied__haut" href="#haut"><span>Revenir en haut</span></a>
  </div>
</footer>
"""


def visionneuse():
    return """
<div class="visio" id="visio" role="dialog" aria-modal="true" aria-label="Photo en plein écran" hidden>
  <div class="visio__fond" data-fermer></div>
  <figure class="visio__scene">
    <picture>
      <source id="visio-src" type="image/webp">
      <img class="visio__img" id="visio-img" alt="" decoding="async">
    </picture>
  </figure>
  <div class="visio__haut">
    <span class="visio__lieu" id="visio-lieu"></span>
    <div class="visio__actions">
      <a class="visio__btn visio__btn--dl" id="visio-dl" download
         aria-label="Télécharger la photo d'origine" title="Télécharger l'original">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 4v11m0 0l-4.5-4.5M12 15l4.5-4.5M5 19h14"/></svg>
      </a>
      <button class="visio__btn visio__btn--fermer" id="visio-fermer" aria-label="Fermer (Échap)">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
    </div>
  </div>
  <button class="visio__nav visio__nav--prec" id="visio-prec" aria-label="Photo précédente">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>
  </button>
  <button class="visio__nav visio__nav--suiv" id="visio-suiv" aria-label="Photo suivante">
    <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg>
  </button>
  <div class="visio__bas">
    <span class="visio__qualite" id="visio-qualite">pleine qualité</span>
    <span class="visio__compte" id="visio-compte"></span>
  </div>
</div>
<div class="curseur" id="curseur" aria-hidden="true"><span>Agrandir</span></div>
<script src="script.js" defer></script>
"""


# =========================================================================
#  Pages
# =========================================================================

def page_accueil(album, jours):
    index = {p["id"]: p for j in jours for p in j["photos"]}
    c = index.get(album.get("couverture")) or jours[0]["couverture"]
    total = sum(len(j["photos"]) for j in jours)

    sommaire = "".join(f"""
    <li class="som__item reveler">
      <a class="som__lien" href="#{j['id']}">
        <span class="som__n">{j['n']:02d}</span>
        <span class="som__vig" style="background-color:{j['couverture']['c']}">
          <img src="photos/w600/{j['couverture']['id']}.webp" alt="" loading="lazy" decoding="async">
        </span>
        <span class="som__lieu">{e(j['lieu'])}</span>
        <span class="som__date">{e(j['libelle'])}</span>
        <span class="som__nb">{len(j['photos'])}</span>
      </a>
      <a class="som__page" href="{j['fichier']}" aria-label="Ouvrir la page « {e(j['lieu'])} »" title="Page dédiée">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 17L17 7M9 7h8v8"/></svg>
      </a>
    </li>""" for j in jours)

    sections = "".join(f"""
<section class="jour" id="{j['id']}">
  {couverture_jour(j, prioritaire=(i == 0))}
  <div class="jour__corps">
    <aside class="jour__rail" aria-hidden="true">
      <div class="jour__rail-int">Jour {j['n']:02d} <span class="pastille"></span> {e(j['lieu'])}</div>
    </aside>
    <div class="jour__flux">{composer(j['photos'], j, CYCLE_ACCUEIL, LEGENDES, j['recit'])}</div>
  </div>
  <div class="jour__fin">{ouvrir_jour(j, 'Revoir cette journée seule')}</div>
</section>""" for i, j in enumerate(jours))

    return (
        tete(f"{album.get('titre','Album')} — {album.get('sousTitre','')}",
             album.get("intro", ""), c["id"], "page-accueil")
        + barre(jours, accueil=True)
        + f"""
<section class="hero" id="haut">
  <picture class="hero__media">
    <source type="image/webp" srcset="{SRCSET.format(i=c['id'])}" sizes="100vw">
    <img src="photos/w1200/{c['id']}.jpg" alt="" fetchpriority="high" decoding="async">
  </picture>
  <span class="hero__voile"></span>
  <div class="hero__texte">
    <p class="hero__sur"><span class="masque"><span class="monte">{e(album.get('sousTitre',''))}</span></span></p>
    <h1 class="hero__titre"><span class="masque"><span class="monte">{e(album.get('titre',''))}</span></span></h1>
    <p class="hero__intro">{e(album.get('intro',''))}</p>
    <p class="hero__chiffres">{total} photos <span class="pastille"></span> {len(jours)} journées</p>
  </div>
  <a class="hero__fleche" href="#contenu" aria-label="Descendre"><span></span></a>
</section>

<nav class="som" id="contenu" aria-label="Les journées">
  <p class="som__sur reveler">Le carnet</p>
  <ol class="som__liste">{sommaire}</ol>
</nav>

<main class="jours">{sections}</main>
"""
        + pied(album, total, len(jours), jours) + visionneuse() + "</body>\n</html>\n"
    )


def page_jour(album, jours, j):
    c = j["couverture"]
    prec = jours[j["n"] - 2] if j["n"] > 1 else None
    suiv = jours[j["n"]] if j["n"] < len(jours) else None

    def voisin(v, sens):
        if not v:
            return '<span class="voisin voisin--vide"></span>'
        return (f'<a class="voisin voisin--{sens}" href="{v["fichier"]}">'
                f'<span class="voisin__sur">{"Journée précédente" if sens == "prec" else "Journée suivante"}</span>'
                f'<span class="voisin__lieu">{e(v["lieu"])}</span>'
                f'<span class="voisin__date">{e(v["libelle"])}</span></a>')

    return (
        tete(f"{j['lieu']} — {j['libelle']} · {album.get('titre','')}",
             j["legende"] or j["lieu"], c["id"], "page-jour")
        + barre(jours, accueil=False, courant=j["id"])
        + f"""
<section class="entete" id="contenu" style="view-transition-name:couv{j['n']};background-color:{c['c']}">
  <picture class="entete__media">
    <source type="image/webp" srcset="{SRCSET.format(i=c['id'])}" sizes="100vw">
    <img src="photos/w1200/{c['id']}.jpg" alt="" fetchpriority="high" decoding="async">
  </picture>
  <span class="entete__voile"></span>
  <div class="entete__texte">
    <p class="entete__n"><span class="masque"><span class="monte">Jour {j['n']:02d} sur {len(jours)}</span></span></p>
    <h1 class="entete__titre"><span class="masque"><span class="monte">{e(j['lieu'])}</span></span></h1>
    <p class="entete__meta"><span class="masque"><span class="monte">{e(j['libelle'])}
       <span class="pastille"></span> {len(j['photos'])} photos</span></span></p>
    {f'<p class="entete__leg">{e(j["legende"])}</p>' if j["legende"] else ''}
  </div>
  <a class="entete__retour" href="index.html#{j['id']}">
    <span class="ouvrir__rond"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg></span>
    <span class="ouvrir__txt">Le carnet complet</span>
  </a>
</section>

<main class="journee">
  <div class="jour__flux">{composer(j['photos'], j, CYCLE_JOUR, LEGENDES, j['recit'])}</div>
</main>

<nav class="voisins" aria-label="Autres journées">{voisin(prec, 'prec')}{voisin(suiv, 'suiv')}</nav>
"""
        + pied(album, sum(len(x["photos"]) for x in jours), len(jours), jours)
        + visionneuse() + "</body>\n</html>\n"
    )


# =========================================================================
#  Assemblage
# =========================================================================

def main():
    if not MANIF.exists():
        sys.exit("photos.json absent — lancer d'abord : python3 outils_images.py")

    photos = json.loads(MANIF.read_text(encoding="utf-8"))
    textes = json.loads(JOURS.read_text(encoding="utf-8")) if JOURS.exists() else {}
    meta, album = textes.get("jours", {}), textes.get("album", {})

    global LEGENDES
    LEGENDES = textes.get("legendes", {})

    par_date = {}
    for p in photos:
        par_date.setdefault(p["jour"], []).append(p)

    jours = []
    for n, (date, liste) in enumerate(sorted(par_date.items()), 1):
        t = meta.get(date, {})
        d = datetime.strptime(date, "%Y-%m-%d")
        libelle = t.get("libelle") or f"{SEMAINE[d.weekday()]} {d.day} {MOIS[d.month-1]}"
        idx = {p["id"]: p for p in liste}
        couv = t.get("couverture") if t.get("couverture") in idx else liste[0]["id"]
        jours.append(dict(
            n=n, id=f"jour-{n}", fichier=f"jour-{n}.html", date=date,
            libelle=libelle.capitalize(),
            court=t.get("court") or f"{d.day} {MOIS[d.month-1]}",
            lieu=t.get("lieu") or libelle.capitalize(),
            legende=t.get("legende", ""),
            recit=t.get("recit", []),
            couverture=idx[couv], photos=liste,
        ))

    SITE.mkdir(parents=True, exist_ok=True)
    (SITE / "index.html").write_text(page_accueil(album, jours), encoding="utf-8")
    for j in jours:
        (SITE / j["fichier"]).write_text(page_jour(album, jours, j), encoding="utf-8")

    log(f"✓ {len(photos)} photos · {len(jours)} journées")
    for j in jours:
        log(f"   {j['fichier']:<12} {len(j['photos']):>2} photos   {j['lieu']}")
    log(f"✓ index.html + {len(jours)} pages de journée")


if __name__ == "__main__":
    main()
