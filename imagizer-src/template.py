#!/usr/bin/python3
# -*- coding: UTF8 -*-

__author__ = "Jérôme Kieffer"
__date__ = "2025-01-05"
__license__ = "GPL"

import sys
import os
import shutil
import logging
import re
from traceback import print_exception
from contextlib import contextmanager
from collections import namedtuple
PieceOfCode = namedtuple("PieceOfCode", "preamble compiled source")
logger = logging.getLogger(__name__)
from .config import Config
config = Config()

#===============================================================================
# DEFAULT TEMPLATES
#===============================================================================

# Important Note: you can always save these with --save-templates and then edit
# them, and they will be used, without modifying this script. You can also put
# new common code in template-rc.py and use it from your templates.

html_preamble = \
"""<!doctype html>
<html lang="fr">
<head>
   <meta charset="utf-8">
   <meta name="viewport" content="width=device-width, initial-scale=1">
   <link rel="stylesheet" href="<!--tag:rel(css_fn, cd)-->">
   <title>%s</title>
</head>
<body>
"""

html_postamble = """
<!--tagcode:
if 'footer' in globals():
    print(footer)
-->
<a name='end'>
</body>
</html>
"""

default_templates = {}

default_templates[ 'template-css' ] = r'''
/* ===========================================================================
   Imagizer — feuille de style web (increment 2 : balisage moderne)
   Responsive (mobile d'abord), sombre par défaut + variante claire.
   100 % statique, aucune dépendance externe (police système, pas de CDN).
   =========================================================================== */

/* Galerie sombre par defaut (comme les versions precedentes d'imagizer) :
   fond #17171a quel que soit le reglage clair/sombre du systeme. Le palette
   clair est conservee ci-dessous mais volontairement inactive (elle ne
   s'active plus via prefers-color-scheme) ; la reactiver = restaurer le
   bloc @media. color-scheme:dark aligne aussi les widgets natifs (scrollbars). */
:root {
    color-scheme:dark;
    --bg:#17171a; --surface:#212127; --surface-2:#2b2b32;
    --text:#e8e8ea; --muted:#9a9aa4; --line:#383840;
    --accent:#6db3f2; --accent-2:#a9d3f8;
    --radius:12px; --gap:clamp(.6rem,2vw,1.2rem); --maxw:1200px;
    --shadow:0 6px 24px rgba(0,0,0,.45);
}

*,*::before,*::after { box-sizing:border-box; }
html { -webkit-text-size-adjust:100%; }
body {
    margin:0 auto; max-width:var(--maxw);
    padding:clamp(.7rem,3vw,1.5rem);
    background:var(--bg); color:var(--text);
    font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
}
a { color:var(--accent); text-decoration:none; }
a:hover,a:focus { color:var(--accent-2); text-decoration:underline; }
img { max-width:100%; height:auto; }

/* --- En-tête de page / fil d'Ariane --------------------------------------- */
.pagehead { margin:0 0 var(--gap); }
.pagehead h1 { margin:.2rem 0; font-size:clamp(1.3rem,5vw,2rem); }
.crumbs { color:var(--muted); font-size:.9rem; margin-bottom:.3rem; }
.subtitle { margin:.1rem 0 .5rem; }
.daycomment { color:var(--muted); margin:.2rem 0 .8rem; max-width:70ch; }
.muted { color:var(--muted); }

.btn {
    display:inline-block; padding:.55rem 1.1rem;
    background:var(--surface-2); color:var(--accent);
    border:1px solid var(--line); border-radius:var(--radius);
    font-weight:600; cursor:pointer;
}
.btn:hover,.btn:focus { border-color:var(--accent); color:var(--accent-2); text-decoration:none; }

/* Barre d'actions : navigation laterale (jour/annee prec. et suiv.) de part et
   d'autre des boutons Diaporama et Telechargement. Le lien "prec." est pousse a
   gauche, "suiv." a droite ; les boutons du centre sont injectes entre les deux
   (le bouton Telechargement est ajoute par zip.js apres #slideshow). */
.pagenav { display:flex; flex-wrap:wrap; gap:.5rem; align-items:center; margin:.6rem 0 0; }
.pagenav .prev { margin-right:auto; }
.pagenav .next { margin-left:auto; }
.navday { min-width:0; max-width:16rem; overflow:hidden;
          text-overflow:ellipsis; white-space:nowrap; }

/* --- Grilles (jours & miniatures) ----------------------------------------- */
.grid {
    list-style:none; margin:0; padding:0; display:grid; gap:var(--gap);
    grid-template-columns:repeat(auto-fill,minmax(150px,1fr));
}
.days { grid-template-columns:repeat(auto-fill,minmax(220px,1fr)); align-items:start; }

.tile {
    display:flex; flex-direction:column; overflow:hidden;
    background:var(--surface); border:1px solid var(--line); border-radius:var(--radius);
    color:inherit; text-decoration:none; transition:transform .15s, box-shadow .15s;
}
.tile:hover,.tile:focus { transform:translateY(-2px); box-shadow:var(--shadow); text-decoration:none; }
/* Cadre de proportion fixe (technique du padding %, universelle) : l'image le
   remplit en object-fit:cover. Robuste sur tous navigateurs, mobile inclus. */
.tile-img { position:relative; display:block; padding-top:100%; height:0;
            overflow:hidden; background:var(--surface-2); }
.days .tile-img { padding-top:75%; }   /* 4:3 pour les couvertures de jour */
.tile-img img { position:absolute; top:0; left:0; width:100%; height:100%;
                object-fit:cover; display:block; }
.tile-cap { padding:.5rem .6rem; font-size:.9rem; color:var(--muted); text-align:center; }
.days .tile-cap { color:var(--text); }
.cardnote { display:block; margin-top:.3rem; font-size:.82rem; color:var(--muted); text-align:left; }

/* --- Page image ----------------------------------------------------------- */
.photo { max-width:1000px; margin-inline:auto; }
.stage { position:relative; margin:var(--gap) 0; }
.viewer { display:block; }
.image { display:block; max-width:100%; height:auto; margin:0 auto;
         border-radius:var(--radius); box-shadow:var(--shadow); }

/* Grandes zones de navigation : colonnes cliquables sur toute la hauteur de
   l'image, a gauche (precedente) et a droite (suivante). Transparentes au
   repos (aucune teinte sur l'image) ; seul le chevron reste visible, lisible
   grace a son ombre portee. Un fond leger n'apparait qu'au survol/focus. */
.navbtn {
    position:absolute; top:0; bottom:0; z-index:2;
    width:clamp(56px, 15%, 130px);
    display:flex; align-items:center; justify-content:center;
    font-size:2.4rem; line-height:1; color:#fff;
    text-shadow:0 1px 4px rgba(0,0,0,.7);
    background:transparent; border:0; text-decoration:none; transition:background .15s;
}
.navbtn:hover,.navbtn:focus {
    background:color-mix(in srgb, var(--surface) 55%, transparent); text-decoration:none;
}
.navbtn.prev { left:0; border-radius:var(--radius) 0 0 var(--radius); }
.navbtn.next { right:0; border-radius:0 var(--radius) var(--radius) 0; }

.title { font-size:clamp(1.2rem,4vw,1.5rem); text-align:center; margin:var(--gap) 0 .2rem; }
.description { text-align:center; color:var(--muted); margin:.2rem 0; }
.backlink { text-align:center; margin:var(--gap) 0; }

.exif {
    display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:.3rem .9rem;
    background:var(--surface); border:1px solid var(--line); border-radius:var(--radius);
    padding:.8rem 1rem; margin:var(--gap) 0; font-size:.85rem;
}
.exif div { display:flex; gap:.4rem; }
.exif dt { color:var(--muted); margin:0; }
.exif dd { margin:0; font-weight:600; }

/* --- Diaporama (lightbox, construit en JS) -------------------------------- */
.lightbox {
    position:fixed; inset:0; z-index:1000; display:none;
    align-items:center; justify-content:center; background:rgba(0,0,0,.93);
}
.lightbox.open { display:flex; }
.lightbox img { max-width:96vw; max-height:82vh; object-fit:contain; border-radius:6px; }
.lb-caption {
    position:absolute; left:0; right:0; bottom:3.4rem; text-align:center;
    color:#f0f0f0; padding:0 1rem; font-size:1rem; text-shadow:0 1px 3px #000;
    white-space:pre-line;   /* respecte les retours à la ligne des légendes */
}
.lb-exif {
    position:absolute; top:.6rem; left:.6rem; max-width:min(80vw, 340px);
    background:rgba(0,0,0,.62); color:#eee; padding:.6rem .8rem; border-radius:8px;
    font-size:.85rem; line-height:1.45; white-space:pre-line; text-shadow:0 1px 2px #000;
}
.lb-exif[hidden] { display:none; }
.lb-bar { position:absolute; left:0; right:0; bottom:.7rem; display:flex; gap:.6rem; justify-content:center; }
.lb-btn {
    width:44px; height:44px; display:flex; align-items:center; justify-content:center;
    font-size:1.3rem; color:#fff; background:rgba(255,255,255,.14);
    border:0; border-radius:50%; cursor:pointer;
}
.lb-btn:hover,.lb-btn:focus { background:rgba(255,255,255,.28); }
.lb-prev { position:absolute; left:.6rem; top:50%; transform:translateY(-50%); }
.lb-next { position:absolute; right:.6rem; top:50%; transform:translateY(-50%); }
.lb-close { position:absolute; top:.6rem; right:.6rem; }
'''

