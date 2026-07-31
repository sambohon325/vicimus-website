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
    "bumper-finance":         {"kind": "per_unit",     "amount": 800,  "label": "F&I gross per vehicle",        "metric": "+$800 average PVR lift",           "hours": 260,  "hours_label": "deal prep & menu presentation"},
    "accessory-accelerator":  {"kind": "per_unit",     "amount": 500,  "label": "Accessory gross per vehicle",  "metric": "New accessory revenue per unit",   "hours": 156,  "hours_label": "accessory quoting & ordering"},
    "odometer-voip":          {"kind": "annual_flat",  "amount": 8400, "label": "Phone cost savings",           "metric": "~70% lower phone bill",            "hours": 180,  "hours_label": "call routing & phone admin"},
    "calls-on-demand":        {"kind": "qual",                                                                  "metric": "~20% of missed calls recovered",   "hours": 1040, "hours_label": "outbound calling handled for you"},
    "bumper-retention":       {"kind": "qual",                                                                  "metric": "Repeat & service retention lift",  "hours": 520,  "hours_label": "list pulling & manual follow-up"},
    "bumper-inventory-ads":   {"kind": "qual",                                                                  "metric": "More qualified inventory leads",   "hours": 312,  "hours_label": "building & refreshing ad creative"},
    "pie":              {"kind": "qual",                                                                  "metric": "Automated insight on one dataset", "hours": 416,  "hours_label": "pulling & reconciling reports"},
    "glovebox-websites":      {"kind": "qual",                                                                  "metric": "Higher website conversion",        "hours": 208,  "hours_label": "website edits without vendor tickets"},
    "powersports-independent":{"kind": "qual",                                                                  "metric": "Flexible, a-la-carte bundle",      "hours": 624,  "hours_label": "one vendor instead of six"},
}
# NOTE: "hours" are directional annual staff-hours-saved estimates for a typical
# single rooftop, expressed as hours/year. They are Vicimus-authored planning
# figures, not measured or audited results, and the tray labels them as such.
# They are deliberately kept in one table so they are easy to revise after
# review. Rough basis: hours/week x 52 (e.g. 10 hrs/wk of manual list-pulling
# and follow-up = 520). Calls on Demand is the outlier because it is an
# outsourced service that absorbs the calling work outright rather than
# speeding it up.

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


def retention_hero_animation(ap=""):
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


def inventory_hero_animation(ap=""):
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


def pie_hero_animation(ap=""):
    """Hero animation: a fixed-height "Dealership Health Monitor" that auto-plays
    the product story on a loop. Score + department statuses show; Service flags
    for attention; the department list then clears and the diagnostics load in the
    same space, one after another: Problem -> Impact -> Cause -> Action.
    Distinct from the page's clickable GM drill-down demo."""
    return '''<div class="phero" id="phero">
  <div class="phero-head">
    <div class="phero-head-l">Dealership health</div>
    <div class="phero-score"><span id="phero-score">0</span><small>/100</small></div>
  </div>
  <div class="phero-body">
    <div class="phero-panel phero-depts is-active" id="phero-depts">
      <div class="phero-dept" data-d="sales"><span class="phero-dot ok"></span>Sales<b class="phero-tag ok">Strong</b></div>
      <div class="phero-dept" data-d="service"><span class="phero-dot ok"></span>Service<b class="phero-tag ok">Healthy</b></div>
      <div class="phero-dept" data-d="inventory"><span class="phero-dot ok"></span>Inventory<b class="phero-tag ok">Healthy</b></div>
      <div class="phero-dept" data-d="parts"><span class="phero-dot ok"></span>Parts<b class="phero-tag ok">Healthy</b></div>
      <div class="phero-dept" data-d="fi"><span class="phero-dot ok"></span>F&amp;I<b class="phero-tag ok">Strong</b></div>
    </div>
    <div class="phero-panel phero-diag" id="phero-diag">
      <div class="phero-diag-head"><span class="phero-dot warn"></span>Service &middot; diagnostics</div>
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
        <div class="phero-ins-big">Advisor utilization <span class="phero-neg">down 11%</span></div>
      </div>
      <div class="phero-ins-step" data-k="3">
        <div class="phero-ins-label phero-pos">&#10022; Recommended focus</div>
        <div class="phero-ins-big">Service advisor team</div>
      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("phero"); if(!root) return;
    var scoreEl=document.getElementById("phero-score");
    var depts=document.getElementById("phero-depts"), diag=document.getElementById("phero-diag");
    var svc=root.querySelector(\'.phero-dept[data-d="service"]\');
    var steps=[].slice.call(diag.querySelectorAll(".phero-ins-step"));
    var seen=false, timers=[];
    function clearAll(){ timers.forEach(clearTimeout); timers=[]; }
    function at(ms,fn){ timers.push(setTimeout(fn,ms)); }
    var body=root.querySelector(".phero-body");
    function fit(panel){ if(body && panel) body.style.height=panel.scrollHeight+"px"; }
    function count(to){ var t0=performance.now(); (function tick(now){ var k=Math.min(1,(now-t0)/1100);
      scoreEl.textContent=Math.round(to*(0.5-Math.cos(k*Math.PI)/2)); if(k<1)requestAnimationFrame(tick); })(performance.now()); }
    function reset(){
      svc.classList.remove("warn");
      svc.querySelector(".phero-dot").className="phero-dot ok";
      var t=svc.querySelector(".phero-tag"); t.className="phero-tag ok"; t.textContent="Healthy";
      steps.forEach(function(s){ s.classList.remove("on"); });
      diag.classList.remove("is-active"); depts.classList.add("is-active");
      fit(depts);
    }
    function run(){
      clearAll(); reset(); count(92);
      // service flags for attention
      at(1500,function(){
        svc.classList.add("warn");
        svc.querySelector(".phero-dot").className="phero-dot warn";
        var t=svc.querySelector(".phero-tag"); t.className="phero-tag warn"; t.textContent="Attention";
      });
      // clear the department list, swap to diagnostics in the same space; box grows to fit
      at(2700,function(){ depts.classList.remove("is-active"); diag.classList.add("is-active"); fit(diag); });
      // diagnostics load one after another: Problem -> Impact -> Cause -> Action
      at(3100,function(){ steps[0].classList.add("on"); });
      at(4100,function(){ steps[1].classList.add("on"); });
      at(5200,function(){ steps[2].classList.add("on"); });
      at(6300,function(){ steps[3].classList.add("on"); });
      // hold on the recommendation, then loop back to the healthy overview
      at(9400, run);
    }
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;fit(depts);run();}});},{threshold:.3}).observe(root); } else { fit(depts); run(); }
  })();
  </script>
</div>'''


def finance_hero_animation(ap=""):
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


def _accessory_car_svg(ap=""):
    """Stacked realistic Jeep photos (cumulative accessory build). Four states
    cross-fade: standard -> +sidestep -> +rack -> fully loaded. The active image
    is set by JS via the .lvl-N class on the wrapper. ap = asset path prefix."""
    names = ["plain", "roof", "boards", "all"]
    imgs = "".join(
        f'<img class="acc-jeep acc-jeep--{i}" src="{ap}assets/img/jeep-{i}-{names[i]}.jpg" alt="">'
        for i in range(4)
    )
    return f'<div class="acc-carwrap lvl-0">{imgs}</div>'


def accessory_hero_animation(ap="../"):
    """Hero: accessories auto-appear on the vehicle while revenue ticks up. Loops."""
    return f'''<div class="ahero" id="ahero">
  <div class="ahero-vehicle">
    {_accessory_car_svg(ap)}
    <div class="ahero-name">2025 Jeep Wrangler</div>
  </div>
  <div class="ahero-tally">
    <div class="ahero-line"><span>Vehicle sale</span><b>$42,995</b></div>
    <div class="ahero-line ahero-add"><span>Accessories added</span><b id="ahero-acc">+$0</b></div>
    <div class="ahero-line ahero-total"><span>Total revenue</span><b id="ahero-total">$42,995</b></div>
    <div class="ahero-gross"><span>Dealer accessory gross</span><b id="ahero-gross">+$0</b></div>
  </div>
  <script>
  (function(){{
    var root=document.getElementById("ahero"); if(!root) return;
    var wrap=root.querySelector(".acc-carwrap");
    var accEl=document.getElementById("ahero-acc"), totEl=document.getElementById("ahero-total"), grEl=document.getElementById("ahero-gross");
    // cumulative levels matching the 4 jeep images: 0 plain, 1 +roof, 2 +boards/wheels, 3 all(final detail)
    var levels=[{{lvl:1,acc:812}},{{lvl:2,acc:2367}},{{lvl:3,acc:2367}}];
    var base=42995, seen=false, timers=[];
    function clr(){{ timers.forEach(clearTimeout); timers=[]; }}
    function at(ms,fn){{ timers.push(setTimeout(fn,ms)); }}
    function money(n){{ return "$"+Math.round(n).toLocaleString(); }}
    function setLvl(n){{ wrap.className="acc-carwrap lvl-"+n; }}
    function run(){{
      clr(); setLvl(0);
      accEl.textContent="+$0"; totEl.textContent=money(base); grEl.textContent="+$0";
      var d=1000;
      levels.forEach(function(it){{
        at(d,function(){{
          setLvl(it.lvl);
          accEl.textContent="+"+money(it.acc); totEl.textContent=money(base+it.acc);
          grEl.textContent="+"+money(it.acc*0.51);
        }});
        d+=950;
      }});
      at(d+2200, run);
    }}
    if("IntersectionObserver" in window){{ new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting&&!seen){{seen=true;run();}}}});}},{{threshold:.3}}).observe(root); }} else run();
  }})();
  </script>
</div>'''


