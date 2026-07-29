# -*- coding: utf-8 -*-
"""Shared page shell, now language-aware.

Two different prefixes are threaded through every page:

  pp  (page prefix)  -- reaches the current LANGUAGE's root.
                       "" for root pages, "../" for /products/ pages.
                       Identical across languages, because each language
                       tree (/, /es/, /fr/) has the same internal shape.
  ap  (asset prefix) -- reaches the TRUE site root, where /assets lives.
                       For English == pp. For es/fr == "../" + pp,
                       since those pages sit one folder deeper.

`page` is the path within a language tree (e.g. "products/pie.html")
and is the same in every language; the picker swaps only the language
prefix in front of it.
"""

LOGO_SVG_DARK = '''<svg height="20" viewBox="0 0 311.029 42.361" xmlns="http://www.w3.org/2000/svg">
<path d="M10.056,0v42.36L31.774,0Z" transform="translate(11.664)" fill="#fbcf09"/><path d="M31.774,0,10.056,42.361H31.774Z" transform="translate(11.664)" fill="#ee3c25"/>
<path d="M0,0l21.718,42.36V0Z" fill="#3fbcc4"/><path d="M0,0v42.36H21.72Z" fill="#2b68ab"/>
<path d="M115.567,28.894a1.736,1.736,0,0,1-1.734-1.734V13.8L106.9,27.65a1.732,1.732,0,0,1-3.1,0L96.858,13.8V27.16a1.734,1.734,0,0,1-3.469,0V6.47a1.734,1.734,0,0,1,3.285-.775L105.344,23l8.672-17.307a1.734,1.734,0,0,1,3.285.775V27.16a1.736,1.736,0,0,1-1.734,1.734" transform="translate(108.324 5.494)" fill="#111"/>
<path d="M40.93,28.608h-.017a1.735,1.735,0,0,1-1.534-.957L29.158,7.246a1.733,1.733,0,1,1,3.1-1.553l8.711,17.387,9.182-17.42a1.734,1.734,0,0,1,3.067,1.618l-10.754,20.4a1.732,1.732,0,0,1-1.534.927" transform="translate(33.607 5.493)" fill="#111"/>
<path d="M51.675,29.178a1.736,1.736,0,0,1-1.734-1.734V6.468a1.734,1.734,0,0,1,3.469,0V27.443a1.736,1.736,0,0,1-1.734,1.734" transform="translate(57.928 5.493)" fill="#111"/>
<path d="M83.545,28.895a1.736,1.736,0,0,1-1.734-1.734V6.47a1.734,1.734,0,0,1,3.469,0V27.16a1.736,1.736,0,0,1-1.734,1.734" transform="translate(94.895 5.493)" fill="#111"/>
<path d="M83.354,28.895H63.938A1.736,1.736,0,0,1,62.2,27.16V6.47a1.736,1.736,0,0,1,1.734-1.734H83.354a1.734,1.734,0,1,1,0,3.469H65.673V25.426H83.354a1.734,1.734,0,1,1,0,3.469" transform="translate(72.152 5.493)" fill="#111"/>
<path d="M144.9,28.895H134.416a1.734,1.734,0,1,1,0-3.469h8.754V6.47A1.736,1.736,0,0,1,144.9,4.736h10.489a1.734,1.734,0,0,1,0,3.469h-8.754V27.16a1.736,1.736,0,0,1-1.734,1.734" transform="translate(153.901 5.493)" fill="#111"/>
<path d="M136.411,28.895H115.433A1.736,1.736,0,0,1,113.7,27.16V6.47a1.734,1.734,0,0,1,3.469,0V25.426h17.508V6.47a1.734,1.734,0,1,1,3.469,0V27.16a1.736,1.736,0,0,1-1.734,1.734" transform="translate(131.882 5.493)" fill="#111"/>
</svg>'''

LOGO_SVG_LIGHT = LOGO_SVG_DARK.replace('height="20"', 'height="16"').replace('fill="#111"', 'fill="#fff"')


