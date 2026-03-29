# Model Uygulama Paketi
## Sensor Ozellikleri, Mimari ve Skor Karti

## 1. Sensor -> Ozellik Haritasi

### Orbital Spektral
- Bant derinlik oranlari
- Spektral egim
- Absorpsiyon merkezi kaymalari
- Hidratasyon gostergeleri
- Termal atalet turevleri

### Jeomorfoloji ve Topografya
- Egim, puruzluluk, drenaj yogunlugu
- Delta/fan morfometri parametreleri
- Katman sureklilik indeksi
- Gomulme olasilik skoru

### Yuzey Goruntuleme
- Fraktal boyut
- Yonlenme dagilimi
- Laminasyon periyodisitesi
- Filament benzerlik skoru
- 3B mikrotopoloji metrikleri

### Kimyasal ve Mineralojik
- Organik pik yogunlugu ve cesitliligi
- Fonksiyonel grup varlik skorlari
- Mineral baglam uyumu (kil/sulfat/silis)
- Redoks dengesizlik indeksleri

### Izotopik
- d13C, d34S, dD sapmalari
- Fraksiyonasyon tutarlilik skoru
- Coklu ornekler arasi izotopik stabilite

### Kalite ve Kontaminasyon
- Blank/witness plate korelasyonu
- Numune isleme zinciri guven puani
- Cihaz drift/kalibrasyon sapma puani

## 2. Onerilen Mimari

### Katman A: Aday Tarama
- Model: 1D-CNN veya Spectral Transformer
- Cikti: `S_remote`

### Katman B: Baglam Degerlendirme
- Model: XGBoost veya Bayes Network
- Cikti: `S_context`

### Katman C: Morfoloji Incelemesi
- Model: Multi-scale CNN + feature fusion
- Cikti: `S_in_situ`

### Katman D: Kimya/Izotop Dogrulama
- Model: Late-fusion ensemble + calibrated logistic head
- Cikti: `S_chem_iso`

### Katman E: Karar Fuzyonu
- Model: Bayes guncelleme + risk ceza terimi
- Cikti: `S_final` ve karar etiketi

## 3. Skor Karti Sablonu (Tek Sayfa)

### Kimlik
- Bolge ID
- Koordinat
- Veri surumu
- Tarih

### Ana Skorlar
- `S_remote`
- `S_context`
- `S_in_situ`
- `S_chem_iso`
- `R_contam`
- `S_final`

### Guven ve Karar
- Guven araligi
- Belirsizlik seviyesi
- Karar etiketi:
  1. Dusuk guven
  2. Orta guven
  3. Yuksek guven
  4. Takip olcumu gerekli

### Kanit Ozeti
- En guclu 3 pozitif kanit
- En kritik 3 risk/karsi kanit
- Abiyotik taklitci kontrol sonucu
- Kontaminasyon kontrol sonucu

### Operasyon Onerisi
1. Derin ornekleme
2. Ek Raman/FTIR turu
3. Izotop tekrar olcumu
4. Bolgeyi dusuk oncelige alma

## 4. Kod Esleme Tablosu

| Dokuman Terimi | Uygulama Dosyasi | Fonksiyon / Parametre |
|---|---|---|
| Katman A → `S_remote` | `score_evidence.py` | `--remote`, `calibrate_scores()` icinde `calibrated_remote` |
| Katman B → `S_context` | `score_evidence.py` | `--context`, `calibrated_context` |
| Katman C → `S_in_situ` | `score_evidence.py` | `--in-situ`, `calibrated_in_situ` |
| Katman D → `S_chem_iso` | `score_evidence.py` | `--chem-iso`, `calibrated_chem_iso` |
| Katman E → `S_final` | `score_evidence.py` | `calibrate_scores() → combined_score` |
| Bayes guncelleme (belirsizlik) | `score_evidence.py` | `--monte-carlo N`, `monte_carlo_uncertainty()` |
| Hassasiyet analizi | `score_evidence.py` | `--sensitivity`, `sensitivity_analysis()` |
| Ozellik cikarma | `feature_extractor.py` | `extract_spectral_features()`, `extract_isotope_features()` |
| Uctan uca pipeline | `run_pipeline.py` | `run_pipeline()` |
| Dogrulama test takimi | `validation_suite.py` | `CANON_TESTS`, 12 bilinen senaryo |
| Earth analog kalibrasyon | `score_evidence.py` | `--morphology/spectral/chemistry-analog`, `--abiotic-risk` |
| Skor karti sablonu | `score_evidence.py` | `--json` ciktisi |
