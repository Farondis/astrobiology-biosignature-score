#!/usr/bin/env python3
"""
Manifest tabanli veri indirici.

Ozellikler:
- CSV manifestten satirlari okur.
- Earthdata CMR granule aramasindan dogrudan dosya linki cozer.
- ODE product sorgusundan dosya baglantisini cozer.
- Dogrudan dosya URL'lerini indirir.
- Yari kalan indirmelerde Range ile devam etmeyi dener.
- Basit rapor uretir.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import urllib.request
import urllib.error
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


class _AuthRedirectHandler(urllib.request.HTTPRedirectHandler):
    """NASA Earthdata URS yonlendirmelerinde Authorization header'ini tasir."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is not None:
            auth = req.get_header("Authorization")
            if auth:
                new_req.add_unredirected_header("Authorization", auth)
        return new_req


def read_manifest(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def row_matches_filters(row: Dict[str, str], category: str = "", doi_contains: str = "") -> bool:
    if category:
        searchable = [
            (row.get("instrument") or "").strip().lower(),
            (row.get("level") or "").strip().lower(),
            (row.get("mission") or "").strip().lower(),
        ]
        wanted_terms = [term.strip().lower() for term in category.split(",") if term.strip()]
        if wanted_terms and not any(
            any(term in value for value in searchable)
            for term in wanted_terms
        ):
            return False

    if doi_contains:
        doi = (row.get("doi") or "").strip().lower()
        if doi_contains.strip().lower() not in doi:
            return False

    return True


def is_sciencebase_direct_file_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False

    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()

    if host == "www.sciencebase.gov" and path.startswith("/catalog/file/get/"):
        return True
    if host == "sciencebase.usgs.gov" and path.startswith("/manager/download/"):
        return True

    return False


def is_reference_only_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False

    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()

    if host == "doi.org":
        return True
    if host.endswith("usgs.gov") and path.startswith("/publications/"):
        return True

    return False


def is_direct_file_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    if parsed.netloc == "cmr.earthdata.nasa.gov":
        return False
    if "oderest.rsl.wustl.edu" in parsed.netloc:
        return False
    if is_sciencebase_direct_file_url(url):
        return True
    # query'siz ve dosya uzantili URL'leri dogrudan kabul et
    filename = Path(parsed.path).name
    return "." in filename


def pick_best_link(links: List[dict], preferred_name: str) -> Optional[str]:
    preferred_name = preferred_name.lower()

    candidates = []
    for link in links:
        href = link.get("href", "")
        rel = link.get("rel", "")
        if not href.startswith("http"):
            continue
        if "opendap" in href.lower() or "search.earthdata.nasa.gov" in href.lower():
            continue
        if "/data#" in rel:
            candidates.append(href)

    if not candidates:
        return None

    # once product_id adini iceren link
    for c in candidates:
        if preferred_name in c.lower():
            return c

    # sonra ilk aday
    return candidates[0]


def resolve_cmr_download_url(source_url: str, product_id: str, timeout: int) -> Tuple[Optional[str], str]:
    parsed = urlparse(source_url)
    query = parse_qs(parsed.query)

    short_name = (query.get("short_name") or [""])[0]
    if not short_name:
        return None, "CMR short_name bulunamadi"

    params = {
        "short_name": short_name,
        "producer_granule_id": product_id,
        "page_size": "10",
    }

    cmr_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        "",
        urlencode(params),
        "",
    ))

    req = Request(cmr_url, headers={"User-Agent": "astrobio-downloader/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return None, f"CMR sorgu hatasi: {exc}"

    entries = data.get("feed", {}).get("entry", [])
    if not entries:
        return None, "CMR sonucunda granule bulunamadi"

    links = entries[0].get("links", [])
    best = pick_best_link(links, product_id)
    if not best:
        return None, "CMR sonucunda indirilebilir data linki bulunamadi"

    return best, "OK"


def pick_ode_product_file(product_files: object, product_id: str) -> Optional[str]:
    if isinstance(product_files, dict):
        files = [product_files]
    elif isinstance(product_files, list):
        files = product_files
    else:
        return None

    product_id_l = product_id.lower()
    candidates: List[str] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        url = str(f.get("URL", "")).strip()
        ftype = str(f.get("Type", "")).strip().lower()
        name = str(f.get("FileName", "")).strip().lower()
        if not url.startswith("http"):
            continue
        # Once asıl urun dosyaları, browse/derived dosyaları değil.
        if ftype != "product":
            continue
        candidates.append(url)
        if product_id_l in name and not name.endswith((".xml", ".lbl", ".txt", ".htm", ".html")):
            return url

    if not candidates:
        return None

    for url in candidates:
        n = Path(urlparse(url).path).name.lower()
        if n.endswith((".xml", ".lbl", ".txt", ".htm", ".html")):
            continue
        return url

    return candidates[0]


def resolve_ode_download_url(row: Dict[str, str], timeout: int) -> Tuple[Optional[str], str]:
    product_id = (row.get("product_id") or "").strip()
    body = (row.get("body") or "").strip().lower()
    ihid = (row.get("mission") or "").strip()
    iid = (row.get("instrument") or "").strip()
    pt = (row.get("level") or "").strip()

    if not all([product_id, body, ihid, iid, pt]):
        return None, "ODE cozumleme icin body/mission/instrument/level/product_id gerekli"

    params = {
        "query": "product",
        "target": body,
        "ihid": ihid,
        "iid": iid,
        "pt": pt,
        "productid": product_id,
        "results": "fm",
        "output": "json",
    }
    ode_url = "https://oderest.rsl.wustl.edu/live2/?" + urlencode(params)
    req = Request(ode_url, headers={"User-Agent": "astrobio-downloader/1.0"})

    try:
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        return None, f"ODE sorgu hatasi: {exc}"

    ode_results = data.get("ODEResults") if isinstance(data, dict) else None
    if not isinstance(ode_results, dict):
        return None, "ODE beklenmeyen cevap formati"

    products = ode_results.get("Products")
    product = (products or {}).get("Product") if isinstance(products, dict) else None
    if not isinstance(product, dict) or not product:
        status = str(ode_results.get("Status", "")).strip() if isinstance(ode_results, dict) else ""
        return None, f"ODE product sonucu bulunamadi ({status or 'no-status'})"

    files = ((product.get("Product_files") or {}).get("Product_file"))
    best = pick_ode_product_file(files, product_id)
    if not best:
        return None, "ODE product dosya URL'si bulunamadi"

    return best, "OK"


def resolve_download_url(row: Dict[str, str], timeout: int) -> Tuple[Optional[str], str]:
    source_url = (row.get("source_url") or "").strip()
    product_id = (row.get("product_id") or "").strip()

    if not source_url:
        return None, "source_url bos"

    if "cmr.earthdata.nasa.gov/search/granules.json" in source_url:
        return resolve_cmr_download_url(source_url, product_id, timeout)

    if "oderest.rsl.wustl.edu" in source_url:
        return resolve_ode_download_url(row, timeout)

    if is_direct_file_url(source_url):
        return source_url, "OK"

    if is_reference_only_url(source_url):
        return None, "REFERENCE_ONLY"

    return None, "Desteklenmeyen URL tipi"


_EARTHDATA_AUTH_HOSTS = {
    "earthdatacloud.nasa.gov",
    "urs.earthdata.nasa.gov",
    "e4ftl01.cr.usgs.gov",
    "lpdaac.eosdis.nasa.gov",
}


def auth_headers(url: str = "") -> Dict[str, str]:
    headers = {"User-Agent": "astrobio-downloader/1.0"}
    token = os.environ.get("EARTHDATA_TOKEN", "").strip()
    if token and url:
        host = urlparse(url).hostname or ""
        if any(host == h or host.endswith("." + h) for h in _EARTHDATA_AUTH_HOSTS):
            headers["Authorization"] = f"Bearer {token}"
    return headers


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def download_with_resume(url: str, dest: Path, timeout: int) -> Tuple[bool, str]:
    ensure_parent(dest)
    headers = auth_headers(url)

    mode = "wb"
    existing = dest.stat().st_size if dest.exists() else 0
    if existing > 0:
        headers["Range"] = f"bytes={existing}-"
        mode = "ab"

    req = Request(url, headers=headers)
    opener = urllib.request.build_opener(_AuthRedirectHandler())
    try:
        with opener.open(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None)
            if status == 200 and mode == "ab":
                # sunucu range desteklemediyse bastan indir
                mode = "wb"

            with dest.open(mode) as f:
                while True:
                    chunk = resp.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)
    except HTTPError as exc:
        if exc.code == 416:
            return True, "Already complete"
        if exc.code == 401:
            token_hint = " (EARTHDATA_TOKEN ortam degiskeni eksik/gecersiz olabilir)" if not os.environ.get("EARTHDATA_TOKEN") else ""
            return False, f"HTTP 401: Yetkisiz erisim{token_hint}"
        return False, f"HTTP {exc.code}: {exc.reason}"
    except URLError as exc:
        return False, f"URL hata: {exc.reason}"
    except Exception as exc:
        return False, str(exc)

    return True, "OK"


def main() -> int:
    parser = argparse.ArgumentParser(description="Manifest tabanli veri indirici")
    parser.add_argument("--manifest", default="veri_manifest_sablonu.csv", help="Manifest CSV yolu")
    parser.add_argument("--only-body", choices=["Earth", "Moon", "Mars"], help="Sadece secili govde")
    parser.add_argument("--limit", type=int, default=0, help="Maksimum satir sayisi (0 = sinirsiz)")
    parser.add_argument("--dry-run", action="store_true", help="Sadece cozumleme yap, indirme yapma")
    parser.add_argument(
        "--report-only-references",
        action="store_true",
        help="Sadece indirilemeyen ama kaynak referansi olarak tutulan satirlari listele",
    )
    parser.add_argument(
        "--category",
        default="",
        help="Satirlari instrument/level/mission alanlarinda kismi eslesme ile filtrele; birden fazla deger icin virgul kullan",
    )
    parser.add_argument(
        "--doi-contains",
        default="",
        help="Satirlari DOI icinde gecen parcaya gore filtrele",
    )
    parser.add_argument("--timeout", type=int, default=60, help="HTTP timeout saniye")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Manifest bulunamadi: {manifest_path}")
        return 2

    if not os.environ.get("EARTHDATA_TOKEN"):
        print("UYARI: EARTHDATA_TOKEN ortam degiskeni set edilmemis.")
        print("       Earthdata gerektiren indirmeler (VIIRS, ASTER vb.) 401 ile basarisiz olabilir.")
        print("       Token almak icin: https://urs.earthdata.nasa.gov/profile -> Generate Token")
        print()

    rows = read_manifest(manifest_path)
    selected = []
    for row in rows:
        if args.only_body and row.get("body") != args.only_body:
            continue
        if not row_matches_filters(row, category=args.category, doi_contains=args.doi_contains):
            continue
        selected.append(row)

    if args.limit > 0:
        selected = selected[: args.limit]

    if args.report_only_references:
        print(f"Toplam secilen satir: {len(selected)}")
        reference = 0
        for row in selected:
            oid = row.get("object_id", "?")
            source_url = (row.get("source_url") or "").strip()
            if is_reference_only_url(source_url):
                print(f"[{oid}] REF - {source_url}")
                reference += 1

        print("\nOzet")
        print(f"REF     : {reference}")
        print(f"DIGER   : {len(selected) - reference}")
        return 0

    print(f"Toplam secilen satir: {len(selected)}")
    ok = 0
    reference = 0
    skipped = 0
    failed = 0

    for row in selected:
        oid = row.get("object_id", "?")
        local_path = (row.get("local_path") or "").strip()
        if not local_path:
            print(f"[{oid}] SKIPPED - local_path bos")
            skipped += 1
            continue

        url, reason = resolve_download_url(row, timeout=args.timeout)
        if not url:
            if reason == "REFERENCE_ONLY":
                print(f"[{oid}] REF - indirilebilir dosya degil, kaynak referansi olarak tutuluyor")
                reference += 1
                continue
            print(f"[{oid}] SKIPPED - {reason}")
            skipped += 1
            continue

        if args.dry_run:
            print(f"[{oid}] DRY-RUN - {url} -> {local_path}")
            ok += 1
            continue

        success, msg = download_with_resume(url, Path(local_path), timeout=args.timeout)
        if success:
            print(f"[{oid}] OK - {local_path}")
            ok += 1
        else:
            print(f"[{oid}] FAIL - {msg}")
            failed += 1

    print("\nOzet")
    print(f"OK      : {ok}")
    print(f"REF     : {reference}")
    print(f"SKIPPED : {skipped}")
    print(f"FAILED  : {failed}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
