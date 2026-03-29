# Derin Uzay Astrobiyolojisi İçin Biyo-iz Güven Skoru

**Uzaktan Algılamadan Yakın Doğrulamaya Çok Modlu Karar Modeli**

> Mars ve Ay görevlerinde yaşam izlerini güvenilir şekilde puanlamak için uzaktan algılama, jeolojik bağlam, yüzey morfolojisi, kimyasal analiz ve izotopik doğrulama kanallarını tek bir güven skorunda birleştiren açık kaynak karar çerçevesi.

**Yazarlar:** Sercan Demirhan · Gizem Demirhan  
**Yapay Zekâ Desteği:** Anthropic Claude Opus 4.6 (yazım, düzenleme, kodlama)

---

## Proje Özeti

Astrobiyolojide en büyük zorluklardan biri, biyotik ve abiyotik süreçlerin benzer gözlemsel izler üretebilmesidir. Tek bir ölçüm kanalına dayalı yorumlar yüksek yanlış pozitif riski taşır. Bu proje, **çoklu kanıt ilkesine** dayanan bir karar çerçevesi sunarak:

- **5 farklı kanıt kanalını** (uzaktan algılama, jeolojik bağlam, yüzey morfolojisi, kimyasal analiz, izotop doğrulama) tek bir Bayes sonsal skorda birleştirir.
- **Dünya analog kalibrasyonu** ile modelin bilinen biyoiz örnekleri üzerinde tutarlılığını doğrular.
- **Monte Carlo belirsizlik analizi** ve hassasiyet testi ile sonuçların güvenilirliğini ölçer.
- **Kontaminasyon riski cezalandırma** mekanizmasıyla yanlış pozitifleri baskılar.
- Manifest-güdümlü, uçtan uca bir veri pipeline'ı ile NASA PDS, USGS, SDSS gibi açık veri kaynaklarından otomatik veri edinim ve analiz sağlar.

**Hedef karar denklemi:**

$$S_{final} = \alpha \cdot S_{remote} + \beta \cdot S_{context} + \gamma \cdot S_{in\_situ} + \delta \cdot S_{chem\_iso} - \lambda \cdot R_{contam}$$

---

## Demo / Sunum

> 📎 *Sunum linki yarışma sisteme yüklenecektir.*

---

## Kullanılan Açık Veri Kaynakları

| Gövde | Kaynak | Araç/Format |
|-------|--------|-------------|
| Mars | NASA PDS (CRISM, HiRISE, SHARAD, SuperCam, PIXL, SHERLOC) | FITS, CSV, IMG |
| Ay | NASA PDS (LRO LOLA, LROC) | IMG, TIF |
| Dünya | NASA Earthdata (MODIS, ASTER, VIIRS), USGS Spectral Library V7 | HDF, H5, ASCII |
| Teleskop | SDSS DR17 | FITS |
| Referans | USGS Publications Warehouse, Mars İzotop Referans Tabloları | DOI, CSV |

Detaylı kaynak envanteri: [orijinal_veri_kaynaklari.md](orijinal_veri_kaynaklari.md)

---

## Hızlı Başlangıç

```powershell
# 1. Manifest'i doğrula
python manifest_lint.py --manifest veri_manifest_sablonu.csv

# 2. Veri indir (kuru çalıştırma)
python manifest_downloader.py --manifest veri_manifest_sablonu.csv --dry-run

# 3. Eksik satırları tespit et
python eksik_veri_doldur.py --manifest veri_manifest_sablonu.csv

# 4. Spektral özet çıkar
python spectral_summary.py raw/earth/usgs_splib07

# 5. Biyoiz güven skoru hesapla
python score_evidence.py --remote 0.72 --context 0.68 --in-situ 0.66 --chem-iso 0.58 --contam 0.18
```

---

## Proje Yapısı

