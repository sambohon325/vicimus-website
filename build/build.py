# -*- coding: utf-8 -*-
"""Generate every interior page, in every language, from data.py + shell.py.

    Run from anywhere:   python3 build/build.py

Output layout:
    /                 English (default)
    /es/              Spanish
    /fr/              French

English pages are authored/generated in English. The /es/ and /fr/ trees are
generated with the SAME text (English) but with correct paths, language
attribute, and language-picker wiring, so navigation works end-to-end
immediately. Running translate.py afterwards replaces the visible text in the
/es/ and /fr/ trees with real translations via Google Cloud Translation.

Path model (see shell.py for the full explanation):
    pp = page prefix  -> reaches the current language root  ("" or "../")
    ap = asset prefix -> reaches the true site root (/assets)
                         == pp for English; "../" + pp for es/fr
"""
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from shell import head, header, footer          # noqa: E402
from data import (                               # noqa: E402
    PRODUCTS, TESTIMONIALS, SOLUTIONS, MARKETS,
    COMPANY_VALUES, MILESTONES, TEAM_DEPARTMENTS, LEADERSHIP,
)

OUT = os.path.dirname(HERE)
LOGODIR = "assets/logos"

# Solutions Builder — directional ROI hints per product. The tray's
# rule-based engine reads these (via the generated catalog) to produce an
# illustrative annual-impact estimate. All figures are directional.
SB_ROI = {
    "bumper-finance":         {"kind": "per_unit",     "amount": 800,  "label": "F&I gross per vehicle",        "metric": "+$800 average PVR lift"},
    "accessory-accelerator":  {"kind": "per_unit",     "amount": 500,  "label": "Accessory gross per vehicle",  "metric": "New accessory revenue per unit"},
    "odometer-voip":          {"kind": "annual_flat",  "amount": 8400, "label": "Phone cost savings",           "metric": "~70% lower phone bill"},
    "calls-on-demand":        {"kind": "qual",                                                                   "metric": "~20% of missed calls recovered"},
    "bumper-retention":       {"kind": "qual",                                                                   "metric": "Repeat & service retention lift"},
    "bumper-inventory-ads":   {"kind": "qual",                                                                   "metric": "More qualified inventory leads"},
    "bumper-bi":              {"kind": "qual",                                                                   "metric": "Decisions on one connected dataset"},
    "glovebox-websites":      {"kind": "qual",                                                                   "metric": "Higher website conversion"},
    "powersports-independent":{"kind": "qual",                                                                   "metric": "Flexible, a-la-carte bundle"},
}

# Languages and the subfolder each lives in.
LANGS = ["en", "es", "fr"]
LANG_DIR = {"en": "", "es": "es/", "fr": "fr/"}


def ap_for(lang, pp):
    """Asset prefix: English == page prefix; es/fr sit one folder deeper."""
    return ("../" + pp) if lang != "en" else pp


def write(lang, relpath, html):
    """Write a page into the correct language tree."""
    path = os.path.join(OUT, LANG_DIR[lang], relpath)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


# ----------------------------------------------------------------------
# Reusable blocks (take pp + ap so assets and links resolve per language)
# ----------------------------------------------------------------------
def related_cards(current_slug, pp, ap):
    picks = [p for p in PRODUCTS if p["slug"] != current_slug][:4]
    out = []
    for p in picks:
        fam = "" if p["family"] == "b" else (" t" if p["family"] == "t" else " r")
        out.append(f'''<a class="rel-card{fam}" href="{p['slug']}.html">
  <div class="rel-card__logo"><img src="{ap}{LOGODIR}/{p['logo']}" alt="{p['name']}"></div>
  <h3 translate="no">{p['name']}</h3>
  <p>{p['hero_p'][:120].rsplit(' ',1)[0]}&hellip;</p>
  <span class="go">View product &rarr;</span>
</a>''')
    return "\n".join(out)


def testimonials_block():
    cards = "\n".join(
        f'<div class="qcard"><p>&ldquo;{t[0]}&rdquo;</p><cite translate="no">{t[1]}</cite></div>'
        for t in TESTIMONIALS[:2]
    )
    return f'''<section class="section section--wash">
  <div class="wrap centered">
    <p class="eyebrow">Happy clients, happy us</p>
    <h2 class="h2">We thrive helping our clients succeed.</h2>
  </div>
  <div class="wrap"><div class="quotes">{cards}</div></div>
</section>'''


def services_block():
    return '''<section class="section">
  <div class="wrap centered">
    <p class="eyebrow">Do more with Vicimus</p>
    <h2 class="h2">Beyond the platform.</h2>
    <p class="lede">Three in-house teams that keep your store connected, creative, and converting.</p>
  </div>
  <div class="wrap">
    <div class="services">
      <div class="svc">
        <div class="svc__ico"><svg viewBox="0 0 24 24"><path d="M4 5h16v11H4z"/><path d="M2 20h20"/></svg></div>
        <h3>Creative Services</h3>
        <p>Our creative team delivers quality content and design for all your marketing needs.</p>
      </div>
      <div class="svc">
        <div class="svc__ico"><svg viewBox="0 0 24 24"><path d="M12 3l8 4v5c0 5-3.5 7.5-8 9-4.5-1.5-8-4-8-9V7z"/></svg></div>
        <h3>I.T. Services</h3>
        <p>Keep your store connected and profitable with the latest networking gear, security, and in-house support.</p>
      </div>
      <div class="svc">
        <div class="svc__ico"><svg viewBox="0 0 24 24"><path d="M4 4h16v12H7l-3 3z"/></svg></div>
        <h3>BDC Services</h3>
        <p>Give your sales and service departments the boost they need with full business development strategy.</p>
      </div>
    </div>
  </div>
</section>'''


def cta_band(pp):
    return f'''<section class="section" style="background:var(--wash)">
  <div class="wrap centered">
    <p class="eyebrow">Ready to start?</p>
    <h2 class="h2">See it running on your store's numbers.</h2>
    <p class="lede">Book a 20-minute demo. No long-term contracts, no tools to rip out.</p>
    <div style="margin-top:26px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap">
      <a class="btn btn-red" href="{pp}book-a-demo.html">Book a demo</a>
      <a class="btn btn-ghost" href="{pp}index.html#suite">View all products</a>
    </div>
  </div>
</section>'''