def accessory_demo(ap="../"):
    """"One customer, multiple profit opportunities" — 3-stage interactive journey
    with a NEW / USED / SERVICE department toggle that changes recommendations."""
    return f'''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">See it work</p>
    <h2 class="h2" style="margin-bottom:8px">One customer. Multiple profit opportunities.</h2>
    <p class="lede">Every purchase and every service visit is an accessory opportunity. Pick a department and watch the incremental revenue add up.</p>
  </div>
  <div class="wrap">
    <div class="accd" id="accd">
      <div class="accd-toggle">
        <button class="accd-dept is-on" data-dept="new">New vehicle</button>
        <button class="accd-dept" data-dept="used">Used vehicle</button>
        <button class="accd-dept" data-dept="service">Service visit</button>
      </div>
      <div class="accd-body">
        <div class="accd-left">
          <div class="accd-vehicle">{_accessory_car_svg(ap)}</div>
          <div class="accd-recs" id="accd-recs"></div>
        </div>
        <div class="accd-right">
          <div class="accd-context" id="accd-context"></div>
          <div class="accd-rows" id="accd-rows"></div>
          <div class="accd-total"><span>Total incremental revenue</span><b id="accd-total">+$0</b></div>
        </div>
      </div>
    </div>
  </div>
  <script>
  (function(){{
    var root=document.getElementById("accd"); if(!root) return;
    // each rec carries the cumulative image level it brings the vehicle to
    var DATA={{
      "new":{{ context:"New vehicle purchase &middot; base sale $42,995",
        recs:[{{n:"Roof rack",p:812,lvl:1}},{{n:"Running boards",p:645,lvl:2}},{{n:"Wheel &amp; trim package",p:700,lvl:3}}],
        install:312 }},
      "used":{{ context:"Used vehicle purchase &middot; base sale $28,400",
        recs:[{{n:"Running boards",p:645,lvl:2}},{{n:"Wheel package",p:1039,lvl:3}}],
        install:180 }},
      "service":{{ context:"Service visit &middot; customer already in the lane",
        recs:[{{n:"Roof rack install",p:812,lvl:1}},{{n:"All-terrain wheel package",p:998,lvl:3}}],
        install:420 }}
    }};
    var recsBox=document.getElementById("accd-recs"), rowsBox=document.getElementById("accd-rows");
    var ctxEl=document.getElementById("accd-context"), totEl=document.getElementById("accd-total");
    var wrap=root.querySelector(".acc-carwrap");
    function money(n){{ return "$"+Math.round(n).toLocaleString(); }}
    function setLvl(n){{ if(wrap) wrap.className="acc-carwrap lvl-"+n; }}
    function animTotal(to){{ var t0=performance.now(); (function tick(now){{ var k=Math.min(1,(now-t0)/700);
      totEl.textContent="+"+money(to*(0.5-Math.cos(k*Math.PI)/2)); if(k<1)requestAnimationFrame(tick); }})(performance.now()); }}
    function render(dept){{
      var d=DATA[dept]; ctxEl.innerHTML=d.context;
      setLvl(0);
      recsBox.innerHTML=""; rowsBox.innerHTML="";
      var accSum=0, delay=0;
      d.recs.forEach(function(r){{
        accSum+=r.p;
        var chip=document.createElement("button"); chip.className="accd-rec"; chip.innerHTML="&#10003; "+r.n+" <span>+"+money(r.p)+"</span>";
        recsBox.appendChild(chip);
        (function(lvl,el){{ setTimeout(function(){{ setLvl(lvl); el.classList.add("in"); }}, delay+=320); }})(r.lvl,chip);
      }});
      // revenue rows
      var baseTxt = dept==="service" ? null : (dept==="used"?28400:42995);
      var rows=[];
      if(baseTxt) rows.push(["Base sale", money(baseTxt), false]);
      rows.push(["Accessory revenue", "+"+money(accSum), true]);
      rows.push(["Service installation", "+"+money(d.install), true]);
      rowsBox.innerHTML=rows.map(function(r){{ return "<div class=\\"accd-row"+(r[2]?" accd-inc":"")+"\\"><span>"+r[0]+"</span><b>"+r[1]+"</b></div>"; }}).join("");
      animTotal(accSum + d.install);
    }}
    root.querySelectorAll(".accd-dept").forEach(function(btn){{
      btn.addEventListener("click",function(){{
        root.querySelectorAll(".accd-dept").forEach(function(x){{x.classList.remove("is-on");}});
        btn.classList.add("is-on"); render(btn.getAttribute("data-dept"));
      }});
    }});
    var seen=false;
    if("IntersectionObserver" in window){{ new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting&&!seen){{seen=true;render("new");}}}});}},{{threshold:.3}}).observe(root); }} else render("new");
  }})();
  </script>
</section>'''


def accessory_comparison():
    """Accessory Accelerator vs Insignia Group vs AddOnAuto — capability matrix."""
    rows = [
        ("New-vehicle accessory sales", ("yes",), ("yes",), ("yes",)),
        ("Used-vehicle accessory sales", ("yes",), ("yes",), ("yes",)),
        ("Service-lane accessory opportunities", ("yes",), ("partial",), ("no",)),
        ("Personalized recommendations", ("yes",), ("yes",), ("yes",)),
        ("Accessory visualization", ("yes",), ("yes",), ("yes",)),
        ("Digital customer experience", ("yes",), ("yes",), ("yes",)),
        ("Multi-department deployment", ("yes",), ("partial",), ("no",)),
        ("Sales-department revenue generation", ("yes",), ("yes",), ("yes",)),
        ("Service-department revenue generation", ("yes",), ("partial",), ("no",)),
        ("Automated marketing campaigns", ("yes",), ("no",), ("no",)),
        ("Integration with retention marketing", ("yes",), ("no",), ("no",)),
        ("Dedicated performance management", ("yes",), ("no",), ("no",)),
        ("Revenue tracking &amp; reporting", ("yes",), ("yes",), ("yes",)),
        ("Accessory-specific campaign strategy", ("yes",), ("no",), ("no",)),
    ]

    def col(idx):
        return [(row[idx + 1][0], row[0], row[idx + 1][1] if len(row[idx + 1]) > 1 else "") for row in rows]

    cards = [
        {"name": "Accessory Accelerator", "badge": "Every department", "highlight": True, "items": col(0)},
        {"name": "Insignia Group", "badge": "Accessory sales", "items": col(1)},
        {"name": "AddOnAuto", "badge": "Point-of-sale", "items": col(2)},
    ]
    disclaimer = ("Comparison reflects Vicimus's understanding of publicly available information about Insignia "
                  "Group and AddOnAuto as of 2026, prepared in good faith. Competitor offerings change and may vary "
                  "by plan, region, and configuration; product and company names are trademarks of their respective "
                  "owners, used here for identification only. Verify current capabilities with each vendor.")
    return comparison_section(
        "How it stacks up",
        "Accessory Accelerator vs. the field.",
        "Selling accessories at the point of sale is table stakes. Accessory Accelerator extends the same engine "
        "across the service lane and into automated, retention-connected campaigns &mdash; not just the showroom.",
        cards, disclaimer,
    )


def glovebox_hero_animation(ap=""):
    """Hero: a live website editor — headline gets edited, preview updates, then
    the 'change request: 0 / wait: 0 days / published: now' payoff. Loops."""
    return '''<div class="gbh" id="gbh">
  <div class="gbh-editor">
    <div class="gbh-editor-bar"><span class="gbh-dot"></span><span class="gbh-dot"></span><span class="gbh-dot"></span><span class="gbh-editor-t">Website editor</span></div>
    <div class="gbh-field">
      <label>Homepage headline</label>
      <div class="gbh-input" id="gbh-input"><span id="gbh-typed"></span><span class="gbh-caret">|</span></div>
    </div>
    <button class="gbh-pub" id="gbh-pub">Publish &rarr;</button>
  </div>
  <div class="gbh-preview">
    <div class="gbh-browser"><span class="gbh-url">yourdealership.com</span></div>
    <div class="gbh-site">
      <div class="gbh-site-hero">
        <div class="gbh-site-h" id="gbh-site-h">Summer Sales Event</div>
        <div class="gbh-site-sub">0% financing available</div>
        <button class="gbh-site-cta">Shop inventory</button>
      </div>
      <div class="gbh-published" id="gbh-published">
        <div class="gbh-pub-row"><span>Change requests</span><b>0</b></div>
        <div class="gbh-pub-row"><span>Wait time</span><b>0 days</b></div>
        <div class="gbh-pub-row gbh-pub-live"><span>Published</span><b>Now &#10003;</b></div>
      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("gbh"); if(!root) return;
    var typed=document.getElementById("gbh-typed"), siteH=document.getElementById("gbh-site-h");
    var pub=document.getElementById("gbh-pub"), published=document.getElementById("gbh-published");
    var target="Truck Month Starts Now", seen=false, timers=[];
    function clr(){ timers.forEach(clearTimeout); timers=[]; }
    function at(ms,fn){ timers.push(setTimeout(fn,ms)); }
    function run(){
      clr();
      typed.textContent=""; siteH.textContent="Summer Sales Event"; siteH.classList.remove("gbh-flash");
      pub.classList.remove("on"); published.classList.remove("on");
      // type the new headline
      var i=0;
      function type(){ if(i<=target.length){ typed.textContent=target.slice(0,i); i++; at(60,type); } else afterType(); }
      at(900, type);
      function afterType(){
        at(400,function(){ pub.classList.add("on"); });
        at(1000,function(){ siteH.textContent=target; siteH.classList.add("gbh-flash"); });
        at(1600,function(){ published.classList.add("on"); });
        at(4200, run);
      }
    }
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;run();}});},{threshold:.3}).observe(root); } else run();
  })();
  </script>
</div>'''


