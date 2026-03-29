# Orijinal Veri Kaynaklari (Dunya, Ay, Mars)

Bu dosya yalnizca birincil (primary/original) gorev verisi saglayan resmi arsivleri listeler.
Hedef: biyo-iz guven skoru modeline dogrudan kaynak veri beslemek.

## 1) Zorunlu Ilke: Orijinallik ve Izlenebilirlik

- Veri kaynagi mutlaka resmi gorev arsivi olmali.
- Her urun icin su alanlar saklanmali:
  - Mission / Instrument
  - Product ID
  - Acquisition time (UTC)
  - Processing level (EDR/RDR vb.)
  - DOI (varsa)
  - SHA256 checksum
  - Download URL
- Isleme oncesi ham veri (raw/EDR) ayri klasorde korunmali.

## 2) Mars - Resmi Birincil Arsivler

### NASA PDS (Planetary Data System)
- Portal: https://pds.nasa.gov/
- Arama: https://pds.nasa.gov/services/search/
- Neden: MRO, MSL Curiosity, Mars 2020 Perseverance dahil birincil gorev urunleri.
- Tipik veri:
  - Orbital: CRISM, HiRISE, CTX
  - Yuzey: Mastcam, SuperCam, PIXL, SHERLOC, SAM (goreve gore)

### USGS Astrogeology
- Portal: https://www.usgs.gov/centers/astrogeology-science-center
- Neden: Harita tabanli gezegen urunleri ve jeo-referansli destek katmanlari.

### ESA PSA (Mars Express / ExoMars)
- Portal: https://www.cosmos.esa.int/web/psa
- Neden: ESA gorevlerine ait birincil urunler.

### Mars 2020 Perseverance — Alet-Ozel Arsivler
Bu workspace'te manifest satirlari MARS-004..007 ile tanimlanan in-situ veri setleri asagidaki PDS alt-arsividir.

- **SHERLOC** (Scanning Habitable Environments with Raman & Luminescence for Organics & Chemicals)
  - Arsiv: https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_sherloc/
  - Referans: Bhartia et al. (2021), *Space Science Reviews*, 217(4), 58. doi:10.1007/s11214-021-00812-z
  - Kullanim: Raman + fluoresans spektrumu → organik tespit, S_chem_iso giris.

- **PIXL** (Planetary Instrument for X-Ray Lithochemistry)
  - Arsiv: https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_pixl/
  - Referans: Allwood et al. (2020), *Space Science Reviews*, 216(8), 134. doi:10.1007/s11214-020-00767-7
  - Kullanim: XRF element haritasi → redoks indeksleri, mineral baglam.

- **SuperCam** (LIBS + Raman + VISIR)
  - Arsiv: https://pds-geosciences.wustl.edu/m2020/urn-nasa-pds-mars2020_supercam/
  - Referans: Maurice et al. (2021), *Space Science Reviews*, 217(3), 47. doi:10.1007/s11214-021-00807-w
  - Kullanim: LIBS element kompozisyonu + Raman mineral/organik faz → S_context, S_chem_iso.

- **Gorev Genel Bakis**
  - Referans: Farley et al. (2020), *Space Science Reviews*, 216(8), 142. doi:10.1007/s11214-020-00762-y

## 3) Ay - Resmi Birincil Arsivler

### NASA PDS Geosciences / Imaging Node
- Portal: https://pds-geosciences.wustl.edu/
- Portal: https://pds-imaging.jpl.nasa.gov/
- Neden: LRO (LOLA, LROC vb.) dahil Ay veri setleri.

### LROC (Arizona State University)
- Portal: https://lroc.sese.asu.edu/
- Neden: Ay yuksek cozunurluk goruntuleri ve urun kataloglari.

### JAXA SELENE (Kaguya) Data Archive
- Portal: https://darts.isas.jaxa.jp/planet/project/kaguya/
- Neden: Kaguya gorev urunleri (Ay topografya/goruntu/veri katmanlari).

## 4) Dunya Analog - Resmi Birincil Kaynaklar

### USGS EarthExplorer
- Portal: https://earthexplorer.usgs.gov/
- Neden: Landsat ve diger resmi uzaktan algilama urunleri.

### NASA Earthdata
- Portal: https://www.earthdata.nasa.gov/
- Neden: MODIS, ASTER, VIIRS vb. birincil/standart urunler.

### ESA Copernicus Data Space Ecosystem
- Portal: https://dataspace.copernicus.eu/
- Neden: Sentinel gorev urunleri (resmi ESA dagitimi).

