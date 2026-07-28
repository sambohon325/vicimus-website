#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Translate the /es and /fr page trees in place, using Google Cloud Translation.

WHAT IT DOES
    build.py generates /es and /fr as English copies with correct paths and
    language wiring. This script walks those trees and replaces the visible
    text with Spanish / French via the Google Cloud Translation API — while
    leaving tags, attributes, scripts, styles, and any element marked
    translate="no" (brand and product names, phone numbers, emails) untouched.

WHY IT RUNS ON YOUR MACHINE, NOT IN THE BUILD
    It needs a Google Cloud API key and network access. Keep the key out of the
    repo. The recommended flow:

        1.  Set up Google Cloud Translation (v2 is simplest):
            https://cloud.google.com/translate/docs/setup
        2.  Create an API key, then in PowerShell:
                $env:GOOGLE_TRANSLATE_API_KEY = "your-key-here"
        3.  pip install requests beautifulsoup4
        4.  python build/build.py       # regenerate English + fresh es/fr copies
            python translate.py         # translate the es/fr copies in place

    Re-run both whenever content changes. Because build.py rewrites /es and /fr
    from English first, every run re-translates from the current source, so the
    translations never drift out of date.

NOTES
    * Uses the Google Cloud Translation v2 REST endpoint with format=html so
      markup is preserved. Text inside <script>, <style>, and any element with
      translate="no" or class="notranslate" is left alone.
    * A tiny on-disk cache (.translate-cache.json) avoids re-paying for strings
      that haven't changed between runs.
    * This is a first-pass machine translation. Have a native Spanish and a
      Quebec-French speaker review before anything customer-facing — industry
      terms (repair order, F&I, fixed ops) and Quebec French (Bill 96) need a
      human eye. Corrections can live in a future overrides file.
"""
import json
import os
import sys

try:
    import requests
except ImportError:
    sys.exit("Missing dependency. Run:  pip install requests beautifulsoup4")

try:
    from bs4 import BeautifulSoup, NavigableString, Comment
except ImportError:
    sys.exit("Missing dependency. Run:  pip install requests beautifulsoup4")

ROOT = os.path.dirname(os.path.abspath(__file__))
API_KEY = os.environ.get("GOOGLE_TRANSLATE_API_KEY", "").strip()
ENDPOINT = "https://translation.googleapis.com/language/translate/v2"
CACHE_PATH = os.path.join(ROOT, ".translate-cache.json")

# Tags whose text must never be translated.
SKIP_PARENTS = {"script", "style", "code", "pre"}

LANG_DIRS = {"es": "es", "fr": "fr"}


def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            return json.load(open(CACHE_PATH, encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_cache(cache):
    json.dump(cache, open(CACHE_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=0)


def in_no_translate(node):
    """True if this text node sits inside a skip tag or a translate=no element."""
    for parent in node.parents:
        name = getattr(parent, "name", None)
        if name in SKIP_PARENTS:
            return True
        attrs = getattr(parent, "attrs", {}) or {}
        if attrs.get("translate") == "no":
            return True
        cls = attrs.get("class") or []
        if "notranslate" in cls:
            return True
    return False


def collect_strings(soup):
    """Return the list of translatable text nodes (non-empty, not skipped)."""
    nodes = []
    for text in soup.find_all(string=True):
        if isinstance(text, Comment):
            continue
        if not text.strip():
            continue
        if in_no_translate(text):
            continue
        nodes.append(text)
    return nodes


def google_translate(texts, target, cache):
    """Translate a list of plain strings to `target`, using cache where possible."""
    out = [None] * len(texts)
    pending, pending_idx = [], []
    for i, t in enumerate(texts):
        key = f"{target}\x00{t}"
        if key in cache:
            out[i] = cache[key]
        else:
            pending.append(t)
            pending_idx.append(i)

    # Google allows batching; send in chunks of 100 segments.
    for start in range(0, len(pending), 100):
        chunk = pending[start:start + 100]
        resp = requests.post(
            ENDPOINT,
            params={"key": API_KEY},
            data={"q": chunk, "target": target, "format": "text", "source": "en"},
            timeout=60,
        )
        if resp.status_code != 200:
            sys.exit(f"Google API error {resp.status_code}: {resp.text[:300]}")
        results = resp.json()["data"]["translations"]
        for j, r in enumerate(results):
            idx = pending_idx[start + j]
            val = r["translatedText"]
            out[idx] = val
            cache[f"{target}\x00{chunk[j]}"] = val
    return out


def translate_file(path, target, cache):
    html = open(path, encoding="utf-8").read()
    soup = BeautifulSoup(html, "html.parser")
    nodes = collect_strings(soup)
    if not nodes:
        return 0
    originals = [str(n) for n in nodes]
    translated = google_translate(originals, target, cache)
    for node, new in zip(nodes, translated):
        # Preserve leading/trailing whitespace of the original node.
        lead = new_lead = ""
        orig = str(node)
        lstrip = orig[: len(orig) - len(orig.lstrip())]
        rstrip = orig[len(orig.rstrip()):]
        node.replace_with(NavigableString(lstrip + new.strip() + rstrip))
    open(path, "w", encoding="utf-8").write(str(soup))
    return len(nodes)


def main():
    if not API_KEY:
        sys.exit(
            "No API key found.\n"
            "Set one first, e.g. in PowerShell:\n"
            '    $env:GOOGLE_TRANSLATE_API_KEY = "your-key-here"\n'
        )
    cache = load_cache()
    total_files = 0
    total_nodes = 0
    for lang, folder in LANG_DIRS.items():
        base = os.path.join(ROOT, folder)
        if not os.path.isdir(base):
            print(f"  (no {folder}/ tree yet — run build/build.py first)")
            continue
        for dirpath, _dirs, files in os.walk(base):
            for fn in files:
                if not fn.endswith(".html"):
                    continue
                path = os.path.join(dirpath, fn)
                n = translate_file(path, lang, cache)
                total_files += 1
                total_nodes += n
                print(f"  {lang}: {os.path.relpath(path, ROOT)}  ({n} segments)")
        save_cache(cache)
    print(f"\nTranslated {total_nodes} text segments across {total_files} files.")
    print("Review with native Spanish and Quebec-French speakers before launch.")


if __name__ == "__main__":
    main()
