/* =========================================================================
   Une semaine en Bretagne
   Apparitions, parallaxe, curseur, visionneuse plein écran.
   Vanilla JS, aucune dépendance.
   ========================================================================= */

(function () {
  "use strict";

  var $  = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return [].slice.call((c || document).querySelectorAll(s)); };

  var doux  = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var souris = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  var WEBP = (function () {
    try {
      return document.createElement("canvas")
        .toDataURL("image/webp").indexOf("data:image/webp") === 0;
    } catch (e) { return false; }
  })();

  requestAnimationFrame(function () { document.body.classList.add("pret"); });
  if (souris) document.body.classList.add("souris");

  /* largeur utile réelle : sert aux blocs à fond perdu (hors barre de défilement) */
  function majLargeur() {
    document.documentElement.style.setProperty(
      "--vw", document.documentElement.clientWidth + "px");
  }
  majLargeur();
  window.addEventListener("resize", majLargeur, { passive: true });

  /* =======================================================================
     1. Apparitions au défilement
     ======================================================================= */

  var aReveler = $$(".cadre, .reveler, .som__item, .entree, .bloc__rail");

  if ("IntersectionObserver" in window) {
    var oeil = new IntersectionObserver(function (lot) {
      var n = 0;
      lot.forEach(function (x) {
        if (!x.isIntersecting) return;
        x.target.style.transitionDelay = Math.min(n++, 6) * 70 + "ms";
        x.target.classList.add("vu");
        oeil.unobserve(x.target);
      });
    }, { rootMargin: "0px 0px -5% 0px", threshold: 0 });
    aReveler.forEach(function (n) { oeil.observe(n); });
  } else {
    aReveler.forEach(function (n) { n.classList.add("vu"); });
  }

  /* =======================================================================
     2. Parallaxe des images pleine fenêtre
     ======================================================================= */

  var parallaxe = [];

  if (doux) {
    $$(".hero__media, .entree__media, .entete__media").forEach(function (media) {
      var cadre = media.parentNode;
      var img = $("img", media);
      if (cadre && img) parallaxe.push({ cadre: cadre, img: img, actif: true });
    });

    if ("IntersectionObserver" in window) {
      parallaxe.forEach(function (p) { p.actif = false; });
      var veille = new IntersectionObserver(function (lot) {
        lot.forEach(function (x) {
          parallaxe.forEach(function (p) {
            if (p.cadre === x.target) p.actif = x.isIntersecting;
          });
        });
      }, { rootMargin: "150px 0px" });
      parallaxe.forEach(function (p) { veille.observe(p.cadre); });
    }
  }

  function majParallaxe() {
    var vh = window.innerHeight;
    parallaxe.forEach(function (p) {
      if (!p.actif) return;
      var b = p.cadre.getBoundingClientRect();
      var avance = (vh / 2 - (b.top + b.height / 2)) / ((vh + b.height) / 2);
      p.img.style.setProperty("--p", (avance * b.height * 0.07).toFixed(1) + "px");
    });
  }

  /* =======================================================================
     3. Fil de progression, barre, journée active
     ======================================================================= */

  var progres = $("#progres span");
  var barre   = $("#barre");
  var hero    = $(".hero");
  var sections = $$(".jour");
  var onglets  = $$(".onglet");
  var courant = null;
  var enAttente = false;

  if (barre && !hero) barre.classList.add("visible");

  function auDefilement() {
    var y = window.scrollY || window.pageYOffset;
    var course = document.documentElement.scrollHeight - window.innerHeight;

    if (progres) progres.style.transform = "scaleX(" + (course > 0 ? y / course : 0) + ")";
    if (barre && hero) barre.classList.toggle("visible", y > hero.offsetHeight - 110);

    if (sections.length) {
      var seuil = parseFloat(getComputedStyle(document.documentElement)
        .getPropertyValue("--barre-h")) + 60;
      var id = null;
      /* getBoundingClientRect : indépendant du parent positionné */
      sections.forEach(function (s) { if (s.getBoundingClientRect().top <= seuil) id = s.id; });
      if (id !== courant) {
        courant = id;
        onglets.forEach(function (o) {
          var on = o.dataset.jour === id;
          o.classList.toggle("actif", on);
          if (on) centrer(o);
        });
      }
    }

    majParallaxe();
    enAttente = false;
  }

  function centrer(o) {
    var z = o.parentNode;
    var cible = o.offsetLeft - (z.clientWidth - o.offsetWidth) / 2;
    if (z.scrollTo) z.scrollTo({ left: cible, behavior: "smooth" });
    else z.scrollLeft = cible;
  }

  window.addEventListener("scroll", function () {
    if (!enAttente) { enAttente = true; requestAnimationFrame(auDefilement); }
  }, { passive: true });
  window.addEventListener("resize", auDefilement, { passive: true });
  auDefilement();

  var dejaActif = $(".onglet.actif");
  if (dejaActif) centrer(dejaActif);

  /* =======================================================================
     4. Curseur personnalisé
     ======================================================================= */

  var curseur = $("#curseur");
  if (curseur && souris && doux) {
    var cx = 0, cy = 0, pose = false;

    document.addEventListener("mousemove", function (ev) {
      cx = ev.clientX; cy = ev.clientY;
      if (!pose) {
        pose = true;
        requestAnimationFrame(function () {
          curseur.style.transform =
            "translate3d(" + cx + "px," + cy + "px,0) translate(-50%,-50%)" +
            (curseur.classList.contains("actif") ? " scale(1)" : " scale(.3)");
          pose = false;
        });
      }
    }, { passive: true });

    document.addEventListener("mouseover", function (ev) {
      var sur = ev.target.closest && ev.target.closest(".cadre__zone");
      curseur.classList.toggle("actif", !!sur && $("#visio").hidden);
    }, { passive: true });
  }

  /* =======================================================================
     5. Visionneuse plein écran
     ======================================================================= */

  var visio = $("#visio");
  if (!visio) return;

  var vImg    = $("#visio-img");
  var vSrc    = $("#visio-src");
  var vLieu   = $("#visio-lieu");
  var vCompte = $("#visio-compte");
  var vQual   = $("#visio-qualite");
  var vDl     = $("#visio-dl");
  var bPrec   = $("#visio-prec");
  var bSuiv   = $("#visio-suiv");
  var bFerme  = $("#visio-fermer");

  var PALIERS = [600, 1200, 2000, 3200];

  /* la largeur la plus juste pour cet écran : ni floue, ni inutilement lourde */
  function palierEcran() {
    var besoin = Math.max(window.innerWidth, window.innerHeight)
               * Math.min(window.devicePixelRatio || 1, 2);
    for (var i = 0; i < PALIERS.length; i++) if (PALIERS[i] >= besoin) return PALIERS[i];
    return 3200;
  }

  function url(id, p, ext) { return "photos/w" + p + "/" + id + "." + (ext || "webp"); }

  var liste = [], idx = 0, origine = null, jeton = 0, pousse = false;

  document.addEventListener("click", function (ev) {
    var z = ev.target.closest && ev.target.closest(".cadre__zone");
    if (!z) return;
    var groupe = z.closest(".jour__flux") || document;
    liste = $$(".cadre__zone", groupe);
    ouvrir(liste.indexOf(z), z);
  });

  function lieuDe(z) {
    var sec = z.closest(".jour, .page-jour, body");
    var t = sec && (sec.querySelector(".entree__lieu") || sec.querySelector(".entete__titre"));
    return t ? t.textContent.trim() : "";
  }

  function ouvrir(i, source) {
    if (i < 0 || !liste.length) return;
    idx = i; origine = source || null;
    if (curseur) curseur.classList.remove("actif");

    visio.hidden = false;
    document.body.classList.add("fige");
    requestAnimationFrame(function () { visio.classList.add("ouverte"); });
    afficher(0);
    bFerme.focus({ preventScroll: true });

    try { history.pushState({ visio: true }, ""); pousse = true; }
    catch (e) { pousse = false; }
  }

  function fermer(viaHistorique) {
    if (visio.hidden) return;
    jeton++;
    visio.classList.remove("ouverte");
    document.body.classList.remove("fige");
    setTimeout(function () {
      visio.hidden = true;
      vImg.removeAttribute("src"); vSrc.removeAttribute("srcset");
    }, 300);
    if (origine) { origine.focus({ preventScroll: true }); origine = null; }
    if (pousse && !viaHistorique) { pousse = false; history.back(); }
    else { pousse = false; }
  }

  /* sens : -1 précédente, +1 suivante, 0 ouverture */
  function afficher(sens) {
    var z = liste[idx];
    var id = z.dataset.id, heure = z.dataset.heure;
    var mien = ++jeton;
    var cible = palierEcran();

    vImg.classList.remove("prete");
    vQual.classList.remove("active");
    if (sens) vImg.classList.add(sens > 0 ? "glisse-g" : "glisse-d");

    function poser() {
      if (mien !== jeton) return;
      vSrc.srcset = url(id, 1200);                    // arrive tout de suite
      vImg.src    = url(id, 1200, "jpg");
      vImg.alt    = lieuDe(z) + " — " + heure;
      vImg.classList.remove("glisse-g", "glisse-d");
      if (vImg.complete) prete();
      if (WEBP && cible > 1200) monterEnQualite(id, cible, mien);
      else vQual.classList.add("active");
    }
    if (sens) setTimeout(poser, 150); else poser();

    vLieu.textContent   = lieuDe(z) + " · " + heure;
    vCompte.textContent = (idx + 1) + " / " + liste.length;
    bPrec.disabled = idx === 0;
    bSuiv.disabled = idx === liste.length - 1;

    if (z.dataset.dl) {
      vDl.href = z.dataset.dl; vDl.download = z.dataset.dlnom || ""; vDl.hidden = false;
    } else { vDl.hidden = true; }

    precharger(idx + 1); precharger(idx - 1);
  }

  function prete() { vImg.classList.add("prete"); }
  vImg.addEventListener("load", prete);

  /* la version pleine définition remplace la première, sans coupure visible */
  function monterEnQualite(id, palier, mien) {
    var im = new Image();
    im.onload = function () {
      if (mien !== jeton) return;
      vSrc.srcset = url(id, palier);
      vQual.classList.add("active");
    };
    im.src = url(id, palier);
  }

  function precharger(i) {
    var z = liste[i];
    if (!z) return;
    var im = new Image();
    im.src = WEBP ? url(z.dataset.id, 1200) : url(z.dataset.id, 1200, "jpg");
  }

  function aller(pas) {
    var n = idx + pas;
    if (n < 0 || n >= liste.length) return;
    idx = n; afficher(pas);
  }

  bPrec.addEventListener("click", function () { aller(-1); });
  bSuiv.addEventListener("click", function () { aller(1); });
  bFerme.addEventListener("click", function () { fermer(false); });
  visio.addEventListener("click", function (ev) {
    if (ev.target.hasAttribute("data-fermer")) fermer(false);
  });

  document.addEventListener("keydown", function (ev) {
    if (visio.hidden) return;
    if (ev.key === "Escape")          { ev.preventDefault(); fermer(false); }
    else if (ev.key === "ArrowLeft")  { ev.preventDefault(); aller(-1); }
    else if (ev.key === "ArrowRight") { ev.preventDefault(); aller(1); }
    else if (ev.key === "Home")       { ev.preventDefault(); idx = 0; afficher(-1); }
    else if (ev.key === "End")        { ev.preventDefault(); idx = liste.length - 1; afficher(1); }
    else if (ev.key === "Tab") {
      var f = [bFerme, vDl, bPrec, bSuiv].filter(function (b) {
        return b && !b.disabled && !b.hidden;
      });
      var pos = f.indexOf(document.activeElement);
      ev.preventDefault();
      f[(pos + (ev.shiftKey ? -1 : 1) + f.length) % f.length].focus();
    }
  });

  window.addEventListener("popstate", function () {
    if (!visio.hidden) fermer(true);
  });

  /* ---- glissement du doigt ---- */
  var x0 = 0, y0 = 0, dx = 0, dy = 0, multi = false;

  visio.addEventListener("touchstart", function (ev) {
    multi = ev.touches.length > 1;
    x0 = ev.touches[0].clientX; y0 = ev.touches[0].clientY; dx = dy = 0;
  }, { passive: true });

  visio.addEventListener("touchmove", function (ev) {
    if (multi) return;
    dx = ev.touches[0].clientX - x0; dy = ev.touches[0].clientY - y0;
  }, { passive: true });

  visio.addEventListener("touchend", function () {
    if (multi) { multi = false; return; }
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) aller(dx < 0 ? 1 : -1);
    else if (dy > 95 && Math.abs(dy) > Math.abs(dx) * 1.4) fermer(false);
    dx = dy = 0;
  }, { passive: true });
})();