# ----------------------------------------------------------------------
# Page builders (each takes a language)
# ----------------------------------------------------------------------
def product_shots(p):
    """Three swappable screenshot frames. Drop real images in
    assets/img/screens/ and list them in the product's 'screens' field."""
    caps = p.get("screens") or [
        "Product dashboard", "Campaign / detail view", "Reporting & results"
    ]
    frames = []
    for cap in caps[:3]:
        frames.append(f'''<div class="shot">
  <div class="shot__frame">
    <div class="shot__ph">
      <svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="14" rx="2"/><path d="M3 9h18"/></svg>
      <span>Screenshot coming soon</span>
    </div>
  </div>
  <div class="shot__cap">{cap}</div>
</div>''')
    return f'''<section class="section section--tight">
  <div class="wrap">
    <p class="eyebrow" style="text-align:center">A look inside</p>
    <h2 class="h2 centered" style="margin-bottom:8px">See it in action.</h2>
    <div class="shots">{"".join(frames)}</div>
  </div>
</section>'''


def retention_journey():
    """Customer Retention Journey Simulator — an interactive, CSS/JS-driven
    lifecycle timeline. Bumper Retention only. Self-contained (styles are in
    site.css under .jsim-*; behaviour is the inline script below)."""
    stages = [
        ("Service Visit", "A customer comes in for routine service. Every RO, every touchpoint is captured automatically from your DMS.",
         "wrench", 1, "", "repair order logged"),
        ("Intent Signal Detected", "Bumper mines the data — equity position, mileage, lease maturity — and flags this customer as in-market before they start shopping.",
         "signal", 92, "%", "purchase-intent confidence"),
        ("Smart Message Sent", "The right message goes out on the customer's preferred channel — here, an SMS, timed to the moment of intent.",
         "sms", 98, "%", "SMS open rate"),
        ("Email Opened", "A personalized lifecycle email lands with an offer built around their vehicle and equity — not a generic blast.",
         "mail", 3, "x", "higher engagement vs. batch email"),
        ("Offer Engaged", "The customer clicks through and books. Behavioral tracking attributes every step back to the campaign.",
         "cursor", 100, "%", "attributed to the campaign"),
        ("Vehicle Purchased", "A retained customer becomes a repeat sale — and re-enters the lifecycle for service, F&I, and their next vehicle.",
         "car", 800, "", "avg. added gross per retained deal"),
    ]
    nodes = ""
    for i, (title, desc, icon, num, suf, lbl) in enumerate(stages):
        nodes += f'''<button class="jsim-node" data-i="{i}" data-num="{num}" data-suf="{suf}" aria-label="{title}">
  <span class="jsim-dot"><span class="jsim-ico jsim-ico--{icon}"></span></span>
  <span class="jsim-node-lbl">{title}</span>
</button>'''
    # detail cards
    cards = ""
    for i, (title, desc, icon, num, suf, lbl) in enumerate(stages):
        cards += f'''<div class="jsim-card" data-i="{i}">
  <div class="jsim-card-step">Stage {i+1} of {len(stages)}</div>
  <h3 class="jsim-card-title">{title}</h3>
  <p class="jsim-card-desc">{desc}</p>
  <div class="jsim-stat"><span class="jsim-stat-num" data-num="{num}" data-suf="{suf}">0{suf}</span><span class="jsim-stat-lbl">{lbl}</span></div>
</div>'''
    return f'''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">See it work</p>
    <h2 class="h2" style="margin-bottom:8px">From service visit to repeat sale.</h2>
    <p class="lede">Watch how one customer moves through the retention lifecycle &mdash; intent mining, smart messaging, and personalization turning a routine visit into revenue.</p>
  </div>
  <div class="wrap">
    <div class="jsim" id="jsim">
      <div class="jsim-track">
        <div class="jsim-line"><span class="jsim-line-fill" id="jsim-fill"></span></div>
        <div class="jsim-nodes">{nodes}</div>
      </div>
      <div class="jsim-cards" id="jsim-cards">{cards}</div>
      <div class="jsim-controls">
        <button class="jsim-btn" id="jsim-prev" aria-label="Previous stage">&larr;</button>
        <div class="jsim-play" id="jsim-play"><span class="jsim-play-ico"></span> <span id="jsim-play-lbl">Playing</span></div>
        <button class="jsim-btn" id="jsim-next" aria-label="Next stage">&rarr;</button>
      </div>
    </div>
  </div>
  <script>
  (function(){{
    var root=document.getElementById('jsim'); if(!root) return;
    var nodes=[].slice.call(root.querySelectorAll('.jsim-node'));
    var cards=[].slice.call(root.querySelectorAll('.jsim-card'));
    var fill=document.getElementById('jsim-fill');
    var N=nodes.length, cur=-1, timer=null, playing=false, started=false;
    function countTo(el){{
      var target=parseFloat(el.getAttribute('data-num'))||0, suf=el.getAttribute('data-suf')||'';
      var dur=700, t0=performance.now();
      function tick(now){{
        var k=Math.min(1,(now-t0)/dur); var val=target*(0.5-Math.cos(k*Math.PI)/2);
        var out = target>=100 ? Math.round(val) : (target%1===0? Math.round(val): val.toFixed(0));
        el.textContent=(target>=1000?Math.round(val).toLocaleString():out)+suf;
        if(k<1) requestAnimationFrame(tick);
      }}
      requestAnimationFrame(tick);
    }}
    function go(i){{
      if(i<0)i=0; if(i>N-1)i=N-1; cur=i;
      nodes.forEach(function(n,idx){{n.classList.toggle('is-active',idx===i);n.classList.toggle('is-done',idx<i);}});
      cards.forEach(function(c,idx){{c.classList.toggle('is-active',idx===i);}});
      fill.style.height=(i/(N-1)*100)+'%'; fill.style.width=(i/(N-1)*100)+'%';
      var active=cards[i].querySelector('.jsim-stat-num'); if(active) countTo(active);
    }}
    function next(){{ if(cur>=N-1){{ go(0); }} else {{ go(cur+1); }} }}
    function play(){{ playing=true; root.classList.add('is-playing'); clearInterval(timer); timer=setInterval(next,2200); document.getElementById('jsim-play-lbl').textContent='Playing'; }}
    function pause(){{ playing=false; root.classList.remove('is-playing'); clearInterval(timer); document.getElementById('jsim-play-lbl').textContent='Paused'; }}
    nodes.forEach(function(n){{ n.addEventListener('click',function(){{ pause(); go(parseInt(n.getAttribute('data-i'))); }}); }});
    document.getElementById('jsim-next').addEventListener('click',function(){{ pause(); go(cur+1); }});
    document.getElementById('jsim-prev').addEventListener('click',function(){{ pause(); go(cur-1); }});
    document.getElementById('jsim-play').addEventListener('click',function(){{ playing?pause():play(); }});
    // autoplay when scrolled into view
    if('IntersectionObserver' in window){{
      new IntersectionObserver(function(es){{ es.forEach(function(e){{
        if(e.isIntersecting && !started){{ started=true; go(0); play(); }}
      }});}},{{threshold:.35}}).observe(root);
    }} else {{ go(0); play(); }}
  }})();
  </script>
</section>'''


