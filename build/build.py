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
    "pie":              {"kind": "qual",                                                                   "metric": "Automated insight on one dataset"},
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
      <div class="jsim-main">
        <div class="jsim-cards" id="jsim-cards">{cards}</div>
        <div class="jsim-controls">
          <button class="jsim-btn" id="jsim-prev" aria-label="Previous stage">&larr;</button>
          <div class="jsim-play" id="jsim-play"><span class="jsim-play-ico"></span> <span id="jsim-play-lbl">Playing</span></div>
          <button class="jsim-btn" id="jsim-next" aria-label="Next stage">&rarr;</button>
        </div>
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


def pie_dashboard_demo():
    """"One question. One answer." — an interactive GM drill-down for Pie.
    Concern -> metrics -> why (advisor breakdown) -> generated insight."""
    return '''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">See it work</p>
    <h2 class="h2" style="margin-bottom:8px">One question. One answer.</h2>
    <p class="lede">Stop digging through reports. Step into the GM's chair &mdash; pick a concern and watch Pie trace it from symptom to source to dollar impact.</p>
  </div>
  <div class="wrap">
    <div class="pie" id="pie">

      <!-- STEP 1 -->
      <div class="pie-panel is-active" data-s="0">
        <div class="pie-q">What's your biggest concern today?</div>
        <div class="pie-concerns">
          <button class="pie-concern" data-c="service"><span class="pie-emoji">&#128295;</span> Service</button>
          <button class="pie-concern" data-c="sales"><span class="pie-emoji">&#128200;</span> Sales</button>
          <button class="pie-concern" data-c="inventory"><span class="pie-emoji">&#128663;</span> Inventory</button>
          <button class="pie-concern" data-c="profit"><span class="pie-emoji">&#128176;</span> Profitability</button>
          <button class="pie-concern" data-c="multi"><span class="pie-emoji">&#127970;</span> Multi-Store</button>
        </div>
        <p class="pie-note">Try <b>Service</b> &mdash; the others are along for the ride in this demo.</p>
      </div>

      <!-- STEP 2 -->
      <div class="pie-panel" data-s="1">
        <div class="pie-crumb"><button class="pie-back" data-go="0">&larr; Concern</button> <span>Service performance</span></div>
        <div class="pie-kpis">
          <div class="pie-kpi pie-up"><div class="pie-kpi-l">Service Revenue</div><div class="pie-kpi-v">&#8593; 12%</div></div>
          <div class="pie-kpi pie-down"><div class="pie-kpi-l">Customer-Pay RO</div><div class="pie-kpi-v">&#8595; 4%</div></div>
          <div class="pie-kpi pie-up"><div class="pie-kpi-l">Appointments</div><div class="pie-kpi-v">&#8593; 8%</div></div>
        </div>
        <div class="pie-flag">
          <span class="pie-flag-ico">!</span>
          <div><b>Pie flagged a concern:</b> revenue is up, but Customer-Pay RO is trending down &mdash; a signal that volume is masking a problem.</div>
        </div>
        <button class="btn btn-blue pie-next" data-go="2">Why is this happening? &rarr;</button>
      </div>

      <!-- STEP 3 -->
      <div class="pie-panel" data-s="2">
        <div class="pie-crumb"><button class="pie-back" data-go="1">&larr; Service metrics</button> <span>Root-cause analysis</span></div>
        <div class="pie-cols">
          <div class="pie-block">
            <div class="pie-block-t">Advisor performance &middot; CPRO</div>
            <div class="pie-bar-row"><span class="pie-bar-n">Advisor A</span><span class="pie-bar"><span class="pie-bar-fill up" style="width:88%"></span></span><span class="pie-bar-v up">+18%</span></div>
            <div class="pie-bar-row"><span class="pie-bar-n">Advisor B</span><span class="pie-bar"><span class="pie-bar-fill down" style="width:52%"></span></span><span class="pie-bar-v down">-11%</span></div>
            <div class="pie-bar-row"><span class="pie-bar-n">Advisor C</span><span class="pie-bar"><span class="pie-bar-fill down" style="width:44%"></span></span><span class="pie-bar-v down">-14%</span></div>
          </div>
          <div class="pie-block">
            <div class="pie-block-t">Appointment show rate</div>
            <div class="pie-bar-row"><span class="pie-bar-n">Advisor A</span><span class="pie-bar"><span class="pie-bar-fill up" style="width:92%"></span></span><span class="pie-bar-v">92%</span></div>
            <div class="pie-bar-row"><span class="pie-bar-n">Advisor B</span><span class="pie-bar"><span class="pie-bar-fill down" style="width:81%"></span></span><span class="pie-bar-v">81%</span></div>
            <div class="pie-bar-row"><span class="pie-bar-n">Advisor C</span><span class="pie-bar"><span class="pie-bar-fill down" style="width:76%"></span></span><span class="pie-bar-v">76%</span></div>
          </div>
        </div>
        <button class="btn btn-blue pie-next" data-go="3">Generate the insight &rarr;</button>
      </div>

      <!-- STEP 4 -->
      <div class="pie-panel" data-s="3">
        <div class="pie-insight">
          <div class="pie-insight-badge">&#10022; Insight generated</div>
          <div class="pie-insight-h">Revenue-loss source identified</div>
          <p class="pie-insight-p">Two advisors account for <b>79%</b> of the Customer-Pay RO decline &mdash; driven by lower appointment show rates and reduced per-RO value.</p>
          <div class="pie-impact">
            <div class="pie-impact-l">Estimated monthly impact</div>
            <div class="pie-impact-v" data-num="24700">$0</div>
          </div>
          <p class="pie-insight-sub">Find issues before they become problems.</p>
        </div>
        <button class="btn btn-yellow pie-restart">&#8635; Ask another question</button>
      </div>

    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById('pie'); if(!root) return;
    var panels=[].slice.call(root.querySelectorAll('.pie-panel'));
    function show(i){
      panels.forEach(function(p){ p.classList.toggle('is-active', parseInt(p.getAttribute('data-s'))===i); });
      if(i===2) animateBars();
      if(i===3) countImpact();
    }
    function animateBars(){
      root.querySelectorAll('.pie-bar-fill').forEach(function(f){
        var w=f.style.width; f.style.width='0'; requestAnimationFrame(function(){ setTimeout(function(){ f.style.width=w; },40); });
      });
    }
    function countImpact(){
      var el=root.querySelector('.pie-impact-v'); if(!el) return;
      var target=parseInt(el.getAttribute('data-num')), t0=performance.now();
      function tick(now){ var k=Math.min(1,(now-t0)/1100); var v=target*(0.5-Math.cos(k*Math.PI)/2);
        el.textContent='$'+Math.round(v).toLocaleString(); if(k<1) requestAnimationFrame(tick); }
      requestAnimationFrame(tick);
    }
    root.querySelectorAll('.pie-concern').forEach(function(b){ b.addEventListener('click',function(){ show(1); }); });
    root.querySelectorAll('.pie-next,.pie-back').forEach(function(b){ b.addEventListener('click',function(){ show(parseInt(b.getAttribute('data-go'))); }); });
    root.querySelector('.pie-restart').addEventListener('click',function(){ show(0); });
  })();
  </script>
</section>'''