def glovebox_demo():
    """"Build a dealer website in 30 seconds" — layout -> content -> brand,
    with a live preview that responds to each choice."""
    return '''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">See it work</p>
    <h2 class="h2" style="margin-bottom:8px">Build a dealer website in 30 seconds.</h2>
    <p class="lede">Pick a layout, switch on the content your store needs, and brand it &mdash; the live preview updates as you go. No developers.</p>
  </div>
  <div class="wrap">
    <div class="gbd" id="gbd">
      <div class="gbd-controls">
        <div class="gbd-step">
          <div class="gbd-step-h"><span>1</span> Choose a layout</div>
          <div class="gbd-layouts">
            <button class="gbd-layout is-on" data-l="modern">Modern</button>
            <button class="gbd-layout" data-l="inventory">Inventory-focused</button>
            <button class="gbd-layout" data-l="luxury">Luxury</button>
            <button class="gbd-layout" data-l="truck">Truck</button>
          </div>
        </div>
        <div class="gbd-step">
          <div class="gbd-step-h"><span>2</span> Add content</div>
          <div class="gbd-content">
            <button class="gbd-mod is-on" data-m="specials">Specials</button>
            <button class="gbd-mod" data-m="financing">Financing</button>
            <button class="gbd-mod" data-m="trade">Trade tool</button>
            <button class="gbd-mod" data-m="service">Service scheduler</button>
          </div>
        </div>
        <div class="gbd-step">
          <div class="gbd-step-h"><span>3</span> Brand it</div>
          <div class="gbd-brand">
            <button class="gbd-color is-on" data-c="#2B68AB" style="--sw:#2B68AB"></button>
            <button class="gbd-color" data-c="#16A34A" style="--sw:#16A34A"></button>
            <button class="gbd-color" data-c="#EE3B25" style="--sw:#EE3B25"></button>
            <button class="gbd-color" data-c="#7A3FA0" style="--sw:#7A3FA0"></button>
            <button class="gbd-color" data-c="#0D2D5C" style="--sw:#0D2D5C"></button>
          </div>
        </div>
      </div>
      <div class="gbd-preview" id="gbd-preview">
        <div class="gbd-browser"><span class="gbd-url">yourdealership.com</span></div>
        <div class="gbd-site" id="gbd-site">
          <div class="gbd-site-nav"><span class="gbd-logo">DEALER</span><span class="gbd-navlinks"><i></i><i></i><i></i></span></div>
          <div class="gbd-site-hero" id="gbd-hero">
            <div class="gbd-hero-tag" id="gbd-tag">Modern</div>
            <div class="gbd-hero-h">Find your next vehicle</div>
            <button class="gbd-hero-cta" id="gbd-cta">Shop now</button>
          </div>
          <div class="gbd-mods" id="gbd-mods"></div>
          <div class="gbd-ready" id="gbd-ready"><b>&#10003; Dealer website ready</b><span>No developers required</span></div>
        </div>
      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("gbd"); if(!root) return;
    var site=document.getElementById("gbd-site"), tag=document.getElementById("gbd-tag");
    var cta=document.getElementById("gbd-cta"), modsBox=document.getElementById("gbd-mods");
    var logo=root.querySelector(".gbd-logo"), navlinks=root.querySelectorAll(".gbd-navlinks i");
    var LAYOUTS={
      modern:{tag:"Modern",bg:"linear-gradient(135deg,#eaf2fb,#d6e6f6)"},
      inventory:{tag:"Inventory-focused",bg:"linear-gradient(135deg,#eef4ea,#e0ecd8)"},
      luxury:{tag:"Luxury",bg:"linear-gradient(135deg,#1b1b1f,#33333b)",dark:true},
      truck:{tag:"Truck",bg:"linear-gradient(135deg,#f4ece0,#e8d9c2)"}
    };
    var MODNAMES={specials:"Specials",financing:"Financing",trade:"Trade tool",service:"Service scheduler"};
    var accent="#2B68AB";
    function renderMods(){
      var on=[].slice.call(root.querySelectorAll(".gbd-mod.is-on")).map(function(b){return b.getAttribute("data-m");});
      modsBox.innerHTML="";
      on.forEach(function(m,idx){
        var card=document.createElement("div"); card.className="gbd-mod-card";
        card.textContent=MODNAMES[m]; card.style.borderTopColor=accent;
        modsBox.appendChild(card);
        setTimeout(function(){ card.classList.add("in"); }, idx*90);
      });
    }
    function applyLayout(l){
      var d=LAYOUTS[l]; var hero=document.getElementById("gbd-hero");
      hero.style.background=d.bg; tag.textContent=d.tag;
      site.classList.toggle("is-dark", !!d.dark);
    }
    function applyAccent(){
      cta.style.background=accent; logo.style.color=accent;
      navlinks.forEach(function(i){ i.style.background=accent; });
      [].slice.call(modsBox.querySelectorAll(".gbd-mod-card")).forEach(function(c){ c.style.borderTopColor=accent; });
      document.getElementById("gbd-tag").style.background=accent;
    }
    root.querySelectorAll(".gbd-layout").forEach(function(b){
      b.addEventListener("click",function(){
        root.querySelectorAll(".gbd-layout").forEach(function(x){x.classList.remove("is-on");});
        b.classList.add("is-on"); applyLayout(b.getAttribute("data-l"));
      });
    });
    root.querySelectorAll(".gbd-mod").forEach(function(b){
      b.addEventListener("click",function(){ b.classList.toggle("is-on"); renderMods(); applyAccent(); });
    });
    root.querySelectorAll(".gbd-color").forEach(function(b){
      b.addEventListener("click",function(){
        root.querySelectorAll(".gbd-color").forEach(function(x){x.classList.remove("is-on");});
        b.classList.add("is-on"); accent=b.getAttribute("data-c"); applyAccent();
      });
    });
    var seen=false;
    function init(){ applyLayout("modern"); renderMods(); applyAccent(); }
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;init();}});},{threshold:.3}).observe(root); } else init();
  })();
  </script>
</section>'''


def glovebox_comparison():
    """GloveBox vs Dealer.com vs Dealer Inspire — capability matrix."""
    rows = [
        ("Dealer-controlled website editing", ("yes",), ("partial",), ("partial",)),
        ("Instant content updates", ("yes",), ("partial",), ("partial",)),
        ("No developer required", ("yes",), ("partial",), ("partial",)),
        ("Custom landing pages", ("yes",), ("yes",), ("yes",)),
        ("Inventory integration", ("yes",), ("yes",), ("yes",)),
        ("Mobile responsive", ("yes",), ("yes",), ("yes",)),
        ("Specials &amp; incentive pages", ("yes",), ("yes",), ("yes",)),
        ("Service &amp; parts pages", ("yes",), ("yes",), ("yes",)),
        ("Fast website launches", ("yes",), ("partial",), ("partial",)),
        ("Dealer-specific customization", ("yes",), ("yes",), ("yes",)),
        ("Performance reporting", ("yes",), ("yes",), ("yes",)),
        ("Dedicated support team", ("yes",), ("yes",), ("yes",)),
        ("Integrated with Vicimus marketing products", ("yes",), ("no",), ("no",)),
        ("Connected retention-campaign landing pages", ("yes",), ("no",), ("no",)),
        ("Connected inventory-ad campaign pages", ("yes",), ("no",), ("no",)),
    ]

    def col(idx):
        return [(row[idx + 1][0], row[0], row[idx + 1][1] if len(row[idx + 1]) > 1 else "") for row in rows]

    cards = [
        {"name": "GloveBox", "badge": "Dealer-controlled", "highlight": True, "items": col(0)},
        {"name": "Dealer.com", "badge": "Website platform", "items": col(1)},
        {"name": "Dealer Inspire", "badge": "Website platform", "items": col(2)},
    ]
    disclaimer = ("Comparison reflects Vicimus's understanding of publicly available information about Dealer.com and "
                  "Dealer Inspire as of 2026, prepared in good faith. Competitor offerings change and may vary by "
                  "plan, region, and configuration; product and company names are trademarks of their respective "
                  "owners, used here for identification only. Verify current capabilities with each vendor.")
    return comparison_section(
        "How it stacks up",
        "Why dealers choose GloveBox.",
        "The website basics are covered everywhere. Where GloveBox pulls ahead is putting editing in the dealer's "
        "hands &mdash; instant updates, no developer, fast launches &mdash; and wiring the site straight into your "
        "Vicimus retention and ad campaigns.",
        cards, disclaimer,
    )


def odometer_hero_animation(ap=""):
    """Hero: 'The Call Journey' — ad spend -> calls -> routed to departments ->
    a missed call flashes red -> lost sale -> Odometer activates -> final stats. Loops."""
    return '''<div class="oh" id="oh">
  <div class="oh-flow">
    <div class="oh-node oh-spend"><span class="oh-lbl">Monthly ad spend</span><b>$15,000</b></div>
    <div class="oh-arrow">&darr;</div>
    <div class="oh-node oh-calls"><span class="oh-lbl">Phone calls generated</span><b id="oh-callnum">247</b></div>
    <div class="oh-arrow">&darr;</div>
    <div class="oh-depts">
      <span class="oh-dept" data-d="0">Sales</span>
      <span class="oh-dept" data-d="1">Service</span>
      <span class="oh-dept" data-d="2">Parts</span>
      <span class="oh-dept" data-d="3">BDC</span>
    </div>
  </div>
  <div class="oh-right">
    <div class="oh-alert" id="oh-alert">
      <div class="oh-alert-flag">&#9888; Missed call</div>
      <div class="oh-alert-sub">Potential sale lost &middot; <b>&minus;$35,000 vehicle</b></div>
    </div>
    <div class="oh-activate" id="oh-activate">
      <div class="oh-act-t">Odometer activates</div>
      <div class="oh-act" data-k="0">&#10003; Call recorded</div>
      <div class="oh-act" data-k="1">&#10003; Call routed</div>
      <div class="oh-act" data-k="2">&#10003; Call tracked</div>
      <div class="oh-act" data-k="3">&#10003; Call reported</div>
    </div>
    <div class="oh-stats" id="oh-stats">
      <div class="oh-stat"><b>247</b><span>Calls</span></div>
      <div class="oh-stat oh-stat-good"><b>96%</b><span>Answer rate</span></div>
      <div class="oh-stat"><b>8</b><span>Missed</span></div>
      <div class="oh-stat oh-stat-rec"><b>5</b><span>Recovered</span></div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("oh"); if(!root) return;
    var depts=[].slice.call(root.querySelectorAll(".oh-dept"));
    var alert=document.getElementById("oh-alert"), activate=document.getElementById("oh-activate"), stats=document.getElementById("oh-stats");
    var acts=[].slice.call(activate.querySelectorAll(".oh-act"));
    var seen=false, timers=[];
    function clr(){ timers.forEach(clearTimeout); timers=[]; }
    function at(ms,fn){ timers.push(setTimeout(fn,ms)); }
    function run(){
      clr();
      depts.forEach(function(d){ d.classList.remove("on","miss"); });
      alert.classList.remove("on"); activate.classList.remove("on"); stats.classList.remove("on");
      acts.forEach(function(a){ a.classList.remove("on"); });
      // calls fan into departments
      depts.forEach(function(d,i){ at(700+i*220,function(){ d.classList.add("on"); }); });
      // one flashes red (Sales)
      at(1900,function(){ depts[0].classList.add("miss"); alert.classList.add("on"); });
      // odometer activates
      at(3100,function(){ activate.classList.add("on"); });
      acts.forEach(function(a,i){ at(3400+i*500,function(){ a.classList.add("on"); }); });
      // final stats
      at(5900,function(){ stats.classList.add("on"); });
      at(9200, run);
    }
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;run();}});},{threshold:.3}).observe(root); } else run();
  })();
  </script>
</div>'''


