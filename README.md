# Vicimus — 2026 Website

Static marketing site for Vicimus. No framework, no build dependencies beyond
Python 3 (standard library only). The homepage is hand-authored; the product
and company pages are generated from a small template + data file so shared
markup (nav, footer, styling) lives in exactly one place.

---

## Quick start

```bash
# Build the interior pages, then preview at http://localhost:8000
python3 serve.py
```

Then open <http://localhost:8000/> and click around. Edit a file, re-run the
build (or just `python3 serve.py` again), and refresh.

To build without serving:

```bash
./build.sh          # or: python3 build/build.py
```

---

## Repo structure

```
.
├── index.html                  ← homepage (hand-authored: the calculator hero)
├── products/                   ← GENERATED — do not edit by hand
│   ├── index.html
│   ├── bumper-retention.html
│   ├── bumper-inventory-ads.html
│   ├── bumper-bi.html
│   ├── bumper-finance.html
│   ├── accessory-accelerator.html
│   ├── glovebox-websites.html
│   ├── odometer-voip.html
│   ├── calls-on-demand.html
│   └── powersports-independent.html
├── why-vicimus.html            ← GENERATED
├── contact.html                ← GENERATED
├── book-a-demo.html            ← GENERATED
├── careers.html                ← GENERATED
├── updates.html                ← GENERATED
│
├── build/                      ← the generator (SOURCE — edit these)
│   ├── data.py                 ← all product copy + testimonials
│   ├── shell.py                ← shared <head>, header/nav, footer
│   └── build.py                ← renders every interior page
│
├── assets/
│   ├── css/site.css            ← the ONE stylesheet, shared by every page
│   ├── img/                    ← photography (hero, category tiles, devices)
│   └── logos/                  ← official product logo SVGs
│
├── serve.py                    ← local preview (build + http server)
├── build.sh                    ← one-line build wrapper
└── .github/workflows/deploy.yml← auto-deploy to GitHub Pages on push
```

---

## How to edit things

**Change product copy** (headline, description, the four feature cards, the
"what sets us apart" band): edit `build/data.py`. Each product is one dictionary.
Then run `./build.sh`.

**Change the nav, header, or footer** (links, phone number, menu columns):
edit `build/shell.py` — it's used by every generated page. The homepage
(`index.html`) has its own copy of the header/footer near the top and bottom,
so change it there too if you touch nav on the homepage.

**Change styling / colours / fonts:** edit `assets/css/site.css`. The brand
palette lives in the `:root { … }` block at the very top. Every page — homepage
included — links to this one file, so a change here updates the whole site.

**Change the homepage hero / calculator:** edit `index.html` directly. The
interactive step logic (product picker, ROI math, dealership-intelligence panel)
is in the `<script>` block at the bottom of that file.

**Add a whole new product:** add a dictionary to the `PRODUCTS` list in
`build/data.py`, drop its logo SVG in `assets/logos/`, and run `./build.sh`.
It automatically appears in the products index and the "related products" grids.
(To add it to the nav menu, also add a line in `build/shell.py`.)

> After any change to `build/`, always re-run `./build.sh` before committing —
> the generated `.html` files are what actually ship.

---

## Deploying to GitHub Pages

1. Push this repo to GitHub.
2. In the repo, go to **Settings → Pages → Build and deployment → Source**,
   and choose **GitHub Actions**.
3. That's it. The included workflow (`.github/workflows/deploy.yml`) rebuilds
   the interior pages and publishes the site on every push to `main`. Your live
   URL appears in the Actions run and under Settings → Pages.

If you'd rather skip Actions entirely, set Pages to **Deploy from a branch →
main → / (root)**. The committed `.html` files serve as-is; just remember to run
`./build.sh` locally before pushing so the generated pages are up to date.

---

## Solutions Builder (pull-out tray + PDF)

A pull-out tray, present on every content page, lets visitors assemble a
tailored brief:

- **Add blocks** — drag any product card into the tray (desktop) or tap the
  **+** on it (works everywhere). Product, solution, and market pages also get
  an "Add to Solutions Builder" button in their hero. Selections persist across
  page navigation (localStorage) so people can browse and collect as they go.
- **Rule-based tailoring** (no API, no backend) — the tray infers the visitor's
  market, recommends complementary products, and estimates a *directional*
  annual ROI. The logic lives in `assets/js/solutions-builder.js`
  (`COMPLEMENTS`, `IMPLIES`, and the `roi()` engine); the ROI figures come from
  `SB_ROI` in `build/build.py`, surfaced through the generated
  `assets/js/sb-catalog.js`.
- **PDF** — builds a branded, printable brief in the browser via a vendored
  copy of jsPDF (`assets/js/vendor/jspdf.umd.min.js` — no CDN dependency, so it
  works on locked-down dealership networks). Cover, selections, recommendations,
  an ROI table, and next steps.
- **Email** — "Email PDF" downloads the brief and opens the visitor's mail app
  with a pre-filled message. Browsers can't auto-attach a file to a `mailto:`
  link, so the visitor attaches the just-downloaded PDF themselves (one drag).

**Desktop vs mobile.** Desktop shows a right-edge tab and a side panel (the page
stays interactive so you can drag into it). Mobile shows a floating button and a
bottom sheet, with tap-to-add instead of drag.