def pie_comparison():
    """Pie vs AutoAlert vs Generic BI — unified card comparison (shared matrix)."""
    rows = [
        ("Sales analytics", ("yes",), ("partial",), ("yes",)),
        ("Service analytics", ("yes",), ("partial",), ("yes",)),
        ("Parts analytics", ("yes",), ("no",), ("partial",)),
        ("Inventory analytics", ("yes",), ("partial",), ("yes",)),
        ("Financial reporting", ("yes",), ("no",), ("partial",)),
        ("Single-dealership view", ("yes",), ("yes",), ("yes",)),
        ("Multi-store reporting", ("yes",), ("partial",), ("yes",)),
        ("Executive KPI dashboard", ("yes",), ("partial",), ("no",)),
        ("Department scorecards", ("yes",), ("no",), ("no",)),
        ("Trend analysis", ("yes",), ("partial",), ("yes",)),
        ("Drill-down reporting", ("yes",), ("partial",), ("yes",)),
        ("Automated insights", ("yes",), ("no",), ("no",)),
        ("Dealer-specific metrics", ("yes",), ("yes",), ("no",)),
        ("One platform for the entire store", ("yes",), ("no",), ("no",)),
        ("Designed for dealers", ("yes",), ("yes",), ("no",)),
    ]

    def col(idx):
        return [(row[idx + 1][0], row[0], row[idx + 1][1] if len(row[idx + 1]) > 1 else "") for row in rows]

    cards = [
        {"name": "Pie", "badge": "Advanced intelligence", "highlight": True, "items": col(0)},
        {"name": "AutoAlert", "badge": "Equity mining", "items": col(1)},
        {"name": "Generic BI", "badge": "Tableau / Power BI", "items": col(2)},
    ]
    disclaimer = ("Comparison reflects Vicimus's understanding of publicly available information about AutoAlert "
                  "and general-purpose BI tools (e.g. Tableau, Power BI) as of 2026, prepared in good faith. "
                  "\u201cGeneric BI\u201d denotes general-purpose business-intelligence platforms not purpose-built for "
                  "dealerships. Capabilities change and vary by plan and configuration; product and company names "
                  "are trademarks of their respective owners, used for identification only. Verify current "
                  "capabilities with each vendor.")
    return comparison_section(
        "How it stacks up",
        "Why dealerships choose Pie.",
        "General BI tools can chart anything but understand nothing about a dealership. Pie is built for the "
        "store &mdash; every department, every metric, with the why built in.",
        cards, disclaimer,
    )


def comparison_section(eyebrow, headline, lede, cards, disclaimer):
    """Unified feature-comparison used across all product pages, so every
    comparison shares one design. Renders N side-by-side cards (first is the
    highlighted Bumper card). Each card: name, optional badge, and a list of
    (mark, label[, note]) items where mark is 'yes' | 'partial' | 'no'.
    For a head-to-head matrix, pass every card the same labels in the same
    order (rows line up across cards); for highlight lists, pass each its own."""
    SYM = {
        "yes": "&#10003;",
        "no": "&times;",
        "partial": '<svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 0 1 0 18Z"/><circle cx="12" cy="12" r="9"/></svg>',
    }
    CLS = {"yes": "cmp-i-yes", "no": "cmp-i-no", "partial": "cmp-i-part"}

    def item(it):
        mark, label = it[0], it[1]
        note = it[2] if len(it) > 2 else ""
        note_html = f'<span class="cmp-note">{note}</span>' if note else ""
        return (f'<li class="{CLS[mark]}"><span class="cmp-i-mark">{SYM[mark]}</span>'
                f'<span class="cmp-i-txt">{label}{note_html}</span></li>')

    cards_html = ""
    for c in cards:
        hl = " icmp-card--hl" if c.get("highlight") else ""
        badge = ""
        if c.get("badge"):
            bcls = "icmp-badge" + ("" if c.get("highlight") else " icmp-badge--muted")
            badge = f'<div class="{bcls}">{c["badge"]}</div>'
        items = "".join(item(it) for it in c["items"])
        cards_html += (f'<div class="icmp-card{hl}"><div class="icmp-name">{c["name"]}</div>'
                       f'{badge}<ul class="cmp-ilist">{items}</ul></div>')

    return f'''<section class="section section--wash">
  <div class="wrap centered">
    <p class="eyebrow">{eyebrow}</p>
    <h2 class="h2" style="margin-bottom:8px">{headline}</h2>
    <p class="lede">{lede}</p>
  </div>
  <div class="wrap">
    <div class="icmp icmp--{len(cards)}">{cards_html}</div>
    <p class="cmp-disc">{disclaimer}</p>
  </div>
</section>'''


def retention_comparison():
    """Credible capability comparison, rendered in the unified card design.
    All three cards share the same 16 capabilities (rows line up), each with
    that competitor's mark, so the head-to-head matrix detail is preserved."""
    # (capability, bumper, autoalert, mastermind); each cell = (mark,) or (mark, note)
    rows = [
        ("Intent mining / purchase signals", ("yes",), ("yes",), ("yes",)),
        ("Sales, service &amp; unsold prospect activation", ("yes",), ("partial",), ("partial",)),
        ("Automated lifecycle campaigns", ("yes",), ("partial",), ("yes",)),
        ("Email marketing", ("yes",), ("yes",), ("yes",)),
        ("SMS marketing", ("yes",), ("yes",), ("partial",)),
        ("Ringless voicemail", ("yes",), ("no",), ("no",)),
        ("Direct mail campaigns", ("yes",), ("yes",), ("yes",)),
        ("Customer preferred-channel learning", ("yes",), ("no",), ("no",)),
        ("Behavioral tracking across campaigns", ("yes",), ("yes",), ("yes",)),
        ("Personalized messaging at scale", ("yes",), ("yes",), ("yes",)),
        ("Service retention campaigns", ("yes",), ("yes",), ("yes",)),
        ("Dedicated performance manager", ("yes", "Included"), ("partial", "Varies"), ("yes",)),
        ("Fully managed campaign deployment", ("yes",), ("no",), ("partial",)),
        ("Unlimited campaign creation", ("yes",), ("no",), ("no",)),
        ("Transparent campaign reporting", ("yes",), ("yes",), ("yes",)),
        ("Sales, service, parts &amp; F&amp;I in one platform", ("yes",), ("partial",), ("partial",)),
    ]

    def col(idx):
        out = []
        for row in rows:
            cap = row[0]
            cell = row[idx + 1]
            note = cell[1] if len(cell) > 1 else ""
            out.append((cell[0], cap, note))
        return out

    cards = [
        {"name": "Bumper Retention", "badge": "Connected lifecycle", "highlight": True, "items": col(0)},
        {"name": "AutoAlert", "badge": "Equity mining", "items": col(1)},
        {"name": "automotiveMastermind", "badge": "Predictive analytics", "items": col(2)},
    ]
    disclaimer = ("Comparison reflects Vicimus's understanding of publicly available information about "
                  "AutoAlert and automotiveMastermind as of 2026, prepared in good faith. Competitor "
                  "offerings change and may vary by plan, region, and configuration; product and company "
                  "names are trademarks of their respective owners, used here for identification only. "
                  "Verify current capabilities with each vendor.")
    return comparison_section(
        "How it stacks up",
        "Bumper Retention vs. the field.",
        "Where dealer retention actually gets won &mdash; identifying opportunities, activating customers, "
        "communicating across every channel, and executing it for you.",
        cards, disclaimer,
    )