# Ressources JavaScript (diaporama + téléchargement ZIP), écrites telles quelles.
GALLERY_JS = r'''
/* Imagizer — diaporama (lightbox) en JavaScript « vanilla ».
   Amélioration progressive : sans JS, les vignettes restent de simples liens
   vers les pages image. Aucune dépendance externe. */
(function () {
    "use strict";
    var gallery = document.getElementById("gallery");
    if (!gallery) return;
    var links = Array.prototype.slice.call(gallery.querySelectorAll("a[data-full]"));
    if (!links.length) return;

    var items = links.map(function (a) {
        return { full: a.getAttribute("data-full"),
                 caption: a.getAttribute("data-caption") || "",
                 exif: a.getAttribute("data-exif") || "" };
    });

    // Delai entre deux photos en lecture auto (ms), issu de imagizer.conf
    // (SlideShowDelay) via l'attribut data-delay ; repli sur 4000 ms.
    var DELAY = parseInt(gallery.getAttribute("data-delay"), 10) || 4000;
    var idx = 0, timer = null;

    var lb = document.createElement("div");
    lb.className = "lightbox";
    lb.setAttribute("role", "dialog");
    lb.setAttribute("aria-label", "Diaporama");
    lb.innerHTML =
        '<button class="lb-btn lb-close" aria-label="Fermer" type="button">✕</button>' +
        '<button class="lb-btn lb-prev" aria-label="Précédente" type="button">‹</button>' +
        '<img alt="">' +
        '<button class="lb-btn lb-next" aria-label="Suivante" type="button">›</button>' +
        '<div class="lb-exif" hidden></div>' +
        '<div class="lb-caption"></div>' +
        '<div class="lb-bar">' +
        '<button class="lb-btn lb-play" aria-label="Lecture / Pause" type="button">▶</button>' +
        '<button class="lb-btn lb-info" aria-label="Informations EXIF" type="button">ⓘ</button>' +
        '</div>';
    document.body.appendChild(lb);

    var img = lb.querySelector("img");
    var cap = lb.querySelector(".lb-caption");
    var playBtn = lb.querySelector(".lb-play");
    var infoBtn = lb.querySelector(".lb-info");
    var exifBox = lb.querySelector(".lb-exif");

    function show(i) {
        idx = (i + items.length) % items.length;
        img.src = items[idx].full;
        img.alt = items[idx].caption;
        cap.textContent = items[idx].caption;
        exifBox.textContent = items[idx].exif ? items[idx].exif.split(" • ").join("\n") : "";
        infoBtn.style.display = items[idx].exif ? "" : "none";
    }
    function open(i) { show(i); lb.classList.add("open"); document.body.style.overflow = "hidden"; }
    function close() { stop(); lb.classList.remove("open"); document.body.style.overflow = ""; img.removeAttribute("src"); exifBox.hidden = true; }
    function next() { show(idx + 1); }
    function prev() { show(idx - 1); }
    function play() { if (timer) return; timer = setInterval(next, DELAY); playBtn.textContent = "⏸"; }
    function stop() { if (!timer) return; clearInterval(timer); timer = null; playBtn.textContent = "▶"; }
    function toggle() { if (timer) { stop(); } else { play(); } }

    // Un clic sur une vignette suit son lien vers la PAGE image (EXIF, lien
    // pleine résolution, préc/suiv) — on n'intercepte donc pas. Le diaporama
    // (lightbox) est réservé au bouton ci-dessous.

    // Bouton « Diaporama » -> ouvre la lightbox et démarre la lecture auto.
    var starter = document.getElementById("slideshow");
    if (starter) starter.addEventListener("click", function (e) {
        e.preventDefault();
        open(0);
        if (!window.matchMedia || !matchMedia("(prefers-reduced-motion: reduce)").matches) play();
    });

    lb.querySelector(".lb-prev").addEventListener("click", function () { stop(); prev(); });
    lb.querySelector(".lb-next").addEventListener("click", function () { stop(); next(); });
    lb.querySelector(".lb-close").addEventListener("click", close);
    playBtn.addEventListener("click", toggle);
    infoBtn.addEventListener("click", function () { exifBox.hidden = !exifBox.hidden; });
    lb.addEventListener("click", function (e) { if (e.target === lb) close(); });

    document.addEventListener("keydown", function (e) {
        if (!lb.classList.contains("open")) return;
        if (e.key === "Escape") close();
        else if (e.key === "ArrowRight") { stop(); next(); }
        else if (e.key === "ArrowLeft") { stop(); prev(); }
        else if (e.key === " ") { e.preventDefault(); toggle(); }
    });

    // Glissement tactile gauche/droite.
    var x0 = null;
    lb.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener("touchend", function (e) {
        if (x0 === null) return;
        var dx = e.changedTouches[0].clientX - x0; x0 = null;
        if (Math.abs(dx) > 40) { stop(); if (dx < 0) { next(); } else { prev(); } }
    });
})();
'''

