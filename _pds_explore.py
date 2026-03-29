#!/usr/bin/env python3
"""PDS Mars 2020 archive explorer - find real downloadable files."""
import urllib.request
import re
import sys
import os

UA = {"User-Agent": "Mozilla/5.0 (astrobiology-workspace)"}

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "replace")

def list_links(html, extensions=None):
    links = re.findall(r'href="([^"]+)"', html)
    links = [l for l in links if l != "../" and not l.startswith("?") and not l.startswith("/")]
    if extensions:
        links = [l for l in links if any(l.lower().endswith(e) for e in extensions)]
    return links

def list_dirs(html):
    links = re.findall(r'href="([^"]+/)"', html)
    return [l for l in links if l != "../" and not l.startswith("?") and not l.startswith("/")]

# ---- SHERLOC ----
print("=" * 60)
print("SHERLOC - exploring data directories")
print("=" * 60)
sherloc_base = "https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_sherloc/"
try:
    html = fetch(sherloc_base)
    dirs = list_dirs(html)
    print(f"Top-level dirs: {dirs}")
    # Look for data directories
    data_dirs = [d for d in dirs if "data" in d.lower() or "spectr" in d.lower()]
    for dd in data_dirs[:5]:
        print(f"\n  Exploring {dd}...")
        try:
            h2 = fetch(sherloc_base + dd)
            subdirs = list_dirs(h2)
            print(f"    Subdirs: {subdirs[:10]}")
            # If there are sol directories, find 0648 or nearby
            sol_dirs = [s for s in subdirs if "06" in s or "sol" in s.lower()]
            if sol_dirs:
                print(f"    Sol-like dirs: {sol_dirs[:5]}")
        except Exception as e:
            print(f"    Error: {e}")
except Exception as e:
    print(f"Error: {e}")

# ---- PIXL ----
print("\n" + "=" * 60)
print("PIXL - exploring data directories")
print("=" * 60)
pixl_base = "https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_pixl/"
try:
    html = fetch(pixl_base)
    dirs = list_dirs(html)
    print(f"Top-level dirs: {dirs}")
    data_dirs = [d for d in dirs if "data" in d.lower()]
    for dd in data_dirs[:5]:
        print(f"\n  Exploring {dd}...")
        try:
            h2 = fetch(pixl_base + dd)
            subdirs = list_dirs(h2)
            print(f"    Subdirs: {subdirs[:10]}")
        except Exception as e:
            print(f"    Error: {e}")
except Exception as e:
    print(f"Error: {e}")

# ---- SuperCam ----
print("\n" + "=" * 60)
print("SUPERCAM - exploring data directories")
print("=" * 60)
scam_base = "https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_supercam/"
try:
    html = fetch(scam_base)
    dirs = list_dirs(html)
    print(f"Top-level dirs: {dirs}")
    data_dirs = [d for d in dirs if "data" in d.lower() or "calib" in d.lower()]
    for dd in data_dirs[:5]:
        print(f"\n  Exploring {dd}...")
        try:
            h2 = fetch(scam_base + dd)
            subdirs = list_dirs(h2)
            print(f"    Subdirs: {subdirs[:10]}")
        except Exception as e:
            print(f"    Error: {e}")
except Exception as e:
    print(f"Error: {e}")