def inventory_campaign_builder():
    """"Launch a campaign in 30 seconds" — an in-depth, interactive 4-step
    builder. Choices in each step flow through to the final results.
    Bumper Inventory Ads only. Inventory -> Audience -> Ads -> Results."""
    return '''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">See it work</p>
    <h2 class="h2" style="margin-bottom:8px">Launch a campaign in 30 seconds.</h2>
    <p class="lede">Filter your inventory, target the right shoppers, and Bumper builds and optimizes the ads across Facebook, Instagram, and Google &mdash; then reports every result back.</p>
  </div>
  <div class="wrap">
    <div class="cb" id="cb">
      <div class="cb-steps">
        <button class="cb-step is-active" data-s="0"><span class="cb-step-n">1</span> Select inventory</button>
        <button class="cb-step" data-s="1"><span class="cb-step-n">2</span> Choose audience</button>
        <button class="cb-step" data-s="2"><span class="cb-step-n">3</span> Ads build</button>
        <button class="cb-step" data-s="3"><span class="cb-step-n">4</span> Results</button>
      </div>
      <div class="cb-stage">

        <!-- STEP 1 -->
        <div class="cb-panel is-active" data-s="0">
          <div class="cb-cols">
            <div>
              <p class="cb-hint" style="text-align:left;margin-bottom:14px">Filter by segment &mdash; Bumper syncs matching vehicles from your DMS in real time.</p>
              <div class="cb-filters">
                <button class="cb-filter is-on" data-seg="all">All inventory</button>
                <button class="cb-filter" data-seg="truck">Trucks</button>
                <button class="cb-filter" data-seg="suv">SUVs</button>
                <button class="cb-filter" data-seg="car">Cars</button>
              </div>
              <div class="cb-inv" id="cb-inv"></div>
            </div>
            <div class="cb-side">
              <div class="cb-side-lbl">Matched inventory</div>
              <div class="cb-counter" id="cb-veh">0</div>
              <div class="cb-side-sub">vehicles ready to advertise</div>
              <div class="cb-side-meta"><span>Avg. age</span><b id="cb-age">— days</b></div>
              <div class="cb-side-meta"><span>Avg. price</span><b id="cb-price">—</b></div>
              <button class="btn btn-blue cb-next" data-go="1">Choose audience &rarr;</button>
            </div>
          </div>
        </div>

        <!-- STEP 2 -->
        <div class="cb-panel" data-s="1">
          <div class="cb-cols">
            <div>
              <p class="cb-hint" style="text-align:left;margin-bottom:14px">Layer in first-party and in-market audiences &mdash; each shows estimated reach and match quality.</p>
              <div class="cb-auds">
                <button class="cb-aud" data-size="12480" data-q="94">Past Customers <span class="cb-aud-meta">12,480 &middot; <b>94% match</b></span></button>
                <button class="cb-aud" data-size="9260" data-q="88">Service Customers <span class="cb-aud-meta">9,260 &middot; <b>88% match</b></span></button>
                <button class="cb-aud" data-size="4310" data-q="91">Lease Maturity <span class="cb-aud-meta">4,310 &middot; <b>91% match</b></span></button>
                <button class="cb-aud" data-size="11890" data-q="72">In-Market Shoppers <span class="cb-aud-meta">11,890 &middot; <b>72% match</b></span></button>
                <button class="cb-aud" data-size="4621" data-q="83">Equity Positive <span class="cb-aud-meta">4,621 &middot; <b>83% match</b></span></button>
              </div>
            </div>
            <div class="cb-side">
              <div class="cb-side-lbl">Total reach</div>
              <div class="cb-counter" id="cb-aud">0</div>
              <div class="cb-side-sub">de-duplicated, matched shoppers</div>
              <div class="cb-side-meta"><span>Blended match</span><b id="cb-match">—</b></div>
              <button class="btn btn-blue cb-next" data-go="2">Build the ads &rarr;</button>
            </div>
          </div>
        </div>

        <!-- STEP 3 -->
        <div class="cb-panel" data-s="2">
          <p class="cb-hint">Bumper generates platform-ready creative for every vehicle and splits budget across the channels you run.</p>
          <div class="cb-plats">
            <button class="cb-plat is-on" data-plat="fb">Facebook</button>
            <button class="cb-plat is-on" data-plat="ig">Instagram</button>
            <button class="cb-plat is-on" data-plat="gg">Google</button>
          </div>
          <div class="cb-budget"><div class="cb-budget-bar" id="cb-budget"></div></div>
          <div class="cb-ads" id="cb-ads"></div>
          <button class="btn btn-blue cb-next" data-go="3" style="margin-top:22px">See the results &rarr;</button>
        </div>

        <!-- STEP 4 -->
        <div class="cb-panel" data-s="3">
          <p class="cb-hint">Real-time performance, tracked as a funnel &mdash; from impression to individual lead.</p>
          <div class="cb-funnel" id="cb-funnel">
            <div class="cb-fstage"><div class="cb-fbar" style="--w:100%"><span class="cb-fbar-fill"></span></div><div class="cb-fmeta"><b class="cb-fn" data-num="487412">0</b><span>Reach</span></div></div>
            <div class="cb-fconv" data-conv="1.3">1.3% CTR</div>
            <div class="cb-fstage"><div class="cb-fbar" style="--w:64%"><span class="cb-fbar-fill"></span></div><div class="cb-fmeta"><b class="cb-fn" data-num="6423">0</b><span>Clicks</span></div></div>
            <div class="cb-fconv" data-conv="176">1.76 pages/click</div>
            <div class="cb-fstage"><div class="cb-fbar" style="--w:44%"><span class="cb-fbar-fill"></span></div><div class="cb-fmeta"><b class="cb-fn" data-num="11329">0</b><span>VDP Views</span></div></div>
            <div class="cb-fconv" data-conv="1.65">1.65% to lead</div>
            <div class="cb-fstage"><div class="cb-fbar" style="--w:22%"><span class="cb-fbar-fill cb-fbar-lead"></span></div><div class="cb-fmeta"><b class="cb-fn" data-num="187">0</b><span>Leads</span></div></div>
          </div>
          <div class="cb-kpis">
            <div class="cb-kpi"><div class="cb-kpi-v" id="cb-cpl">$0</div><div class="cb-kpi-l">Cost per lead</div></div>
            <div class="cb-kpi"><div class="cb-kpi-v" id="cb-spend">$0</div><div class="cb-kpi-l">Ad spend</div></div>
            <div class="cb-kpi"><div class="cb-kpi-v" id="cb-roas">0x</div><div class="cb-kpi-l">Est. ROAS</div></div>
          </div>
          <button class="btn btn-yellow cb-restart">&#8635; Run it again</button>
        </div>

      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById('cb'); if(!root) return;
    var steps=[].slice.call(root.querySelectorAll('.cb-step'));
    var panels=[].slice.call(root.querySelectorAll('.cb-panel'));
    var cur=0, started=false;

    // ---- inventory data ----
    var INV={
      truck:[{n:"2024 Ford F-150 XLT",v:38,age:22,p:54995},{n:"2023 RAM 1500 Big Horn",v:19,age:41,p:47500},{n:"2024 Chevy Silverado LT",v:24,age:17,p:51200}],
      suv:[{n:"2023 Chevy Tahoe LT",v:24,age:35,p:58900},{n:"2024 Toyota RAV4 XLE",v:34,age:12,p:33400},{n:"2024 Honda CR-V EX",v:21,age:28,p:34950}],
      car:[{n:"2025 Honda Civic Sport",v:31,age:9,p:28600},{n:"2024 Toyota Camry SE",v:26,age:19,p:30100}]
    };
    function seg(sel){ if(sel==="all") return INV.truck.concat(INV.suv,INV.car); return INV[sel]||[]; }
    var curSeg="all";
    function money(n){ return "$"+Math.round(n).toLocaleString(); }
    function animCount(el,target,dur){ dur=dur||700; var t0=performance.now();
      (function tick(now){ var k=Math.min(1,(now-t0)/dur); var v=target*(0.5-Math.cos(k*Math.PI)/2);
        el.textContent=Math.round(v).toLocaleString(); if(k<1) requestAnimationFrame(tick); })(performance.now()); }

    // ---- STEP 1: inventory ----
    function renderInv(){
      var list=seg(curSeg), box=document.getElementById("cb-inv");
      box.innerHTML="";
      var total=0, ageSum=0, priceSum=0, d=0;
      list.forEach(function(r){
        total+=r.v; ageSum+=r.age*r.v; priceSum+=r.p*r.v;
        var row=document.createElement("div"); row.className="cb-inv-row";
        row.innerHTML=r.n+" <span class=\'cb-inv-v\'>"+r.v+" units</span>";
        box.appendChild(row);
        setTimeout(function(){ row.classList.add("is-sel"); }, d+=90);
      });
      animCount(document.getElementById("cb-veh"),total,500);
      document.getElementById("cb-age").textContent=(total?Math.round(ageSum/total):0)+" days";
      document.getElementById("cb-price").textContent=total?money(priceSum/total):"—";
    }
    root.querySelectorAll(".cb-filter").forEach(function(f){
      f.addEventListener("click",function(){
        root.querySelectorAll(".cb-filter").forEach(function(x){x.classList.remove("is-on");});
        f.classList.add("is-on"); curSeg=f.getAttribute("data-seg"); renderInv();
      });
    });

    // ---- STEP 2: audiences ----
    var audTotal=0, qAccum=0, qCount=0;
    root.querySelectorAll(".cb-aud").forEach(function(btn){
      btn.addEventListener("click",function(){
        var sz=parseInt(btn.getAttribute("data-size")), q=parseInt(btn.getAttribute("data-q"));
        if(btn.classList.toggle("is-on")){ audTotal+=sz; qAccum+=q; qCount++; }
        else { audTotal-=sz; qAccum-=q; qCount--; }
        animCount(document.getElementById("cb-aud"),audTotal,500);
        document.getElementById("cb-match").textContent=qCount?Math.round(qAccum/qCount)+"% avg":"—";
      });
    });

    // ---- STEP 3: platforms + budget + ads ----
    var PLAT={fb:{label:"Facebook",cls:"cb-ad--fb"},ig:{label:"Instagram",cls:"cb-ad--ig"},gg:{label:"Google Vehicle Ad",cls:"cb-ad--gg"}};
    function activePlats(){ return [].slice.call(root.querySelectorAll(".cb-plat.is-on")).map(function(p){return p.getAttribute("data-plat");}); }
    function renderBudget(){
      var plats=activePlats(), bar=document.getElementById("cb-budget"); bar.innerHTML="";
      if(!plats.length) return;
      var share=(100/plats.length);
      plats.forEach(function(p){
        var seg=document.createElement("span"); seg.className="cb-budget-seg cb-bud-"+p;
        seg.style.width=share+"%"; seg.textContent=PLAT[p].label+" "+Math.round(share)+"%";
        bar.appendChild(seg);
      });
    }
    function buildAds(){
      var box=document.getElementById("cb-ads"); box.innerHTML="";
      var list=seg(curSeg).slice(0,2), plats=activePlats(), d=0, made=0;
      list.forEach(function(veh){
        plats.forEach(function(pl){
          if(made>=3) return; made++;
          var ad=document.createElement("div"); ad.className="cb-ad "+PLAT[pl].cls;
          var priceMo=Math.round(veh.p/90/10)*10;
          ad.innerHTML="<div class=\'cb-ad-tag\'>"+PLAT[pl].label+"</div>"+
            "<div class=\'cb-ad-img\'><span class=\'cb-ico-car\'></span></div>"+
            "<div class=\'cb-ad-body\'><div class=\'cb-ad-t\'>"+veh.n+"</div>"+
            (pl==="gg"?"<div class=\'cb-ad-dealer\'>Lakeview Motors &middot; Dallas, TX</div><div class=\'cb-ad-price\'>"+money(veh.p)+"</div>":
              "<div class=\'cb-ad-p\'>$"+priceMo+"/mo</div><div class=\'cb-ad-cta\'>Shop Now</div>")+"</div>";
          box.appendChild(ad);
          setTimeout(function(){ ad.classList.add("is-in"); }, d+=260);
        });
      });
    }
    root.querySelectorAll(".cb-plat").forEach(function(p){
      p.addEventListener("click",function(){
        if(activePlats().length===1 && p.classList.contains("is-on")) return; // keep at least one
        p.classList.toggle("is-on"); renderBudget(); buildAds();
      });
    });

    // ---- STEP 4: funnel + KPIs ----
    function rollResults(){
      root.querySelectorAll(".cb-fn").forEach(function(el,i){
        setTimeout(function(){ animCount(el,parseInt(el.getAttribute("data-num")),1100); }, i*160);
      });
      root.querySelectorAll(".cb-fbar-fill").forEach(function(f){ f.style.width="0"; requestAnimationFrame(function(){ setTimeout(function(){ f.style.width="100%"; },60); }); });
      var spend=8940, leads=187;
      setTimeout(function(){
        animCountMoney(document.getElementById("cb-cpl"), spend/leads, 900, true);
        animCountMoney(document.getElementById("cb-spend"), spend, 900);
        var roas=document.getElementById("cb-roas"), t0=performance.now();
        (function tick(now){ var k=Math.min(1,(now-t0)/900); roas.textContent=(6.2*(0.5-Math.cos(k*Math.PI)/2)).toFixed(1)+"x"; if(k<1)requestAnimationFrame(tick); })(performance.now());
      }, 400);
    }
    function animCountMoney(el,target,dur,cents){ var t0=performance.now();
      (function tick(now){ var k=Math.min(1,(now-t0)/dur); var v=target*(0.5-Math.cos(k*Math.PI)/2);
        el.textContent="$"+(cents?v.toFixed(0):Math.round(v).toLocaleString()); if(k<1)requestAnimationFrame(tick); })(performance.now()); }

    function show(i){
      cur=i;
      steps.forEach(function(s,idx){ s.classList.toggle("is-active",idx===i); s.classList.toggle("is-done",idx<i); });
      panels.forEach(function(p,idx){ p.classList.toggle("is-active",idx===i); });
      if(i===0) renderInv();
      if(i===2){ renderBudget(); buildAds(); }
      if(i===3) rollResults();
    }
    steps.forEach(function(s){ s.addEventListener("click",function(){ show(parseInt(s.getAttribute("data-s"))); }); });
    root.querySelectorAll(".cb-next").forEach(function(b){ b.addEventListener("click",function(){ show(parseInt(b.getAttribute("data-go"))); }); });
    root.querySelector(".cb-restart").addEventListener("click",function(){
      curSeg="all"; audTotal=0; qAccum=0; qCount=0;
      root.querySelectorAll(".cb-filter").forEach(function(x){x.classList.toggle("is-on",x.getAttribute("data-seg")==="all");});
      root.querySelectorAll(".cb-aud").forEach(function(a){a.classList.remove("is-on");});
      root.querySelectorAll(".cb-plat").forEach(function(p){p.classList.add("is-on");});
      document.getElementById("cb-aud").textContent="0"; document.getElementById("cb-match").textContent="—";
      show(0);
    });
    if("IntersectionObserver" in window){
      new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting && !started){ started=true; renderInv(); } }); },{threshold:.35}).observe(root);
    } else { renderInv(); }
  })();
  </script>
</section>'''


