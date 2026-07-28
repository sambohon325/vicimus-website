/* ============================================================
   Vicimus — language + region picker
   Each page sets window.SITE = { root, page, lang } before loading
   this file. `root` reaches the true site root, `page` is the path
   within a language tree (identical across languages), `lang` is the
   current page's language. Switching language just swaps the prefix.
   ============================================================ */
(function () {
  var LANG_SHORT = { en: "EN", es: "ES", fr: "FR" };
  var REGIONS = {
    us: { label: "United States", langs: ["en", "es"] },
    ca: { label: "Canada", langs: ["en", "fr", "es"] }
  };

  var site = window.SITE || { root: "", page: "index.html", lang: "en" };

  function lsGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }

  // Which region to display: last chosen if it supports the current
  // language, otherwise a sensible default for that language.
  function currentRegion() {
    var r = lsGet("vic_region");
    if (r && REGIONS[r] && REGIONS[r].langs.indexOf(site.lang) >= 0) return r;
    return site.lang === "fr" ? "ca" : "us";
  }

  // Public: navigate to the same page in another language.
  window.setLang = function (region, lang) {
    lsSet("vic_region", region);
    lsSet("vic_lang", lang);
    var target = site.root + (lang === "en" ? "" : lang + "/") + site.page;
    window.location.href = target;
  };

  window.toggleLangMenu = function () {
    var m = document.getElementById("lp-menu");
    if (m) m.classList.toggle("is-open");
  };

  // Close the menu on any outside click.
  document.addEventListener("click", function (e) {
    var pick = document.getElementById("langpick");
    var m = document.getElementById("lp-menu");
    if (pick && m && !pick.contains(e.target)) m.classList.remove("is-open");
  });

  document.addEventListener("DOMContentLoaded", function () {
    var region = currentRegion();
    var rEl = document.getElementById("lp-region");
    var lEl = document.getElementById("lp-lang");
    if (rEl) rEl.textContent = region.toUpperCase();
    if (lEl) lEl.textContent = LANG_SHORT[site.lang] || "EN";

    var menu = document.getElementById("lp-menu");
    if (menu) {
      var btns = menu.querySelectorAll("[data-lang]");
      for (var i = 0; i < btns.length; i++) {
        var b = btns[i];
        b.classList.toggle(
          "is-active",
          b.getAttribute("data-region") === region &&
            b.getAttribute("data-lang") === site.lang
        );
      }
    }

    // Homepage only: region also swaps the English hero copy (US vs CA).
    if (site.lang === "en" && typeof window.setMarket === "function") {
      window.setMarket(region);
    }
  });
})();