def retention_comparison():
    """Credible capability comparison. Bumper Retention only.
    Cells: 'yes' | 'partial' | 'no', with optional short label."""
    cols = ["Bumper Retention", "AutoAlert", "automotiveMastermind"]
    # (capability, bumper, autoalert, mastermind); each cell = (mark, label?)
    rows = [
        ("Intent Mining / Purchase Signals", ("yes",), ("yes",), ("yes",)),
        ("Sales, Service &amp; Unsold Prospect Database Activation", ("yes",), ("partial",), ("partial",)),
        ("Automated Lifecycle Campaigns", ("yes",), ("partial",), ("yes",)),
        ("Email Marketing", ("yes",), ("yes",), ("yes",)),
        ("SMS Marketing", ("yes",), ("yes",), ("partial",)),
        ("Ringless Voicemail", ("yes",), ("no",), ("no",)),
        ("Direct Mail Campaigns", ("yes",), ("yes",), ("yes",)),
        ("Customer Preferred-Channel Learning", ("yes",), ("no",), ("no",)),
        ("Behavioral Tracking Across Campaigns", ("yes",), ("yes",), ("yes",)),
        ("Personalized Messaging at Scale", ("yes",), ("yes",), ("yes",)),
        ("Service Retention Campaigns", ("yes",), ("yes",), ("yes",)),
        ("Dedicated Performance Manager", ("yes", "Included"), ("partial", "Varies"), ("yes",)),
        ("Fully Managed Campaign Deployment", ("yes",), ("no",), ("partial",)),
        ("Unlimited Campaign Creation", ("yes",), ("no",), ("no",)),
        ("Transparent Campaign Reporting", ("yes",), ("yes",), ("yes",)),
        ("Sales, Service, Parts, F&amp;I Marketing in One Platform", ("yes",), ("partial",), ("partial",)),
    ]
    MARK = {
        "yes": '<span class="cmp-mark cmp-yes" title="Yes"><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg></span>',
        "partial": '<span class="cmp-mark cmp-part" title="Partial"><svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 0 1 0 18Z"/><circle cx="12" cy="12" r="9"/></svg></span>',
        "no": '<span class="cmp-mark cmp-no" title="Not offered"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg></span>',
    }
    def cell(c, highlight=False):
        mark = MARK[c[0]]
        label = f'<span class="cmp-lbl">{c[1]}</span>' if len(c) > 1 else ""
        return f'<td class="{"cmp-col-hl" if highlight else ""}">{mark}{label}</td>'

    body = ""
    for cap, b, a, m in rows:
        body += f'<tr><th scope="row">{cap}</th>{cell(b, True)}{cell(a)}{cell(m)}</tr>'

    heads = f'<th class="cmp-col-hl">{cols[0]}</th><th>{cols[1]}</th><th>{cols[2]}</th>'
    return f'''<section class="section section--wash">
  <div class="wrap centered">
    <p class="eyebrow">How it stacks up</p>
    <h2 class="h2" style="margin-bottom:8px">Bumper Retention vs. the field.</h2>
    <p class="lede">Where dealer retention actually gets won &mdash; identifying opportunities, activating customers, communicating across every channel, and executing it for you.</p>
  </div>
  <div class="wrap">
    <div class="cmp-legend">
      <span><span class="cmp-mark cmp-yes"><svg viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg></span> Full</span>
      <span><span class="cmp-mark cmp-part"><svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 0 1 0 18Z"/><circle cx="12" cy="12" r="9"/></svg></span> Partial / varies</span>
      <span><span class="cmp-mark cmp-no"><svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6 6 18"/></svg></span> Not offered</span>
    </div>
    <div class="cmp-wrap">
      <table class="cmp">
        <thead><tr><th scope="col">Capability</th>{heads}</tr></thead>
        <tbody>{body}</tbody>
      </table>
    </div>
    <p class="cmp-disc">Comparison reflects Vicimus's understanding of publicly available information about AutoAlert and automotiveMastermind as of 2026, prepared in good faith. Competitor offerings change and may vary by plan, region, and configuration; product and company names are trademarks of their respective owners, used here for identification only. Verify current capabilities with each vendor.</p>
  </div>
</section>'''


def build_product(p, lang):
    pp = "../"                      # product pages live one level under lang root
    ap = ap_for(lang, pp)
    page = f"products/{p['slug']}.html"

    features = "\n".join(
        f'''<div class="feature {f[0]}">
  <span class="feature__k">{i:02d}</span>
  <h3>{f[1]}</h3>
  <p>{f[2]}</p>
</div>''' for i, f in enumerate(p["features"], 1)
    )

    html = head(p["seo_title"], p["seo_desc"], ap, lang)
    html += header(pp, ap, lang)
    # Per-product custom sections (Bumper Retention gets the journey simulator
    # under Key Capabilities and a capability comparison after the screenshots).
    extra_after_capabilities = retention_journey() if p["slug"] == "bumper-retention" else ""
    extra_after_shots = retention_comparison() if p["slug"] == "bumper-retention" else ""
    html += f'''
<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <img class="subhero__logo" src="{ap}{LOGODIR}/{p['logo']}" alt="{p['name']}">
    <p class="eyebrow" translate="no">{p['eyebrow']}</p>
    <h1 class="h1">{p['hero_h']}</h1>
    <p class="subhero__lead">{p['hero_p']}</p>
    <div class="subhero__actions">
      <a class="btn btn-yellow" href="{pp}book-a-demo.html">Schedule a demo &rarr;</a>
    </div>
  </div>
</section>

<div class="crumbs"><div class="crumbs__inner">
  <a href="{pp}index.html">Home</a><span class="sep">/</span>
  <a href="{pp}products/index.html">Products</a><span class="sep">/</span><span translate="no">{p['name']}</span>
</div></div>

<section class="section">
  <div class="wrap">
    <div class="intro-split">
      <div><p class="eyebrow">Overview</p><h2 class="h2">{p['intro_h']}</h2></div>
      <div class="prose"><p>{p['intro_p']}</p></div>
    </div>
  </div>
</section>

<section class="section section--wash section--tight">
  <div class="wrap">
    <p class="eyebrow" style="text-align:center">Key capabilities</p>
    <h2 class="h2 centered" style="margin-bottom:8px">{p['features_h']}</h2>
    <div class="feature-grid">{features}</div>
  </div>
</section>

{extra_after_capabilities}

{product_shots(p)}

{extra_after_shots}

<section class="band">
  <div class="band__inner">
    <div>
      <p class="eyebrow">{p['band_eyebrow']}</p>
      <h2 class="h2">{p['band_h']}</h2>
      <p>{p['band_p']}</p>
    </div>
    <div class="band__actions">
      <a class="btn btn-yellow" href="{pp}book-a-demo.html">Book a demo</a>
    </div>
  </div>
</section>

{testimonials_block()}

<section class="related">
  <div class="wrap centered">
    <p class="eyebrow">Our products</p>
    <h2 class="h2">Tech that keeps your dealership on top.</h2>
  </div>
  <div class="wrap"><div class="related-grid">{related_cards(p['slug'], pp, ap)}</div></div>
</section>

{cta_band(pp)}
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


def build_products_index(lang):
    pp = "../"
    ap = ap_for(lang, pp)
    page = "products/index.html"
    cards = []
    for p in PRODUCTS:
        fam = "" if p["family"] == "b" else (" t" if p["family"] == "t" else " r")
        cards.append(f'''<a class="rel-card{fam}" href="{p['slug']}.html">
  <div class="rel-card__logo"><img src="{ap}{LOGODIR}/{p['logo']}" alt="{p['name']}"></div>
  <h3 translate="no">{p['name']}</h3>
  <p>{p['hero_p'][:130].rsplit(' ',1)[0]}&hellip;</p>
  <span class="go">View product &rarr;</span>