def inventory_comparison():
    """Competitor comparison in the unified card design. Each card carries its
    own capability highlights (not a shared matrix)."""
    cards = [
        {"name": "Bumper Inventory Ads", "badge": "Connected lifecycle", "highlight": True, "items": [
            ("yes", "Inventory advertising"),
            ("yes", "Facebook &amp; Google campaigns"),
            ("yes", "Retention audiences"),
            ("yes", "Intent-mining integration"),
            ("yes", "Customer lifecycle activation"),
            ("yes", "Dedicated performance manager"),
        ]},
        {"name": "Dealer.com", "badge": "Website ecosystem", "items": [
            ("yes", "Large website + digital ecosystem"),
            ("yes", "Inventory advertising"),
            ("no", "Customer intent mining"),
            ("no", "Retention automation"),
            ("no", "Connected customer lifecycle marketing"),
        ]},
        {"name": "PureCars", "badge": "Advertising platform", "items": [
            ("yes", "Advertising platform"),
            ("yes", "Conquest campaigns"),
            ("no", "Ringless voicemail"),
            ("no", "Lifecycle campaigns"),
            ("no", "Customer intent mining"),
        ]},
    ]
    disclaimer = ("Comparison reflects Vicimus's understanding of publicly available information about "
                  "Dealer.com and PureCars as of 2026, prepared in good faith. Competitor offerings change "
                  "and may vary by plan, region, and configuration; product and company names are "
                  "trademarks of their respective owners, used here for identification only. Verify current "
                  "capabilities with each vendor.")
    return comparison_section(
        "How it stacks up",
        "More than an ad platform.",
        "Most inventory advertising stops at the click. Bumper connects the same ad spend to intent mining, "
        "retention audiences, and the full customer lifecycle.",
        cards, disclaimer,
    )