```
.
├── README.md                          ← Bu dosya
├── veri_manifest_sablonu.csv          ← Ana manifest (34 satır, tek doğruluk kaynağı)
├── rover_latest_urls.txt              ← Mars 2020 rover yem dosyası
│
├── manifest_downloader.py             ← Manifest güdümlü URL çözücü ve indirici
├── eksik_veri_doldur.py               ← Eksik veri tespiti, rover yem sindirimi, checksum doldurucu
├── spectral_summary.py                ← USGS spektral arşivlerden özet metrik çıkarıcı
├── feature_extractor.py               ← Spektral + izotop özellik çıkarıcı (model girdisi üretir)
├── score_evidence.py                  ← Biyoiz güven skoru + MC belirsizlik + hassasiyet analizi
├── run_pipeline.py                    ← Uçtan uca otomatik pipeline (özellik → skor → rapor)
├── validation_suite.py                ← 12 senaryolu doğrulama test takımı + confusion matrix
├── manifest_lint.py                   ← Manifest kalite kontrol aracı
├── checksum_dogrulama.ps1             ← SHA256 hesaplama ve CSV geri doldurucu (PowerShell)
│
├── astrobiology.md                    ← Analiz kategorileri (jeoloji, morfoloji, kimya)
├── guven_skoru_karar_modeli.md        ← Karar modeli dokümantasyonu + score_evidence.py kullanımı
├── model-uygulama-paketi.md           ← Sensör özellikleri, mimari ve skor kartı şablonu
├── earth_biosignature_notes.md        ← Dünya analog → Mars biyoiz eşleme notları
├── earth_mars_spectral_comparison.md  ← CRISM/ASTER/Global spektral karşılaştırma
├── orijinal_veri_kaynaklari.md        ← Resmi veri kaynakları envanteri
├── biyo_iz_guven_skoru_makale.tex     ← LaTeX makale taslağı
│
└── raw/                               ← İndirilen ham veri
    ├── earth/
    │   ├── aster/
    │   ├── modis/
    │   ├── viirs/
    │   ├── usgs/
    │   └── usgs_splib07/              ← USGS Spectral Library V7 paketleri
    ├── mars/
    │   ├── mro/                       ← CRISM, HiRISE, SHARAD
    │   ├── perseverance/              ← SHERLOC, Mastcam-Z, SuperCam, PIXL
    │   │   ├── shrlc/                 ← Watson fotoğrafları
    │   │   ├── shrlc_spectra/         ← SHERLOC RDR Raman+floresan
    │   │   ├── pixl/                  ← PIXL element haritaları
    │   │   └── supercam/              ← SuperCam LIBS + Raman
    │   └── reference/                 ← İzotop referans tabloları
    ├── moon/
    │   └── lro/                       ← LROC, LOLA
    └── telescope/
        └── sdss/                      ← SDSS DR17 FITS spektrumları
```

---

## Araçlar

### manifest_downloader.py

Manifest-güdümlü URL çözücü ve indirici. CMR, ODE, ScienceBase, doğrudan dosya
ve referans-only URL tiplerini destekler.

| Flag | Açıklama |
|------|----------|
| `--manifest` | CSV manifest yolu |
| `--only-body` | Gövde filtresi (Earth, Mars, Moon, DeepSpace) |
| `--category` | Virgülle ayrılmış kısmi eşleşme (ör. `spectral,organic`) |
| `--doi-contains` | DOI alt-dizi filtresi |
| `--dry-run` | İndirmeden URL çözümle |
| `--report-only-references` | Yalnızca referans satırları raporla |
| `--limit` | İndirilecek maksimum kayıt |
| `--timeout` | HTTP zaman aşımı (saniye) |

### eksik_veri_doldur.py

Manifest'teki eksik verileri tespit eder, rover yem dosyasından yeni satır sindirir,
isteğe bağlı indirme yapar ve SHA256 checksum doldurur.

| Flag | Açıklama |
|------|----------|
| `--manifest` | CSV manifest yolu |
| `--rover-feed` | Rover URL yem dosyası (varsayılan: `rover_latest_urls.txt`) |
| `--download` | Eksik dosyaları indir |

### spectral_summary.py

USGS Spectral Library V7 ZIP arşivlerini tarar, her spektrum için min/max/mean/delta
ve ASCII sparkline izi çıkarır, CSV'ye yazar.

```powershell
python spectral_summary.py raw/earth/usgs_splib07
# Çıktı: raw/earth/usgs_splib07/usgs_spectral_summary.csv (9.336 satır)
```

### score_evidence.py

Güven skoru karar modelinin çalıştırılabilir uygulaması.
Dünya analog kalibrasyonu ile birlikte `S_final` ve karar etiketi üretir.

```powershell
python score_evidence.py \
  --remote 0.72 --context 0.68 --in-situ 0.66 \
  --chem-iso 0.58 --contam 0.18 \
  --morphology-analog 0.80 --spectral-analog 0.83 \
  --chemistry-analog 0.77 --abiotic-risk 0.12
```