</a>''')
    grid = "\n".join(cards)
    html = head("Products &mdash; Vicimus", "The full Vicimus product suite: Bumper Retention, Inventory Ads, BI, Finance, Accessory Accelerator, GloveBox, Odometer, Calls on Demand, and PSI.", ap, lang)
    html += header(pp, ap, lang)
    html += f'''
<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <p class="eyebrow">Product suite</p>
    <h1 class="h1">Everything your dealership needs &mdash; and nothing it doesn't.</h1>
    <p class="subhero__lead">Every product layers onto your existing DMS, CRM, and OEM data. Start with one, expand when you're ready.</p>
    <div class="subhero__actions"><a class="btn btn-yellow" href="{pp}book-a-demo.html">Book a demo &rarr;</a></div>
  </div>
</section>
<div class="crumbs"><div class="crumbs__inner">
  <a href="{pp}index.html">Home</a><span class="sep">/</span>Products
</div></div>
<section class="related" style="background:#fff">
  <div class="wrap"><div class="related-grid" style="margin-top:8px">{grid}</div></div>
</section>
{services_block()}
{cta_band(pp)}
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


def build_why(lang):
    """Retired page. 'Why Vicimus' content is now folded into About Us.
    We keep a lightweight redirect so any existing /why-vicimus.html links
    (the page was previously live) forward to about.html instead of 404ing."""
    pp = ""
    ap = ap_for(lang, pp)
    page = "why-vicimus.html"
    html = f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url={pp}about.html">
<link rel="canonical" href="{pp}about.html">
<meta name="robots" content="noindex">
<title>Redirecting&hellip; &mdash; Vicimus</title>
</head>
<body>
<p>This page has moved to <a href="{pp}about.html">About Us</a>.</p>
<script>location.replace("{pp}about.html");</script>
</body>
</html>'''
    return write(lang, page, html)


def build_contact(lang):
    pp = ""
    ap = ap_for(lang, pp)
    page = "contact.html"
    html = head("Contact &mdash; Vicimus", "Get in touch with the Vicimus team. Sales, support, and general enquiries for dealerships across the US and Canada.", ap, lang)
    html += header(pp, ap, lang)
    html += f'''
<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <p class="eyebrow">Get in touch</p>
    <h1 class="h1">Let's talk about your store.</h1>
    <p class="subhero__lead">Whether you're comparing options or ready to get started, our team responds fast &mdash; and you'll always talk to a real person who knows the automotive business.</p>
  </div>
</section>
<div class="crumbs"><div class="crumbs__inner"><a href="{pp}index.html">Home</a><span class="sep">/</span>Contact</div></div>

<section class="section">
  <div class="wrap">
    <div class="contact-grid">
      <div>
        <p class="eyebrow">Reach us directly</p>
        <h2 class="h2">Talk to a human.</h2>
        <ul class="contact-list">
          <li><div><div class="lbl">Phone</div><a href="tel:+18883016178" translate="no">888-301-6178</a></div></li>
          <li><div><div class="lbl">Sales</div><a href="mailto:sales@vicimus.com" translate="no">sales@vicimus.com</a></div></li>
          <li><div><div class="lbl">Support</div><a href="mailto:support@vicimus.com" translate="no">support@vicimus.com</a></div></li>
          <li><div><div class="lbl">Login</div><a href="https://bumper.vicimus.com/login" translate="no">bumper.vicimus.com/login</a></div></li>
          <li><div><div class="lbl">Head office</div><span class="v">Ontario, Canada &middot; Serving US &amp; CA markets</span></div></li>
        </ul>
      </div>
      <div class="contact-card">
        <span class="form__legend">Send us a message</span>
        <form method="post" action="#">
          <div class="form-row cols-2">
            <div class="field"><label>First name</label><input type="text" autocomplete="given-name" required></div>
            <div class="field"><label>Last name</label><input type="text" autocomplete="family-name" required></div>
          </div>
          <div class="form-row"><div class="field"><label>Work email</label><input type="email" autocomplete="email" required></div></div>
          <div class="form-row"><div class="field"><label>Dealership</label><input type="text"></div></div>
          <div class="form-row"><div class="field"><label>How can we help?</label><textarea></textarea></div></div>
          <button class="form__submit" type="submit">Send message</button>
        </form>
      </div>
    </div>
  </div>
</section>
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