def retention_hero_animation():
    """Hero micro-animation: a customer about to churn, re-engaged and retained,
    with lifetime value ticking up. (Distinct from the page's lifecycle demo.)"""
    return '''<div class="rhero" id="rhero">
  <div class="rhero-status">
    <div class="rhero-avatar">&#128100;</div>
    <div class="rhero-stat">
      <div class="rhero-state rhero-state--risk" id="rhero-state">At risk of leaving</div>
      <div class="rhero-sub" id="rhero-sub">No service visit in 14 months</div>
    </div>
    <div class="rhero-pulse" id="rhero-pulse"></div>
  </div>
  <div class="rhero-flow">
    <div class="rhero-chip" data-step="1">Intent detected</div>
    <div class="rhero-chip" data-step="2">Smart outreach sent</div>
    <div class="rhero-chip" data-step="3">Customer re-engaged</div>
  </div>
  <div class="rhero-ltv">
    <div class="rhero-ltv-l">Customer lifetime value</div>
    <div class="rhero-ltv-v" id="rhero-ltv">$0</div>
  </div>
  <script>
  (function(){
    var root=document.getElementById('rhero'); if(!root) return;
    var chips=[].slice.call(root.querySelectorAll('.rhero-chip'));
    var state=document.getElementById('rhero-state'), sub=document.getElementById('rhero-sub');
    var ltvEl=document.getElementById('rhero-ltv'), pulse=document.getElementById('rhero-pulse');
    var seen=false;
    function count(to,cb){ var t0=performance.now(); (function tick(now){ var k=Math.min(1,(now-t0)/900);
      ltvEl.textContent='$'+Math.round(to*(0.5-Math.cos(k*Math.PI)/2)).toLocaleString(); if(k<1)requestAnimationFrame(tick); else if(cb)cb(); })(performance.now()); }
    function run(){
      chips.forEach(function(c){c.classList.remove('on');});
      state.className='rhero-state rhero-state--risk'; state.textContent='At risk of leaving';
      sub.textContent='No service visit in 14 months'; pulse.className='rhero-pulse'; ltvEl.textContent='$0';
      var d=700;
      chips.forEach(function(c,i){ setTimeout(function(){ c.classList.add('on'); }, d+i*760); });
      setTimeout(function(){
        state.className='rhero-state rhero-state--won'; state.textContent='Retained';
        sub.textContent='Booked service + next vehicle'; pulse.className='rhero-pulse on';
        count(38400);
      }, d+3*760);
      setTimeout(run, d+3*760+3200);
    }
    if('IntersectionObserver' in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;run();}});},{threshold:.3}).observe(root); } else run();
  })();
  </script>
</div>'''


def inventory_hero_animation():
    """Hero micro-animation: an inventory tile auto-morphs into a Facebook/Google
    ad, looping across vehicles. (Distinct from the page's campaign builder.)"""
    return '''<div class="ihero" id="ihero">
  <div class="ihero-stage">
    <div class="ihero-inv" id="ihero-inv">
      <div class="ihero-inv-badge">Live inventory</div>
      <div class="ihero-inv-name" id="ihero-name">2024 Ford F-150</div>
      <div class="ihero-inv-vin" id="ihero-vin">VIN &middot; 1FTFW1E58</div>
    </div>
    <div class="ihero-arrow">&rarr;</div>
    <div class="ihero-ad" id="ihero-ad">
      <div class="ihero-ad-tag" id="ihero-tag">Facebook</div>
      <div class="ihero-ad-img"><span class="cb-ico-car"></span></div>
      <div class="ihero-ad-body">
        <div class="ihero-ad-t" id="ihero-ad-name">2024 Ford F-150</div>
        <div class="ihero-ad-p" id="ihero-ad-price">$599/mo</div>
      </div>
    </div>
  </div>
  <div class="ihero-cap">Every vehicle, auto-built into ads &mdash; synced to your live stock.</div>
  <script>
  (function(){
    var root=document.getElementById('ihero'); if(!root) return;
    var cars=[
      {n:'2024 Ford F-150', vin:'1FTFW1E58', p:'$599/mo', plat:'Facebook'},
      {n:'2023 Chevy Tahoe', vin:'1GNSKBKC7', p:'$679/mo', plat:'Google'},
      {n:'2025 Honda Civic', vin:'2HGFE2F5', p:'$329/mo', plat:'Facebook'}
    ];
    var ad=document.getElementById('ihero-ad'), inv=document.getElementById('ihero-inv');
    var i=0, seen=false;
    function set(c){
      document.getElementById('ihero-name').textContent=c.n;
      document.getElementById('ihero-vin').textContent='VIN \u00b7 '+c.vin;
      document.getElementById('ihero-ad-name').textContent=c.n;
      document.getElementById('ihero-ad-price').textContent=c.p;
      var tag=document.getElementById('ihero-tag'); tag.textContent=c.plat;
      tag.className='ihero-ad-tag '+(c.plat==='Google'?'is-google':'is-fb');
    }
    function cycle(){
      var c=cars[i%cars.length]; set(c);
      inv.classList.remove('in'); ad.classList.remove('in');
      requestAnimationFrame(function(){ inv.classList.add('in'); setTimeout(function(){ ad.classList.add('in'); }, 550); });
      i++; setTimeout(cycle, 2600);
    }
    if('IntersectionObserver' in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;cycle();}});},{threshold:.3}).observe(root); } else cycle();
  })();
  </script>
</div>'''