Karar etiketleri:
- **Düşük güven** — `S_final < 0.35`
- **Orta güven** — `0.35 ≤ S_final < 0.60`
- **Ek örnekleme gerekli** — tek kanal baskınlığı veya eksik kanal
- **Yüksek güven** — çoklu kanal uyumu + kimyasal destek + düşük abiyotik risk

### feature_extractor.py

Spektral özet + izotop referans verilerinden model girdisi özellik vektörleri üretir.
Bant derinliği, spektral eğim, absorpsiyon merkezi, eğrilik, biyoiz hint skorları.

```powershell
python feature_extractor.py
# Çıktı: features_spectral.csv, features_isotope.csv, features_aggregate.csv
```

### run_pipeline.py

Uçtan uca otomatik pipeline: özellik çıkarma → toplama → puanlama → belirsizlik → rapor.
İnsan girişi olmadan manifest verisinden nihai skor üretir.

```powershell
python run_pipeline.py
python run_pipeline.py --context 0.70 --morphology 0.80  # override ile
python run_pipeline.py --json                              # JSON çıktı
```

### validation_suite.py

12 bilinen senaryo (Earth pozitif/negatif + Mars + tek-kanal kontrolleri) ile
karar modelini doğrulayan test takımı. Confusion matrix üretir.

```powershell
python validation_suite.py               # 12 test + confusion matrix
python validation_suite.py --json        # JSON çıktı
```

### Monte Carlo Belirsizlik & Hassasiyet

`score_evidence.py` artık güven aralığı ve ağırlık hassasiyeti üretir:

```powershell
python score_evidence.py --remote 0.72 --context 0.68 --in-situ 0.66 \
  --chem-iso 0.58 --contam 0.18 --monte-carlo 1000 --sensitivity
```

### manifest_lint.py

Manifest kalite kontrol aracı. Zorunlu alan, tekil kontrol, gövde-yol tutarlılığı,
hash eksikliği ve dosya varlığı denetimleri yapar.

```powershell
python manifest_lint.py --manifest veri_manifest_sablonu.csv
python manifest_lint.py --manifest veri_manifest_sablonu.csv --check-files
```

---

## Veri Kaynakları

| Gövde | Kaynak | Erişim |
|-------|--------|--------|
| Mars | NASA PDS, ODE REST, Mars 2020 Raw Images | Açık |
| Ay | NASA PDS, ODE REST | Açık |
| Dünya | NASA Earthdata (CMR), USGS Media, ScienceBase | Earthdata token gerekli |
| Teleskop | SDSS DR17 | Açık |
| Referans | USGS Publications Warehouse | DOI erişimi |

Earthdata korumalı indirmeler için:

```powershell
$env:EARTHDATA_TOKEN = "<JWT token>"
python manifest_downloader.py --manifest veri_manifest_sablonu.csv --only-body Earth
```

---

## Karar Modeli Özeti

$$S_{final} = \alpha \cdot S_{remote} + \beta \cdot S_{context} + \gamma \cdot S_{in\_situ} + \delta \cdot S_{chem\_iso} - \lambda \cdot R_{contam}$$

Dünya analog kalibrasyonu mevcut alt skorları doğrudan besler:

| Analog katmanı | Manifest kayıtları | Etkilediği skor |
|---|---|---|
| Morfolojik | EARTH-004, EARTH-005 | `S_in_situ` |
| Kimyasal | EARTH-006, EARTH-007 | `S_chem_iso` |
| Spektral | EARTH-008 – EARTH-012 | `S_remote` |
| Abiyotik kontrol | Spektral kütüphane negatif sınıflar | `R_contam` |

Detaylar: [guven_skoru_karar_modeli.md](guven_skoru_karar_modeli.md)

---

## Bilinen Açık Noktalar

- `MOON-003`, `EARTH-008`, `EARTH-009`: SHA256 hash eksik (indirme sonrası doldurulacak)
- `EARTH-001`: CMR granül eşleşme uyumsuzluğu (kozmik olmayan, izleniyor)

---

## Gereksinimler

- Python ≥ 3.9 (yalnızca standart kütüphane)
- PowerShell 5.1+ (checksum doğrulama için)
- LaTeX dağıtımı (makale derlemek için, isteğe bağlı)