def build_book_demo(lang):
    pp = ""
    ap = ap_for(lang, pp)
    page = "book-a-demo.html"
    html = head("Book a Demo &mdash; Vicimus", "Book a 20-minute demo. See exactly what Vicimus would do for a store like yours. No long-term contracts, no tools to rip out.", ap, lang)
    html += header(pp, ap, lang)
    html += f'''
<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <p class="eyebrow">Book a 20-minute demo</p>
    <h1 class="h1">See it running on your store's numbers.</h1>
    <p class="subhero__lead">No long-term contracts. No tools to rip out. We'll show you exactly what Bumper would do for a store like yours.</p>
  </div>
</section>
<div class="crumbs"><div class="crumbs__inner"><a href="{pp}index.html">Home</a><span class="sep">/</span>Book a Demo</div></div>

<section class="section">
  <div class="wrap">
    <div class="contact-grid">
      <div>
        <p class="eyebrow">What to expect</p>
        <h2 class="h2">A working session, not a sales pitch.</h2>
        <ul class="checklist">
          <li>A walkthrough of the products that fit your store &mdash; nothing you don't need.</li>
          <li>A live look at how retention, ads, websites, and call tracking connect to your DMS and CRM.</li>
          <li>A directional ROI estimate built on your own repair-order volume and values.</li>
          <li>Straight answers on onboarding, pricing flexibility, and timelines.</li>
        </ul>
        <p style="margin-top:24px;font-size:.85rem;color:var(--muted)">Prefer the phone? Call <a href="tel:+18883016178" style="color:var(--blue);font-weight:600" translate="no">888-301-6178</a>.</p>
      </div>
      <div class="contact-card">
        <span class="form__legend">Request a demo</span>
        <form method="post" action="#">
          <div class="form-row cols-2">
            <div class="field"><label>First name</label><input type="text" required></div>
            <div class="field"><label>Last name</label><input type="text" required></div>
          </div>
          <div class="form-row"><div class="field"><label>Work email</label><input type="email" required></div></div>
          <div class="form-row"><div class="field"><label>Dealership name</label><input type="text" required></div></div>
          <div class="form-row cols-2">
            <div class="field"><label>Market</label><select><option>United States</option><option>Canada</option></select></div>
            <div class="field"><label>Role</label><select><option>General Manager</option><option>Dealer Principal</option><option>Fixed Operations Director</option><option>Marketing / BDC</option><option>Other</option></select></div>
          </div>
          <div class="form-row"><div class="field"><label>Anything specific you'd like to see? (optional)</label><textarea></textarea></div></div>
          <button class="form__submit" type="submit">Request my demo</button>
        </form>
      </div>
    </div>
  </div>
</section>
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


def build_careers(lang):
    pp = ""
    ap = ap_for(lang, pp)
    page = "careers.html"
    jobs = [
        ("Performance Manager", "Client Success &middot; Remote (US/CA)", "Own a book of dealer accounts and run monthly strategy sessions that keep clients winning."),
        ("Full-Stack Developer", "Engineering &middot; Ontario / Remote", "Build and scale the Bumper platform across retention, BI, and websites."),
        ("BDC Call Specialist", "Calls on Demand &middot; North America", "Set appointments and deliver white-glove phone engagement for our dealer partners."),
        ("Digital Advertising Specialist", "Marketing Services &middot; Remote", "Run Facebook and Google inventory-ad campaigns and optimize spend for dealer ROI."),
    ]
    jobs_html = "\n".join(f'''<div class="job">
  <div><h3>{t}</h3><div class="meta">{m}</div><p style="margin:8px 0 0;font-size:.85rem;color:var(--muted)">{d}</p></div>
  <a class="btn btn-blue" href="{pp}contact.html">Apply &rarr;</a>
</div>''' for t, m, d in jobs)
    html = head("Careers &mdash; Vicimus", "Join a team on a mission. Open roles across client success, engineering, BDC, and marketing services.", ap, lang)
    html += header(pp, ap, lang)
    html += f'''
<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <p class="eyebrow">Careers</p>
    <h1 class="h1">Join a team on a mission.</h1>
    <p class="subhero__lead">We're building the retention layer the automotive industry was missing &mdash; and we do it with a white-glove standard that starts with our own people.</p>
  </div>
</section>
<div class="crumbs"><div class="crumbs__inner"><a href="{pp}index.html">Home</a><span class="sep">/</span>Careers</div></div>

<section class="section">
  <div class="wrap">
    <div class="intro-split">
      <div><p class="eyebrow">Life at Vicimus</p><h2 class="h2">Owner-operated, dealer-obsessed.</h2></div>
      <div class="prose"><p>We're bootstrapped and independent, which means we answer to our clients and our team &mdash; not to outside investors. If you care about doing right by dealers and want the room to do your best work, you'll fit in here.</p></div>
    </div>
  </div>
</section>

<section class="section section--wash">
  <div class="wrap">
    <p class="eyebrow" style="text-align:center">Open roles</p>
    <h2 class="h2 centered" style="margin-bottom:32px">We're hiring.</h2>
    <div class="jobs">{jobs_html}</div>
    <p class="centered" style="margin-top:28px;font-size:.85rem;color:var(--muted)">Don't see your role? <a href="{pp}contact.html" style="color:var(--blue);font-weight:600">Introduce yourself &rarr;</a></p>
  </div>
</section>
{cta_band(pp)}
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


# ----------------------------------------------------------------------
# Homepage: hand-authored index.html at root is the English source.
# Derive /es/index.html and /fr/index.html from it (correct paths + wiring).
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# LAYOUT A — Solutions & Markets (problem-first). Shared renderer.
# ----------------------------------------------------------------------
def _by_product_slug(slug):
    return next((p for p in PRODUCTS if p["slug"] == slug), None)