def pie_hero_animation():
    """Hero animation: a living "Dealership Health Monitor" that auto-plays the
    product story on a loop \u2014 health score, a department flags for attention,
    then Problem -> Impact -> Cause -> Action. Distinct from the page's clickable
    GM drill-down demo (this one plays itself and is glanceable)."""
    return '''<div class="phero" id="phero">
  <div class="phero-head">
    <div class="phero-head-l">Dealership health</div>
    <div class="phero-score"><span id="phero-score">0</span><small>/100</small></div>
  </div>
  <div class="phero-depts">
    <div class="phero-dept" data-d="sales"><span class="phero-dot ok"></span>Sales<b class="phero-tag ok">Strong</b></div>
    <div class="phero-dept" data-d="service"><span class="phero-dot ok"></span>Service<b class="phero-tag ok">Healthy</b></div>
    <div class="phero-dept" data-d="inventory"><span class="phero-dot ok"></span>Inventory<b class="phero-tag ok">Healthy</b></div>
    <div class="phero-dept" data-d="parts"><span class="phero-dot ok"></span>Parts<b class="phero-tag ok">Healthy</b></div>
    <div class="phero-dept" data-d="fi"><span class="phero-dot ok"></span>F&amp;I<b class="phero-tag ok">Strong</b></div>
  </div>
  <div class="phero-insight" id="phero-insight">
    <div class="phero-ins-step" data-k="0">
      <div class="phero-ins-flag">&#9888; Service profitability declining</div>
    </div>
    <div class="phero-ins-step" data-k="1">
      <div class="phero-ins-label">Impact</div>
      <div class="phero-ins-big phero-neg">&minus;$18,400<small>/mo</small></div>
      <div class="phero-ins-sub">CPRO down 6%</div>
    </div>
    <div class="phero-ins-step" data-k="2">
      <div class="phero-ins-label">Root cause</div>
      <div class="phero-ins-big">Advisor utilization</div>
      <div class="phero-ins-sub phero-neg">down 11%</div>
    </div>
    <div class="phero-ins-step" data-k="3">
      <div class="phero-ins-label phero-pos">&#10022; Recommended focus</div>
      <div class="phero-ins-big">Service advisor team</div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("phero"); if(!root) return;
    var scoreEl=document.getElementById("phero-score");
    var svc=root.querySelector(\'.phero-dept[data-d="service"]\');
    var steps=[].slice.call(root.querySelectorAll(".phero-ins-step"));
    var seen=false, timers=[];
    function clearAll(){ timers.forEach(clearTimeout); timers=[]; }
    function at(ms,fn){ timers.push(setTimeout(fn,ms)); }
    function count(to){ var t0=performance.now(); (function tick(now){ var k=Math.min(1,(now-t0)/1100);
      scoreEl.textContent=Math.round(to*(0.5-Math.cos(k*Math.PI)/2)); if(k<1)requestAnimationFrame(tick); })(performance.now()); }
    function reset(){
      svc.classList.remove("warn");
      svc.querySelector(".phero-dot").className="phero-dot ok";
      svc.querySelector(".phero-tag").className="phero-tag ok"; svc.querySelector(".phero-tag").textContent="Healthy";
      steps.forEach(function(s){ s.classList.remove("on"); });
      root.classList.remove("expanded");
    }
    function run(){
      clearAll(); reset(); count(92);
      // service flags for attention
      at(1600,function(){
        svc.classList.add("warn");
        svc.querySelector(".phero-dot").className="phero-dot warn";
        var t=svc.querySelector(".phero-tag"); t.className="phero-tag warn"; t.textContent="Attention";
      });
      // Problem -> Impact -> Cause -> Action
      at(2400,function(){ root.classList.add("expanded"); steps[0].classList.add("on"); });
      at(3500,function(){ steps[1].classList.add("on"); });
      at(4700,function(){ steps[2].classList.add("on"); });
      at(5900,function(){ steps[3].classList.add("on"); });
      at(9000, run); // loop
    }
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;run();}});},{threshold:.3}).observe(root); } else run();
  })();
  </script>
</div>'''


def finance_hero_animation():
    """Before/After waiting-room animation for the Finance hero right column."""
    return '''<div class="fhero" id="fhero">
  <div class="fhero-card fhero-before">
    <div class="fhero-tag">Before Bumper Finance</div>
    <div class="fhero-timer">&#9201; <span>22:00</span> waiting</div>
    <ul class="fhero-list">
      <li class="miss">No engagement</li>
      <li class="miss">No education</li>
      <li class="miss">No product exposure</li>
    </ul>
  </div>
  <div class="fhero-card fhero-after">
    <div class="fhero-tag fhero-tag--on">With Bumper Finance</div>
    <div class="fhero-timer">&#9201; <span>22:00</span> engaged</div>
    <div class="fhero-bar"><span class="fhero-bar-fill" id="fhero-fill"></span></div>
    <ul class="fhero-list">
      <li data-step="1">Exploring products</li>
      <li data-step="2">Building a package</li>
      <li data-step="3">Watching videos</li>
      <li data-step="4">Learning benefits</li>
      <li data-step="5">Ready for F&amp;I</li>
    </ul>
  </div>
  <script>
  (function(){
    var root=document.getElementById('fhero'); if(!root) return;
    var items=[].slice.call(root.querySelectorAll('.fhero-after li'));
    var fill=document.getElementById('fhero-fill');
    var i=0, timer=null;
    function reset(){ items.forEach(function(x){x.classList.remove('on');}); fill.style.width='0'; i=0; }
    function step(){
      if(i<items.length){ items[i].classList.add('on'); i++; fill.style.width=(i/items.length*100)+'%'; }
      else { clearInterval(timer); setTimeout(function(){ reset(); run(); }, 2200); }
    }
    function run(){ clearInterval(timer); timer=setInterval(step, 900); }
    if('IntersectionObserver' in window){
      var seen=false;
      new IntersectionObserver(function(es){ es.forEach(function(e){ if(e.isIntersecting && !seen){ seen=true; run(); } }); },{threshold:.3}).observe(root);
    } else { run(); }
  })();
  </script>
</div>'''