def odometer_demo():
    """Call Recovery Simulator — without vs with Odometer, sliders drive a
    recovered-revenue payoff. The money shot."""
    return '''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">See it work</p>
    <h2 class="h2" style="margin-bottom:8px">Most dealerships track leads. Odometer tracks conversations.</h2>
    <p class="lede">Set your call volume and see what slips through &mdash; and what Odometer puts back on the board.</p>
  </div>
  <div class="wrap">
    <div class="ocr" id="ocr">
      <div class="ocr-controls">
        <label class="ocr-slider">
          <span class="ocr-slider-top">Monthly calls <b id="ocr-calls-v">500</b></span>
          <input type="range" id="ocr-calls" min="100" max="2000" step="50" value="500">
        </label>
        <label class="ocr-slider">
          <span class="ocr-slider-top">Missed-call rate <b id="ocr-miss-v">15%</b></span>
          <input type="range" id="ocr-miss" min="4" max="30" step="1" value="15">
        </label>
        <label class="ocr-slider">
          <span class="ocr-slider-top">Avg. revenue per recovered call <b id="ocr-val-v">$1,400</b></span>
          <input type="range" id="ocr-val" min="400" max="3500" step="100" value="1400">
        </label>
      </div>
      <div class="ocr-panels">
        <div class="ocr-card ocr-without">
          <div class="ocr-card-t">Without Odometer</div>
          <div class="ocr-row"><span>Monthly calls</span><b id="ocr-w-calls">500</b></div>
          <div class="ocr-row"><span>Missed calls</span><b id="ocr-w-miss">73</b></div>
          <div class="ocr-row ocr-row-bad"><span>Status</span><b>Unknown</b></div>
        </div>
        <div class="ocr-card ocr-with">
          <div class="ocr-card-t">With Odometer</div>
          <div class="ocr-row"><span>Monthly calls</span><b id="ocr-c-calls">500</b></div>
          <div class="ocr-row"><span>Missed calls</span><b id="ocr-c-miss">73</b></div>
          <div class="ocr-row ocr-row-good"><span>Recovered</span><b id="ocr-rec">41</b></div>
          <div class="ocr-row ocr-row-good"><span>Appointments</span><b id="ocr-appt">18</b></div>
          <div class="ocr-row ocr-row-good"><span>Sales</span><b id="ocr-sales">7</b></div>
        </div>
      </div>
      <div class="ocr-payoff">
        <span>Recovered revenue / year</span>
        <b id="ocr-revenue">$688,800</b>
      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("ocr"); if(!root) return;
    var calls=document.getElementById("ocr-calls"), miss=document.getElementById("ocr-miss"), val=document.getElementById("ocr-val");
    function money(n){ return "$"+Math.round(n).toLocaleString(); }
    function calc(){
      var c=+calls.value, mr=+miss.value/100, v=+val.value;
      var missed=Math.round(c*mr);
      var recovered=Math.round(missed*0.56);   // Odometer surfaces & recovers a share
      var appts=Math.round(recovered*0.44);
      var sales=Math.round(appts*0.38);
      document.getElementById("ocr-calls-v").textContent=c.toLocaleString();
      document.getElementById("ocr-miss-v").textContent=miss.value+"%";
      document.getElementById("ocr-val-v").textContent=money(v);
      document.getElementById("ocr-w-calls").textContent=c.toLocaleString();
      document.getElementById("ocr-c-calls").textContent=c.toLocaleString();
      document.getElementById("ocr-w-miss").textContent=missed;
      document.getElementById("ocr-c-miss").textContent=missed;
      document.getElementById("ocr-rec").textContent=recovered;
      document.getElementById("ocr-appt").textContent=appts;
      document.getElementById("ocr-sales").textContent=sales;
      var annual=recovered*v*12;
      var el=document.getElementById("ocr-revenue"); el.textContent=money(annual);
    }
    [calls,miss,val].forEach(function(s){ s.addEventListener("input",calc); });
    calc();
  })();
  </script>
</section>'''


def odometer_comparison():
    """Odometer vs RingCentral vs Dialpad capability matrix."""
    rows = [
        ("VoIP calling", ("yes",), ("yes",), ("yes",)),
        ("Call recording", ("yes",), ("yes",), ("yes",)),
        ("Call tracking", ("yes",), ("partial",), ("partial",)),
        ("Dealership reporting", ("yes",), ("no",), ("no",)),
        ("Sales-department analytics", ("yes",), ("no",), ("no",)),
        ("Service-department analytics", ("yes",), ("no",), ("no",)),
        ("Automotive workflow focus", ("yes",), ("no",), ("no",)),
        ("Missed-opportunity reporting", ("yes",), ("no",), ("no",)),
        ("Multi-rooftop visibility", ("yes",), ("partial",), ("partial",)),
        ("Dealer-specific support", ("yes",), ("no",), ("no",)),
    ]

    def col(idx):
        return [(row[idx + 1][0], row[0], row[idx + 1][1] if len(row[idx + 1]) > 1 else "") for row in rows]

    cards = [
        {"name": "Odometer", "badge": "Built for dealers", "highlight": True, "items": col(0)},
        {"name": "RingCentral", "badge": "General VoIP", "items": col(1)},
        {"name": "Dialpad", "badge": "General VoIP", "items": col(2)},
    ]
    disclaimer = ("Comparison reflects Vicimus's understanding of publicly available information about RingCentral and "
                  "Dialpad as of 2026, prepared in good faith. These are capable general-purpose business phone "
                  "platforms; the contrast here is dealership-specific reporting and workflow, not overall quality. "
                  "Offerings change and vary by plan; product and company names are trademarks of their respective "
                  "owners, used for identification only. Verify current capabilities with each vendor.")
    return comparison_section(
        "How it stacks up",
        "Why dealers choose Odometer.",
        "General VoIP platforms make and record calls well. Odometer adds what a dealership actually needs on top: "
        "department-level analytics, missed-opportunity reporting, and multi-rooftop visibility built for the "
        "automotive workflow.",
        cards, disclaimer,
    )


def cod_hero_animation(ap=""):
    """Hero: The Opportunity Meter — today's opportunities tally -> without COD
    (79 missed) -> COD activates -> results (2 missed). Loops."""
    return '''<div class="cod" id="cod">
    <div class="cod-meter">
      <div class="cod-meter-t">Today's opportunities</div>
      <div class="cod-src"><span>Inbound calls</span><b>47</b></div>
      <div class="cod-src"><span>Web leads</span><b>23</b></div>
      <div class="cod-src"><span>Service due</span><b>62</b></div>
      <div class="cod-src"><span>Unsold prospects</span><b>89</b></div>
      <div class="cod-total"><span>Total</span><b>221</b></div>
    </div>
    <div class="cod-right">
      <div class="cod-result cod-without" id="cod-without">
        <div class="cod-result-t">Without COD</div>
        <div class="cod-r-row"><span>Handled</span><b>142</b></div>
        <div class="cod-r-row cod-r-miss"><span>Missed</span><b>79 opportunities</b></div>
      </div>
      <div class="cod-activate" id="cod-activate">
        <div class="cod-act-t"><span class="cod-live"></span> Calls on Demand online</div>
        <div class="cod-act" data-k="0">&#10003; Inbound coverage</div>
        <div class="cod-act" data-k="1">&#10003; Outbound follow-up</div>
        <div class="cod-act" data-k="2">&#10003; Appointment setting</div>
        <div class="cod-act" data-k="3">&#10003; Retention campaigns</div>
      </div>
      <div class="cod-result cod-with" id="cod-with">
        <div class="cod-result-t">With COD</div>
        <div class="cod-r-row"><span>Handled</span><b id="cod-handled">219</b></div>
        <div class="cod-r-row cod-r-good"><span>Missed</span><b>2 opportunities</b></div>
      </div>
    </div>
  <script>
  (function(){
    var root=document.getElementById("cod"); if(!root) return;
    var without=document.getElementById("cod-without"), activate=document.getElementById("cod-activate"), withc=document.getElementById("cod-with");
    var acts=[].slice.call(activate.querySelectorAll(".cod-act"));
    var seen=false, timers=[];
    function clr(){ timers.forEach(clearTimeout); timers=[]; }
    function at(ms,fn){ timers.push(setTimeout(fn,ms)); }
    function run(){
      clr();
      without.classList.remove("on"); activate.classList.remove("on"); withc.classList.remove("on");
      acts.forEach(function(a){ a.classList.remove("on"); });
      at(700,function(){ without.classList.add("on"); });
      at(2100,function(){ activate.classList.add("on"); });
      acts.forEach(function(a,i){ at(2500+i*450,function(){ a.classList.add("on"); }); });
      at(4700,function(){ withc.classList.add("on"); });
      at(8200, run);
    }
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;run();}});},{threshold:.3}).observe(root); } else run();
  })();
  </script>
</div>'''


def cod_demo():
    """"One Lead. Two Outcomes." — split screen, without vs with COD, with a
    lead-type toggle that changes the scenario."""
    return '''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">See it work</p>
    <h2 class="h2" style="margin-bottom:8px">One lead. Two outcomes.</h2>
    <p class="lede">The difference isn't the lead &mdash; it's the follow-up. Pick a scenario and watch it play out both ways.</p>
  </div>
  <div class="wrap">
    <div class="cod2" id="cod2">
      <div class="cod2-toggle">
        <button class="cod2-t is-on" data-s="sales">Sales lead</button>
        <button class="cod2-t" data-s="service">Service lead</button>
        <button class="cod2-t" data-s="missed">Missed call</button>
        <button class="cod2-t" data-s="retention">Retention opportunity</button>
      </div>
      <div class="cod2-split">
        <div class="cod2-side cod2-lose">
          <div class="cod2-side-t">Without COD</div>
          <div class="cod2-steps" id="cod2-lose-steps"></div>
          <div class="cod2-outcome cod2-outcome-bad" id="cod2-lose-out">Lost opportunity</div>
        </div>
        <div class="cod2-side cod2-win">
          <div class="cod2-side-t">With COD</div>
          <div class="cod2-steps" id="cod2-win-steps"></div>
          <div class="cod2-outcome cod2-outcome-good" id="cod2-win-out">Showroom visit</div>
        </div>
      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("cod2"); if(!root) return;
    var SCEN={
      sales:{
        start:"Internet lead arrives",
        lose:["Sales team busy","No response","Customer shops elsewhere"], loseOut:"Lost opportunity",
        win:["COD responds in minutes","Appointment scheduled","Sales team engaged"], winOut:"Showroom visit"
      },
      service:{
        start:"Service-due customer",
        lose:["Advisors overloaded","Reminder never sent","Customer skips service"], loseOut:"Lost RO revenue",
        win:["COD calls the customer","Appointment booked","Advisor prepped"], winOut:"Service visit"
      },
      missed:{
        start:"Inbound call rings",
        lose:["No one available","Call goes to voicemail","Caller hangs up"], loseOut:"Missed sale",
        win:["COD picks up the overflow","Need captured","Routed to the right team"], winOut:"Opportunity saved"
      },
      retention:{
        start:"Equity / lease-end prospect",
        lose:["No outbound capacity","Prospect never contacted","Defects to a competitor"], loseOut:"Lost loyalty",
        win:["COD runs the campaign","Prospect re-engaged","Upgrade offer presented"], winOut:"Repeat customer"
      }
    };
    var loseSteps=document.getElementById("cod2-lose-steps"), winSteps=document.getElementById("cod2-win-steps");
    var loseOut=document.getElementById("cod2-lose-out"), winOut=document.getElementById("cod2-win-out");
    function build(box, start, steps){
      box.innerHTML="";
      var all=[start].concat(steps);
      all.forEach(function(txt,i){
        var step=document.createElement("div"); step.className="cod2-step"; step.textContent=txt;
        box.appendChild(step);
        if(i<all.length-1){ var ar=document.createElement("div"); ar.className="cod2-arrow"; ar.innerHTML="&darr;"; box.appendChild(ar); }
        setTimeout(function(){ step.classList.add("in"); }, i*280);
      });
    }
    function render(s){
      var d=SCEN[s];
      loseOut.classList.remove("show"); winOut.classList.remove("show");
      loseOut.textContent=d.loseOut; winOut.textContent=d.winOut;
      build(loseSteps, d.start, d.lose); build(winSteps, d.start, d.win);
      var total=(d.lose.length+1);
      setTimeout(function(){ loseOut.classList.add("show"); winOut.classList.add("show"); }, total*280+200);
    }
    root.querySelectorAll(".cod2-t").forEach(function(btn){
      btn.addEventListener("click",function(){
        root.querySelectorAll(".cod2-t").forEach(function(x){x.classList.remove("is-on");});
        btn.classList.add("is-on"); render(btn.getAttribute("data-s"));
      });
    });
    var seen=false;
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;render("sales");}});},{threshold:.3}).observe(root); } else render("sales");
  })();
  </script>
</section>'''