ZIP_JS = r'''
/* Imagizer — téléchargement d'une journée en ZIP mode « store » (sans recompression).
   Les JPEG sont déjà compressés : on se contente de les concaténer avec les en-têtes
   ZIP. Vanilla JS, sans dépendance. Amélioration progressive : le bouton n'est ajouté
   que si JavaScript est actif (sinon rien, les photos restent accessibles une à une).
   Mémoire maîtrisée : on ne garde en RAM qu'une image à la fois (pour son CRC) ; les
   données sont ensuite référencées comme Blob (adossé au disque par le navigateur). */
(function () {
    "use strict";
    var gallery = document.getElementById("gallery");
    if (!gallery) return;
    var tiles = Array.prototype.slice.call(gallery.querySelectorAll("a[data-download]"));
    if (!tiles.length) return;

    var entries = tiles.map(function (a) {
        var url = a.getAttribute("data-download");
        return { url: url, name: decodeURIComponent(url.split("/").pop()) };
    });
    var zipname = gallery.getAttribute("data-zipname") || "photos";

    // --- CRC32 ---
    var TABLE = (function () {
        var t = new Uint32Array(256), c, n, k;
        for (n = 0; n < 256; n++) {
            c = n;
            for (k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
            t[n] = c >>> 0;
        }
        return t;
    })();
    function crc32(u8) {
        var c = 0xFFFFFFFF;
        for (var i = 0; i < u8.length; i++) c = TABLE[(c ^ u8[i]) & 0xFF] ^ (c >>> 8);
        return (c ^ 0xFFFFFFFF) >>> 0;
    }

    // --- helpers octets (little-endian) ---
    function u16(v) { return [v & 255, (v >>> 8) & 255]; }
    function u32(v) { return [v & 255, (v >>> 8) & 255, (v >>> 16) & 255, (v >>> 24) & 255]; }
    function utf8(s) {
        var e = unescape(encodeURIComponent(s)), a = [];
        for (var i = 0; i < e.length; i++) a.push(e.charCodeAt(i));
        return a;
    }
    var SIG_LOCAL = 0x04034b50, SIG_CENTRAL = 0x02014b50, SIG_EOCD = 0x06054b50;
    var FLAG_UTF8 = 0x0800, DOSDATE = 0x0021;   // 1980-01-01, méthode 0 = store

    function localHeader(name, crc, size) {
        return Uint8Array.from([].concat(
            u32(SIG_LOCAL), u16(20), u16(FLAG_UTF8), u16(0), u16(0), u16(DOSDATE),
            u32(crc), u32(size), u32(size), u16(name.length), u16(0), name));
    }
    function centralHeader(name, crc, size, offset) {
        return Uint8Array.from([].concat(
            u32(SIG_CENTRAL), u16(20), u16(20), u16(FLAG_UTF8), u16(0), u16(0), u16(DOSDATE),
            u32(crc), u32(size), u32(size), u16(name.length),
            u16(0), u16(0), u16(0), u16(0), u32(0), u32(offset), name));
    }
    function eocd(count, size, offset) {
        return Uint8Array.from([].concat(
            u32(SIG_EOCD), u16(0), u16(0), u16(count), u16(count), u32(size), u32(offset), u16(0)));
    }

    async function buildZip(setProgress) {
        var parts = [], central = [], offset = 0;
        for (var i = 0; i < entries.length; i++) {
            setProgress(i + 1, entries.length);
            var resp = await fetch(entries[i].url);
            if (!resp.ok) throw new Error("HTTP " + resp.status + " sur " + entries[i].url);
            var buf = await resp.arrayBuffer();
            var u8 = new Uint8Array(buf);
            var crc = crc32(u8), size = u8.length, name = utf8(entries[i].name);
            var lh = localHeader(name, crc, size);
            parts.push(lh, new Blob([buf]));                 // en-tête + donnée (Blob)
            central.push(centralHeader(name, crc, size, offset));
            offset += lh.length + size;
            buf = u8 = null;                                 // libère la RAM
        }
        var cdStart = offset, cdSize = 0;
        for (var j = 0; j < central.length; j++) { parts.push(central[j]); cdSize += central[j].length; }
        parts.push(eocd(entries.length, cdSize, cdStart));
        return new Blob(parts, { type: "application/zip" });
    }

    function triggerDownload(blob) {
        var url = URL.createObjectURL(blob);
        var a = document.createElement("a");
        a.href = url; a.download = zipname + ".zip";
        document.body.appendChild(a); a.click(); a.remove();
        setTimeout(function () { URL.revokeObjectURL(url); }, 10000);
    }

    // --- bouton (injecté seulement si JS) ---
    var btn = document.createElement("button");
    btn.type = "button"; btn.className = "btn"; btn.id = "download-day";
    var label = "⬇ Télécharger la journée (" + entries.length + " photos)";
    btn.textContent = label;
    var slideshow = document.getElementById("slideshow");
    if (slideshow && slideshow.parentNode) slideshow.parentNode.insertBefore(btn, slideshow.nextSibling);
    else gallery.parentNode.insertBefore(btn, gallery);

    btn.addEventListener("click", async function () {
        if (btn.disabled) return;
        btn.disabled = true;
        try {
            var blob = await buildZip(function (i, n) { btn.textContent = "Préparation… " + i + "/" + n; });
            triggerDownload(blob);
            btn.textContent = "✓ Téléchargement lancé";
        } catch (e) {
            btn.textContent = "Échec — réessayer";
            if (window.console) console.error(e);
        } finally {
            setTimeout(function () { btn.disabled = false; btn.textContent = label; }, 4000);
        }
    });
})();
'''


