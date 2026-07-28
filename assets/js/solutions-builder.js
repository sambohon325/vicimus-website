/* ============================================================
   Vicimus — Solutions Builder
   A pull-out tray. Visitors add products / solutions / markets
   from anywhere on the site (drag on desktop, tap on mobile).
   A rule-based engine (no API) infers their industry, recommends
   complementary products, and estimates directional ROI, then
   builds a printable PDF they can download or email (mailto).

   Depends on:  window.SB_CATALOG (generated), window.SITE,
                window.jspdf (vendored jsPDF).
   ============================================================ */
(function () {
  var LS_KEY = "vic_sb_v1";
  var CAT = window.SB_CATALOG || { products: {}, solutions: {}, markets: {} };
  var SITE = window.SITE || { root: "", page: "index.html", lang: "en" };

  // Complementary products — what to recommend alongside a selection.
  var COMPLEMENTS = {
    "bumper-retention": ["odometer-voip", "calls-on-demand"],
    "bumper-inventory-ads": ["glovebox-websites", "bumper-bi"],
    "glovebox-websites": ["calls-on-demand", "bumper-retention"],
    "odometer-voip": ["calls-on-demand", "bumper-bi"],
    "bumper-finance": ["accessory-accelerator", "bumper-bi"],
    "accessory-accelerator": ["bumper-finance"],
    "calls-on-demand": ["odometer-voip", "bumper-retention"],
    "bumper-bi": ["bumper-retention", "bumper-inventory-ads"],
    "powersports-independent": ["glovebox-websites", "odometer-voip"]
  };
  // Which products each solution / market implies (seeds recommendations).
  var IMPLIES = {
    "retention-lifecycle": ["bumper-retention", "bumper-finance"],
    "inventory-advertising": ["bumper-inventory-ads", "glovebox-websites"],
    "lead-management": ["glovebox-websites", "calls-on-demand"],
    "call-tracking": ["odometer-voip", "calls-on-demand"],
    "franchise-retail": ["bumper-retention", "bumper-finance", "accessory-accelerator"],
    "independent-retail": ["powersports-independent", "glovebox-websites"],
    "bhph": ["bumper-retention", "calls-on-demand", "odometer-voip"],
    "enterprise": ["bumper-bi", "bumper-retention", "bumper-inventory-ads"]
  };

  var state = load();

  function load() {
    try {
      var s = JSON.parse(localStorage.getItem(LS_KEY));
      if (s && s.items) return s;
    } catch (e) {}
    return { items: [], units: 75, market: "", dealer: "" };
  }
  function save() { try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch (e) {} }

  function meta(id, type) { return (CAT[type] || {})[id]; }
  function has(id, type) { return state.items.some(function (x) { return x.id === id && x.type === type; }); }
  function add(id, type) {
    if (!meta(id, type) || has(id, type)) return;
    state.items.push({ id: id, type: type });
    save(); render(); flashTab(); markAdds();
  }
  function remove(id, type) {
    state.items = state.items.filter(function (x) { return !(x.id === id && x.type === type); });
    save(); render(); markAdds();
  }
  function clearAll() { state.items = []; save(); render(); markAdds(); }

  function linkTo(path) { return SITE.root + path; }

  // ---------- rule-based engine ----------
  function selectedOf(type) {
    return state.items.filter(function (x) { return x.type === type; }).map(function (x) { return x.id; });
  }
  function industry() {
    if (state.market && CAT.markets[state.market]) return CAT.markets[state.market].name;
    var m = selectedOf("markets");
    if (m.length) return CAT.markets[m[0]].name;
    var prods = selectedOf("products");
    if (prods.indexOf("powersports-independent") >= 0) return "Independent / Powersports";
    return "Retail Automotive";
  }
  function recommended() {
    var set = [];
    function push(id) { if (CAT.products[id] && set.indexOf(id) < 0) set.push(id); }
    selectedOf("products").forEach(push);                     // explicit picks first
    selectedOf("solutions").forEach(function (s) { (IMPLIES[s] || []).forEach(push); });
    selectedOf("markets").forEach(function (m) { (IMPLIES[m] || []).forEach(push); });
    // then complements of explicit product picks
    selectedOf("products").forEach(function (id) { (COMPLEMENTS[id] || []).forEach(push); });
    return set.slice(0, 6);
  }
  function roi() {
    var units = Math.max(0, parseInt(state.units, 10) || 0);
    var annualUnits = units * 12;
    var rows = [], total = 0;
    recommended().forEach(function (id) {
      var r = (CAT.products[id] || {}).roi || {};
      if (r.kind === "per_unit" && annualUnits > 0) {
        var amt = r.amount * annualUnits;
        rows.push({ name: CAT.products[id].name, detail: r.label, value: amt });
        total += amt;
      } else if (r.kind === "annual_flat") {
        rows.push({ name: CAT.products[id].name, detail: r.label, value: r.amount });
        total += r.amount;
      } else if (r.metric) {
        rows.push({ name: CAT.products[id].name, detail: r.metric, value: null });
      }
    });
    return { rows: rows, total: total, units: units };
  }
  function money(n) { return "$" + Math.round(n).toLocaleString("en-US"); }

  // ---------- tray DOM ----------
  var panel, tab, overlay, countEl;

  function injectTray() {
    tab = document.createElement("button");
    tab.className = "sb-tab";
    tab.setAttribute("aria-label", "Open Solutions Builder");
    tab.innerHTML =
      '<svg class="sb-tab__icon" viewBox="0 0 24 24" aria-hidden="true">' +
      '<path d="M12 2 3 6.5v11L12 22l9-4.5v-11L12 2Z"/>' +
      '<path d="M3 6.5 12 11l9-4.5"/><path d="M12 11v11"/>' +
      '</svg>' +
      '<span class="sb-tab__count" id="sb-count"></span>';
    tab.addEventListener("click", togglePanel);
    document.body.appendChild(tab);

    overlay = document.createElement("div");
    overlay.className = "sb-overlay";
    overlay.addEventListener("click", closePanel);
    document.body.appendChild(overlay);

    panel = document.createElement("aside");
    panel.className = "sb-panel";
    panel.setAttribute("aria-label", "Solutions Builder");
    panel.innerHTML =
      '<div class="sb-panel__head"><h3>Solutions Builder</h3><button class="sb-x" aria-label="Close">&times;</button></div>' +
      '<div class="sb-panel__body" id="sb-body"></div>' +
      '<div class="sb-panel__foot" id="sb-foot"></div>';
    document.body.appendChild(panel);

    panel.querySelector(".sb-x").addEventListener("click", closePanel);
    countEl = document.getElementById("sb-count");

    // Close when clicking anywhere outside the panel (but not on the FAB, which
    // toggles), and on Escape. The overlay handles this on mobile; this covers
    // desktop where the overlay is hidden so the page stays interactive.
    document.addEventListener("mousedown", function (e) {
      if (!panel.classList.contains("is-open")) return;
      if (panel.contains(e.target) || tab.contains(e.target)) return;
      closePanel();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && panel.classList.contains("is-open")) closePanel();
    });

    // drop target (desktop drag)
    panel.addEventListener("dragover", function (e) { e.preventDefault(); panel.classList.add("drop-hot"); });
    panel.addEventListener("dragleave", function (e) { if (!panel.contains(e.relatedTarget)) panel.classList.remove("drop-hot"); });
    panel.addEventListener("drop", function (e) {
      e.preventDefault(); panel.classList.remove("drop-hot");
      var d = (e.dataTransfer.getData("text/plain") || "").split(":");
      if (d.length === 2) add(d[1], d[0]);
    });
  }

  function openPanel() { panel.classList.add("is-open"); overlay.classList.add("is-open"); tab.classList.add("is-open", "is-tray-open"); render(); }
  function closePanel() { panel.classList.remove("is-open"); overlay.classList.remove("is-open"); tab.classList.remove("is-open", "is-tray-open"); }
  function togglePanel() { if (panel.classList.contains("is-open")) closePanel(); else openPanel(); }
  function flashTab() {
    tab.animate(
      [{ transform: "scale(1)" }, { transform: "scale(1.12)" }, { transform: "scale(1)" }],
      { duration: 260 }
    );
  }

  var TYPE_LABEL = { products: "Products", solutions: "Goals", markets: "Your market" };
  var FAM_CLASS = { b: "", t: "t", r: "r" };

  function render() {
    var n = state.items.length;
    if (countEl) { countEl.textContent = n ? n : ""; countEl.setAttribute("data-n", n); }

    var body = document.getElementById("sb-body");
    if (!body) return;

    if (!n) {
      body.innerHTML =
        '<div class="sb-hint">Drag any product, goal, or market into this tray (or tap the <b>+</b> on a card). ' +
        'We\'ll recommend a fit and estimate the impact &mdash; then you can download or email a tailored PDF brief.</div>' +
        '<div class="sb-empty">Nothing added yet.</div>';
      renderFoot(false);
      return;
    }

    var html = "";
    ["solutions", "markets", "products"].forEach(function (type) {
      var ids = selectedOf(type);
      if (!ids.length) return;
      html += '<div class="sb-section-t">' + TYPE_LABEL[type] + "</div>";
      ids.forEach(function (id) {
        var m = meta(id, type);
        var fam = type === "products" ? (FAM_CLASS[m.family] || "") : (type === "solutions" ? "g" : "t");
        html += '<div class="sb-item ' + fam + '">' +
          '<span class="sb-item__dot"></span>' +
          '<div class="sb-item__main"><div class="sb-item__name">' + esc(m.name) + "</div>" +
          '<div class="sb-item__blurb">' + esc(m.blurb) + "</div></div>" +
          '<button class="sb-item__x" data-id="' + id + '" data-type="' + type + '" aria-label="Remove">&times;</button>' +
          "</div>";
      });
    });

    // tailoring inputs
    html +=
      '<div class="sb-section-t">Tailor the estimate</div>' +
      '<div class="sb-fields">' +
      '<div><label>Vehicles / month</label><input id="sb-units" type="number" min="0" value="' + (state.units || "") + '"></div>' +
      '<div><label>Market</label><select id="sb-market"><option value="">Auto-detect</option>' +
      Object.keys(CAT.markets).map(function (k) {
        return '<option value="' + k + '"' + (state.market === k ? " selected" : "") + ">" + esc(CAT.markets[k].name) + "</option>";
      }).join("") +
      "</select></div>" +
      '<div class="full"><label>Dealership name (for the PDF)</label><input id="sb-dealer" type="text" placeholder="Optional" value="' + esc(state.dealer || "") + '"></div>' +
      "</div>";

    // live summary
    var rec = recommended(), r = roi();
    html += '<div class="sb-summary">';
    html += "<h4>Detected market</h4><div class=\"sb-item__blurb\" style=\"margin-bottom:10px\">" + esc(industry()) + "</div>";
    if (rec.length) {
      html += "<h4>We'd recommend</h4><div class=\"sb-reco\">" +
        rec.map(function (id) { return "<span>" + esc(CAT.products[id].name) + "</span>"; }).join("") + "</div>";
    }
    if (r.total > 0) {
      html += "<h4 style=\"margin-top:12px\">Estimated annual impact</h4>" +
        '<div class="sb-impact">' + money(r.total) + "</div>" +
        '<div class="sb-disclaimer">Directional estimate based on ' + (r.units || 0) +
        " vehicles/month and published, non-guaranteed figures. Your team should validate against your numbers.</div>";
    }
    html += "</div>";

    body.innerHTML = html;

    // wire remove buttons
    body.querySelectorAll(".sb-item__x").forEach(function (b) {
      b.addEventListener("click", function () { remove(b.getAttribute("data-id"), b.getAttribute("data-type")); });
    });
    // wire inputs
    var u = document.getElementById("sb-units");
    if (u) u.addEventListener("input", function () { state.units = u.value; save(); debounceSummary(); });
    var mk = document.getElementById("sb-market");
    if (mk) mk.addEventListener("change", function () { state.market = mk.value; save(); render(); });
    var dl = document.getElementById("sb-dealer");
    if (dl) dl.addEventListener("input", function () { state.dealer = dl.value; save(); });

    renderFoot(true);
  }

  var summaryTimer;
  function debounceSummary() { clearTimeout(summaryTimer); summaryTimer = setTimeout(render, 350); }

  function renderFoot(enabled) {
    var foot = document.getElementById("sb-foot");
    if (!foot) return;
    if (!enabled) { foot.innerHTML = ""; return; }
    foot.innerHTML =
      '<div class="row">' +
      '<button class="btn btn-red" id="sb-pdf">Download PDF</button>' +
      '<button class="btn btn-ghost" id="sb-email">Email PDF</button>' +
      "</div>" +
      '<button class="sb-clear" id="sb-clear">Clear all</button>';
    document.getElementById("sb-pdf").addEventListener("click", function () { buildPDF(true); });
    document.getElementById("sb-email").addEventListener("click", emailFlow);
    document.getElementById("sb-clear").addEventListener("click", clearAll);
  }

  function esc(s) { return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }

  // ---------- auto-instrument the page ----------
  function instrument() {
    // 1) any product card whose href points at a product page — the href may be
    //    relative ("bumper-bi.html" on a product page) or include the folder
    //    ("products/bumper-bi.html" elsewhere), so match on the filename slug
    //    and confirm it against the catalog.
    document.querySelectorAll('a.rel-card[href], a.product[href]').forEach(function (card) {
      var href = card.getAttribute("href") || "";
      var fm = href.match(/([a-z0-9-]+)\.html(?:[#?].*)?$/);
      if (!fm) return;
      var slug = fm[1];
      if (!CAT.products[slug]) return;
      // guard: on non-product pages, only wire links that actually go to /products/
      var onProductPage = /^products\//.test(SITE.page || "");
      if (!onProductPage && !/products\//.test(href)) return;
      if (card.getAttribute("data-sb-wired")) return;
      wireCard(card, slug, "products");
    });

    // 1b) homepage category tiles -> matched to Solutions by title text
    document.querySelectorAll(".tiles .tile").forEach(function (tile) {
      if (tile.getAttribute("data-sb-wired")) return;
      var titleEl = tile.querySelector(".tile__title");
      if (!titleEl) return;
      var title = titleEl.textContent.trim().toLowerCase();
      var id = null;
      Object.keys(CAT.solutions).forEach(function (k) {
        if (CAT.solutions[k].name.trim().toLowerCase() === title) id = k;
      });
      if (id) wireCard(tile, id, "solutions");
    });
    // 2) current page hero — add a button if this is a product/solution/market page
    var pm = (SITE.page || "").match(/^(products|solutions|markets)\/([a-z0-9-]+)\.html$/);
    if (pm) {
      var type = pm[1]; var id = pm[2];
      if (meta(id, type)) addHeroButton(type, id);
    }
    markAdds();
  }

  function wireCard(card, id, type) {
    type = type || "products";
    card.setAttribute("data-sb-wired", "1");
    if (getComputedStyle(card).position === "static") card.style.position = "relative";
    card.setAttribute("draggable", "true");
    card.addEventListener("dragstart", function (e) {
      e.dataTransfer.setData("text/plain", type + ":" + id);
      e.dataTransfer.effectAllowed = "copy";
    });
    var btn = document.createElement("button");
    btn.className = "sb-add"; btn.type = "button";
    btn.setAttribute("aria-label", "Add to Solutions Builder");
    btn.setAttribute("data-sb-id", id); btn.setAttribute("data-sb-type", type);
    btn.textContent = "+";
    btn.addEventListener("click", function (e) {
      e.preventDefault(); e.stopPropagation();
      if (has(id, type)) { remove(id, type); } else { add(id, type); openPanel(); }
    });
    card.appendChild(btn);
  }

  function addHeroButton(type, id) {
    var actions = document.querySelector(".subhero__actions");
    if (!actions) return;
    var b = document.createElement("button");
    b.type = "button";
    // Always the secondary/ghost treatment on the dark hero — sits next to the
    // primary yellow CTA (Schedule a demo / Talk to us) without competing.
    b.className = "btn btn-ghost sb-hero-btn";
    b.style.color = "rgba(255,255,255,.9)";
    b.style.borderColor = "rgba(255,255,255,.45)";
    b.setAttribute("data-sb-id", id); b.setAttribute("data-sb-type", type);
    var LABEL = "+ Add to Solutions Builder";
    b.textContent = has(id, type) ? "\u2713 Added" : LABEL;
    b.addEventListener("click", function () {
      if (has(id, type)) { remove(id, type); b.textContent = LABEL; }
      else { add(id, type); b.textContent = "\u2713 Added"; openPanel(); }
    });
    actions.appendChild(b);
  }

  function markAdds() {
    document.querySelectorAll("[data-sb-id]").forEach(function (el) {
      var inSet = has(el.getAttribute("data-sb-id"), el.getAttribute("data-sb-type"));
      if (el.classList.contains("sb-add")) el.classList.toggle("is-in", inSet);
    });
  }

  // ---------- PDF ----------
  function brandBar(doc, y, h) {
    var cols = ["#2B68AB", "#3EBDC4", "#FBCF09", "#EE3B25"];
    var w = 612 / 4;
    for (var i = 0; i < 4; i++) { doc.setFillColor(cols[i]); doc.rect(i * w, y, w, h, "F"); }
  }
  function buildPDF(doSave) {
    if (!(window.jspdf && window.jspdf.jsPDF)) { alert("PDF engine still loading — try again in a second."); return null; }
    var doc = new window.jspdf.jsPDF({ unit: "pt", format: "letter" });
    var W = 612, L = 54, R = W - 54, y = 0;

    // Cover
    brandBar(doc, 0, 10);
    doc.setFont("helvetica", "bold"); doc.setTextColor("#0D2D5C");
    doc.setFontSize(30); doc.text("VICIMUS", L, 90);
    doc.setFontSize(20); doc.setTextColor("#2A2A28");
    doc.text("Your Tailored Solutions Brief", L, 122);
    doc.setFont("helvetica", "normal"); doc.setFontSize(11); doc.setTextColor("#6E6E6C");
    var dealer = (state.dealer || "").trim();
    var prepared = dealer ? "Prepared for " + dealer : "Prepared for your dealership";
    doc.text(prepared, L, 146);
    doc.text("Market: " + industry(), L, 163);
    doc.text(new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }), L, 180);
    y = 214;

    function heading(t) {
      doc.setFont("helvetica", "bold"); doc.setFontSize(13); doc.setTextColor("#2B68AB");
      doc.text(t.toUpperCase(), L, y); y += 8;
      doc.setDrawColor("#DFE7EF"); doc.line(L, y, R, y); y += 18;
    }
    function para(t, size, color) {
      doc.setFont("helvetica", "normal"); doc.setFontSize(size || 10.5); doc.setTextColor(color || "#33332f");
      var lines = doc.splitTextToSize(t, R - L);
      lines.forEach(function (ln) { pageBreak(16); doc.text(ln, L, y); y += 15; });
    }
    function pageBreak(need) { if (y + (need || 0) > 720) { doc.addPage(); brandBar(doc, 0, 6); y = 60; } }

    // Selections
    var sols = selectedOf("solutions"), mkts = selectedOf("markets"), prods = selectedOf("products");
    if (sols.length || mkts.length || prods.length) {
      heading("What you selected");
      if (sols.length) para("Goals: " + sols.map(function (s) { return CAT.solutions[s].name; }).join(", "), 10.5, "#2A2A28");
      if (mkts.length) para("Market focus: " + mkts.map(function (s) { return CAT.markets[s].name; }).join(", "), 10.5, "#2A2A28");
      if (prods.length) para("Products of interest: " + prods.map(function (s) { return CAT.products[s].name; }).join(", "), 10.5, "#2A2A28");
      y += 8;
    }

    // Recommendations
    var rec = recommended();
    if (rec.length) {
      heading("Recommended for you");
      rec.forEach(function (id) {
        var p = CAT.products[id]; pageBreak(52);
        doc.setFont("helvetica", "bold"); doc.setFontSize(11); doc.setTextColor("#0D2D5C");
        doc.text(p.name, L, y); y += 15;
        var metric = (p.roi && p.roi.metric) ? p.roi.metric : "";
        if (metric) { doc.setFont("helvetica", "bold"); doc.setFontSize(9.5); doc.setTextColor("#3EBDC4"); doc.text(metric, L, y); y += 13; }
        para(p.blurb, 10, "#4a4a47"); y += 6;
      });
    }

    // ROI
    var r = roi();
    if (r.rows.length) {
      pageBreak(120); heading("Estimated annual impact");
      r.rows.forEach(function (row) {
        pageBreak(18);
        doc.setFont("helvetica", "normal"); doc.setFontSize(10.5); doc.setTextColor("#2A2A28");
        doc.text(row.name, L, y);
        doc.setTextColor("#6E6E6C"); doc.setFontSize(9);
        doc.text(row.detail || "", L + 4, y + 12);
        if (row.value != null) {
          doc.setFont("helvetica", "bold"); doc.setFontSize(10.5); doc.setTextColor("#16A34A");
          doc.text(money(row.value), R, y, { align: "right" });
        }
        y += 26;
      });
      if (r.total > 0) {
        pageBreak(30); doc.setDrawColor("#DFE7EF"); doc.line(L, y, R, y); y += 18;
        doc.setFont("helvetica", "bold"); doc.setFontSize(13); doc.setTextColor("#0D2D5C");
        doc.text("Estimated annual impact", L, y);
        doc.text(money(r.total), R, y, { align: "right" }); y += 20;
        para("Directional estimate based on " + r.units + " vehicles/month and published, non-guaranteed figures. Validate against your store's actuals.", 8.5, "#9A9A98");
      }
    }

    // Next steps
    pageBreak(90); heading("Next steps");
    para("Let's put these numbers against your store's actuals in a 20-minute working session.", 10.5, "#2A2A28");
    doc.setFont("helvetica", "bold"); doc.setFontSize(10.5); doc.setTextColor("#2B68AB");
    y += 4; doc.text("888-301-6178", L, y); y += 15;
    doc.text("sales@vicimus.com", L, y); y += 15;
    doc.text("vicimus.com", L, y);

    // footer band
    brandBar(doc, 782, 10);

    if (doSave) doc.save(pdfName());
    return doc;
  }
  function pdfName() {
    var d = (state.dealer || "vicimus").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
    return (d || "vicimus") + "-solutions-brief.pdf";
  }

  function emailFlow() {
    buildPDF(true); // download first (browsers can't auto-attach to mailto)
    var lines = recommended().map(function (id) { return "- " + CAT.products[id].name; }).join("\n");
    var r = roi();
    var body =
      "Hi,\n\nI put together a tailored Vicimus solutions brief" +
      (state.dealer ? " for " + state.dealer : "") + ".\n\n" +
      "Market: " + industry() + "\n" +
      (lines ? "Recommended:\n" + lines + "\n" : "") +
      (r.total > 0 ? "\nEstimated annual impact: " + money(r.total) + " (directional)\n" : "") +
      "\nThe full brief just downloaded to my device (\"" + pdfName() + "\") — attaching it here.\n\n" +
      "Take a look:  " + siteURL() + "\n\nThanks";
    var url = "mailto:?subject=" + encodeURIComponent("Vicimus — Tailored Solutions Brief") +
      "&body=" + encodeURIComponent(body);
    setTimeout(function () { window.location.href = url; }, 400);
  }
  function siteURL() {
    try { return window.location.origin + window.location.pathname.replace(/[^/]*$/, ""); }
    catch (e) { return "vicimus.com"; }
  }

  // ---------- boot ----------
  function setupHomepageGate() {
    // On the homepage, the hero already has an interactive ROI calculator,
    // so keep the Solutions Builder tab hidden until the visitor scrolls past
    // the hero. Everywhere else the tab shows immediately.
    var isHome = /(^|\/)index\.html$/.test(SITE.page || "") || (SITE.page || "") === "";
    if (!isHome) return;
    var hero = document.querySelector(".hero");
    if (!hero) return;
    tab.classList.add("sb-tab--gated");            // hidden until revealed
    function check() {
      var past = hero.getBoundingClientRect().bottom <= 60;
      tab.classList.toggle("sb-tab--reveal", past);
      // if the panel is open and we scroll back up into the hero, tuck it away
      if (!past && panel.classList.contains("is-open")) closePanel();
    }
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function () { check(); }, { threshold: [0, 0.01, 1] }).observe(hero);
    }
    window.addEventListener("scroll", check, { passive: true });
    window.addEventListener("resize", check);
    check();
  }

  function boot() { injectTray(); instrument(); render(); setupHomepageGate(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