def finance_package_builder():
    """"Build your protection package" — 4-step customer-journey demo."""
    return '''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">See it work</p>
    <h2 class="h2" style="margin-bottom:8px">Build your protection package.</h2>
    <p class="lede">Customers explore protection products while they wait &mdash; arriving at the F&amp;I office educated, engaged, and ready to buy.</p>
  </div>
  <div class="wrap">
    <div class="fpb" id="fpb">
      <div class="fpb-steps">
        <button class="fpb-step is-active" data-s="0"><span class="fpb-step-n">1</span> Vehicle</button>
        <button class="fpb-step" data-s="1"><span class="fpb-step-n">2</span> Explore</button>
        <button class="fpb-step" data-s="2"><span class="fpb-step-n">3</span> Build package</button>
        <button class="fpb-step" data-s="3"><span class="fpb-step-n">4</span> F&amp;I handoff</button>
      </div>
      <div class="fpb-stage">

        <!-- STEP 1 -->
        <div class="fpb-panel is-active" data-s="0">
          <div class="fpb-vehicle">
            <div class="fpb-vehicle-badge">&#10003; Vehicle selected</div>
            <div class="fpb-vehicle-name">2025 Ford F-150 XLT</div>
            <div class="fpb-vehicle-price">$58,495</div>
            <div class="fpb-waiting">Waiting for finance approval&hellip; <span class="fpb-dots"><i></i><i></i><i></i></span></div>
          </div>
          <button class="btn btn-blue fpb-next" data-go="1">Start exploring &rarr;</button>
        </div>

        <!-- STEP 2 -->
        <div class="fpb-panel" data-s="1">
          <p class="fpb-hint">While they wait, customers explore protection products at their own pace &mdash; each with plain-language coverage, cost, and real claim examples.</p>
          <div class="fpb-products">
            <div class="fpb-prod"><div class="fpb-prod-t">Extended Warranty</div><div class="fpb-prod-d">Covers major components after the factory warranty ends.</div><div class="fpb-prod-c">~$38/mo &middot; e.g. transmission, $4,200 claim</div></div>
            <div class="fpb-prod"><div class="fpb-prod-t">Tire &amp; Wheel</div><div class="fpb-prod-d">Road-hazard repair or replacement for tires and wheels.</div><div class="fpb-prod-c">~$14/mo &middot; e.g. bent wheel, $680 claim</div></div>
            <div class="fpb-prod"><div class="fpb-prod-t">Appearance Protection</div><div class="fpb-prod-d">Interior and exterior surface protection and repair.</div><div class="fpb-prod-c">~$12/mo &middot; e.g. seat tear, $340 claim</div></div>
            <div class="fpb-prod"><div class="fpb-prod-t">GAP Coverage</div><div class="fpb-prod-d">Covers the gap between loan balance and payout if totaled.</div><div class="fpb-prod-c">~$9/mo &middot; e.g. total loss, $5,900 gap</div></div>
            <div class="fpb-prod"><div class="fpb-prod-t">Maintenance Plan</div><div class="fpb-prod-d">Prepaid, scheduled maintenance at the dealership.</div><div class="fpb-prod-c">~$22/mo &middot; oil, rotation, inspections</div></div>
          </div>
          <button class="btn btn-blue fpb-next" data-go="2">Build my package &rarr;</button>
        </div>

        <!-- STEP 3 -->
        <div class="fpb-panel" data-s="2">
          <div class="fpb-build">
            <div class="fpb-picks">
              <p class="fpb-hint" style="text-align:left;margin-bottom:14px">Tap products to add them &mdash; watch the payment update in real time.</p>
              <button class="fpb-pick" data-amt="38">Extended Warranty <span>+$38/mo</span></button>
              <button class="fpb-pick" data-amt="14">Tire &amp; Wheel <span>+$14/mo</span></button>
              <button class="fpb-pick" data-amt="12">Appearance Protection <span>+$12/mo</span></button>
              <button class="fpb-pick" data-amt="9">GAP Coverage <span>+$9/mo</span></button>
              <button class="fpb-pick" data-amt="22">Maintenance Plan <span>+$22/mo</span></button>
            </div>
            <div class="fpb-payment">
              <div class="fpb-pay-row"><span>Vehicle payment</span><span class="fpb-pay-base">$699/mo</span></div>
              <div class="fpb-pay-row fpb-pay-add"><span>Protection</span><span id="fpb-add">+$0/mo</span></div>
              <div class="fpb-pay-total"><span>With protection</span><span id="fpb-total">$699/mo</span></div>
              <p class="fpb-pay-note">Affordability stays in the customer's control &mdash; no surprises at the finance desk.</p>
            </div>
          </div>
          <button class="btn btn-blue fpb-next" data-go="3">Head to F&amp;I &rarr;</button>
        </div>

        <!-- STEP 4 -->
        <div class="fpb-panel" data-s="3">
          <p class="fpb-hint">Same customer, two very different finance-office experiences.</p>
          <div class="fpb-compare">
            <div class="fpb-flow fpb-flow--old">
              <div class="fpb-flow-h">Traditional process</div>
              <ol><li>First time seeing products</li><li>Questions</li><li>Objections</li><li>Longer transaction</li></ol>
            </div>
            <div class="fpb-flow fpb-flow--new">
              <div class="fpb-flow-h">With Bumper Finance</div>
              <ol><li>Already educated</li><li>Package pre-selected</li><li>Confident purchase</li><li>Faster delivery</li></ol>
            </div>
          </div>
          <button class="btn btn-yellow fpb-restart">&#8635; Run it again</button>
        </div>

      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById('fpb'); if(!root) return;
    var steps=[].slice.call(root.querySelectorAll('.fpb-step'));
    var panels=[].slice.call(root.querySelectorAll('.fpb-panel'));
    var base=699, add=0;
    function show(i){
      steps.forEach(function(s,idx){ s.classList.toggle('is-active',idx===i); s.classList.toggle('is-done',idx<i); });
      panels.forEach(function(p,idx){ p.classList.toggle('is-active',idx===i); });
      if(i===1) staggerProducts();
    }
    function staggerProducts(){
      var ps=[].slice.call(root.querySelectorAll('.fpb-prod')); var d=0;
      ps.forEach(function(x){ x.classList.remove('in'); });
      ps.forEach(function(x){ setTimeout(function(){ x.classList.add('in'); }, d+=110); });
    }
    root.querySelectorAll('.fpb-pick').forEach(function(b){
      b.addEventListener('click',function(){
        var amt=parseInt(b.getAttribute('data-amt'));
        if(b.classList.toggle('on')){ add+=amt; } else { add-=amt; }
        document.getElementById('fpb-add').textContent='+$'+add+'/mo';
        var t=document.getElementById('fpb-total'); t.textContent='$'+(base+add)+'/mo';
        t.classList.remove('bump'); void t.offsetWidth; t.classList.add('bump');
      });
    });
    steps.forEach(function(s){ s.addEventListener('click',function(){ show(parseInt(s.getAttribute('data-s'))); }); });
    root.querySelectorAll('.fpb-next').forEach(function(b){ b.addEventListener('click',function(){ show(parseInt(b.getAttribute('data-go'))); }); });
    root.querySelector('.fpb-restart').addEventListener('click',function(){
      add=0; document.getElementById('fpb-add').textContent='+$0/mo'; document.getElementById('fpb-total').textContent='$699/mo';
      root.querySelectorAll('.fpb-pick').forEach(function(x){x.classList.remove('on');});
      show(0);
    });
  })();
  </script>
</section>'''