# Navigation clavier sur les pages image (asset statique partage). Amelioration
# progressive : sans JS, les liens prec./suiv. restent cliquables.
PHOTO_JS = r'''
/* Imagizer -- navigation clavier sur les pages image.
   Fleches gauche/droite ET pave numerique (4/6), quel que soit l'etat de
   NumLock : NumLock eteint -> e.key ArrowLeft/ArrowRight ; NumLock allume ->
   e.code Numpad4/Numpad6. On suit simplement le lien prec./suiv. de la page. */
(function () {
    "use strict";
    function go(sel) {
        var a = document.querySelector(sel);
        if (a && a.getAttribute("href")) window.location.href = a.href;
    }
    document.addEventListener("keydown", function (e) {
        if (e.defaultPrevented || e.altKey || e.ctrlKey || e.metaKey) return;
        var t = e.target;
        if (t && (t.isContentEditable ||
                  /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName))) return;
        if (e.key === "ArrowLeft" || e.code === "Numpad4") {
            e.preventDefault(); go(".navbtn.prev");
        } else if (e.key === "ArrowRight" || e.code === "Numpad6") {
            e.preventDefault(); go(".navbtn.next");
        }
    });
})();
'''


default_templates[ 'template-image' ] = \
(html_preamble % 'Image: <!--tag:unicode2html(image._base)-->') + \
"""
<main class="photo">
<!--tagcode:
import html as _h
_desc = image._comment or (image._attr and image._attr.get('description')) or ''
_lines = _desc.replace('<BR>', chr(10)).split(chr(10))
_title = (_lines[0].strip() or image._base) if _desc else image._base
_rest = chr(10).join(_lines[1:]).strip()
_pi = prev(image, allimages)
_ni = next(image, allimages)
_scaled = image._scaledfn or image._filename
-->
  <nav class="crumbs"><!--tag:dirnav(cd, image._dir)--></nav>
  <div class="stage">
<!--tagcode:
if _pi:
    print('<a class="navbtn prev" href="' + urlquote(rel(_pi._pagefn, cd)) + '" rel="prev" aria-label="Photo precedente">&lsaquo;</a>')
_sz = ''
if image._scaledsize:
    _sz = ' width="' + str(image._scaledsize[0]) + '" height="' + str(image._scaledsize[1]) + '"'
print('<a class="viewer" href="' + urlquote(rel(image._filename, cd)) + '" title="Voir en pleine resolution">'
      '<img class="image" src="' + urlquote(rel(_scaled, cd)) + '" alt="' + _h.escape(_title, quote=True) + '"' + _sz + '></a>')
if _ni:
    print('<a class="navbtn next" href="' + urlquote(rel(_ni._pagefn, cd)) + '" rel="next" aria-label="Photo suivante">&rsaquo;</a>')
-->
  </div>
  <h1 class="title"><!--tag:_h.escape(_title)--></h1>
<!--tagcode:
if _rest:
    print('<p class="description">' + _h.escape(_rest).replace(chr(10), '<br>') + '</p>')
_etags = ['Marque','Modele','Date','Focale','Ouverture','Vitesse','Iso','Flash']
_ekeys = {'Marque':'Exif.Image.Make', 'Modele':'Exif.Image.Model', 'Date':'Exif.Photo.DateTimeOriginal',
          'Focale':'Exif.Photo.FocalLength', 'Vitesse':'Exif.Photo.ExposureTime', 'Ouverture':'Exif.Photo.FNumber',
          'Iso':'Exif.Photo.ISOSpeedRatings', 'Flash':'Exif.Photo.Flash'}
if image._exif:
    _rows = [(_t, image._exif[_ekeys[_t]]) for _t in _etags if _ekeys[_t] in image._exif]
    if _rows:
        print('<dl class="exif">')
        for _lab, _val in _rows:
            print('  <div><dt>' + _h.escape(_lab) + '</dt><dd>' + _h.escape(str(_val)) + '</dd></div>')
        print('</dl>')
-->
  <p class="backlink"><a href="<!--tag:urlquote(rel(image._dir._pagefn, cd))-->">&#8617; Retour a la galerie</a></p>
</main>
<script src="<!--tag:urlquote(rel(photojs_fn, cd))-->" defer></script>
""" + html_postamble