# The region -> language dropdown. Shared verbatim by every page
# (generated pages via header(); the homepage embeds the same markup).
LANG_PICKER = '''<div class="langpick" id="langpick">
  <button class="langpick__btn" type="button" onclick="toggleLangMenu()" aria-haspopup="true" aria-label="Choose region and language">
    <span id="lp-region">US</span><span class="langpick__dot">&middot;</span><span id="lp-lang">EN</span><span class="langpick__chev">&#9662;</span>
  </button>
  <div class="langpick__menu" id="lp-menu" role="menu">
    <div class="langpick__grp">United States</div>
    <button type="button" data-region="us" data-lang="en" onclick="setLang('us','en')">English</button>
    <button type="button" data-region="us" data-lang="es" onclick="setLang('us','es')">Espa&ntilde;ol</button>
    <div class="langpick__grp">Canada</div>
    <button type="button" data-region="ca" data-lang="en" onclick="setLang('ca','en')">English</button>
    <button type="button" data-region="ca" data-lang="fr" onclick="setLang('ca','fr')">Fran&ccedil;ais</button>
    <button type="button" data-region="ca" data-lang="es" onclick="setLang('ca','es')">Espa&ntilde;ol</button>
  </div>
</div>'''


def head(title, desc, ap="", lang="en"):
    return f'''<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:ital,wght@0,400;0,500;0,600;0,700;1,600;1,700;1,800&family=Barlow:ital,wght@0,400;0,500;0,600;0,700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{ap}assets/css/site.css">
</head>
<body>'''


def header(pp="", ap="", lang="en"):
    return f'''
<header class="site-header">
  <div class="site-header__inner">
    <div class="header__left">
      <button class="hamburger" id="hamburger" aria-label="Open menu" aria-expanded="false" onclick="toggleMenu()">
        <span></span><span></span><span></span>
      </button>
    </div>
    <a class="wordmark" href="{pp}index.html" aria-label="Vicimus home">{LOGO_SVG_DARK}</a>
    <div class="util">
      {LANG_PICKER}
      <span class="bar hide-sm" aria-hidden="true"></span>
      <a class="hide-sm" href="tel:+18883016178">888-301-6178</a>
      <span class="bar hide-sm" aria-hidden="true"></span>
      <a class="hide-sm" href="{pp}contact.html">Support</a>
      <span class="bar hide-sm" aria-hidden="true"></span>
      <a class="hide-sm" href="https://bumper.vicimus.com/login">Login</a>
      <a class="btn btn-red" href="{pp}book-a-demo.html">Book a demo</a>
    </div>
  </div>

  <div class="mega" id="mega">
    <div class="mega__grid">
      <div class="mega__col">
        <h4>Solutions</h4>
        <a href="{pp}solutions/retention-lifecycle.html">Retention &amp; Lifecycle</a>
        <a href="{pp}solutions/inventory-advertising.html">Inventory Advertising</a>
        <a href="{pp}solutions/lead-management.html">Lead Management &amp; Websites</a>
        <a href="{pp}solutions/call-tracking.html">Call Tracking &amp; VoIP</a>
      </div>
      <div class="mega__col t">
        <h4>Products</h4>
        <a class="sub" href="{pp}products/bumper-retention.html">Bumper Retention</a>
        <a class="sub" href="{pp}products/bumper-inventory-ads.html">Bumper Inventory Ads</a>
        <a class="sub" href="{pp}products/pie.html">Pie</a>
        <a class="sub" href="{pp}products/bumper-finance.html">Bumper Finance</a>
        <a class="sub" href="{pp}products/accessory-accelerator.html">Accessory Accelerator</a>
        <a class="sub" href="{pp}products/glovebox-websites.html">GloveBox Websites</a>
        <a class="sub" href="{pp}products/odometer-voip.html">Odometer VoIP</a>
        <a class="sub" href="{pp}products/calls-on-demand.html">Calls on Demand</a>
        <a class="sub" href="{pp}products/powersports-independent.html">Powersports Independent (PSI)</a>
      </div>
      <div class="mega__col y">
        <h4>Markets Served</h4>
        <a href="{pp}markets/franchise-retail.html">Franchise Retail</a>
        <a href="{pp}markets/independent-retail.html">Independent Retail</a>
        <a href="{pp}markets/bhph.html">Buy Here Pay Here</a>
        <a href="{pp}markets/enterprise.html">Enterprise &amp; Groups</a>
      </div>
      <div class="mega__col r">
        <h4>Company</h4>
        <a href="{pp}about.html">About Us</a>
        <a href="{pp}team.html">Team</a>
        <a href="{pp}updates.html">Updates</a>
        <a href="{pp}careers.html">Careers</a>
        <a href="{pp}contact.html">Contact</a>
      </div>
    </div>
  </div>
</header>'''


