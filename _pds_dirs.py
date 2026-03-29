import urllib.request, re, os, hashlib
UA = {"User-Agent": "Mozilla/5.0"}
base = "https://pds-geosciences.wustl.edu"
WORKSPACE = os.path.dirname(os.path.abspath(__file__))

def get_links(path):
    url = base + path
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    return re.findall(r'HREF="([^"]+)"', html)

def download(url_path, local_path):
    url = base + url_path
    req = urllib.request.Request(url, headers=UA)
    resp = urllib.request.urlopen(req, timeout=120)
    h = hashlib.sha256()
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)
            h.update(chunk)
    sz = os.path.getsize(local_path)
    return h.hexdigest(), sz

downloaded = []

# --- 1. SuperCam: try existing sols shown in listing ---
print("=== SUPERCAM ===")
scam_base = "/m2020/urn-nasa-pds-mars2020_supercam/data_calibrated_spectra/"
# Try a few sols from the listing we saw earlier
for sol in ["00011", "00012", "00013", "00026", "00027"]:
    sol_path = f"{scam_base}sol_{sol}/"
    try:
        links = get_links(sol_path)
        files = [l for l in links if not l.endswith("/") and not l.startswith("?")]
        csv_files = [l for l in files if l.endswith(".csv")]
        print(f"  Sol {sol}: {len(files)} files, {len(csv_files)} CSV")
        if csv_files:
            # Download first 2 CSV files
            for fpath in csv_files[:2]:
                fname = fpath.split("/")[-1]
                local = os.path.join(WORKSPACE, "raw", "mars", "perseverance", "supercam", fname)
                print(f"    Downloading: {fname}")
                sha, sz = download(fpath, local)
                print(f"    => {sz:,} B, sha256={sha[:16]}...")
                downloaded.append(("SUPERCAM", fname, sha, sz, base + fpath))
            break  # got what we need
    except Exception as e:
        print(f"  Sol {sol}: {e}")

# --- 2. PIXL: download CSV/MSA spectral data (not TIF images) ---
print("\n=== PIXL spectral data ===")
pixl_sol_path = "/m2020/urn-nasa-pds-mars2020_pixl/data_processed/sol_00186/"
try:
    links = get_links(pixl_sol_path)
    files = [l for l in links if not l.endswith("/") and not l.startswith("?")]
    spec_files = [l for l in files if l.endswith(".csv") or l.endswith(".msa")]
    print(f"  Sol 00186 spectral files: {len(spec_files)}")
    for fpath in spec_files[:3]:
        fname = fpath.split("/")[-1]
        local = os.path.join(WORKSPACE, "raw", "mars", "perseverance", "pixl", fname)
        if os.path.exists(local):
            print(f"    Already exists: {fname}")
            continue
        print(f"    Downloading: {fname}")
        sha, sz = download(fpath, local)
        print(f"    => {sz:,} B, sha256={sha[:16]}...")
        downloaded.append(("PIXL", fname, sha, sz, base + fpath))
except Exception as e:
    print(f"  Error: {e}")

print(f"\n{'='*60}")
print(f"NEW: {len(downloaded)} additional files downloaded")
for name, fname, sha, sz, url in downloaded:
    print(f"  {name}: {fname} ({sz:,} B) sha256={sha[:16]}...")