def finance_penetration_roi():
    """F&I penetration simulator — two sliders -> monthly revenue impact."""
    return '''<section class="section section--wash">
  <div class="wrap centered">
    <p class="eyebrow">The opportunity</p>
    <h2 class="h2" style="margin-bottom:8px">How much is sitting in your waiting area?</h2>
    <p class="lede">Every educated customer is a penetration point. Move the sliders to size the monthly opportunity a self-guided experience can unlock.</p>
  </div>
  <div class="wrap">
    <div class="fsim" id="fsim">
      <div class="fsim-controls">
        <div class="fsim-field">
          <label>Monthly deliveries <b id="fsim-del-v">150</b></label>
          <input type="range" id="fsim-del" min="50" max="500" step="10" value="150">
          <div class="fsim-scale"><span>50</span><span>500</span></div>
        </div>
        <div class="fsim-field">
          <label>Current product penetration <b id="fsim-pen-v">45%</b></label>
          <input type="range" id="fsim-pen" min="20" max="80" step="1" value="45">
          <div class="fsim-scale"><span>20%</span><span>80%</span></div>
        </div>
        <p class="fsim-note">Assumes a self-guided lift of ~12 penetration points at ~$540 average product gross. Directional &mdash; validate against your store.</p>
      </div>
      <div class="fsim-result">
        <div class="fsim-rows">
          <div class="fsim-row"><span>VSC revenue</span><span id="fsim-vsc">$0</span></div>
          <div class="fsim-row"><span>GAP revenue</span><span id="fsim-gap">$0</span></div>
          <div class="fsim-row"><span>Protection revenue</span><span id="fsim-prot">$0</span></div>
        </div>
        <div class="fsim-impact">
          <div class="fsim-impact-l">Estimated monthly impact</div>
          <div class="fsim-impact-v" id="fsim-impact">+$0</div>
        </div>
      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById('fsim'); if(!root) return;
    var del=document.getElementById('fsim-del'), pen=document.getElementById('fsim-pen');
    var LIFT=0.12, GROSS=540, mix={vsc:0.45,gap:0.20,prot:0.35};
    function money(n){ return '$'+Math.round(n).toLocaleString(); }
    function calc(){
      var d=+del.value, p=+pen.value;
      document.getElementById('fsim-del-v').textContent=d;
      document.getElementById('fsim-pen-v').textContent=p+'%';
      var extraUnits=d*LIFT;               // additional penetrated products/mo
      var total=extraUnits*GROSS;
      document.getElementById('fsim-vsc').textContent=money(total*mix.vsc);
      document.getElementById('fsim-gap').textContent=money(total*mix.gap);
      document.getElementById('fsim-prot').textContent=money(total*mix.prot);
      var imp=document.getElementById('fsim-impact'); imp.textContent='+'+money(total);
      imp.classList.remove('bump'); void imp.offsetWidth; imp.classList.add('bump');
    }
    del.addEventListener('input',calc); pen.addEventListener('input',calc); calc();
  })();
  </script>
</section>'''


def finance_comparison():
    """Bumper Finance vs Darwin vs MaximTrak — capability matrix in the shared cards."""
    rows = [
        ("Self-guided product education", ("yes",), ("yes",), ("yes",)),
        ("Product videos &amp; explanations", ("yes",), ("yes",), ("yes",)),
        ("Customer package builder", ("yes",), ("yes",), ("yes",)),
        ("Mobile-friendly experience", ("yes",), ("yes",), ("yes",)),
        ("Payment-impact visualization", ("yes",), ("yes",), ("yes",)),
        ("Digital product presentation", ("yes",), ("yes",), ("yes",)),
        ("Waiting-room engagement", ("yes",), ("partial",), ("partial",)),
        ("Customer product pre-selection", ("yes",), ("yes",), ("yes",)),
        ("Dealer branding &amp; customization", ("yes",), ("yes",), ("yes",)),
        ("Real-time customer insights", ("yes",), ("partial",), ("partial",)),
        ("Seamless F&amp;I handoff", ("yes",), ("yes",), ("yes",)),
        ("Dealer-focused support", ("yes",), ("partial",), ("partial",)),
    ]

    def col(idx):
        return [(row[idx + 1][0], row[0], row[idx + 1][1] if len(row[idx + 1]) > 1 else "") for row in rows]

    cards = [
        {"name": "Bumper Finance", "badge": "Modern retailing", "highlight": True, "items": col(0)},
        {"name": "Darwin", "badge": "Digital F&amp;I", "items": col(1)},
        {"name": "MaximTrak", "badge": "F&amp;I menu", "items": col(2)},
    ]
    disclaimer = ("Comparison reflects Vicimus's understanding of publicly available information about Darwin "
                  "Automotive and MaximTrak as of 2026, prepared in good faith. Competitor offerings change and "
                  "may vary by plan, region, and configuration; product and company names are trademarks of their "
                  "respective owners, used here for identification only. Verify current capabilities with each vendor.")
    return comparison_section(
        "How it stacks up",
        "Bumper Finance vs. the field.",
        "The digital F&amp;I basics are table stakes. Where Bumper pulls ahead is turning waiting-room time into "
        "engagement, surfacing real-time customer insight, and backing it with dealer-focused support.",
        cards, disclaimer,
    )


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
    # under Key Capabilities and a capability comparison after the screenshots;
    # Bumper Inventory Ads gets the campaign builder + interactive comparison).
    if p["slug"] == "bumper-retention":
        extra_after_capabilities = retention_journey()
        extra_after_shots = retention_comparison()
    elif p["slug"] == "bumper-inventory-ads":
        extra_after_capabilities = inventory_campaign_builder()
        extra_after_shots = inventory_comparison()
    elif p["slug"] == "pie":
        extra_after_capabilities = pie_dashboard_demo()
        extra_after_shots = pie_comparison()
    elif p["slug"] == "bumper-finance":
        extra_after_capabilities = finance_package_builder()
        extra_after_shots = finance_comparison() + finance_penetration_roi()
    else:
        extra_after_capabilities = ""
        extra_after_shots = ""

    HERO_DEMOS = {
        "bumper-finance": finance_hero_animation,
        "bumper-retention": retention_hero_animation,
        "bumper-inventory-ads": inventory_hero_animation,
        "pie": pie_hero_animation,
    }
    if p["slug"] in HERO_DEMOS:
        subhero = f'''<section class="subhero subhero--split">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__split">
    <div class="subhero__col">
      <img class="subhero__logo" src="{ap}{LOGODIR}/{p.get('logo_light', p['logo'])}" alt="{p['name']}">
      <h1 class="h1">{p['hero_h']}</h1>
      <p class="subhero__lead">{p['hero_p']}</p>
      <div class="subhero__actions">
        <a class="btn btn-yellow" href="{pp}book-a-demo.html">Schedule a demo &rarr;</a>
      </div>
    </div>
    <div class="subhero__demo">{HERO_DEMOS[p["slug"]]()}</div>
  </div>
</section>'''
    else:
        subhero = f'''<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <img class="subhero__logo" src="{ap}{LOGODIR}/{p.get('logo_light', p['logo'])}" alt="{p['name']}">
    <p class="eyebrow" translate="no">{p['eyebrow']}</p>
    <h1 class="h1">{p['hero_h']}</h1>
    <p class="subhero__lead">{p['hero_p']}</p>
    <div class="subhero__actions">
      <a class="btn btn-yellow" href="{pp}book-a-demo.html">Schedule a demo &rarr;</a>
    </div>
  </div>
</section>'''

    html += f'''
{subhero}

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
    # Preview site — keep it out of search engines entirely.
    with open(os.path.join(OUT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write("# Preview site — not for indexing.\nUser-agent: *\nDisallow: /\n")
    print("  wrote robots.txt")

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
