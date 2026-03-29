# Earth-Mars Spectral Comparison Notes

Bu not, indirilen USGS Spectral Library alt paketlerinin Mars odakli kullanimini hizli gozden gecirmek icin hazirlandi.

## 1) Incelenen paketler

- EARTH-010: `ASCIIdata_splib07b_cvCRISMjMTR3.zip`
- EARTH-011: `ASCIIdata_splib07b_cvCRISM-global.zip`
- EARTH-012: `ASCIIdata_splib07b_rsASTER.zip`

## 2) Paket yapisi

Uc pakette de ayni temel chapter yapisi bulunuyor:

- `ChapterA_ArtificialMaterials`
- `ChapterC_Coatings`
- `ChapterL_Liquids`
- `ChapterM_Minerals`
- `ChapterO_OrganicCompounds`
- `ChapterS_SoilsAndMixtures`
- `ChapterV_Vegetation`

Bu, ayni Earth analog kutuphanesinin farkli sensör tepkilerine yeniden orneklenmis surumleriyle calistigimizi gosterir.

## 3) Onek farklari

### CRISM joined MTR3
- Dosya oneki: `s07CRSMj_`
- Ornek organik kayit:
  - `s07CRSMj_1-2-3-Trimethylbenzene_85K_ASDHRb_AREF.txt`
- Ornek biyolojik karisik kayit:
  - `s07CRSMj_Antigorite+.2DryGrass_AMX26_ASDFRa_AREF.txt`

### CRISM global
- Dosya oneki: `s07CRSMg_`
- Ornek organik kayit:
  - `s07CRSMg_1-2-3-Trimethylbenzene_85K_ASDHRb_AREF.txt`
- Ornek biyolojik karisik kayit:
  - `s07CRSMg_Antigorite+.2DryGrass_AMX26_ASDFRa_AREF.txt`

### ASTER resampled
- Dosya oneki: `S07ASTER_`
- Ornek organik kayit:
  - `S07ASTER_1-2-3-Trimethylbenzene_85K_ASDHRb_AREF.txt`
- Ornek biyolojik karisik kayit:
  - `S07ASTER_Antigorite+.2DryGrass_AMX26_ASDFRa_AREF.txt`

## 4) Teknik yorum

### CRISM joined MTR3 neden daha guclu
- `s07CRSMj` paketi daha ayrintili CRISM hedef moduna karsilik gelir.
- Organik, kaplama ve mineral bantlarini daha ayrintili ayirmak icin daha uygundur.
- Mars orbital teyit adiminda once bu paketle bakilmasi daha dogru olur.

### CRISM global neden gerekli
- `s07CRSMg` paketi daha genis alan taramasi icin uygundur.
- Aday bolgeleri hizli filtrelemek, sonra `s07CRSMj` ile ayrintilandirmak icin kullanilabilir.

### ASTER paketi neden hala degerli
- `S07ASTER` Earth tarafinda multispektral analog testleri icin pratiktir.
- Planetary sensör kadar ayrintili degildir ama Earth analoglarini daha basit bant setlerinde karsilastirmaya izin verir.

## 5) Ornek spektrum tablosu

| Paket | Chapter | Ornek dosya | Ilk 9 kanal izi | Ilk 9 deger ozeti | Teknik yorum |
| --- | --- | --- | --- | --- | --- |
| EARTH-010 `s07CRSMj` | OrganicCompounds | `s07CRSMj_1-2-3-Trimethylbenzene_85K_ASDHRb_AREF.txt` | `. - : = + * # % @` | `min=0.870269`, `max=0.960875`, `delta=+0.090606` | ilk kanallarda belirgin ve duzenli artis var; CRISM joined mod organik referansi daha kararlı bir yukselen imzaya indirgemis gorunuyor |
| EARTH-011 `s07CRSMg` | Minerals | `s07CRSMg_Acmite_NMNH133746_Pyroxene_BECKa_AREF.txt` | `+ * @ * = - . . .` | `min=0.036726`, `max=0.046683`, `delta=-0.005526` | mineral ornek dusuk genlikte ve dar bir aralikta seyrediyor; global mod hizli tarama icin yeterli ama ayristirma gucu daha sinirli |
| EARTH-012 `S07ASTER` | Coatings | `S07ASTER_Blck_Mn_Coat_Tailngs_LV95-3_BECKb_AREF.txt` | `. . . = % % % % @` | `min=0.067343`, `max=0.154511`, `delta=+0.087169` | kaplama/taklitci spektrum bile ilk bantlarda keskin artis uretiyor; bu nedenle coating negatif kontrolleri zorunlu |