def build_audience_page(item, kind, lang):
    """kind: 'solutions' or 'markets'. Both use Layout A."""
    pp = "../"
    ap = ap_for(lang, pp)
    page = f"{kind}/{item['slug']}.html"

    challenges = "\n".join(
        f'''<div class="challenge">
  <span class="challenge__n">{i:02d}</span>
  <h3>{c[0]}</h3>
  <p>{c[1]}</p>
</div>''' for i, c in enumerate(item["challenges"], 1)
    )

    help_cards = []
    for slug in item["products"]:
        pr = _by_product_slug(slug)
        if not pr:
            continue
        fam = "" if pr["family"] == "b" else (" t" if pr["family"] == "t" else " r")
        help_cards.append(f'''<a class="rel-card{fam}" href="{pp}products/{pr['slug']}.html">
  <div class="rel-card__logo"><img src="{ap}{LOGODIR}/{pr['logo']}" alt="{pr['name']}"></div>
  <h3 translate="no">{pr['name']}</h3>
  <p>{pr['hero_p'][:110].rsplit(' ',1)[0]}&hellip;</p>
  <span class="go">View product &rarr;</span>
</a>''')
    help_html = "\n".join(help_cards)

    outcomes = "\n".join(
        f'<div class="centered"><div class="fig {o[0]}">{o[1]}</div><div class="cap">{o[2]}</div></div>'
        for o in item["outcomes"]
    )
    quotes = "\n".join(
        f'<div class="qcard"><p>&ldquo;{t[0]}&rdquo;</p><cite translate="no">{t[1]}</cite></div>'
        for t in TESTIMONIALS[:2]
    )
    crumb_label = "Solutions" if kind == "solutions" else "Markets Served"

    html = head(item["seo_title"], item["seo_desc"], ap, lang)
    html += header(pp, ap, lang)
    html += f'''
<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <p class="eyebrow">{item['eyebrow']}</p>
    <h1 class="h1">{item['hero_h']}</h1>
    <p class="subhero__lead">{item['hero_p']}</p>
    <div class="subhero__actions">
      <a class="btn btn-yellow" href="{pp}contact.html">Talk to us &rarr;</a>
    </div>
  </div>
</section>

<div class="crumbs"><div class="crumbs__inner">
  <a href="{pp}index.html">Home</a><span class="sep">/</span>{crumb_label}<span class="sep">/</span>{item['name']}
</div></div>

<section class="section">
  <div class="wrap">
    <div class="section-head" style="margin-bottom:44px">
      <p class="eyebrow">The challenge</p>
      <h2 class="h2">{item['challenge_h']}</h2>
    </div>
    <div class="challenges">{challenges}</div>
  </div>
</section>

<section class="section section--wash">
  <div class="wrap centered">
    <p class="eyebrow">How we help</p>
    <h2 class="h2">The products that move the needle here.</h2>
    <p class="lede">Each layers onto what you already run &mdash; start with one, add more when you're ready.</p>
  </div>
  <div class="wrap"><div class="helpgrid">{help_html}</div></div>
</section>

<section class="section">
  <div class="wrap centered">
    <p class="eyebrow">What good looks like</p>
    <h2 class="h2">Outcomes dealers see.</h2>
  </div>
  <div class="wrap"><div class="stat-strip" style="max-width:820px;margin:44px auto 0">{outcomes}</div></div>
</section>

<section class="section section--wash">
  <div class="wrap centered"><p class="eyebrow">In their words</p><h2 class="h2">Dealers who made the switch.</h2></div>
  <div class="wrap"><div class="quotes">{quotes}</div></div>
</section>

<section class="section">
  <div class="wrap centered">
    <p class="eyebrow">Ready to start?</p>
    <h2 class="h2">Let's talk about your store.</h2>
    <p class="lede">A 20-minute conversation is enough to see whether we're a fit. No long-term contracts, no tools to rip out.</p>
    <div style="margin-top:26px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap">
      <a class="btn btn-red" href="{pp}contact.html">Contact us</a>
      <a class="btn btn-ghost" href="{pp}book-a-demo.html">Book a demo</a>
    </div>
  </div>
</section>
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


# ----------------------------------------------------------------------
# LAYOUT C — About & Team
# ----------------------------------------------------------------------
def build_about(lang):
    pp = ""
    ap = ap_for(lang, pp)
    page = "about.html"
    values = "\n".join(
        f'<div class="value"><h3>{t}</h3><p>{d}</p></div>' for t, d in COMPANY_VALUES
    )
    timeline = "\n".join(
        f'<div class="tl"><h3>{t}</h3><p>{d}</p></div>' for t, d in MILESTONES
    )
    whiteglove = [
        ("Premium Customer Service", "Top-tier service with a personal touch &mdash; clients work with the same Vicimus team member to deliver the best results."),
        ("Exemplary Concierge Support", "Our dedicated performance management team provides unparalleled concierge-style assistance."),
        ("First-Class Customer Care", "A first-class experience from simple, thorough onboarding to monthly performance reviews and on-demand support."),
        ("White Glove Expertise", "Meticulous, highly personalized support that delivers the results your store is looking for."),
    ]
    wg_html = "\n".join(
        f'<div class="feature"><span class="feature__k">{i:02d}</span><h3>{t}</h3><p>{d}</p></div>'
        for i, (t, d) in enumerate(whiteglove, 1)
    )
    quotes = "\n".join(
        f'<div class="qcard"><p>&ldquo;{t[0]}&rdquo;</p><cite translate="no">{t[1]}</cite></div>'
        for t in TESTIMONIALS
    )
    html = head("About Us &mdash; Vicimus", "Vicimus builds the retention layer the automotive industry was missing — connected dealer marketing and technology, backed by white-glove performance management.", ap, lang)
    html += header(pp, ap, lang)
    html += f'''
<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <p class="eyebrow">About us</p>
    <h1 class="h1">We built the retention layer the industry was missing.</h1>
    <p class="subhero__lead">Vicimus was founded in Ontario, Canada on one observation: most dealers had the data to retain their customers &mdash; they just didn't have the tools to act on it systematically. Every product we've built since works on that principle.</p>
    <div class="subhero__actions"><a class="btn btn-yellow" href="{pp}contact.html">Get in touch &rarr;</a></div>
  </div>
</section>
<div class="crumbs"><div class="crumbs__inner"><a href="{pp}index.html">Home</a><span class="sep">/</span>About Us</div></div>

<section class="section">
  <div class="wrap">
    <div class="intro-split">
      <div><p class="eyebrow">Our mission</p><h2 class="h2">Connect what dealers have. Close the gaps.</h2></div>
      <div class="prose">
        <p>Dealers already own the relationships and the data. What they lack is the connective tissue &mdash; the tooling to turn that data into systematic retention, sharper advertising, captured leads, and clear reporting across every department.</p>
        <p>We make it easy for a small team to run like a large one: modular products that layer onto your existing DMS, CRM, and OEM data, each backed by a dedicated performance manager who owns the outcome.</p>
      </div>
    </div>
  </div>
</section>

<section class="section section--wash">
  <div class="wrap centered">
    <p class="eyebrow">What we stand for</p>
    <h2 class="h2">The principles behind every account.</h2>
  </div>
  <div class="wrap"><div class="values">{values}</div></div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head" style="margin-bottom:8px">
      <p class="eyebrow">The story so far</p>
      <h2 class="h2">Sixteen-plus years, one principle.</h2>
    </div>
    <div class="wrap" style="max-width:760px;padding:0"><div class="timeline">{timeline}</div></div>
  </div>
</section>

<section class="section section--wash">
  <div class="wrap centered">
    <div class="stat-strip" style="max-width:760px;margin:0 auto">
      <div class="centered"><div class="fig">16+</div><div class="cap">Years serving dealers</div></div>
      <div class="centered"><div class="fig t">US &amp; CA</div><div class="cap">Markets served</div></div>
      <div class="centered"><div class="fig r">Bootstrapped</div><div class="cap">Independent &amp; owner-operated</div></div>
    </div>
  </div>
</section>

<section class="section">
  <div class="wrap">
    <div class="section-head" style="margin-bottom:44px">
      <p class="eyebrow">The vendor partnership you've been looking for</p>
      <h2 class="h2">White-glove, every step.</h2>
      <p class="lede">In a landscape where automotive vendor support is dwindling, we're the exception &mdash; we cap active clients per team member so every dealer gets real attention, not a ticket number.</p>
    </div>
    <div class="feature-grid">{wg_html}</div>
  </div>
