# Derin Uzay Astrobiyolojisi: Biyo-İz Avı

## 1) Jeolojik oluşumların analizi

### Ay (Negatif Kontrol Gövdesi)

> **Not:** Ay, bu projede biyolojik potansiyeli en düşük gövde olarak değerlendirilir.
> Ay verileri (MOON-001..003) *negatif kontrol* işlevi görür:
> modelin düşük sinyal ortamında doğru "Düşük güven" etiketini üretip üretmediğini test eder.

Volkanik bazaltlar (mare), anortozit kabuk → düşük su aktivitesi → biyolojik potansiyel zayıf

Regolit stratigrafisi: mikrometeorit bombardımanı, cam kürecikler (agglutinates)

Permanently shadowed regions (PSR): krater içi buz depoları

Yöntemler

Yüksek çözünürlüklü görüntüleme + fotogrametri: stratigrafi, katman sürekliliği

Spektral haritalama (VNIR, SWIR): Fe²⁺/Fe³⁺ oranları, piroksen/olivin ayrımı

Nötron spektrometresi: hidrojen (su/ice proxy)

Yer radarı (GPR): gömülü buz, lav tüpleri

İzotop jeokronolojisi (U-Pb, Ar-Ar): yüzey yenilenme tarihleri

Mars
Delta/fan sistemleri, paleolakustrin çökeller, kil mineralleri (smektit), sülfatlar, silis zenginleşmeleri

Hidrotermal alterasyon zonları, damar yapıları (vein)

Sedimanter laminasyon (mikrobiyal mat analoğu olabilecek ince tabakalanma)

Yöntemler

Orbital + in-situ jeomorfoloji: delta morfometrisi, kanal ağları

Mineraloji (VNIR/IR, Raman, XRD): kil/sülfat/silika faz tayini

Mikro-doku analizi (µ-imaging): laminasyon, stromatolit-benzeri yapılar

Jeokimyasal haritalama (LIBS, XRF): element dağılımı ve redoks gradyanları

2) Görsel işaretlerin (morfolojik biosignature) analizi
Hedef işaretler
Mikrometre–milimetre ölçekli stromatolitik kubbeler, sütunlar

Filamenter/koloni benzeri yapılar (biyofilmler)

Sediman içinde ritmik laminasyon (günlük/mevsimsel döngüler)

Yöntemler

Makro/mikro görüntüleme: stereo kameralar, mikroskopik imager

3D rekonstrüksiyon: fotogrametri/LiDAR ile yüzey topolojisi

Tekstür metrikleri: fraktal boyut, yönlenme dağılımı (abiotik vs biyotik ayrımı)

Çapraz kesit inceleme: mikro-tomografi (µCT) ile iç yapı sürekliliği

Kontrol karşılaştırmaları: abiyotik analoglar (evaporit kristalleri, rüzgâr oyukları) ile istatistiksel ayrım

3) Kimyasal/biyokimyasal işaretlerin analizi
Hedef işaretler
Organik moleküller: aromatikler, alifatik zincirler, potansiyel biyomarkerlar (lipid türevleri)

İzotopik fraksiyonasyon: δ¹³C, δ³⁴S, δD (biyotik süreçler genelde hafif izotop zenginleşmesi üretir)

Redoks çiftleri: Fe²⁺/Fe³⁺, S²⁻/SO₄²⁻ dengesizlikleri

Perklorat/oksidan ortam etkileri (özellikle Mars’ta organik bozunma)

Yöntemler

GC-MS / Pyrolysis-GC-MS: uçucu/yarı uçucu organikler

LC-MS: termal bozunmaya hassas bileşikler

Raman spektroskopisi: organik bantlar + mineral bağlamı birlikte

FTIR: fonksiyonel grup tayini

İzotop oran kütle spektrometrisi (IRMS): δ ölçümleri

Elektrokimya sensörleri: redoks profilleri, oksidan yük

4) Operasyonel mimari (uçuş + yüzey)
Orbital keşif → iniş sahası seçimi: suyla ilişkili litolojiler, düşük radyasyon gömülme derinliği

Rover/lander enstrüman seti: kamera + Raman + XRD + LIBS + GC-MS

Örnek seçimi: ince taneli, hızlı gömülmüş, kil/silika matrisli hedefler

Derin örnekleme: 5–10 cm+ (radyasyon/oksidan etkisinden kaçınma)

Sterilizasyon ve kontaminasyon kontrolü: biyolojik “false positive” riskini minimize etme

5) Veri füzyonu ve karar verme
Çoklu kanıt yaklaşımı (converging lines of evidence)

Morfoloji + mineralojik bağlam + organik kimya + izotoplar birlikte tutarlı olmalı

Bayesyen çıkarım

P(yaşam | veri) = farklı sensörlerden gelen olasılıkların güncellenmesi

Makine öğrenmesi

Spektral imza sınıflandırma (CNN/Transformer tabanlı), anomali tespiti

Yanlış pozitif/negatif analizi

Abiyotik süreçlerin taklit kapasitesi (örn. silika çökelmeleri, evaporitler)

6) Ay vs Mars karşılaştırmalı risk
Parametre	Ay	Mars
Su geçmişi	Çok sınırlı	Güçlü kanıt (eski göller/deltalar)
Radyasyon	Çok yüksek	Orta (atmosfer zayıf)
Oksidanlar	Düşük	Yüksek (perklorat)
Organik korunumu	Zayıf	Gömülü ortamlarda mümkün
Yaşam potansiyeli	Çok düşük	Düşük–orta (geçmişte daha yüksek)
7) Kritik ayrım kriterleri
Morfoloji tek başına yeterli değil

İzotopik fraksiyonasyon + spesifik organikler + uygun jeolojik bağlam birlikte gerekli

Tekrarlanabilirlik: farklı lokasyon/örneklerde benzer sinyaller

Kontaminasyon dışlama: Dünya kaynaklı organiklerin izlenmesi (blank, witness plate)

## 8) Teleskop Verisi Köprüsü (SDSS DR17)

Bu projede TELESKOP-001..007 satırları SDSS DR17 FITS spektral dosyalarıdır.
Bunlar doğrudan Mars/Ay biyoiz pipeline'ına girmez. Kullanım senaryoları:

- **Yıldız kompozisyon taraması:** Hedef yıldız sistemlerinin metallisite ve element
  dağılımı, yaşanabilir bölge potansiyelini etkiler.
- **Ekzogezegen atmosfer öncül taraması:** SDSS spektrumları geniş alan taramasında
  ilginç hedefleri filtreleyebilir.
- **Uzaktan algılama pipeline testi:** `S_remote` katmanının FITS dosyalarla
  çalışabilirliğini test etmek için referans veri seti.

SDSS verileri şu anda `spectral_summary.py` ile işlenmiyor (ZIP olmayan FITS format).
İleride `astropy` bağımlılığı eklenerek FITS → özellik çıkarma entegrasyonu yapılabilir.