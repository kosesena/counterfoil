# PayPal AI Hackathon — proje taslağı v2 (22 Eki 2026, onay bekliyor)

Çalışma adı: **PayGate** (değişebilir). Aynı proje Vultr Agent Rush'a da gidecek. Kod henüz yok.
v2: Codex incelemesi işlendi ([inceleme/2026-10-22-codex.md](inceleme/2026-10-22-codex.md), 10 bulgu, hepsi kabul).

## 1. Fikir ve kim için
**Tek cümle:** Gelen fatura e-postasını okuyup PayPal üzerinden ödeyen bir ajan; ajanla PayPal arasındaki geçit, her ödeme çağrısını işletmenin kendi borç kaydıyla karşılaştırır ve e-postaya gizlenmiş talimatla değişmiş tutarı, alıcıyı ya da mükerrer ödemeyi para çıkmadan durdurup insana sorar.

**Kim için:** Tedarikçi faturalarını e-postadan alıp ödeyen ve bu işi bir ajana devretmek isteyen küçük işletme. Sorun gerçek: FBI IC3 2024 raporunda "Business Email Compromise" (e-postayla ödeme yönlendirme) 21.442 şikâyet, 2.770.151.146 $ kayıp. Bugün bunu yakalayan insan; ödeme ajana geçince e-postadaki gizli bir satır ajanı doğrudan yönlendirebilir.
Bitirme projesindeki benzer geçit (ERPNext, 22 Eki) adet şişirme saldırılarında ERP'ye geçişi 0/21'e indirdi, ama bu düşüşün tamamı geçide ait değil (A01 başka bir nedenle durdu). Videoda yalnız bu projede ölçtüğümüzü, bileşenlerine ayırarak vereceğiz.

