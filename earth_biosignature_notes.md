# Earth Biosignature Analogs

Bu dosya Earth analog veri setlerini Mars biyoi̇saret senaryolari ile eslemek icin tutulur.

## 1) Morfolojik analoglar

### Shark Bay stromatolitleri
- Manifest kaydi: EARTH-004
- Kaynak tipi: USGS saha goruntusu
- Temsil ettigi isaret: stromatolitik kubbe, kolon ve tabakali buyume geometrisi
- Mars eslesmesi: ince laminasyon, stromatolit-benzeri kubbeler, mikrobiyal mat benzeri sedimanter dokular
- Birlikte okunmali veri: kil, silis, karbonat veya evaporit baglami

### Yellowstone silisli sinter ve SEM filament korunumu
- Manifest kaydi: EARTH-005
- Kaynak tipi: USGS saha goruntusu + SEM goruntu
- Temsil ettigi isaret: fotosentetik mikrobiyal mat etrafinda silis kabuklanmasi ve filament bosluklari
- Mars eslesmesi: hidrotermal silis zenginlesmeleri, filamenter doku, mikro-gobekli biyofilm korunumu
- Birlikte okunmali veri: Raman, XRD, element haritalama, tekstur analizi

## 2) Kimyasal analoglar

### Arsenik turlesmesi olan mikrobiyal matlar
- Manifest kaydi: EARTH-006
- Kaynak tipi: USGS yayin / DOI referansi
- Olcum tipi: XAFS tabanli As turlesmesi
- Temsil ettigi isaret: EPS ile element baglanmasi, Fe-oksihidroksit ve mikrobiyal mat iliskisi
- Mars eslesmesi: redoks kontrollu element dagilimlari, biyolojik matris ile mineral etkilesimi, Fe-S-As benzeri jeokimyasal gradyanlar

### Yellowstone metilciva mikrobiyal matlari
- Manifest kaydi: EARTH-007
- Kaynak tipi: USGS yayin / DOI referansi
- Olcum tipi: jeokimyasal zenginlesme ve trofik aktarim
- Temsil ettigi isaret: mat biyokutlesinde MeHg birikimi ve biyolojik transfer
- Mars eslesmesi: dusuk derisimli bileşiklerin biyolojik konsantrasyonu, redoks dengesizligi, biyolojik niş isaretleri

## 3) Spektral analoglar

### Chapter O organics
- Manifest kaydi: EARTH-008
- Kaynak tipi: USGS Spectral Library ASCII spectra
- Icerik: amino asitler, alkanlar, alkenler, alkinler, aromatikler, lignin, seluloz, amiloz, nisasta
- Mars eslesmesi: Raman / VNIR / SWIR organik bant adaylari ve kimyasal islevsel grup eslesmesi
- Uygulama: organik bantlari abiyotik mineral bantlarindan ayirmak icin kutuphane referansi

### Chapter V biological materials
- Manifest kaydi: EARTH-009
- Kaynak tipi: USGS Spectral Library metadata + linked photos
- Icerik: bitki bilesenleri, likenler, biological soil crusts, karisik bitki ortamlari
- Mars eslesmesi: yuzey biyofilm benzeri kaplamalar, biyolojik kabuk yapilari, karisik organik-mineral sahalar
- Uygulama: spektral imza ile morfolojik baglami ayni anda kurmak

### CRISM uyumlu resampled layer
- Manifest kaydi: EARTH-010
- Kaynak tipi: USGS Spectral Library ASCII child item
- Icerik: CRISM global ve CRISM joined MTR3 konvolusyonlu kutuphane
- Mars eslesmesi: orbital Mars spektrasi ile Earth analog referanslarini ayni sensör cevabinda karsilastirma
- Uygulama: Earth analog kutuphanelerini CRISM odakli anomali taramasina baglamak

### CRISM global hizli tarama paketi
- Manifest kaydi: EARTH-011
- Kaynak tipi: USGS Spectral Library direct ASCII package
- Icerik: CRISM global mode konvolusyonu
- Mars eslesmesi: bolgesel orbital tarama ve genis alan aday filtreleme
- Uygulama: hizli eleme, dusuk spektral detayli ama genis alan uyum testi

## 4) Guven skoru kural seti

Bu Earth analoglari, [guven_skoru_karar_modeli.md](guven_skoru_karar_modeli.md) icindeki ana terimleri kalibre etmek icin kullanilir; yeni bir paralel skor degil, mevcut alt skorlari besleyen referans katmanidir.

### Kural 1: Morfoloji tek basina karar vermez
- Yalnizca EARTH-004 veya EARTH-005 ile goruntu benzerligi varsa durum en fazla orta oncelikli aday kabul edilir.
- Sadece morfolojik uyum varsa `S_in_situ` artar, ama `S_final` yuksek guvene cikamaz.

### Kural 2: Kimyasal teyit guven carpani verir
- EARTH-006 ve EARTH-007 turu element baglanmasi, redoks dengesizligi veya biyolojik zenginlesme benzeri bulgular varsa `S_chem_iso` guclu artirilir.
- Kimyasal sinyal yoksa, morfoloji ve spektral uyum ne kadar yuksek olursa olsun nihai etiket temkinli tutulur.

### Kural 3: Spektral uyum iki seviyede okunur
- EARTH-011 ile CRISM global uyumu: aday tarama seviyesi
- EARTH-010 ile CRISM joined MTR3 uyumu: ayrintili orbital teyit seviyesi
- EARTH-008 ve EARTH-009 ile organik/biyolojik kutuphane uyumu: bant kimligi ve baglam teyidi

### Kural 4: Abiyotik taklitci cezası zorunlu
- Evaporit, silis, demir oksit, kerogen ve kaplama spektrumlari da benzerlik verebilir.
- Organik veya biyofilm benzerligi iddiasi varsa mutlaka abiyotik taklitci spektrumlarla fark analizi yapilir.
- Bu ayrim zayifsa `R_contam` veya abiyotik-risk cezasi yukseltirilir.

### Kural 5: Yuksek guven esigi coklu-kanit ister
- Yuksek guven icin asgari kosul:
	1. morfolojik analog uyumu
	2. spektral analog uyumu
	3. kimyasal veya izotopik destek
- Bu ucluden biri eksikse sonuc ya orta guven ya da ek ornekleme gerekli sinifina dusurulur.

## 5) Pratik kullanim

1. Morfolojik aday bolgeleri EARTH-004 ve EARTH-005 ile etiketle.
2. Kimyasal guven katmanini EARTH-006 ve EARTH-007 ile kur.
3. Spektral esitligi EARTH-008, EARTH-009, EARTH-010 ve EARTH-011 ile test et.
4. Son karari tek bir iz uzerinden degil, morfoloji + kimya + spektral uyum birlikteligi ile ver.