def cod_comparison():
    """Calls on Demand vs Other BDC Provider vs Hiring In-House."""
    rows = [
        # (label, COD, Other BDC, In-House)
        ("Inbound call handling", ("yes",), ("yes",), ("yes",)),
        ("Outbound sales calls", ("yes",), ("yes",), ("partial",)),
        ("Service appointment setting", ("yes",), ("yes",), ("yes",)),
        ("Retention-campaign support", ("yes",), ("partial",), ("no",)),
        ("Equity-mining outreach", ("yes",), ("no",), ("no",)),
        ("Service-lane opportunities", ("yes",), ("no",), ("partial",)),
        ("Multi-channel customer engagement", ("yes",), ("partial",), ("no",)),
        ("Integrated with the Vicimus ecosystem", ("yes",), ("no",), ("no",)),
        ("Retention + advertising + BDC alignment", ("yes",), ("no",), ("no",)),
        ("Scales without new payroll", ("yes",), ("partial",), ("no",)),
    ]

    def col(idx):
        return [(row[idx + 1][0], row[0], row[idx + 1][1] if len(row[idx + 1]) > 1 else "") for row in rows]

    cards = [
        {"name": "Calls on Demand", "badge": "Built for dealers", "highlight": True, "items": col(0)},
        {"name": "Other BDC Provider", "badge": "Generic call center", "items": col(1)},
        {"name": "Hiring In-House", "badge": "Your own team", "items": col(2)},
    ]
    disclaimer = ("Illustrative comparison of Calls on Demand against a typical third-party BDC / call-center "
                  "arrangement and against building an in-house team, based on Vicimus's understanding of common "
                  "industry realities as of 2026. Every store and provider is different; staffing outcomes, scope, "
                  "and cost vary widely. Use this as a starting point, not a guarantee.")
    return comparison_section(
        "How it stacks up",
        "Calls on Demand vs. the alternatives.",
        "Most dealers weigh three options: a generic BDC, hiring and training their own team, or Calls on Demand. "
        "Only one works your opportunities like part of your store &mdash; equity mining, the service lane, and "
        "retention &mdash; and scales up without adding to payroll.",
        cards, disclaimer,
    )


def psi_hero_animation(ap=""):
    """Hero: Build Your Dealership Stack — cycles business types, assembles the
    stack, shows Enterprise $$$ vs PSI $ cost. Loops."""
    return '''<div class="psi" id="psi">
    <div class="psi-pick">
      <div class="psi-pick-t">Choose your business</div>
      <div class="psi-biz" data-b="0">&#127949; Powersports</div>
      <div class="psi-biz" data-b="1">&#128664; Independent auto</div>
      <div class="psi-biz" data-b="2">&#128665; Used vehicles</div>
      <div class="psi-biz" data-b="3">&#128676; Marine</div>
      <div class="psi-biz" data-b="4">&#128679; Utility / equipment</div>
    </div>
    <div class="psi-build">
      <div class="psi-selected" id="psi-selected">Powersports dealer selected</div>
      <div class="psi-stack">
        <div class="psi-item" data-k="0">&#10003; Retention marketing</div>
        <div class="psi-item" data-k="1">&#10003; Facebook advertising</div>
        <div class="psi-item" data-k="2">&#10003; Google advertising</div>
        <div class="psi-item" data-k="3">&#10003; Website platform</div>
        <div class="psi-item" data-k="4">&#10003; VoIP &amp; call tracking</div>
        <div class="psi-item" data-k="5">&#10003; Business intelligence</div>
      </div>
      <div class="psi-cost" id="psi-cost">
        <div class="psi-cost-row"><span>Enterprise solution</span><b class="psi-ent">$$$</b></div>
        <div class="psi-cost-row psi-cost-psi"><span>PSI solution</span><b>$</b></div>
      </div>
    </div>
  <script>
  (function(){
    var root=document.getElementById("psi"); if(!root) return;
    var bizes=[].slice.call(root.querySelectorAll(".psi-biz"));
    var names=["Powersports dealer selected","Independent auto dealer selected","Used-vehicle dealer selected","Marine dealer selected","Utility / equipment dealer selected"];
    var selected=document.getElementById("psi-selected");
    var items=[].slice.call(root.querySelectorAll(".psi-item"));
    var cost=document.getElementById("psi-cost");
    var seen=false, timers=[], bi=0;
    function clr(){ timers.forEach(clearTimeout); timers=[]; }
    function at(ms,fn){ timers.push(setTimeout(fn,ms)); }
    function cycle(){
      clr();
      bizes.forEach(function(b){ b.classList.remove("on"); });
      selected.classList.remove("on"); cost.classList.remove("on");
      items.forEach(function(it){ it.classList.remove("on"); });
      at(500,function(){ bizes[bi].classList.add("on"); selected.textContent=names[bi]; selected.classList.add("on"); });
      items.forEach(function(it,i){ at(1100+i*260,function(){ it.classList.add("on"); }); });
      at(3000,function(){ cost.classList.add("on"); });
      at(5200,function(){ bi=(bi+1)%bizes.length; cycle(); });
    }
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;cycle();}});},{threshold:.3}).observe(root); } else cycle();
  })();
  </script>
</div>'''


def psi_demo(ap=""):
    """Goal-based recommender — 'Choose your goal, see your solution.' PSI acts
    as a consultant, recommending real Vicimus products + expected outcomes."""
    return '''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">One dealer. Multiple growth opportunities.</p>
    <h2 class="h2" style="margin-bottom:8px">Choose your goal. See your solution.</h2>
    <p class="lede">Tell PSI what you're trying to grow and it recommends the right combination of Vicimus products &mdash; and what to expect from them.</p>
  </div>
  <div class="wrap">
    <div class="pgb" id="pgb">
      <div class="pgb-goals-col">
        <button class="pgb-goal2 is-on" data-g="sell">&#128200; Sell more vehicles</button>
        <button class="pgb-goal2" data-g="repeat">&#128260; Increase repeat customers</button>
        <button class="pgb-goal2" data-g="leads">&#128222; Improve lead handling</button>
        <button class="pgb-goal2" data-g="website">&#127760; Upgrade my website</button>
        <button class="pgb-goal2" data-g="performance">&#128202; Understand performance</button>
      </div>
      <div class="pgb-rec">
        <div class="pgb-rec-t">PSI recommends</div>
        <div class="pgb-stack" id="pgb-stack"></div>
        <div class="pgb-out-t">Expected outcomes</div>
        <div class="pgb-outcomes" id="pgb-outcomes"></div>
      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("pgb"); if(!root) return;
    var GOALS={
      sell:{ products:["Bumper Inventory Ads","GloveBox Websites","Calls on Demand"],
        outcomes:["More qualified showroom traffic","Faster lead response","More closed deals"] },
      repeat:{ products:["Bumper Retention","Accessory Accelerator","Odometer VoIP"],
        outcomes:["More service visits","More trade cycles","Higher customer retention","Lower marketing waste"] },
      leads:{ products:["Odometer VoIP","Calls on Demand","Bumper Retention"],
        outcomes:["Fewer missed calls","Every lead followed up","More appointments set"] },
      website:{ products:["GloveBox Websites","Bumper Inventory Ads","Pie"],
        outcomes:["Instant, dealer-controlled updates","Inventory that stays in sync","Faster launches, no developers"] },
      performance:{ products:["Pie","Odometer VoIP","Bumper Retention"],
        outcomes:["One connected view of the store","Department-level visibility","Decisions backed by data"] }
    };
    var stackBox=document.getElementById("pgb-stack"), outBox=document.getElementById("pgb-outcomes");
    function render(g){
      var d=GOALS[g];
      stackBox.innerHTML=""; outBox.innerHTML="";
      d.products.forEach(function(name,i){
        if(i>0){ var plus=document.createElement("div"); plus.className="pgb-plus"; plus.textContent="+"; stackBox.appendChild(plus); }
        var card=document.createElement("div"); card.className="pgb-prod2"; card.textContent=name;
        stackBox.appendChild(card);
        setTimeout(function(){ card.classList.add("in"); }, i*160);
      });
      d.outcomes.forEach(function(txt,i){
        var row=document.createElement("div"); row.className="pgb-outcome"; row.innerHTML="&#10003; "+txt;
        outBox.appendChild(row);
        setTimeout(function(){ row.classList.add("in"); }, 400+i*140);
      });
    }
    root.querySelectorAll(".pgb-goal2").forEach(function(btn){
      btn.addEventListener("click",function(){
        root.querySelectorAll(".pgb-goal2").forEach(function(x){x.classList.remove("is-on");});
        btn.classList.add("is-on"); render(btn.getAttribute("data-g"));
      });
    });
    var seen=false;
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;render("sell");}});},{threshold:.3}).observe(root); } else render("sell");
  })();
  </script>
</section>'''