### USGS Spectral Library
- Portal: https://www.usgs.gov/labs/spectroscopy-lab/usgs-spectral-library
- Neden: Mineral spektral referanslari (abiotik taklitci kontrolu icin kritik).

## 4.1) Dunya Biyoi̇saret Analoglari Icin Cekirdek Ornekler

Bu workspace icin Earth tarafinda yalnizca genel uzaktan algilama degil, bizzat yasam izi veya biyolojik doku korunumu gosteren analog yapilar da tutulmali.

### Gorsel / Morfolojik analoglar
- USGS: Stromatolites of Australia
  - Hedef: Shark Bay / Hamelin Pool yasayan stromatolitleri
  - Deger: stromatolitik kubbe ve kolon morfolojisi, makro-olcekli biyoi̇saret geometrisi
  - Kaynak: https://www.usgs.gov/media/images/stromatolites-australia
- USGS: Siliceous sinter in the field and viewed via Scanning Electron Microscope
  - Hedef: Yellowstone'da fotosentetik mikrobiyal mat uzerinde silis kabuklanmasi
  - Deger: filament kaliplari, mat dokusu ve mikroskobik korunma ornegi
  - Kaynak: https://www.usgs.gov/media/images/siliceous-sinter-field-and-viewed-scanning-electron-microscope

### Kimyasal / Jeokimyasal analoglar
- USGS publication: Characterization of arsenic species in microbial mats from an inactive gold mine
  - DOI: 10.1144/1467-787302-029
  - Deger: XAFS ile As turlesmesi; EPS, Fe-oksihidroksit ve mikrobiyal mat iliskisi
  - Kaynak: https://www.usgs.gov/publications/characterization-arsenic-species-microbial-mats-inactive-gold-mine
- USGS publication: Methylmercury enters an aquatic food web through acidophilic microbial mats in Yellowstone National Park, Wyoming
  - DOI: 10.1111/j.1462-2920.2008.01820.x
  - Deger: mikrobiyal mat biyokutlesinde MeHg birikimi ve trofik aktarim
  - Kaynak: https://www.usgs.gov/publications/methylmercury-enters-aquatic-food-web-through-acidophilic-microbial-mats-yellowstone

Not:
- Bu dortlu set, Mars'taki stromatolit-benzeri laminasyonlar, silisli hidrotermal cokeller ve redoks kontrollu biyokimyasal sinyaller icin dogrudan analog baglam saglar.
- Gorsel veriler indirilebilir varlik olarak manifestte tutulabilir; kimyasal referanslar ise DOI ve yayin sayfasi uzerinden izlenebilirlik katmani saglar.

### Spektral referans katmani
- USGS Spectral Library Version 7 Data release: https://doi.org/10.5066/F7RR1WDJ
  - Spektral kapsama: 0.2-200 um
  - Chapter O: organics ve bitki biyokimyasal bilesenleri; amino asitler, aromatikler, lignin, seluloz, amiloz, nisasta
  - Chapter V: biyolojik materyaller; bitki bilesenleri, likenler, biological soil crusts, karisik bitki ortamlari
  - Planetary transfer: ASCII paketlerinde CRISM global ve CRISM joined MTR3 konvolusyonlari hazir bulunur
- ASCII spectra child item: https://www.sciencebase.gov/catalog/item/586e8c88e4b0f5ce109fccae
- HTML metadata child item: https://www.sciencebase.gov/catalog/item/586e8d4de4b0f5ce109fccbb
- SPECPR child item: https://www.sciencebase.gov/catalog/item/586e8bf2e4b0f5ce109fcca2

## 5) Veri Paketleme Standardi (Oneri)

Her indirilen urun icin bir satir manifest:

- object_id
- body (Earth/Moon/Mars)
- mission
- instrument
- product_id
- level
- acquired_utc
- doi
- source_url
- sha256
- local_path
- notes

## 6) Teleskop Veri Kaynaklari

### SDSS DR17 (Sloan Digital Sky Survey)
- Portal: https://www.sdss.org/dr17/
- Referans: Abdurro'uf et al. (2022), *ApJS*, 259(2), 35. doi:10.3847/1538-4365/ac4414
- Kullanim: Yildiz/galaksi kompozisyon taramasi, ekzogezegen onsecimi, S_remote pipeline test verisi.
- Manifest: TEL-001

## 7) Metodoloji ve Referans Yayinlar

Bu projedeki modelleme ve analiz araclarinin dayandigi temel referanslar:

