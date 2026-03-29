#!/usr/bin/env python3
"""Search PDS archives for Mars 2020 Perseverance data - multi-strategy."""
import urllib.request
import urllib.parse
import json
import sys
import os
import re
import hashlib

UA = {"User-Agent": "Mozilla/5.0 (astrobiology-workspace)"}
WORKSPACE = os.path.dirname(os.path.abspath(__file__))

def fetch_json(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    resp = urllib.request.urlopen(req, timeout=timeout)
    return json.loads(resp.read().decode("utf-8"))

def fetch_text(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    resp = urllib.request.urlopen(req, timeout=timeout)
    return resp.read().decode("utf-8", "replace")

def download_file(url, dest, timeout=120):
    req = urllib.request.Request(url, headers=UA)
    resp = urllib.request.urlopen(req, timeout=timeout)
    h = hashlib.sha256()
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
    return h.hexdigest()

# ================================================================
# Strategy 1: PDS Search API with proper URL encoding
# ================================================================
print("=" * 60)
print("Strategy 1: PDS Search API (URL-encoded)")
print("=" * 60)

instruments = {
    "SHERLOC": "mars2020_sherloc",
    "PIXL": "mars2020_pixl",
    "SUPERCAM": "mars2020_supercam",
}

for name, bundle in instruments.items():
    print(f"\n--- {name} ---")
    q = f'ref_lid_collection like "urn:nasa:pds:{bundle}:*spectr*"'
    params = urllib.parse.urlencode({"q": q, "limit": 5})
    search_url = f"https://pds.nasa.gov/api/search/1/products?{params}"
    print(f"  URL: {search_url[:120]}...")
    try:
        data = fetch_json(search_url)
        summary = data.get("summary", {})
        print(f"  Hits (summary): {summary}")
        hits = data.get("data", [])
        print(f"  Data count: {len(hits)}")
        for hit in hits[:3]:
            pid = hit.get("id", "?")
            props = hit.get("properties", {})
            print(f"    ID: {pid[:90]}")
            for k in ["ops:Data_File_Info.ops:file_ref", "pds:File.pds:file_name"]:
                if k in props:
                    print(f"      {k}: {props[k]}")
    except Exception as e:
        print(f"  Error: {e}")

# ================================================================
# Strategy 2: ODE REST - try different query params / instrument IDs
# ================================================================
print("\n" + "=" * 60)
print("Strategy 2: ODE REST API - find valid instrument IDs")
print("=" * 60)

# First: list available M2020 instruments
print("\n--- Listing M2020 instruments via ODE ---")
ode_meta_url = "https://oderest.rsl.wustl.edu/live2/?target=mars&ih=M20&output=JSON&query=instruments"
print(f"  {ode_meta_url[:100]}")
try:
    data = fetch_json(ode_meta_url)
    print(f"  Response keys: {list(data.keys())[:10]}")
    results = data.get("ODEResults", data)
    if isinstance(results, dict):
        for k, v in results.items():
            if isinstance(v, (list, dict)):
                print(f"    {k}: {str(v)[:200]}")
            else:
                print(f"    {k}: {v}")
except Exception as e:
    print(f"  Error: {e}")

# Try several ODE product type / instrument combos
ode_combos = [
    ("M20", "SHERLOC", "RDRSP"),
    ("M20", "SHERLOC", "CDR"),
    ("M20", "SHRLC", "RDR"),
    ("M20", "SHRLC", "CDR"),
    ("M20", "PIXL", "CDR"),
    ("M20", "PIXL", "EDR"),
    ("M20", "SUPERCAM", "CDR"),
    ("M20", "SCAM", "RDR"),
    ("M20", "SCAM", "CDR"),
]

for ih, iid, pt in ode_combos:
    url = (
        f"https://oderest.rsl.wustl.edu/live2/?"
        f"target=mars&ih={ih}&iid={iid}&pt={pt}&output=JSON&limit=2&offset=0"
    )
    try:
        data = fetch_json(url)
        count = data.get("ODEResults", {}).get("Count", 0)
        if int(count) > 0:
            print(f"  HIT: ih={ih} iid={iid} pt={pt} => count={count}")
            products = data["ODEResults"].get("Products", {}).get("Product", [])
            if isinstance(products, dict):
                products = [products]
            for p in products[:1]:
                pid = p.get("Product_id", p.get("pdsid", "?"))
                print(f"    PID: {pid}")
                flinks = p.get("Product_files", {}).get("Product_file", [])
                if isinstance(flinks, dict):
                    flinks = [flinks]
                for fl in flinks[:3]:
                    print(f"      {fl.get('Type','?')}: {fl.get('URL','?')[:100]}")
    except:
        pass

# ================================================================
# Strategy 3: Explore M2020 parent directory at PDS Geosciences
# ================================================================
print("\n" + "=" * 60)
print("Strategy 3: Browse m2020 parent directory at PDS Geosciences")
print("=" * 60)

m2020_base = "https://pds-geosciences.wustl.edu/m2020/"
print(f"\n  Parent: {m2020_base}")
try:
    html = fetch_text(m2020_base, timeout=15)
    links = re.findall(r'href="([^"]+)"', html)
    links = [l for l in links if "mars2020" in l.lower() or "m2020" in l.lower()]
    print(f"  Mars2020 bundles: {len(links)}")
    for l in sorted(links)[:20]:
        print(f"    {l}")
except Exception as e:
    print(f"  Error: {e}")

# Now explore each bundle's subdirectories
for name, bundle in [
    ("SHERLOC", "urn-nasa-pds-mars2020_sherloc"),
    ("PIXL", "urn-nasa-pds-mars2020_pixl"),
    ("SUPERCAM", "urn-nasa-pds-mars2020_supercam"),
]:
    base = f"https://pds-geosciences.wustl.edu/m2020/{bundle}/"
    print(f"\n  {name} bundle root: {base}")
    try:
        html = fetch_text(base, timeout=15)
        # Print raw HTML snippet to understand page structure
        print(f"    HTML length: {len(html)}")
        print(f"    HTML[:500]: {html[:500]}")
        links = re.findall(r'href="([^"]*)"', html)
        links = [l for l in links if l and l != "../" and not l.startswith("?") and not l.startswith("/") and not l.startswith("http")]
        print(f"    Local links: {links[:15]}")
    except Exception as e:
        print(f"    Error: {e}")