def footer(pp="", ap="", lang="en", page="index.html"):
    return f'''
<div class="divider" role="presentation"></div>
<footer class="site-footer">
  <div class="wrap">
    <div class="site-footer__grid">
      <div>
        {LOGO_SVG_LIGHT}
        <p class="footer__note">Dealer retention and lifecycle marketing. Ontario, Canada. Serving US &amp; CA markets.</p>
      </div>
      <div>
        <h4>Products</h4>
        <ul>
          <li><a href="{pp}products/bumper-retention.html">Bumper Retention</a></li>
          <li><a href="{pp}products/bumper-inventory-ads.html">Bumper Inventory Ads</a></li>
          <li><a href="{pp}products/pie.html">Pie</a></li>
          <li><a href="{pp}products/glovebox-websites.html">GloveBox Websites</a></li>
          <li><a href="{pp}products/odometer-voip.html">Odometer VoIP</a></li>
          <li><a href="{pp}products/powersports-independent.html">Powersports Independent (PSI)</a></li>
        </ul>
      </div>
      <div>
        <h4>Company</h4>
        <ul>
          <li><a href="{pp}about.html">About Us</a></li>
          <li><a href="{pp}team.html">Team</a></li>
          <li><a href="{pp}careers.html">Careers</a></li>
          <li><a href="{pp}updates.html">Updates</a></li>
        </ul>
      </div>
      <div>
        <h4>Contact</h4>
        <ul>
          <li><a href="tel:+18883016178">888-301-6178</a></li>
          <li><a href="mailto:sales@vicimus.com">sales@vicimus.com</a></li>
          <li><a href="https://bumper.vicimus.com/login">Login</a></li>
          <li><a href="{pp}book-a-demo.html">Book a Demo</a></li>
        </ul>
      </div>
    </div>
    <div class="footer__base">
      <span>&copy; 2026 Vicimus Inc. All rights reserved.</span>
      <nav>
        <a href="#privacy">Privacy Policy</a>
        <a href="#terms">Terms of Service</a>
        <a href="#casl">CASL Compliance</a>
      </nav>
    </div>
  </div>
</footer>

<script>
function toggleMenu(){{
  var m=document.getElementById('mega'), h=document.getElementById('hamburger');
  var open=!m.classList.contains('is-open');
  m.classList.toggle('is-open',open); h.classList.toggle('is-open',open);
  h.setAttribute('aria-expanded',open);
}}
document.querySelectorAll('#mega a').forEach(function(a){{
  a.addEventListener('click',function(){{
    document.getElementById('mega').classList.remove('is-open');
    document.getElementById('hamburger').classList.remove('is-open');
  }});
}});
</script>
<script>window.SITE={{root:"{ap}",page:"{page}",lang:"{lang}"}};</script>
<script src="{ap}assets/js/i18n.js"></script>
<script src="{ap}assets/js/sb-catalog.js"></script>
<script src="{ap}assets/js/vendor/jspdf.umd.min.js"></script>
<script src="{ap}assets/js/solutions-builder.js"></script>
</body>
</html>'''