**Editing what it recommends / estimates.** Recommendation rules and ROI hints
are the two knobs: `COMPLEMENTS` / `IMPLIES` in `solutions-builder.js` for what
gets recommended, and `SB_ROI` in `build/build.py` for the dollar figures. After
changing `SB_ROI`, re-run `build/build.py` to regenerate the catalog.

> The ROI numbers are directional and clearly labeled as such in both the tray
> and the PDF. Have the team confirm the per-unit and savings figures before
> this is customer-facing. Fully automatic emailing and any AI-written
> tailoring would need the backend move (Netlify/Vercel + a serverless
> function) — the same requirement as the contact forms and the homepage
> intelligence panel.

---

## Page types (four layouts)

The site uses four distinct layouts, all generated from `build/` in the
homepage's look and feel:

1. **Solutions & Markets Served** (`solutions/*.html`, `markets/*.html`) —
   problem-first. Each speaks to one audience's struggles, shows the products
   that help, testimonials, and a CTA to the contact page. There is **one**
   contact form, not one per page. Edit content in `SOLUTIONS` / `MARKETS` in
   `build/data.py`.
2. **Product pages** (`products/*.html`) — what it is, features, screenshots,
   related products, CTA. Screenshot frames are placeholders; drop real images
   in `assets/img/screens/` and reference them from the product's data.
3. **About & Team** (`about.html`, `team.html`) — company story, values,
   timeline, and team. Team profiles are placeholders (initials avatars) — swap
   in real names, roles, and photos in `LEADERSHIP` / `TEAM_DEPARTMENTS`.
4. **Blog** (`updates.html`, `post.html`) — see below.

## Blog + editor

The blog is data-driven and needs no backend. Posts live in
`assets/posts.json`. `updates.html` renders the card index and `post.html`
renders a single post (via `post.html?slug=…`), both client-side.

**To write a post**, open `admin.html` (an internal editor — served locally via
`serve.py`, or you can open the live URL). It loads the current posts, lets you
add / edit / delete, and gives you an updated `posts.json` to **Download** (or
Copy). Then:

```
1. Replace assets/posts.json in the repo with the downloaded file
2. git add -A && git commit -m "new post" && git push
```

The live blog updates on the next deploy. Post bodies support light Markdown
(`##`/`###` headings, `**bold**`, `- lists`, `[links](url)`, blank-line
paragraphs). `admin.html` is marked `noindex` and is just a tool — it isn't
linked from the public nav.

> Because there's no server, "publish" is a git commit — that's the trade-off
> for staying fully static on GitHub Pages. If you later move to Netlify, this
> can be upgraded to a real login-and-publish admin without changing the rest
> of the site.

---

## Languages (English / Spanish / French)

The site is trilingual. Each language is a full copy of the site in its own
folder:

```
/            English  (default)
/es/         Spanish
/fr/         French
```

The nav has a **region → language picker**: United States (English, Español)
and Canada (English, Français, Español). Choosing one routes to the same page
in that language and remembers the choice. Region currently affects language
only — it does not fork the copy — except the English homepage, which still
swaps its hero headline between the US and Canada messaging.

**How the translation works.** `build/build.py` generates all three trees. The
`/es` and `/fr` trees start as English copies with correct paths and language
wiring, so navigation works immediately. `translate.py` then replaces the
visible text in those trees with Spanish / French via Google Cloud Translation,
leaving markup, brand names, phone numbers, and emails (anything marked
`translate="no"`) untouched.

**To produce the translations (runs on your machine, needs a Google key):**

```powershell
# one-time setup
pip install requests beautifulsoup4
$env:GOOGLE_TRANSLATE_API_KEY = "your-key-here"   # from Google Cloud

# each time content changes
python build/build.py     # regenerate English + fresh es/fr copies
python translate.py       # translate the es/fr copies in place
```

Because `build.py` rewrites `/es` and `/fr` from English first, re-running both
keeps translations current — they never drift out of date. A small
`.translate-cache.json` avoids re-paying for unchanged strings.

> **Machine translation needs a human check before launch.** Spanish and
> especially Quebec French (legally sensitive under Bill 96) will mistranslate
> industry terms — "repair order", "F&I", "fixed ops", "conquest". Have native
> speakers review. Brand/product names are already protected with
> `translate="no"`; add that attribute to anything else that must stay verbatim.

> **Note on JS-embedded text.** The homepage's hero copy is set by JavaScript,
> so it isn't caught by the HTML translation pass. The static content on every
> page translates fine; the homepage's dynamic hero strings would need handling
> separately if you want them localized too.

---

## Notes / to-do before go-live

- **Forms** post to `#` — wire them to your CRM or a form handler (e.g. HubSpot,
  Netlify Forms, or a serverless endpoint).
- **Dealership Intelligence panel** on the homepage calls the Anthropic API from
  the browser. That needs a small server-side proxy in production so no API key
  is exposed. See the `analyzeDealer()` function in `index.html`.
- **Calls on Demand** has no dedicated logo in the asset pack yet — it currently
  reuses a neutral mark. Drop a real SVG in `assets/logos/` and point
  `data.py` at it.
- **Careers listings** and **Updates posts** are realistic placeholders.
- Verify the ROI percentages and stat citations with the team; they're labeled
  as directional estimates, not guarantees.
```