</section>

<section class="section section--wash" id="clients">
  <div class="wrap centered"><p class="eyebrow">Happy clients, happy us</p><h2 class="h2">We thrive helping our clients succeed.</h2></div>
  <div class="wrap"><div class="quotes" style="grid-template-columns:repeat(3,1fr)">{quotes}</div></div>
</section>

<section class="section">
  <div class="wrap centered">
    <p class="eyebrow">Meet the people</p>
    <h2 class="h2">A team that picks up the phone.</h2>
    <p class="lede">Our people are the product. <a href="{pp}team.html" style="color:var(--blue);font-weight:600">Meet the team &rarr;</a></p>
  </div>
</section>
{cta_band(pp)}
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


def build_team(lang):
    pp = ""
    ap = ap_for(lang, pp)
    page = "team.html"

    def initials(label, i):
        return ["VC", "VM", "VP", "DP"][i % 4]

    members = "\n".join(
        f'''<div class="member">
  <div class="member__avatar">{initials(r, i)}</div>
  <h3>{d}</h3>
  <div class="role">{r}</div>
  <p>Photo &amp; bio coming soon.</p>
</div>''' for i, (r, d) in enumerate(LEADERSHIP)
    )
    depts = "\n".join(
        f'<div class="value"><h3>{t}</h3><p>{d}</p></div>' for t, d in TEAM_DEPARTMENTS
    )
    html = head("Team &mdash; Vicimus", "The people behind Vicimus: performance management, product and engineering, creative services, and BDC — a team built around dealer success.", ap, lang)
    html += header(pp, ap, lang)
    html += f'''
<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <p class="eyebrow">Our team</p>
    <h1 class="h1">The people are the product.</h1>
    <p class="subhero__lead">We cap the number of active clients per team member so every dealer gets real attention. Here's who makes that possible.</p>
    <div class="subhero__actions"><a class="btn btn-yellow" href="{pp}careers.html">Join us &rarr;</a></div>
  </div>
</section>
<div class="crumbs"><div class="crumbs__inner"><a href="{pp}index.html">Home</a><span class="sep">/</span>Team</div></div>

<section class="section">
  <div class="wrap centered">
    <p class="eyebrow">Leadership</p>
    <h2 class="h2">Guiding the mission.</h2>
    <p class="lede">Placeholder profiles &mdash; swap in real names, roles, and photos when ready.</p>
  </div>
  <div class="wrap"><div class="team-grid">{members}</div></div>
</section>

<section class="section section--wash">
  <div class="wrap centered">
    <p class="eyebrow">How we're organized</p>
    <h2 class="h2">Four teams, one standard.</h2>
  </div>
  <div class="wrap"><div class="values">{depts}</div></div>
</section>

<section class="section">
  <div class="wrap centered">
    <p class="eyebrow">Want in?</p>
    <h2 class="h2">We're hiring.</h2>
    <p class="lede">If you care about doing right by dealers, we should talk.</p>
    <div style="margin-top:26px;display:flex;gap:14px;justify-content:center;flex-wrap:wrap">
      <a class="btn btn-red" href="{pp}careers.html">See open roles</a>
      <a class="btn btn-ghost" href="{pp}contact.html">Introduce yourself</a>
    </div>
  </div>
</section>
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


# ----------------------------------------------------------------------
# LAYOUT D — Blog (client-side rendered from assets/posts.json)
# ----------------------------------------------------------------------
def build_blog_index(lang):
    pp = ""
    ap = ap_for(lang, pp)
    page = "updates.html"
    html = head("Updates &mdash; Vicimus", "Product news, company updates, and retention insights from the Vicimus team.", ap, lang)
    html += header(pp, ap, lang)
    html += f'''
<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <p class="eyebrow">Updates</p>
    <h1 class="h1">Product news &amp; retention insights.</h1>
    <p class="subhero__lead">What we're shipping, what we're learning, and what's changing in dealer marketing.</p>
  </div>
</section>
<div class="crumbs"><div class="crumbs__inner"><a href="{pp}index.html">Home</a><span class="sep">/</span>Updates</div></div>

<section class="section">
  <div class="wrap">
    <div id="blog-list" class="blog-grid"></div>
    <div id="blog-empty" class="blog-empty" style="display:none">No posts yet. Add one from the editor.</div>
  </div>
</section>

<script>
(function(){{
  var POSTS_URL = "{ap}assets/posts.json";
  var covers = ["", "t", "r"];
  fetch(POSTS_URL).then(function(r){{return r.json();}}).then(function(data){{
    var posts = (data.posts||[]).slice().sort(function(a,b){{return (b.date||"").localeCompare(a.date||"");}});
    var list = document.getElementById("blog-list");
    if(!posts.length){{ document.getElementById("blog-empty").style.display="block"; return; }}
    list.innerHTML = posts.map(function(p, i){{
      var d = p.date ? new Date(p.date+"T00:00:00").toLocaleDateString("en-US",{{year:"numeric",month:"long",day:"numeric"}}) : "";
      var cover = p.image
        ? '<div class="bcard__cover"><img src="'+p.image+'" alt=""></div>'
        : '<div class="bcard__cover '+covers[i%3]+'"></div>';
      return '<a class="bcard" href="post.html?slug='+encodeURIComponent(p.slug)+'">'
        + cover
        + '<div class="bcard__body">'
        + '<div class="bcard__tag">'+(p.tag||"Update")+'</div>'
        + '<h3>'+p.title+'</h3>'
        + '<p>'+(p.excerpt||"")+'</p>'
        + '<div class="bcard__meta">'+(p.author?'<b>'+p.author+'</b> &middot; ':'')+d+'</div>'
        + '</div></a>';
    }}).join("");
  }}).catch(function(){{
    document.getElementById("blog-empty").style.display="block";
    document.getElementById("blog-empty").textContent="Couldn't load posts. (The blog needs to be served over http — use serve.py locally, or view it live.)";
  }});
}})();
</script>
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


