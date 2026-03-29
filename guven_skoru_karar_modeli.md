# Biyo-Iz Guven Skoru Veren Karar Modeli
## Uzak Olcumden Yakin Dogrulamaya ML Tabanli Yol Haritasi

## 1. Amac
Ay/Mars astrobiyoloji gorevlerinde, uzaktan algilama ve yerinde analiz verilerini birlestirerek tek bir Biyo-Iz Guven Skoru uretmek.

## 2. Temel Model
Nihai hedef olasilik:

S_bio = P(yasam benzeri surec | X_orbital, X_surface, X_chem, X_iso, X_qc)

Pratik birlesik skor:

S_final = alpha * S_remote + beta * S_context + gamma * S_in_situ + delta * S_chem_iso - lambda * R_contam

Parametreler:
- `S_remote`: Uzaktan algilama tarama skoru
- `S_context`: Jeolojik baglam uygunluk skoru
- `S_in_situ`: Yuzey morfoloji skoru
- `S_chem_iso`: Kimyasal ve izotopik dogrulama skoru
- `R_contam`: Kontaminasyon ve abiyotik taklit riski

### 2.1 Earth Analog Kalibrasyon Katmani
- Earth analog veri kutuphanesi ana skora yeni bir terim eklemez; mevcut alt skorlarin esiklerini kalibre eder.
- Kalibrasyon eslemesi:
  - `S_remote` icin: EARTH-008, EARTH-010, EARTH-011
  - `S_in_situ` icin: EARTH-004, EARTH-005
  - `S_chem_iso` icin: EARTH-006, EARTH-007
  - `R_contam` icin: Earth spektral kutuphanesindeki abiyotik taklitciler ve uyumsuz jeolojik baglam
- Prensip:
  - Tek kanallı benzerlik karar vermez
  - Morfoloji + spektral uyum + kimyasal destek birlikteliginde esik yukseltilir
  - Earth analog uyumu yuksek ama abiyotik aciklama gucluyse ceza uygulanir

## 3. Uctan Uca Asamalar

### 3.1 Faz 0: Etiket ve Referans Kutuphanesi
- Dunya analog veri setleri toplanir: hidrotermal, evaporitik, biyofilmli, abiyotik
- Siniflar tanimlanir: biyotik-benzeri, abiyotik-benzeri, belirsiz
- Cikti: Egitim verisi semasi ve kalite protokolu
- Referans cekirdegi:
  - Morfoloji: EARTH-004, EARTH-005
  - Kimya: EARTH-006, EARTH-007
  - Spektral: EARTH-008, EARTH-010, EARTH-011

### 3.2 Faz 1: Uzaktan Tarama Modeli (Teleskop/Spektro)
- Girdi: VNIR-SWIR spektrum, termal bantlar, topografya, morfometri
- Model: Spektral siniflandirma icin 1D-CNN veya Transformer
- Ek model: Jeomorfolojik segmentasyon icin CNN
- Cikti: Adaylik haritasi + `S_remote`

### 3.3 Faz 2: Jeolojik Baglam Skoru
- Girdi: Delta, paleolakustrin birimler, kil/sulfat/silis varligi, gomulme olasiligi
- Model: Gradient boosting veya Bayes aglari
- Cikti: `S_context`

### 3.4 Faz 3: Yuzey Yakin Goruntu Analizi
- Girdi: Makro-mikro goruntu, 3B yuzey, tekstur metrikleri
- Hedef yapilar: stromatolit-benzeri kubbe/sutun, filamenter doku, ritmik laminasyon
- Model: Cok olcekli goruntu agi + oznitelik tabanli istatistik
- Cikti: `S_in_situ`

### 3.5 Faz 4: Kimyasal ve Izotopik Dogrulama
- Girdi: GC-MS, LC-MS, Raman, FTIR, IRMS, redoks sensorleri
- Model: Cok-modlu fuzyon (late fusion + kalibre lojistik katman)
- Cikti: `S_chem_iso`

### 3.6 Faz 5: Birlesik Karar Motoru
- Bayes guncelleme ile posterior hesaplanir
- Belirsizlik tahmini eklenir (guven araligi, veri eksikligi cezasi)
- Karar etiketleri:
  1. Dusuk guven
  2. Orta guven
  3. Yuksek guven
  4. Ek ornekleme gerekli

Karar kurali ek notu:
- Yalnizca `S_in_situ` veya yalnizca `S_remote` yuksekse etiket en fazla `Orta guven` olabilir.
- `Yuksek guven` icin `S_chem_iso` sifir olmamali ve Earth analog kutuphanesi ile en az iki bagimsiz kanal uyumu gorulmeli.

### 3.7 Faz 6: Operasyonel Planlama
- Yuksek skorda derin ornekleme onceligi
- Orta skorda ek olcum tetikleme
- Dusuk skorda kaynak optimizasyonu icin eleme
- Cikti: Inis/rota/ornekleme plani

## 4. 90 Gunluk MVP

### Gun 1-30
- Veri semasi ve etiket standardi tamamlanir
- Uzaktan modelin ilk surumu cikar
- Cikti: Adaylik isi haritasi

### Gun 31-60
- Morfoloji ve baglam modeli entegre edilir
- Abiyotik taklitci negatif siniflari genisletilir
- Cikti: Birlesik on skor paneli

### Gun 61-90
- Kimyasal-izotopik fuzyon katmani eklenir
- Kalibrasyon, esik optimizasyonu, yanlis pozitif analizi yapilir
- Cikti: Biyo-Iz Guven Skoru panosu + teknik rapor

## 5. Basari Kriterleri
1. Yanlis pozitif oraninin hedef esik altinda olmasi
2. Farkli sahalarda tekrarlanabilir skor davranisi
3. Coklu-kanit fuzyonunda tek-kanala gore anlamli performans artisi
4. Belirsizlik raporlamasi ile birlikte karar uretimi

## 6. Calistirilabilir Skorlama Araci

- Uygulama dosyasi: `score_evidence.py`
- Arac, dokumandaki `S_remote`, `S_context`, `S_in_situ`, `S_chem_iso` ve `R_contam` terimlerini dogrudan alir.
- Earth analog kalibrasyonunu su ek girislerle uygular:
  - `--morphology-analog`
  - `--spectral-analog`
  - `--chemistry-analog`
  - `--abiotic-risk`
  - `--missing-channels`

Temel kullanim:

- `python .\score_evidence.py --remote 0.72 --context 0.68 --in-situ 0.66 --chem-iso 0.58 --contam 0.18 --morphology-analog 0.80 --spectral-analog 0.83 --chemistry-analog 0.77 --abiotic-risk 0.12`

JSON cikti icin:

- `python .\score_evidence.py --remote 0.86 --context 0.78 --in-situ 0.82 --chem-iso 0.74 --contam 0.08 --morphology-analog 0.92 --spectral-analog 0.91 --chemistry-analog 0.89 --abiotic-risk 0.05 --json`

Operasyonel yorum:

- Tek kanalli guclu sinyaller, kimyasal dogrulama ve coklu kanal uyumu olmadan `Yuksek guven` etiketi alamaz.
- Abiyotik risk ve eksik kanal sayisi nihai skoru asagi ceker.
- `Yuksek guven` etiketi icin guclu kimyasal destek, dusuk abiyotik risk ve Earth analog uclusunun birlikte guclu olmasi gerekir.
