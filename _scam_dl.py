import urllib.request, re, os, hashlib
UA = {"User-Agent": "Mozilla/5.0"}
base = "https://pds-geosciences.wustl.edu"
WS = r"c:\Users\Hites\Desktop\New folder"

def get_links(path):
    url = base + path
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=30).read().decode()
    return re.findall(r'HREF="([^"]+)"', html)

def dl(url_path, local_path):
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
    return h.hexdigest(), os.path.getsize(local_path)

scam_base = "/m2020/urn-nasa-pds-mars2020_supercam/data_calibrated_spectra/"
for sol in ["00027", "00030", "00031", "00034", "00035"]:
    sol_path = f"{scam_base}sol_{sol}/"
    try:
        links = get_links(sol_path)
        files = [l for l in links if not l.endswith("/") and not l.startswith("?")]
        exts = set(l.rsplit(".", 1)[-1] for l in files if "." in l)
        print(f"Sol {sol}: {len(files)} files, exts={exts}")
        for f in files[:3]:
            print(f"  {f.split('/')[-1]}")
        data_files = [l for l in files if not l.endswith(".xml")]
        if data_files:
            for fpath in data_files[:2]:
                fname = fpath.split("/")[-1]
                local = os.path.join(WS, "raw", "mars", "perseverance", "supercam", fname)
                sha, sz = dl(fpath, local)
                print(f"  DL: {fname} ({sz:,} B) sha={sha[:16]}...")
            break
    except Exception as e:
        print(f"Sol {sol}: {e}")