def build_post_page(lang):
    pp = ""
    ap = ap_for(lang, pp)
    page = "post.html"
    html = head("Update &mdash; Vicimus", "A post from the Vicimus team.", ap, lang)
    html += header(pp, ap, lang)
    html += f'''
<section class="section" style="padding-top:52px">
  <div class="wrap">
    <article class="article" id="article">
      <a class="article__back" href="updates.html">&larr; All updates</a>
      <div id="article-body"><p style="color:var(--muted)">Loading&hellip;</p></div>
    </article>
  </div>
</section>

<script>
(function(){{
  var POSTS_URL = "{ap}assets/posts.json";
  function esc(s){{return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}}
  // Minimal markdown: ## h2, ### h3, **bold**, [text](url), - lists, blank-line paragraphs.
  function md(src){{
    var blocks = (src||"").split(/\\n{{2,}}/), out = [];
    blocks.forEach(function(b){{
      b = b.trim(); if(!b) return;
      if(/^### /.test(b)) {{ out.push("<h3>"+inline(b.slice(4))+"</h3>"); return; }}
      if(/^## /.test(b))  {{ out.push("<h2>"+inline(b.slice(3))+"</h2>"); return; }}
      if(/^(- |\\* )/.test(b)){{
        var items = b.split(/\\n/).map(function(l){{return l.replace(/^(- |\\* )/,"").trim();}}).filter(Boolean);
        out.push("<ul>"+items.map(function(i){{return "<li>"+inline(i)+"</li>";}}).join("")+"</ul>"); return;
      }}
      out.push("<p>"+inline(b.replace(/\\n/g,"<br>"))+"</p>");
    }});
    return out.join("\\n");
  }}
  function inline(s){{
    s = esc(s);
    s = s.replace(/\\*\\*([^*]+)\\*\\*/g,"<strong>$1</strong>");
    s = s.replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g,'<a href="$2">$1</a>');
    return s;
  }}
  var slug = new URLSearchParams(location.search).get("slug");
  fetch(POSTS_URL).then(function(r){{return r.json();}}).then(function(data){{
    var post = (data.posts||[]).filter(function(p){{return p.slug===slug;}})[0];
    var el = document.getElementById("article-body");
    if(!post){{ el.innerHTML = '<h1 class="h2">Post not found</h1><p style="color:var(--muted)">This update may have moved. <a href="updates.html" style="color:var(--blue)">Back to all updates</a>.</p>'; return; }}
    document.title = post.title + " — Vicimus";
    var d = post.date ? new Date(post.date+"T00:00:00").toLocaleDateString("en-US",{{year:"numeric",month:"long",day:"numeric"}}) : "";
    var cover = post.image ? '<div class="article__cover"><img src="'+post.image+'" alt=""></div>' : '<div class="article__cover"></div>';
    el.innerHTML =
      '<div class="article__meta"><span class="tag">'+(post.tag||"Update")+'</span>'+(post.author?esc(post.author)+" &middot; ":"")+d+'</div>'
      + '<h1 class="h1" style="color:var(--ink);font-size:clamp(1.8rem,3vw,2.6rem);margin-bottom:6px">'+esc(post.title)+'</h1>'
      + cover
      + '<div class="article__body">'+md(post.body||post.excerpt||"")+'</div>';
  }}).catch(function(){{
    document.getElementById("article-body").innerHTML = '<p style="color:var(--muted)">Couldn\\'t load this post.</p>';
  }});
}})();
</script>
'''
    html += footer(pp, ap, lang, page)
    return write(lang, page, html)


def build_sb_catalog():
    """Emit assets/js/sb-catalog.js — the block catalog the Solutions Builder
    tray reads (products, solutions, markets, with ROI hints). Generated from
    data.py so it stays in sync with the rest of the site."""
    import json as _json

    def clean(s):
        return (s or "").replace("&mdash;", "—").replace("&amp;", "&").replace("&rarr;", "→")

    products = {}
    for p in PRODUCTS:
        products[p["slug"]] = {
            "name": p["name"],
            "blurb": clean(p["hero_p"])[:170],
            "family": p["family"],
            "path": f"products/{p['slug']}.html",
            "roi": SB_ROI.get(p["slug"], {"kind": "qual", "metric": ""}),
        }
    solutions = {
        s["slug"]: {"name": s["name"], "blurb": clean(s["hero_p"])[:170],
                    "path": f"solutions/{s['slug']}.html"}
        for s in SOLUTIONS
    }
    markets = {
        m["slug"]: {"name": m["name"], "blurb": clean(m["hero_p"])[:170],
                    "path": f"markets/{m['slug']}.html"}
        for m in MARKETS
    }
    catalog = {"products": products, "solutions": solutions, "markets": markets}
    js = "/* Auto-generated by build.py — do not edit by hand. */\n"
    js += "window.SB_CATALOG = " + _json.dumps(catalog, ensure_ascii=False, indent=2) + ";\n"
    path = os.path.join(OUT, "assets", "js", "sb-catalog.js")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(js)
    return path


def build_home_translations():
    src = os.path.join(OUT, "index.html")
    if not os.path.exists(src):
        print("  ! index.html not found; skipping home translations")
        return []
    english = open(src, encoding="utf-8").read()
    out = []
    for lang in ("es", "fr"):
        h = english
        # 1) assets sit one level up from /es|fr/  ->  ="assets/  becomes  ="../assets/
        h = h.replace('="assets/', '="../assets/')
        # 2) html language attribute
        h = re.sub(r'<html lang="[^"]*">', f'<html lang="{lang}">', h, count=1)
        # 3) language-picker wiring (SITE object): root one level up, set lang
        h = h.replace('window.SITE={root:"",page:"index.html",lang:"en"}',
                      f'window.SITE={{root:"../",page:"index.html",lang:"{lang}"}}')
        write(lang, "index.html", h)
        out.append(os.path.join(OUT, LANG_DIR[lang], "index.html"))
    return out


def main():
    built = []
    for lang in LANGS:
        for p in PRODUCTS:
            built.append(build_product(p, lang))
        built.append(build_products_index(lang))
        for sol in SOLUTIONS:
            built.append(build_audience_page(sol, "solutions", lang))
        for mkt in MARKETS:
            built.append(build_audience_page(mkt, "markets", lang))
        built.append(build_about(lang))
        built.append(build_team(lang))
        built.append(build_why(lang))
        built.append(build_contact(lang))
        built.append(build_book_demo(lang))
        built.append(build_careers(lang))
        built.append(build_blog_index(lang))
        built.append(build_post_page(lang))
    built += build_home_translations()
    build_sb_catalog()
    print("  wrote assets/js/sb-catalog.js")

    by_lang = {}
    for b in built:
        rel = os.path.relpath(b, OUT)
        top = rel.split(os.sep)[0]
        key = top if top in ("es", "fr") else "en"
        by_lang.setdefault(key, 0)
        by_lang[key] += 1
    print("Generated pages:")
    for k in ("en", "es", "fr"):
        print(f"  {k}: {by_lang.get(k,0)}")
    print(f"  total: {len(built)}")
    print("\nEnglish text is in place across all three trees. Run translate.py")
    print("with a Google Cloud key to translate the /es and /fr trees.")


if __name__ == "__main__":
    main()