Kanal izi satirlarinda karakterler dusukten yuksege dogru goreli genligi temsil eder. `@` en yuksek, `.` en dusuk goreli seviyeyi gosterir.

### Kanal-kesit ozeti

- EARTH-010 `s07CRSMj`: `0.870269, 0.883441, 0.896495, 0.909259, 0.921666, 0.933514, 0.944443, 0.953661, 0.960875`
- EARTH-011 `s07CRSMg`: `0.042252, 0.043104, 0.046683, 0.043555, 0.040636, 0.038980, 0.037900, 0.037007, 0.036726`
- EARTH-012 `S07ASTER`: `0.067343, 0.069915, 0.073372, 0.106974, 0.150917, 0.152710, 0.154343, 0.151302, 0.154511`

Tablodaki `delta`, ilk 9 ornek icinde son deger ile ilk deger arasindaki farki ifade eder. Bu basit metrik tek basina siniflandirma yapmaz; yalnizca erken kanal davranisinin kabaca nasil degistigini gosterir.

## 6) Biyoi̇saret acisindan cikan sonuc

- `ChapterO_OrganicCompounds` varligi, organik ve biyokimyasal bilesenleri sensör cevabina indirgenmis halde test etmemizi saglar.
- `ChapterV_Vegetation` varligi, salt organik kimya degil biyolojik materyal ve karisik saha spektrumlarini da karsilastirmaya izin verir.
- `ChapterC_Coatings` ve `ChapterM_Minerals` varligi kritik onemdedir; cunku biyoi̇saret adaylarini abiyotik taklitcilerden ayirmak icin ayni paket icinde negatif kontrol bulunur.

## 7) Operasyonel kullanim sirasi

1. Earth multispektral analoglari icin `EARTH-012` ile kaba tarama yap.
2. Mars orbital genis alan adayligi icin `EARTH-011` ile CRISM global eslesmesi kur.
3. Guclu adaylarda `EARTH-010` ile CRISM joined MTR3 karsilastirmasi yap.
4. Yorumlari `EARTH-004` ve `EARTH-005` morfolojik analoglari ile capraz kontrol et.
5. Nihai guveni `EARTH-006` ve `EARTH-007` kimyasal analog mantigi ile destekle.

## 8) Otomatik ozet cikti

- Bu paketin makinece taranmis ozetleri `raw/earth/usgs_splib07/usgs_spectral_summary.csv` dosyasina yazilir.
- Ureten arac: `spectral_summary.py`
- Varsayilan komut:
  - `python .\spectral_summary.py`

CSV icindeki temel alanlar:

- `chapter`: spektrumun ait oldugu kutuphane bolumu
- `sample_count`: gecerli sayisal kanal sayisi
- `global_min`, `global_max`, `global_mean`: tum spektrum ozetleri
- `first_n_delta`: ilk 9 kanal icindeki net degisim
- `first_n_trace`: ilk 9 kanal icin ASCII iz
- `first_n_values`: ilk 9 kanal degerinin acik listesi

Arac, `NaN` ve asiri buyuk sentinel degerleri ayiklayarak yalnizca gecerli sayisal kanallari raporlar.