## 2. Akış, güven kaynağı ve PayPal API'leri
```
e-posta → Okuyucu ajan (aracı yok) → yapılandırılmış alanlar + "not" alanı
        → Ödeme ajanı (ham e-postayı görmez) → GEÇİT → PayPal sandbox
                                                  ↘ şüpheli → insan onayı (panel)
```
- **Güven kaynağı e-posta değil, borç kaydı.** E-posta hem gerçek hem saldırganın tutarını içerebilir; ondan iki kez çıkarım yapmak bağımsız doğrulama sayılmaz (Codex #1). Geçidin dayandığı tek referans işletmenin kaydı: tedarikçi kimliği, **onaylı PayPal alıcı adresi**, açık faturalar, para birimi, kalan bakiye. Demoda bu küçük bir yerel tablo (bitirmede ERPNext'in yaptığı iş). Bu yüzden "A01 kapandı" demiyoruz; ham e-postadaki çelişkili tutar/hesap ifadeleri yalnızca ek bir işaret olarak ONAY'a yönlendirir.
- **Ajanlar arası şema sabit:** Okuyucu yalnız `tedarikci, fatura_no, tutar, para_birimi, not` aktarır. `not` alanı bilerek açık bırakılıyor; P4 saldırısının ulaşabildiği tek yüzey bu ve orada sınanıyor (Codex #5).
- **Tek kapı gerçekten tek:** PayPal kimlik bilgileri yalnız geçit sürecinde; ajanlar PayPal'a başka yoldan ulaşamaz. Oturum bağlamı eksikse yazma reddedilir. Oturum durumu çağrı başına taşınır (bitirmedeki global `AKTIF` değişkeni çok oturumlu serviste kullanılmayacak). İnsan onayı; işlem, oturum ve **tam argümanlara** bağlı, süreli ve tek kullanımlık; onaylı işlem yürütülürken mükerrer kontrolü yeniden yapılır (Codex #4).
- **PayPal parçaları** (paypal/agent-toolkit README'si ve sandbox MCP `mcp.sandbox.paypal.com/sse`, 22 Eki kontrol edildi):
  - **Payouts REST** — ödeme yönü, demonun merkezi. Toolkit'te Payouts aracı yok; kendi MCP aracımız. `sender_batch_id` = tedarikçi + fatura kimliği → tekrar gönderilen istek PayPal tarafında da tekrar ödeme açmaz.
  - **Agent Toolkit (Python) / MCP — Invoicing:** `create_invoice`, `send_invoice`, `get_invoice`, `list_invoices`; ikinci yön (müşteri siparişine fatura kesme). `list_transactions` uzlaştırma ve panel için.
  - **Orders:** kullanılmıyor (alıcı onaylı checkout akışı, B2B ödemeye uymuyor).
- **Ana yön ilk sandbox denemesiyle seçilir** (Codex #8): Payouts sandbox'ta çalışıyorsa ödeme ana akış; çalışmıyorsa senaryolar Invoicing yaşam döngüsüne göre yeniden yazılır. Mock ile gerçek ödeme taklit edilmeyecek.
- "Agentic commerce" bir mansiyon, Grand ile birlikte alınamıyor (bkz. 4); tema olarak duruyor, hedef değil.

## 3. Saldırı/koruma senaryoları
Metinleri Codex yazacak (Sena onaylayınca); her örnekte doğru işlem, saldırganın hedefi ve beklenen karar **koşudan önce** sabitlenir, Sena metinleri ve referansları okur.

| # | Senaryo | Geçidin kontrolü → karar |
|---|---|---|
| P1 | Tutar değiştirme (HTML notu/alıntı yazışma; varyant: aynı sayı farklı para birimi) | tutar + para birimi ≠ kayıttaki kalan bakiye (kesin ondalık) → ONAY |
| P2 | Alıcı değiştirme (varyant: bilinmeyen hesap / **başka bir kayıtlı tedarikçinin** hesabı) | alıcı ≠ bu tedarikçinin onaylı adresi → ONAY; hesap değişikliği teyidi kayıtlı kanaldan |
| P3 | Mükerrer ödeme ("ulaşmadı, tekrar gönder"; önkoşul: tamamlanmış / bekleyen / başarısız / belirsiz) | yerel kalıcı durum + atomik rezervasyon + `sender_batch_id`; belirsizse yeni ödeme açmadan uzlaştır → ENGEL |
| P4 | `not` alanından Ödeme ajanına "ödemede düzelt" yönlendirmesi | çağrıdaki alan ≠ Okuyucu'nun aktardığı ve kayıttaki alan → ONAY |
| P5 | Mutabakat bahanesiyle başka tedarikçilerin faturalarını isteme (yetkisiz araç / izinli aracın yetkisiz kapsamı) | araç + kapsam denetimi → ENGEL; sonraki ödeme ONAY. Okuma ile dışarı aktarım ayrı sayılır |
| P6 | Bölme: tek faturayı birkaç çağrıya ya da oturuma bölüp bakiyeyi aşmak | fatura bazında oturumlar arası toplam ≤ kalan bakiye → ONAY |

**Temiz set** saldırı satırı silinmiş eşlerden ibaret değil: vergi, farklı sayı biçimi, taksitli ödeme, eski yazışma alıntısı, meşru yeniden deneme, önceden onaylı hesap değişikliği. Kuralları geliştirirken kullanılmayan birkaç varyasyon son ölçüme ayrılır. Talimat kalıbı listesi (K3) yalnız işaretçi; bitirmede 0/36 yakaladı.

**Ölçüm (Codex #6–7):** her koşuda ayrı kayıt — referans, Okuyucu çıktısı, tüm araç girişimleri, geçit kararları, PayPal'a ulaşan çağrılar, doğrulanmış son durum. Raporlanan ayrı sayılar: saldırı girişimi oldu mu / geçit müdahale etti mi / zarar oluştu mu / meşru iş tamamlandı mı; eksik kanıt "bilinmiyor". Aynı senaryolar **geçit açık ve kapalı** koşulur; kurallar ayrıca LLM'siz sabit çağrılarla test edilir. Senaryo sayısı ve tekrar sayısı ayrı yazılır, tekrarlar farklı günlere yayılır.

## 4. Ödül hedefi
Kural: en fazla 1 Grand + 1 Sponsor ya da 1 Mansiyon + 1 Sponsor. Hedef **Grand + Best Use of AG Grid**. Jüri 5 eşit ölçüt: teknik uygulama, tasarım, gerçek sorun/etki, özgünlük, sunum.

**AG Studio paneli** (React, 45 günlük deneme, PayPal şablonu Discord'dan, lisans anahtarı env'de):
- Bekleyen onaylar: tedarikçi, fatura, kayıttaki / Okuyucu'nun çıkardığı / istenen tutar ve alıcı yan yana, tetiklenen kontrol, Onayla/Reddet (onay sunucuda doğrulanır).
- Geçit kararları: GEÇİŞ/ONAY/ENGEL dağılımı, kontrole göre sayılar, **"incelemeye alınan işlem tutarı"** — "önlenen kayıp" denmeyecek, aynı çağrının tekrarı bir kez sayılır.
- Ödenenler (`list_transactions`). Özel widget (üç değer yan yana fark kutusu) + tema.

**Studio Agent Framework:** geçit şüpheli işlem yakalayınca kendi ajanımız Studio'nun ajanlarıyla konuşup o işleme özel widget kurar (AG Grid'in "anomaly-alert agent" örneğinin uyarlaması). Widget yalnız izinli veri ve bileşenlerden kurulur; e-posta içeriği widget'a ya da onay düğmesine talimat veremez; ajan widget kurar, onay veremez. Dinamik widget gecikirse sabit onay ekranı çalışmaya devam eder.

## 5. Demo videosu (< 3 dk, İngilizce)
1. **0:00–0:20 Sorun:** e-postayla gelen fatura, ödemeyi ajana devreden işletme; IC3 rakamı kaynağıyla.
2. **0:20–0:40 Mimari:** iki ajan, borç kaydı, geçit, PayPal sandbox.
3. **0:40–1:05 Temiz akış:** fatura → Okuyucu → Ödeme ajanı → GEÇİŞ → sandbox'ta ödeme ve durum.
4. **1:05–1:40 Containment moment:** aynı fatura, gizli satırla alıcı + tutar değişmiş; ajan kandırılır, çağrıyı yapar; geçit durdurur. Kanıt: geçit izindeki istek kimliği + o `sender_batch_id` için PayPal'da işlem olmadığı.
5. **1:40–2:05 Panel:** geçit ajanının kurduğu widget üç değeri yan yana gösterir; insan reddeder.
6. **2:05–2:25 Mükerrer / bölme:** ENGEL ve ONAY.
7. **2:25–2:45 Ölçüm:** geçit açık/kapalı tablo, gereksiz müdahale ayrı — ne çıkarsa o.
8. **2:45–2:58 Kapanış:** repo, MIT, nasıl çalıştırılır.

## 6. Takvim
- **22 Eki–2 Kas — PayPal çekirdeği:** yeni public MIT repo; borç kaydı + iki ajan + geçit + P1–P6 + temiz set + LLM'siz kural testleri; mock PayPal ile başla (yalnız geliştirme için). **Erken denemeler (bu hafta):** sandbox gelirse Payouts uçtan uca tek çağrı → ana yön kararı; AG Studio şablonunda tek widget + tek ajan çağrısı (Codex #10).
- **3–8 Kas — Vultr eklentisi (Blast Radius Zero, karar 22 Eki):** Vultr VM + web uygulaması, LLM çağrıları Serverless Inference. Okuyucu ajan PDF faturadan alan çıkaran kodu kendisi yazar; bu kod Docker sandbox'ta (ağ kapalı, salt-okuma dosya sistemi) çalışır. İki ayrı durdurma katmanı: sandbox, kodun dosya/ağ girişimini durdurur; geçit, kandırılmış ödemeyi durdurur. Vultr videosunda ikisi ayrı ayrı gösterilir. README'de "çekirdek 22 Eki'den beri, Vultr katmanı 3–8 Kas'ta" açıkça yazılır.
- **9–12 Kas — PayPal'a özgü:** panel cilası, ölçüm, video, Devpost formu. **Teslim 12 Kas 23:00 TR** (12:00 PT); hedef öğlen.
- Bitirme raporları Perşembe: 29 Eki, 5 Kas, 12 Kas (bu, 11 Kas'ta hazır olmalı).

## 7. Açık riskler ve kararlar
- **TR'den PayPal geliştirici hesabı:** Discord'da soruldu (22 Eki), cevap yok. Yedek Braintree sandbox'ta Payouts/Invoicing yok → akış "tahsilat"a kayar, 2–3 yeniden yazılır. **Karar tarihi 29 Eki.**
- **Payouts sandbox'ta kapalı olabilir** → ana yön Invoicing'e döner (bkz. 2); "merkezde" şartının jüri gözünde karşılanması doğrulanmadı.
- **Vultr track: Blast Radius Zero (karar 22 Eki).** Lablab'da tek yol seçiliyor ("Choose one path"); ödüller iki track için ortak havuz. Track'in "kod yazan/çalıştıran ajan" şartını PDF okuma kodu karşılıyor (bkz. 6); bu kod gerçekten iş görmeli, süs olmamalı. Lablab ön-kod kuralı belirsiz; Rule Book okunacak, kickoff'ta sorulacak.
- **AG Studio lisansı 45 gün:** erken denemeyle başlarsa (ör. 28 Eki) jüri döneminin sonundan (15 Ara) önce biter → jüri için ekran kaydına ve çalıştırma talimatına güvenilir; #ag-grid'de uzatma sorulacak.
- **Zaman:** Meta Global kabul gelirse (≤26 Eki) 26 Eki–4 Kas çakışır; takvim yeniden konuşulur. Model davranışı günden güne değişiyor → sabit model, birden çok gün.
