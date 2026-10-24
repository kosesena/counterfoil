# Hackathon'daki rakip projeler (24 Eki 2026)

**Kaynaklar:**
- PayPal Developer Discord'daki `#what-i-built` kanalı. Sadece okundu, hiçbir şey yazılmadı.
- GitHub araması: bu hackathon için yaklaşık 120 repo var, çoğu boş ya da taslak.
- Devpost galerisi henüz yayımlanmadı, oradan bir şey görülemedi.

## Doğrudan rakipler (ajan ile PayPal arasında bir kontrol katmanı)

| Proje | Ne yapıyor | Olgunluk | Bizden farkı |
|---|---|---|---|
| **Stood** (github.com/ma-za-kpe/stood) | Aşamalı (milestone) ödemeler için açık kaynak serbest bırakma kapısı. Orders v2 ile tutarı tutuyor (authorize); imzalı kabul testleri geçerse ödüyor (RELEASE), geçmezse iptal ediyor (REFUSE), belirsizse insana soruyor (WAIT). Sloganı: "AI helps, never pays". | Çok olgun: 729 test, 61 PR, 24 mimari karar kaydı (ADR), CodeQL, OpenSSF, PayPal AI Toolkit (MCP), APIMatic; Render'da yayında. | Alıcı tarafında, emanet (escrow) ödemesi. Bizde ise para hareketini ajanın kendisi yapıyor; geçit mağazanın kayıtlarına bakıyor ve saldırılarla ölçülmüş. |
| **Bursar** (bursar-demo.onrender.com, video youtu.be/aMtzavsN-k0) | Ajan ile PayPal arasında harcama kontrolü. "Gizli talimatla kandırılma" tehdidini bizimle aynı cümleyle anlatıyor. Ajan önerir, kurallar karar verir, PayPal doğrular. | Demosu yayında, videosu hazır. | Alıcı tarafında, satın alma. Mağaza kaydı ya da iade kaydı (RMA) kontrolü yok, ölçüm yok. |
| **Spendwall** (github.com/AndrewDongminYoo/spendwall) | En yakın rakip. Mağazanın iade, itiraz ve fatura işini ajana veriyor, ajan ile PayPal arasına bir kural duvarı koyuyor. Karar mantığında LLM yok. Güvenilir ödeme bağlamı, ayırma (reservation), argümana bağlı onay, denetim izi, tehdit modeli, AG Studio paneli var. | Yaklaşık 97 test dosyası ve jüri rehberi var. Yayında demo yok; sandbox kanıtı kayıttan. | Mağaza kayıtlarıyla (RMA, sipariş sahipliği) karşılaştırma yok, çok modelli ölçüm yok. |
| **Gauntlet** (github.com/Yuvraj-Malik/Gauntlet) | Kırmızı takım (saldırı) ölçümü artı çalışma anı koruması. Saldırıları: alıcı değiştirme, tutar kaydırma, tavanın altına bölme, tekrarlanan tahsilat, sahte fatura. CaMeL ve AgentDojo'ya atıf yapıyor. | Erken aşamada, son push 5 Ekim. | Ölçüm fikri bize benziyor, ama yarım kalmış görünüyor. |
| **PHALANX** (github.com/maitray-agrawal/PHALANX) | İmzalı yetki belgeleri (mandate), kurallarla çalışan bir çekirdek (yetki yolunda LLM yok), içerik özetine bağlı ek onay, zincirleme kayıt defteri. | CI ve yaklaşık 43 test dosyası var. | Alıcı tarafında, yetki belgesi yaklaşımı. |
| **Countersign** (github.com/vincentvega011/countersign) | Satıcı tarafında. Tahsilat anında müşterinin onayını kriptografik olarak doğruluyor. | README'ye göre "henüz kullanılamaz". | Adı "Counterfoil"e çok benziyor; README'de ayrımı netleştirmek gerekebilir. |

## Daha uzak olanlar

- **İade ve itiraz otomasyonu (geçit yok):** Refund Sentinel, ReturnGate, FairPlay, PayGuard AI, dispute-autopilot, SubGuard.
- **ShopCrew:** ajanlar dükkânı yönetiyor, sahibi her kararı AG Grid'de onaylıyor. Yani insan onayı var, kural kontrolü yok.
- **Alıcı tarafı harcama kuralları:** Spend Guardrails, SpendGuard, Mandat, Leash, IntentLock, pulse-safe-commerce-agent.
- **Konusu farklı:** SarafuPay, AgentDeal, PayTrace AI, Unitus, Acquit, ShortWork, MergePay, Keel (Disputes API kullanıyor).

## Bizi ayıran (bugünkü durum)

1. **Mağazanın kendi kayıtlarıyla kontrol:** iade kaydı (RMA), sipariş toplamı ve sahiplik. Taradığımız projelerin hiçbiri bunu yapmıyor; onlar tavan, yetki belgesi ya da insan onayı kullanıyor.
2. **Ölçüm:** 8 model × 3 tekrar, üç koşul (geçitsiz, 200 $ tavan, Counterfoil). Tavanın hiçbir saldırıyı durdurmadığı sayılarla gösterilmiş. Başka kimsede bu ölçüm yok.
3. **Braintree üzerinden gerçek sandbox işlemi:** satış, iade ve müdür onayı canlı demoda çalışıyor. Taradığımız repoların hiçbirinde Braintree yok.

## Açıklarımız (rakiplere göre)

- **Mühendislik olgunluğu:** Stood'da 729 test, CodeQL, OpenSSF ve 24 ADR var. Bizde yaklaşık 200 test ve 7 ADR var.
- **PayPal REST ve Agent Toolkit kullanmıyoruz:** Stood, Bursar ve ShopCrew kullanıyor. Biz Türkiye'den hesap açamadığımız için Braintree kullanıyoruz.
- **Video:** Bursar'ın videosu hazır (2:49), bizim videomuz henüz yok.
