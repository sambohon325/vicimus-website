#!/usr/bin/env python3
"""Local preview server for the Vicimus site.

    python3 serve.py            # build once, then serve at http://localhost:8000
    python3 serve.py --no-build # just serve what's already built
    python3 serve.py --port 9000

Open the printed URL in your browser. Edit files in build/ (data.py, shell.py)
or the CSS/homepage directly, re-run the build (python3 build/build.py), and
refresh the page.
"""
import argparse
import http.server
import os
import socketserver
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))


def build():
    print("Building pages…")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "build", "build.py")])
    if r.returncode != 0:
        print("Build failed — serving existing files.", file=sys.stderr)


def serve(port):
    os.chdir(ROOT)
    handler = http.server.SimpleHTTPRequestHandler
    # Avoid "Address already in use" on quick restarts
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"\nServing {ROOT}")
        print(f"  →  http://localhost:{port}/")
        print("Press Ctrl+C to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-build", action="store_true", help="skip the build step")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    if not args.no_build:
        build()
    serve(args.port)