def psi_comparison():
    """PSI (bundled) vs Multiple Vendors / typical independent stack."""
    rows = [
        ("Marketing automation", ("yes",), ("yes",)),
        ("Inventory advertising", ("yes",), ("yes",)),
        ("Website platform", ("yes",), ("yes",)),
        ("Call tracking", ("yes",), ("partial",)),
        ("Customer retention", ("yes",), ("partial",)),
        ("Business intelligence", ("yes",), ("partial",)),
        ("Single support team", ("yes",), ("no",)),
        ("One vendor relationship", ("yes",), ("no",)),
        ("Connected reporting", ("yes",), ("no",)),
        ("Unified customer data", ("yes",), ("no",)),
        ("Scalable growth platform", ("yes",), ("partial",)),
        ("Built for powersports &amp; independents", ("yes",), ("no",)),
    ]

    def col(idx):
        return [(row[idx + 1][0], row[0], row[idx + 1][1] if len(row[idx + 1]) > 1 else "") for row in rows]

    cards = [
        {"name": "PSI", "badge": "One connected platform", "highlight": True, "items": col(0)},
        {"name": "Multiple Vendors", "badge": "The usual stack", "items": col(1)},
    ]
    disclaimer = ("Illustrative comparison of a single connected platform (PSI) against a typical independent-dealer "
                  "setup stitched together from multiple point vendors, based on Vicimus's understanding of common "
                  "industry realities as of 2026. Every dealer's stack is different; capabilities, integration, and "
                  "support vary by the specific vendors involved.")
    return comparison_section(
        "How it stacks up",
        "Why dealers choose PSI.",
        "The individual tools exist everywhere. What independent and powersports dealers rarely get is all of them "
        "from one vendor &mdash; connected reporting, unified customer data, and a single team &mdash; instead of "
        "juggling six logins and six invoices.",
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
    elif p["slug"] == "accessory-accelerator":
        extra_after_capabilities = accessory_demo(ap)
        extra_after_shots = accessory_comparison()
    elif p["slug"] == "glovebox-websites":
        extra_after_capabilities = glovebox_demo()
        extra_after_shots = glovebox_comparison()
    elif p["slug"] == "odometer-voip":
        extra_after_capabilities = odometer_demo()
        extra_after_shots = odometer_comparison()
    elif p["slug"] == "calls-on-demand":
        extra_after_capabilities = cod_demo()
        extra_after_shots = cod_comparison()
    elif p["slug"] == "powersports-independent":
        extra_after_capabilities = psi_demo(ap)
        extra_after_shots = psi_comparison()
    else:
        extra_after_capabilities = ""
        extra_after_shots = ""

    HERO_DEMOS = {
        "bumper-finance": finance_hero_animation,
        "bumper-retention": retention_hero_animation,
        "bumper-inventory-ads": inventory_hero_animation,
        "pie": pie_hero_animation,
        "accessory-accelerator": accessory_hero_animation,
        "glovebox-websites": glovebox_hero_animation,
        "odometer-voip": odometer_hero_animation,
        "calls-on-demand": cod_hero_animation,
        "powersports-independent": psi_hero_animation,
    }
    if p["slug"] in HERO_DEMOS:
        subhero = f'''<section class="subhero subhero--split subhero--{p['slug']}">
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
    <div class="subhero__demo">{HERO_DEMOS[p["slug"]](ap)}</div>
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
        <div id="bd-sb-summary"></div>
        <form method="post" action="#" id="bd-form">
          <div class="form-row cols-2">
            <div class="field"><label for="bd-first">First name</label><input id="bd-first" name="first_name" type="text" required></div>
            <div class="field"><label for="bd-last">Last name</label><input id="bd-last" name="last_name" type="text" required></div>
          </div>
          <div class="form-row"><div class="field"><label for="bd-email">Work email</label><input id="bd-email" name="email" type="email" required></div></div>
          <div class="form-row"><div class="field"><label for="bd-dealership">Dealership name</label><input id="bd-dealership" name="dealership" type="text" required></div></div>
          <div class="form-row cols-2">
            <div class="field"><label for="bd-market">Market</label><select id="bd-market" name="market"><option>United States</option><option>Canada</option></select></div>
            <div class="field"><label for="bd-role">Role</label><select id="bd-role" name="role"><option>General Manager</option><option>Dealer Principal</option><option>Fixed Operations Director</option><option>Marketing / BDC</option><option>Other</option></select></div>
          </div>
          <div class="form-row"><div class="field"><label for="bd-notes">Anything specific you'd like to see? (optional)</label><textarea id="bd-notes" name="notes"></textarea></div></div>
          <input type="hidden" id="bd-sb-payload" name="solutions_builder" value="">
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
def franchise_hero_animation(ap=""):
    """Franchise Retail hero: 'What are your biggest challenges right now?'
    Six multi-selectable challenge cards; the panel resolves the union of the
    selected challenges into Vicimus products and outcomes, and feeds those
    products to the Solutions Builder alongside the market itself."""
    return '''<div class="fch" id="fch">
    <div class="fch-q">What are your biggest challenges right now? <span class="fch-hint">Pick as many as apply</span></div>
    <div class="fch-cards">
      <button class="fch-card" data-c="retention"><span class="fch-ico">&#128201;</span>Customer retention</button>
      <button class="fch-card" data-c="turn"><span class="fch-ico">&#128663;</span>Inventory turn</button>
      <button class="fch-card" data-c="fixed"><span class="fch-ico">&#128295;</span>Fixed ops growth</button>
      <button class="fch-card" data-c="leads"><span class="fch-ico">&#128222;</span>Lead response</button>
      <button class="fch-card" data-c="visibility"><span class="fch-ico">&#128202;</span>Executive visibility</button>
      <button class="fch-card" data-c="profit"><span class="fch-ico">&#128176;</span>Profitability</button>
    </div>
    <div class="fch-panel">
      <div class="fch-out">
        <div class="fch-step" id="fch-s1">
          <div class="fch-step-t" id="fch-prob-t">Challenge identified</div>
          <div class="fch-body" id="fch-prob"></div>
          <div class="fch-chips" id="fch-chips"></div>
        </div>
        <div class="fch-arrow" id="fch-a1">&darr;</div>
        <div class="fch-step" id="fch-s2">
          <div class="fch-step-t" id="fch-sol-t">Vicimus solution</div>
          <div class="fch-prods" id="fch-prods"></div>
        </div>
        <div class="fch-arrow" id="fch-a2">&darr;</div>
        <div class="fch-step fch-step--pay" id="fch-s3">
          <div class="fch-step-t">Outcome</div>
          <div class="fch-tags" id="fch-outcome"></div>
        </div>
      </div>
    </div>
  <script>
  (function(){
    var root=document.getElementById("fch"); if(!root) return;
    var NAMES={"bumper-retention":"Bumper Retention","bumper-inventory-ads":"Bumper Inventory Ads",
      "pie":"Pie","bumper-finance":"Bumper Finance","accessory-accelerator":"Accessory Accelerator",
      "glovebox-websites":"GloveBox Websites","odometer-voip":"Odometer VoIP","calls-on-demand":"Calls on Demand"};
    var ORDER=["bumper-retention","calls-on-demand","odometer-voip","bumper-inventory-ads",
      "glovebox-websites","accessory-accelerator","bumper-finance","pie"];
    var C={
      retention:{ label:"Customer retention",
        problem:"Customers are returning to market before your dealership knows about it.",
        products:["bumper-retention","calls-on-demand","odometer-voip"],
        tags:["More appointments set","More repeat purchases","Higher lifetime value"] },
      turn:{ label:"Inventory turn",
        problem:"Units age past 60 days while ad spend stays flat across the whole lot.",
        products:["bumper-inventory-ads","glovebox-websites","pie"],
        tags:["Faster inventory turn","Less aged stock","Ad spend that follows the metal"] },
      fixed:{ label:"Fixed ops growth",
        problem:"Service customers drift to independents once the warranty runs out.",
        products:["bumper-retention","accessory-accelerator","odometer-voip"],
        tags:["More RO count","Higher CPRO","Service share you keep"] },
      leads:{ label:"Lead response",
        problem:"Calls ring out and leads go cold before anyone follows up.",
        products:["odometer-voip","calls-on-demand","bumper-retention"],
        tags:["Every call answered","Every lead worked","More appointments set"] },
      visibility:{ label:"Executive visibility",
        problem:"Every department reports differently, so nobody sees the whole store.",
        products:["pie","odometer-voip","bumper-retention"],
        tags:["One connected view","Department-level detail","Decisions backed by data"] },
      profit:{ label:"Profitability",
        problem:"Margin compression squeezes front-end gross on every single deal.",
        products:["bumper-finance","accessory-accelerator","pie"],
        tags:["Higher PVR","More back-end gross","Revenue from existing customers"] }
    };
    var cycle=["retention","turn","fixed","leads","visibility","profit"];
    var cards=[].slice.call(root.querySelectorAll(".fch-card"));
    var probT=document.getElementById("fch-prob-t"), prob=document.getElementById("fch-prob"),
        chips=document.getElementById("fch-chips"), prods=document.getElementById("fch-prods"),
        outc=document.getElementById("fch-outcome");
    var steps=["fch-s1","fch-a1","fch-s2","fch-a2","fch-s3"].map(function(id){return document.getElementById(id);});
    var sel=[], timers=[], ci=0, auto=true, seen=false;
    function clr(){ timers.forEach(clearTimeout); timers=[]; }
    function at(ms,fn){ timers.push(setTimeout(fn,ms)); }

    function unionProducts(){
      var s={};
      sel.forEach(function(k){ C[k].products.forEach(function(p){ s[p]=1; }); });
      return ORDER.filter(function(p){ return s[p]; });
    }
    function unionTags(){
      var out=[], seenT={};
      sel.forEach(function(k){ C[k].tags.forEach(function(t){ if(!seenT[t]){ seenT[t]=1; out.push(t); } }); });
      return out;
    }
    // Exposed so the Solutions Builder hero button carries the recommended
    // products across with the market itself.
    window.SB_HERO_EXTRAS=function(){
      return unionProducts().map(function(p){ return { id:p, type:"products" }; });
    };

    function render(){
      clr();
      steps.forEach(function(s){ s.classList.remove("on"); });
      cards.forEach(function(c){ c.classList.toggle("on", sel.indexOf(c.getAttribute("data-c"))>=0); });

      var multi = sel.length>1;
      probT.textContent = multi ? ("Challenges identified ("+sel.length+")") : "Challenge identified";
      prob.textContent = multi ? "" : (sel.length ? C[sel[0]].problem : "");
      prob.style.display = multi ? "none" : "";
      chips.innerHTML="";
      if(multi){
        sel.forEach(function(k){
          var c=document.createElement("span"); c.className="fch-chip"; c.textContent=C[k].label;
          chips.appendChild(c);
        });
      }

      var plist=unionProducts();
      document.getElementById("fch-sol-t").textContent =
        plist.length>3 ? ("Vicimus solution \u2014 "+plist.length+" products") : "Vicimus solution";
      prods.innerHTML="";
      prods.classList.toggle("fch-prods--dense", plist.length>4);
      plist.slice(0,6).forEach(function(slug){
        var r=document.createElement("div"); r.className="fch-prod";
        r.innerHTML=\'<span class="fch-tick">&#10003;</span>\'+NAMES[slug];
        prods.appendChild(r);
      });

      var tags=unionTags(), cap=4;
      outc.innerHTML="";
      tags.slice(0,cap).forEach(function(t){
        var el=document.createElement("span"); el.className="fch-tag"; el.textContent=t;
        outc.appendChild(el);
      });
      if(tags.length>cap){
        var more=document.createElement("span"); more.className="fch-tag fch-tag--more";
        more.textContent="+"+(tags.length-cap)+" more"; outc.appendChild(more);
      }

      var pchips=[].slice.call(prods.children);
      at(240,function(){ steps[0].classList.add("on"); });
      at(820,function(){ steps[1].classList.add("on"); });
      at(1000,function(){ steps[2].classList.add("on"); });
      pchips.forEach(function(c,i){ at(1080+i*140,function(){ c.classList.add("in"); }); });
      at(1900,function(){ steps[3].classList.add("on"); });
      at(2080,function(){ steps[4].classList.add("on"); });
      if(auto) at(5400,function(){ ci=(ci+1)%cycle.length; sel=[cycle[ci]]; render(); });
      syncBuilder();
    }

    // If the visitor has already added this page to the Solutions Builder,
    // keep the recommended products in step as they change their selection.
    function syncBuilder(){
      if(!(window.SB && window.SB.has && window.SB.has("franchise-retail","markets"))) return;
      unionProducts().forEach(function(p){ window.SB.add(p,"products"); });
    }

    cards.forEach(function(c){
      c.addEventListener("click",function(){
        auto=false;
        var k=c.getAttribute("data-c"), i=sel.indexOf(k);
        if(i>=0){ if(sel.length>1) sel.splice(i,1); }
        else { sel.push(k); }
        render();
      });
    });
    function start(){ sel=[cycle[0]]; render(); }
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;start();}});},{threshold:.25}).observe(root); } else start();
  })();
  </script>