default_templates[ 'template-dirindex' ] = \
(html_preamble % 'Galerie : <!--tag:unicode2html((dir._attrfile or {}).get("title") or dir._basename or "photo")-->') + \
"""
<main>
<!--tagcode:
import html as _h
_af = dir._attrfile or {}
_title = _af.get('title') or dir._basename or 'Galerie'
_date = _af.get('date') or ''
_comment = _af.get('comment') or ''
_imgs = dir._images
_subs = dir._subdirs
-->
  <header class="pagehead">
    <nav class="crumbs"><!--tag:dirnav(cd, dir)--></nav>
    <h1><!--tag:_h.escape(_title)--></h1>
<!--tagcode:
if _date:
    print('<p class="subtitle muted">' + _h.escape(_date) + '</p>')
if _comment:
    print('<p class="daycomment">' + _h.escape(_comment.replace('<BR>', chr(10))).replace(chr(10), '<br>') + '</p>')
# Navigation laterale : repertoires freres (jours, ou annees) dans le parent.
# _subdirs est trie -> pour des dossiers YYYY-MM-DD-* l'ordre est chronologique.
_prevd = _nextd = None
_par = dir._parent
if _par is not None:
    _sibs = _par._subdirs
    try:
        _k = _sibs.index(dir)
    except ValueError:
        _k = -1
    if _k > 0:
        _prevd = _sibs[_k - 1]
    if 0 <= _k < len(_sibs) - 1:
        _nextd = _sibs[_k + 1]
if _prevd or _nextd or len(_imgs) > 0:
    print('<div class="pagenav">')
    if _prevd:
        _pa = _prevd._attrfile or {}
        _plab = _pa.get('title') or _prevd._basename or ''
        _ptip = ' '.join(_x for _x in (_pa.get('date') or '', _plab) if _x)
        print('<a class="btn navday prev" href="' + urlquote(rel(_prevd._pagefn, cd)) +
              '" title="' + _h.escape(_ptip, quote=True) + '">&lsaquo; ' + _h.escape(_plab) + '</a>')
    if len(_imgs) > 0:
        print('<a class="btn" id="slideshow" href="' + urlquote(rel(_imgs[0]._pagefn, cd)) + '">&#9654; Diaporama (' + str(len(_imgs)) + ' photos)</a>')
    if _nextd:
        _na = _nextd._attrfile or {}
        _nlab = _na.get('title') or _nextd._basename or ''
        _ntip = ' '.join(_x for _x in (_na.get('date') or '', _nlab) if _x)
        print('<a class="btn navday next" href="' + urlquote(rel(_nextd._pagefn, cd)) +
              '" title="' + _h.escape(_ntip, quote=True) + '">' + _h.escape(_nlab) + ' &rsaquo;</a>')
    print('</div>')
-->
  </header>
<!--tagcode:
if len(_subs) > 0:
    import os.path as _op
    print('<ul class="grid days">')
    for _d in _subs:
        _daf = _d._attrfile or {}
        _all = _d.get_all_images()
        _cover = None
        if _daf.get('image'):
            _cb = _op.splitext(_op.basename(_daf['image']))[0]
            for _im in _all:
                if _im._base == _cb:
                    _cover = _im
                    break
        if _cover is None and _all:
            _cover = _all[0]
        _dt = _daf.get('title') or _d._basename
        _dd = _daf.get('date') or ''
        _dc = _daf.get('comment') or ''
        print('<li><a class="tile" href="' + urlquote(rel(_d._pagefn, cd)) + '">')
        if _cover is not None and _cover._thumbfn:
            print('  <span class="tile-img"><img src="' + urlquote(rel(_cover._thumbfn, cd)) + '" alt="" loading="lazy" decoding="async"></span>')
        _cap = '<strong>' + _h.escape(_dt) + '</strong>'
        if _dd:
            _cap = _cap + '<br><span class="muted">' + _h.escape(_dd) + '</span>'
        if _dc:
            _cap = _cap + '<br><span class="cardnote">' + _h.escape(_dc.replace('<BR>', chr(10))).replace(chr(10), '<br>') + '</span>'
        print('  <span class="tile-cap">' + _cap + '</span>')
        print('</a></li>')
    print('</ul>')
-->
<!--tagcode:
if len(_imgs) > 0:
    _etags = ['Marque','Modele','Date','Focale','Ouverture','Vitesse','Iso','Flash']
    _ekeys = {'Marque':'Exif.Image.Make', 'Modele':'Exif.Image.Model', 'Date':'Exif.Photo.DateTimeOriginal',
              'Focale':'Exif.Photo.FocalLength', 'Vitesse':'Exif.Photo.ExposureTime', 'Ouverture':'Exif.Photo.FNumber',
              'Iso':'Exif.Photo.ISOSpeedRatings', 'Flash':'Exif.Photo.Flash'}
    _sep = ' ' + chr(0x2022) + ' '
    print('<ul class="grid gallery" id="gallery" data-zipname="' + _h.escape(dir._basename or 'photos', quote=True) + '" data-delay="' + str(int(config.SlideShowDelay * 1000)) + '">')
    for _i in _imgs:
        _cap = _i._comment or (_i._attr and _i._attr.get('description')) or ''
        _cap1 = ' '.join(_cap.replace('<BR>', ' ').split())
        _exif = ''
        if _i._exif:
            _exif = _sep.join(_t + ' : ' + str(_i._exif[_ekeys[_t]]) for _t in _etags if _ekeys[_t] in _i._exif)
        print('<li><a class="tile" href="' + urlquote(rel(_i._pagefn, cd)) +
              '" data-full="' + urlquote(rel(_i._scaledfn, cd)) +
              '" data-download="' + urlquote(rel(_i._filename, cd)) +
              '" data-caption="' + _h.escape(_cap1, quote=True) +
              '" data-exif="' + _h.escape(_exif, quote=True) + '">')
        print('  <span class="tile-img"><img src="' + urlquote(rel(_i._thumbfn, cd)) +
              '" alt="' + _h.escape(_cap1, quote=True) + '" loading="lazy" decoding="async"></span>')
        if _cap:
            print('  <span class="tile-cap">' + _h.escape(_cap.replace('<BR>', chr(10))).replace(chr(10), '<br>') + '</span>')
        print('</a></li>')
    print('</ul>')
-->
</main>
<!--tagcode:
if len(_imgs) > 0:
    print('<script src="' + urlquote(rel(gallery_fn, cd)) + '" defer></script>')
    print('<script src="' + urlquote(rel(zipjs_fn, cd)) + '" defer></script>')
-->
""" + html_postamble