| Konu | Referans | DOI |
|------|----------|-----|
| Spektral bant derinligi ve uzaktan algilama | Clark & Roush (1984), *JGR*, 89(B7), 6329-6340 | 10.1029/JB089iB07p06329 |
| Karbon izotop biyoizleri | Schidlowski (2001), *Precambrian Research*, 106, 117-134 | 10.1016/S0301-9268(00)00128-5 |
| Stromatolit referans | Allwood et al. (2006), *Nature*, 441, 714-718 | 10.1038/nature04764 |
| Fischer-Tropsch abiyotik kontrol | McCollom & Seewald (2006), *EPSL*, 243, 74-84 | 10.1016/j.epsl.2006.01.027 |
| Monte Carlo yontemi | Metropolis & Ulam (1949), *JASA*, 44(247), 335-341 | 10.1080/01621459.1949.10483310 |
| MRO CRISM aleti | Murchie et al. (2007), *JGR*, 112(E5), E05S03 | 10.1029/2006JE002682 |
| MRO HiRISE aleti | McEwen et al. (2007), *JGR*, 112(E5), E05S02 | 10.1029/2005JE002605 |
| MRO SHARAD aleti | Seu et al. (2007), *JGR*, 112(E5), E05S05 | 10.1029/2006JE002745 |
| LRO LOLA aleti | Smith et al. (2010), *Space Sci Rev*, 150, 209-241 | 10.1007/s11214-009-9512-y |
| LRO LROC aleti | Robinson et al. (2010), *Space Sci Rev*, 150, 81-124 | 10.1007/s11214-010-9634-2 |
| USGS Spectral Library V7 | Kokaly et al. (2017), USGS Data Series 1035 | 10.5066/F7RR1WDJ |

## 6) Kalite ve Dogrulama Protokolu

1. URL dogrulama: alan adi resmi kuruma ait olmali (nasa.gov, usgs.gov, esa.int, jaxa.jp).
2. Metadata dogrulama: product_id, acquisition time, processing level zorunlu.
3. Checksum dogrulama: indirilen her dosya icin SHA256 hesapla ve manifestte sakla.
4. Ham veriyi kilitle: raw klasorune yaz, uzerine yazma.
5. Islenmis veri ayir: processed klasorunde versiyonlu tut.

## 7) Bu Proje Icin Minimum Orijinal Veri Sepeti

### Mars
- 1 adet mineralojik spektral urun (orbital)
- 1 adet yuksek cozunurluk jeomorfoloji urunu (orbital)
- 1 adet yuzey kimyasal/spektroskopik urun (in-situ)

### Ay
- 1 adet polar/PSR odakli urun
- 1 adet yuksek cozunurluk goruntu urunu
- 1 adet topografya veya radar turevi urun

### Dunya (analog)
- 1 adet hidrotermal analog saha urunu
- 1 adet evaporitik analog saha urunu
- 1 adet spektral kutuphane referansi

## 8) Sonraki Adim (Uygulama)

Bir sonraki asamada, secilen her govde (Dunya/Ay/Mars) icin 10-15 urunluk kesin Product ID listesi cikarilip manifest dosyasi doldurulmalidir. Bu liste hazirlandiginda model egitim ve dogrulama pipeline'ina dogrudan baglanabilir.

## 9) Bu Workspace Icin Hazir Cekirdek Set

- Doldurulmus ornek manifest: `veri_manifest_sablonu.csv`
- SHA256 guncelleme betigi: `checksum_dogrulama.ps1`
- Downloader: `manifest_downloader.py`

Kullanim:

1. Orijinal dosyalari `local_path` alanlarina indir.
2. PowerShell'de calistir:
  - `./checksum_dogrulama.ps1 -ManifestPath .\\veri_manifest_sablonu.csv`
3. Manifestte `sha256` kolonunun doldugunu kontrol et.

Downloader kullanim ornekleri:

1. Earth dry-run (onerilen ilk adim):
  - `python .\\manifest_downloader.py --manifest .\\veri_manifest_sablonu.csv --only-body Earth --dry-run`
2. Earth gercek indirme:
  - `python .\\manifest_downloader.py --manifest .\\veri_manifest_sablonu.csv --only-body Earth`
3. Tum satirlar (Moon/Mars satirlari direct file URL icermiyorsa SKIPPED olur):
  - `python .\\manifest_downloader.py --manifest .\\veri_manifest_sablonu.csv`
4. Checksum guncelleme:
  - `./checksum_dogrulama.ps1 -ManifestPath .\\veri_manifest_sablonu.csv`

Not:
- Earthdata korumali dosyalar icin `EARTHDATA_TOKEN` ortami degiskeni gerekebilir.