</div>'''


def franchise_challenge_map():
    """The Modern Dealership Challenge Map — departments around a central
    dealership, six live problems, each resolving into a different product.
    Effectively the cross-sell engine for the franchise audience."""
    return '''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">The modern dealership challenge map</p>
    <h2 class="h2" style="margin-bottom:8px">Every dealership problem is connected. So are our solutions.</h2>
    <p class="lede">Pick a problem you recognise and follow it all the way through &mdash; from the moment it shows up in your data to the revenue it puts back on the board.</p>
  </div>
  <div class="wrap">
    <div class="fmap" id="fmap">
      <div class="fmap-left">
        <div class="fmap-diagram">
          <div class="fmap-dept" data-d="sales" style="grid-area:a">Sales</div>
          <div class="fmap-dept" data-d="inventory" style="grid-area:b">Inventory</div>
          <div class="fmap-dept" data-d="marketing" style="grid-area:c">Marketing</div>
          <div class="fmap-hub" id="fmap-hub">Your<br>dealership</div>
          <div class="fmap-dept" data-d="service" style="grid-area:e">Service</div>
          <div class="fmap-dept" data-d="operations" style="grid-area:f">Operations</div>
        </div>
        <div class="fmap-probs">
          <button class="fmap-prob" data-p="aging">&#9888; Aging inventory</button>
          <button class="fmap-prob" data-p="calls">&#9888; Missed calls</button>
          <button class="fmap-prob" data-p="service">&#9888; Lost service customers</button>
          <button class="fmap-prob" data-p="accessory">&#9888; Low accessory penetration</button>
          <button class="fmap-prob" data-p="cpro">&#9888; Declining CPRO</button>
          <button class="fmap-prob" data-p="website">&#9888; Slow website updates</button>
        </div>
      </div>
      <div class="fmap-right">
        <div class="fmap-chain" id="fmap-chain"></div>
      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("fmap"); if(!root) return;
    var P={
      service:{ dept:"service", steps:[
        ["Problem","Customer has not serviced in 10 months."],
        ["Vicimus identifies the opportunity","Lifecycle data flags the lapse before the customer is gone."],
        ["Bumper Retention","product"],
        ["Automated outreach","Personalised service offer by email, SMS, and voicemail."],
        ["Appointment scheduled","Booked straight into the service drive."],
        ["Revenue recovered","payoff"]]},
      aging:{ dept:"inventory", steps:[
        ["Problem","Units are sitting past 60 days on the lot."],
        ["Vicimus identifies the opportunity","Age and turn data surface the units that need help."],
        ["Bumper Inventory Ads","product"],
        ["Automated ad generation","Ads built per unit and weighted toward aged stock."],
        ["Traffic to the vehicle page","Shoppers land on the units you need to move."],
        ["Unit turned","payoff"]]},
      calls:{ dept:"sales", steps:[
        ["Problem","A sales call rang out at 4:50pm and nobody called back."],
        ["Vicimus identifies the opportunity","Call tracking logs the miss and who it belonged to."],
        ["Odometer VoIP + Calls on Demand","product"],
        ["The call gets returned","A trained BDC agent follows up the same day."],
        ["Appointment set","The lead lands back in the sales process."],
        ["Deal saved","payoff"]]},
      accessory:{ dept:"sales", steps:[
        ["Problem","Accessories were never presented at delivery."],
        ["Vicimus identifies the opportunity","The gap shows up in attachment rates by deal."],
        ["Accessory Accelerator","product"],
        ["Accessories presented in the deal","Fitted, priced, and financed into the payment."],
        ["Attachment on the repair order","Parts and installation flow to fixed ops."],
        ["Back-end gross added","payoff"]]},
      cpro:{ dept:"service", steps:[
        ["Problem","Customer-pay per repair order is trending down."],
        ["Vicimus identifies the opportunity","Advisor and opcode gaps surface in the reporting."],
        ["Pie","product"],
        ["Targeted service campaigns","Declined work and due maintenance get worked deliberately."],
        ["Advisors coached on the gaps","Everyone sees the same numbers, weekly."],
        ["CPRO recovers","payoff"]]},
      website:{ dept:"marketing", steps:[
        ["Problem","The OEM incentive changed three days ago and the site still shows the old one."],
        ["Vicimus identifies the opportunity","The offer mismatch is caught before more traffic lands."],
        ["GloveBox Websites","product"],
        ["Your team edits it directly","No ticket, no vendor queue, no developer."],
        ["Offer live across the site","Campaign landing pages stay in step."],
        ["No wasted traffic","payoff"]]}
    };
    var chain=document.getElementById("fmap-chain"), hub=document.getElementById("fmap-hub");
    var depts=[].slice.call(root.querySelectorAll(".fmap-dept"));
    var probs=[].slice.call(root.querySelectorAll(".fmap-prob"));
    var timers=[];
    function clr(){ timers.forEach(clearTimeout); timers=[]; }
    function render(key){
      clr();
      var d=P[key];
      probs.forEach(function(b){ b.classList.toggle("on", b.getAttribute("data-p")===key); });
      depts.forEach(function(x){ x.classList.toggle("on", x.getAttribute("data-d")===d.dept); });
      hub.classList.add("on");
      chain.innerHTML="";
      d.steps.forEach(function(s,i){
        var kind = s[1]==="product" ? "product" : (s[1]==="payoff" ? "payoff" : "plain");
        var el=document.createElement("div");
        el.className="fmap-step fmap-step--"+kind;
        if(kind==="plain"){
          el.innerHTML='<div class="fmap-step-t">'+s[0]+'</div><div class="fmap-step-b">'+s[1]+'</div>';
        } else if(kind==="product"){
          el.innerHTML='<div class="fmap-step-k">Vicimus solution</div><div class="fmap-step-p">'+s[0]+'</div>';
        } else {
          el.innerHTML='<div class="fmap-step-p">'+s[0]+'</div>';
        }
        chain.appendChild(el);
        if(i < d.steps.length-1){
          var a=document.createElement("div"); a.className="fmap-link"; a.innerHTML="&darr;";
          chain.appendChild(a);
        }
        timers.push(setTimeout(function(){ el.classList.add("in"); }, 120+i*300));
      });
      [].slice.call(chain.querySelectorAll(".fmap-link")).forEach(function(a,i){
        timers.push(setTimeout(function(){ a.classList.add("in"); }, 260+i*300));
      });
    }
    probs.forEach(function(b){ b.addEventListener("click",function(){ render(b.getAttribute("data-p")); }); });
    var seen=false;
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;render("service");}});},{threshold:.2}).observe(root); } else render("service");
  })();
  </script>