default_templates[ 'template-trackindex' ] = \
(html_preamble % 'Track Index: <!--tag:track-->') + \
"""

<table class=\"toptable tracktop\"><tr><td>
<p class=\"toptitle\">Track index: <!--tag:track--></p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
images = trackmap[track]

if len(images) > 0:
    print('<h3>Images:</h3>')
    print(imagePile( cd, images ))

    print('<h3>Images by name:</h3>')
    print(twoColumns(cd, images))
-->
""" + html_postamble

default_templates[ 'template-allindex' ] = \
(html_preamble % 'Global Index') + \
"""

<table class=\"toptable globaltop\"><tr><td>
<p class=\"toptitle\">Global Index</p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
if len(alldirs) > 0:
    print('<H3>Directories:</H3>')
    print('<UL>')
    for d in alldirs:
        if d._parent:
            pname = d._path
        else:
            pname = '(root)'
        print(f'<li><a href=\"{rel(d._pagefn, cd)}\">{pname}</a></li>')
    print('</ul><p>')
-->

<!--tagcode:
if len(tracks) > 0:
    print('<h3>Tracks:</h3>')
    print('<ul>')
    for t in tracks:
        print(f'<li><a href=\"{trackindex_fns[t]}\">{t}</a></li>')
    print('</ul>')
-->

<!--tagcode:
if len(allimages) > 0:
    print('<h3>Images:</h3>')
    print(imagePile( cd, allimages ))

    print('<h3>Images by name:</h3>')
    print(twoColumns(cd, allimages))
-->
""" + html_postamble

default_templates[ 'template-sortindex' ] = \
(html_preamble % '\"Sorted index\"') + \
"""
<table class=\"toptable sortedtop\"><tr><td>
<p class=\"toptitle\">Sorted index</p>
</td></tr></table>

<div class=\"mininav\">
<a href=\"<!--tag:rel(rootdir._pagefn, cd)-->\">Root</a> |
<a href=\"<!--tag:rel(allindex_fn, cd)-->\">Global</a> |
<a href=\"<!--tag:rel(sortindex_fn, cd)-->\">Sorted</a>
</div>

<!--tagcode:
if len(allimages) > 0:
    import os
    import os.path as op
    print('<h3>Images sorted by name:</h3>')
    ilist = list(allimages)
    ilist.sort( key = lambda x: x._base )

    for i in ilist:
        print('<p>')
        print(thumbImage( cd, i, 'align=\"middle\"' ))
        print(f'<a href=\"{rel(i._pagefn, cd)}\">{i._base}</a>')
        print()
-->
""" + html_postamble


@contextmanager
def custom_redirection(fileobj):
    old = sys.stdout
    sys.stdout = fileobj
    try:
        yield fileobj
    finally:
        sys.stdout = old


class Templates(object):
    "A class responsible for reading and providing all kind of templates"

    def __init__(self):
        """Constructor ... behaves like a dictionary


        :param opts: an option parser object with the command line options
        """
        self.opts = None
        self.templates = {}  # key: type of template, value=list of PieceOfCode

    def set_opts(self, opts):
        self.opts = opts
        self.read_all()

    def read_all(self):
        """Reads the template files."""

        if self.opts is None:
            raise RuntimeError("You need to first set the parsed command line options")

        # Compile HTML templates.

        for tt in [ 'image', 'dirindex', 'allindex', 'trackindex', 'sortindex' ]:
            fn = f'template-{tt}' + self.opts.htmlext
            templatetxt = self.read_one(fn)
            self.templates[ tt ] = self.compile_template(templatetxt, fn)

        fn = 'template-css.css'
        templatetxt = self.read_one(fn)
        self.templates[ 'css' ] = self.compile_template(templatetxt, fn)

        # Compile user-specified rc file.
        rcsfx = 'rc'
        self.templates[ rcsfx ] = []
        if self.opts.rc:
            try:
                with  open(opts.rc, "r") as tfile:
                    orc = tfile.read()
            except IOError as error:
                logger.error("Error: can't open user rc file: %s; %s", self.opts.rc, error)
                sys.exit(1)
            self.templates[rcsfx].append(self.compile_code('', orc, self.opts.rc))

        # Compile user-specified code.
        if self.opts.rccode:
            self.templates[rcsfx].append(self.compile_code('', opts.rccode, "rccode option"))

        # Compile global rc file without HTML tags, just python code.
        tt = 'template-%s.py' % rcsfx
        code = self.read_one(tt)
        self.templates[rcsfx].append(self.compile_code('', code, tt))

    def read_one(self, tfn):

        """Reads a template file.
        :param tfn: a simple filename.
        :return: some text file which was read

        """
        logger.debug("Fetching template %s", tfn)

        found = 0
        foundInRoot = 0

        # check in user-specified template root.
        if self.opts.templates:
            fn = os.path.join(self.opts.templates, tfn)
            logger.debug("  looking in %s", fn)
            if os.path.exists(fn):
                found = 1

        # check in hierarchy root
        if not found:
            fn = os.path.join(self.opts.root, tfn)
            logger.debug("  looking in %s", fn)
            if os.path.exists(fn):
                foundInRoot = 1
                found = 1

        # look for it in the environment var path
        if not found:
            try:
                curatorPath = os.environ[ 'CURATOR_TEMPLATE' ]
                pathlist = curatorPath.split(os.pathsep)
                for p in pathlist:
                    fn = os.path.join(p, tfn)
                    logger.debug("  looking in %s", fn)
                    if exists(fn):
                        found = 1
                        break
            except KeyError:
                pass

        if found:
            # read the file
            try:
                with open(fn, "r") as tfile:
                    t = tfile.read()
            except IOError as e:
                logger.error("Can't open image template file: %s; %s", fn, e)
                sys.exit(1)
            logger.debug("  succesfully loaded template %s", tfn)

        else:
            # bah... can't load it, use fallback templates
            logger.debug("  falling back on simplistic default templates.")
            t = default_templates.get(os.path.splitext(tfn)[0], "")

        # Save templates in root, if it was requested.
        if self.opts.save_templates and not foundInRoot:
            rootfn = join(opts.root, tfn)
            logger.debug("  saving template in %s", rootfn)

            # saving the file template
            if exists(rootfn):
                bakfn = join(opts.root, tfn + '.bak')
                logger.debug("  making backup in %s", bakfn)

                try:
                    shutil.copy(rootfn, bakfn)
                except:
                    logger.error("Can't copy backup template %s", bakfn)

            try:
                with open(rootfn, "w") as ofile:
                    ofile.write(t)
            except IOError as e:
                logger.error("Can't save template file to: %s ; %s", rootfn, e)
        return t

    def compile_template(self, templatetxt, filename):
        """Compiles template text and return a list of piece of html and


        :param templatetxt: string with the template in it
        :param filename: name of the file
        :return: list of PieceOfCode (3-tuple with text, compiled code and the source)
        """
        output = []
        mre1 = re.compile(r"<!--tag(?P<code>code)?:\s*")
        mre2 = re.compile("-->")
        pos = 0
        errors = 0

        while pos < len(templatetxt):
            mo1 = mre1.search(templatetxt, pos)
            if not mo1:
                break
            mo2 = mre2.search(templatetxt, mo1.end())
            if not mo2:
                logger.error("Error: unfinished tag.")
                sys.exit(1)

            pretext = templatetxt[ pos: mo1.start() ]
            code = templatetxt[ mo1.end(): mo2.start() ]
            if not mo1.group('code'):
                code = f"sys.stdout.write({code})"
            output.append(self.compile_code(pretext, code, filename))
            pos = mo2.end()

        if pos < len(templatetxt):
            # Finally the last piece of text ...
            output.append(PieceOfCode(templatetxt[pos:], None, None))

        if errors == 1 and not self.opts.ignore_errors:
            sys.exit(1)

        return output

    def compile_code(self, preamble, source, filename):

        """Compile a chunk of code.

        :param preamble: piece of pure html text not compiled
        :param source: the actual python source code to be compiles
        :param filename: an indication of the filename ... mainly to help debugging
        :return: a PieceOfCode which contains the (preamble,compiled,source)
        """

        try:
            if source:
                co = compile(source, filename, "exec")
                poc = PieceOfCode(preamble, co, source)
            else:
                poc = PieceOfCode(preamble, None, source)
        except Exception as error:
            poc = PieceOfCode(preamble, None, source)

            logger.error("Error %s compiling template %s in the following code:", error, filename)
            logger.error(source)

            try:
                etype, value, tb = sys.exc_info()
                print_exception(etype, value, tb, None, sys.stderr)
            finally:
                etype = value = tb = None
            if not self.opts.ignore_errors:
                errors = 1

        return poc

    def execute(self, fileobj, template_name, env):
        """Executes template text.  Output is written to outfile.
        :param fileobj: opened file object to write to
        :param template_name: the name of the template to use
        :param env: the environment of the execution
        """
        errors = 0
        for poc in self.templates[template_name]:
            preamble = poc.preamble.encode() if "b" in fileobj.mode else  poc.preamble
            fileobj.write(preamble)
            if poc.compiled:
                try:
                    with custom_redirection(fileobj):
                        eval(poc.compiled, env)

                except Exception as err:
                    logger.error("Error: %s executing template in the following code:\n%s", err, poc.source)
                    try:
                        etype, value, tb = sys.exc_info()
                        print_exception(etype, value, tb, None, sys.stderr)
                    finally:
                        etype = value = tb = None
                    if not self.opts.ignore_errors:
                        errors = 1

        if errors == 1 and not self.opts.ignore_errors:
            sys.exit(1)