</section>'''


def franchise_growth_builder():
    """The Dealer Growth Builder — store profile + goals generate a customised
    Vicimus stack. Sliders genuinely change the output (deal volume pulls in
    F&I tooling, database size pulls in BDC capacity), and the whole stack can
    be pushed into the Solutions Builder in one click."""
    return '''<section class="section section--tight">
  <div class="wrap centered">
    <p class="eyebrow" style="color:var(--teal)">The dealer growth builder</p>
    <h2 class="h2" style="margin-bottom:8px">Tell us your store. We&rsquo;ll build the stack.</h2>
    <p class="lede">Set your volume, pick what you&rsquo;re trying to grow, and see exactly which Vicimus products your dealership would run &mdash; and why each one is in there.</p>
  </div>
  <div class="wrap">
    <div class="dgb" id="dgb">
      <div class="dgb-controls">
        <div class="dgb-field">
          <div class="dgb-label">Annual sales <b id="dgb-units-v">150 units</b></div>
          <input class="dgb-range" id="dgb-units" type="range" min="50" max="1200" step="25" value="150">
        </div>
        <div class="dgb-field">
          <div class="dgb-label">Customers in your database <b id="dgb-cust-v">2,000</b></div>
          <input class="dgb-range" id="dgb-cust" type="range" min="500" max="20000" step="250" value="2000">
        </div>
        <div class="dgb-goals-t">What are you trying to grow?</div>
        <div class="dgb-goals">
          <button class="dgb-goal is-on" data-g="marketing">Marketing</button>
          <button class="dgb-goal is-on" data-g="retention">Retention</button>
          <button class="dgb-goal is-on" data-g="advertising">Advertising</button>
          <button class="dgb-goal is-on" data-g="phones">Phone management</button>
          <button class="dgb-goal is-on" data-g="reporting">Reporting</button>
        </div>
      </div>
      <div class="dgb-result">
        <div class="dgb-result-head">
          <div class="dgb-result-t">Your stack</div>
          <div class="dgb-count" id="dgb-count"></div>
        </div>
        <div class="dgb-stack" id="dgb-stack"></div>
        <div class="dgb-empty" id="dgb-empty">Pick at least one goal to generate a stack.</div>
        <div class="dgb-foot">
          <div class="dgb-scale" id="dgb-scale"></div>
          <button class="btn btn-red dgb-add" id="dgb-add" type="button">Add this stack to the Solutions Builder</button>
        </div>
      </div>
    </div>
  </div>
  <script>
  (function(){
    var root=document.getElementById("dgb"); if(!root) return;
    var P={
      "bumper-retention":"Bumper Retention","bumper-inventory-ads":"Bumper Inventory Ads","pie":"Pie",
      "bumper-finance":"Bumper Finance","accessory-accelerator":"Accessory Accelerator",
      "glovebox-websites":"GloveBox Websites","odometer-voip":"Odometer VoIP","calls-on-demand":"Calls on Demand"};
    var ORDER=["glovebox-websites","bumper-inventory-ads","bumper-retention","calls-on-demand",
      "odometer-voip","accessory-accelerator","bumper-finance","pie"];
    var unitsEl=document.getElementById("dgb-units"), custEl=document.getElementById("dgb-cust"),
        unitsV=document.getElementById("dgb-units-v"), custV=document.getElementById("dgb-cust-v"),
        stackEl=document.getElementById("dgb-stack"), countEl=document.getElementById("dgb-count"),
        emptyEl=document.getElementById("dgb-empty"), scaleEl=document.getElementById("dgb-scale"),
        addBtn=document.getElementById("dgb-add");
    function fmt(n){ return String(n).replace(/\\B(?=(\\d{3})+(?!\\d))/g,","); }
    function goals(){
      return [].slice.call(root.querySelectorAll(".dgb-goal.is-on")).map(function(b){return b.getAttribute("data-g");});
    }
    function build(){
      var g=goals(), units=+unitsEl.value, cust=+custEl.value, out={};
      function put(slug,why){ if(!out[slug]) out[slug]={slug:slug,why:why}; }
      if(g.indexOf("marketing")>=0){ put("glovebox-websites","Your storefront and landing pages, editable by your team"); put("bumper-retention","Lifecycle campaigns to the customers you already have"); }
      if(g.indexOf("retention")>=0){ put("bumper-retention","Brings service and trade-cycle customers back on schedule"); put("accessory-accelerator","Adds revenue to deals and repair orders you already write"); }
      if(g.indexOf("advertising")>=0){ put("bumper-inventory-ads","Ads generated per unit and weighted toward aged stock"); }
      if(g.indexOf("phones")>=0){ put("odometer-voip","Every call recorded, routed, and attributed by department"); put("calls-on-demand","Trained BDC agents cover overflow and after-hours"); }
      if(g.indexOf("reporting")>=0){ put("pie","One connected view across sales, service, and marketing"); }
      // Scale signals — the sliders genuinely change the recommendation.
      if(units>=200 && g.length) put("bumper-finance","At "+fmt(units)+" units a year, a modern F&I menu pays for itself");
      if(cust>=6000 && g.indexOf("phones")<0 && g.length) put("calls-on-demand","A "+fmt(cust)+"-customer database needs more outreach capacity than a store can staff");
      var list=ORDER.filter(function(s){return out[s];}).map(function(s){return out[s];});
      stackEl.innerHTML="";
      list.forEach(function(item,i){
        var el=document.createElement("div"); el.className="dgb-prod";
        el.innerHTML=\'<div class="dgb-prod-n">\'+P[item.slug]+\'</div><div class="dgb-prod-w">\'+item.why+\'</div>\';
        stackEl.appendChild(el);
        setTimeout(function(){ el.classList.add("in"); }, 40+i*70);
      });
      emptyEl.style.display = list.length ? "none" : "block";
      countEl.textContent = list.length ? list.length+" products" : "";
      addBtn.style.display = list.length ? "" : "none";
      var tier = units>=600 ? "multi-rooftop scale" : (units>=250 ? "high-volume store" : "single-rooftop store");
      scaleEl.textContent = fmt(units)+" units/yr \u00b7 "+fmt(cust)+" customers \u00b7 "+tier;
      root.setAttribute("data-slugs", list.map(function(x){return x.slug;}).join(","));
      return list;
    }
    function sync(){ unitsV.textContent=fmt(+unitsEl.value)+" units"; custV.textContent=fmt(+custEl.value); build(); }
    unitsEl.addEventListener("input",sync); custEl.addEventListener("input",sync);
    root.querySelectorAll(".dgb-goal").forEach(function(b){
      b.addEventListener("click",function(){ b.classList.toggle("is-on"); build(); });
    });
    addBtn.addEventListener("click",function(){
      if(!(window.SB && window.SB.add)) return;
      (root.getAttribute("data-slugs")||"").split(",").filter(Boolean).forEach(function(s){ window.SB.add(s,"products"); });
      window.SB.add("franchise-retail","markets");
      window.SB.open();
      addBtn.textContent="\u2713 Added to your Solutions Builder";
      setTimeout(function(){ addBtn.textContent="Add this stack to the Solutions Builder"; }, 2600);
    });
    var seen=false;
    if("IntersectionObserver" in window){ new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting&&!seen){seen=true;sync();}});},{threshold:.2}).observe(root); } else sync();
  })();
  </script>
</section>'''


def franchise_comparison():
    """Approach comparison rather than product comparison: Vicimus, a named
    category leader, and the fragmented status quo. Cox marks reflect core
    productized offerings and need team sign-off before this goes public."""
    rows = [
        # (capability,               Vicimus, Cox Automotive, Typical vendor mix)
        ("Customer retention",                     "yes", "yes",     "partial"),
        ("Inventory advertising",                  "yes", "yes",     "yes"),
        ("Business intelligence",                  "yes", "partial", "partial"),
        ("Website platform",                       "yes", "yes",     "yes"),
        ("VoIP &amp; call tracking",               "yes", "partial", "partial"),
        ("Outsourced BDC services",                "yes", "no",      "no"),
        ("Accessory revenue programs",             "yes", "no",      "no"),
        ("F&amp;I retailing tools",                "yes", "yes",     "partial"),
        ("Integrated reporting across solutions",  "yes", "partial", "no"),
        ("Single strategic partner",               "yes", "partial", "no"),
        ("Automotive-specific expertise",          "yes", "yes",     "partial"),
        ("Dedicated performance management",       "yes", "partial", "no"),
    ]
    cards = [
        {"name": "Vicimus", "badge": "One connected partner", "highlight": True,
         "items": [(r[1], r[0]) for r in rows]},
        {"name": "Cox Automotive", "badge": "Enterprise suite",
         "items": [(r[2], r[0]) for r in rows]},
        {"name": "Typical Vendor Mix", "badge": "Assembled piece by piece",
         "items": [(r[3], r[0]) for r in rows]},
    ]
    disclaimer = (
        "Illustrative comparison prepared by Vicimus and current as of 2026. Cox Automotive is a category leader "
        "whose retail brands &mdash; including Dealer.com, VinSolutions, Xtime, and Dealertrack &mdash; are strong in "
        "their own right, and marks here reflect our reading of each vendor&rsquo;s core productized offering rather "
        "than what can be assembled through partners, integrations, or third-party add-ons. &ldquo;Typical vendor "
        "mix&rdquo; describes a stack stitched together from separate point vendors, agencies, website providers, and "
        "software companies; no specific vendor is described, and every dealership&rsquo;s mix differs. The contrast "
        "drawn here is about breadth, integration, and single-point accountability, not the quality of any individual "
        "tool. Product lineups change &mdash; if anything here is out of date, tell us and we&rsquo;ll correct it."
    )
    return comparison_section(
        "Why franchise dealers choose Vicimus",
        "Compare approaches, not features.",
        "Most franchise stores can buy every one of these capabilities somewhere &mdash; from an enterprise suite, or "
        "from a shelf of point vendors. What&rsquo;s rare is getting all of them from a partner that connects the "
        "reporting, knows the retail automotive business, and answers for the result.",
        cards, disclaimer,
    )


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

    # Franchise Retail answers "why Vicimus?" rather than "why this product?" —
    # so it gets an interactive challenge-selector hero, the challenge map, and
    # an approach comparison. Every other audience page keeps Layout A as-is.
    AUD_HERO_DEMOS = {"franchise-retail": franchise_hero_animation}
    # franchise_challenge_map() is still defined above and can be swapped back
    # in here (or added alongside) if the map earns its place again.
    AUD_EXTRA_BEFORE_HELP = {"franchise-retail": franchise_growth_builder}
    AUD_EXTRA_AFTER_HELP = {"franchise-retail": franchise_comparison}
    slug = item["slug"]
    extra_before_help = AUD_EXTRA_BEFORE_HELP[slug]() if slug in AUD_EXTRA_BEFORE_HELP else ""
    extra_after_help = AUD_EXTRA_AFTER_HELP[slug]() if slug in AUD_EXTRA_AFTER_HELP else ""

    if slug in AUD_HERO_DEMOS:
        subhero = f'''<section class="subhero subhero--split subhero--{slug}">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__split">
    <div class="subhero__col">
      <p class="eyebrow">{item['eyebrow']}</p>
      <h1 class="h1">{item['hero_h']}</h1>
      <p class="subhero__lead">{item['hero_p']}</p>
      <div class="subhero__actions">
        <a class="btn btn-yellow" href="{pp}contact.html">Talk to us &rarr;</a>
      </div>
    </div>
    <div class="subhero__demo">{AUD_HERO_DEMOS[slug](ap)}</div>
  </div>
</section>'''
    else:
        subhero = f'''<section class="subhero">
  <img class="subhero__bg" src="{ap}assets/img/hero.jpg" alt="">
  <div class="subhero__inner">
    <p class="eyebrow">{item['eyebrow']}</p>
    <h1 class="h1">{item['hero_h']}</h1>
    <p class="subhero__lead">{item['hero_p']}</p>
    <div class="subhero__actions">
      <a class="btn btn-yellow" href="{pp}contact.html">Talk to us &rarr;</a>
    </div>
  </div>
</section>'''

    html = head(item["seo_title"], item["seo_desc"], ap, lang)
    html += header(pp, ap, lang)
    html += "\n" + subhero + f'''

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

{extra_before_help}

<section class="section section--wash">
  <div class="wrap centered">
    <p class="eyebrow">How we help</p>
    <h2 class="h2">The products that move the needle here.</h2>
    <p class="lede">Each layers onto what you already run &mdash; start with one, add more when you're ready.</p>
  </div>
  <div class="wrap"><div class="helpgrid">{help_html}</div></div>
</section>

{extra_after_help}

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
