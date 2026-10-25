# PayPal AI Hackathon içi rakip taraması (25 Eki 2026)

[23 Ekim taramasının](2026-10-23-rakipler.md) devamı; bu sefer yalnızca **bu hackathon'a girdiğini söyleyen projeler** ve hackathon sayfasının kendisi. Kaynak: Sena'nın LinkedIn'de bulup ekran görüntüsüyle paylaştığı gönderiler ve Devpost sayfası. Devpost bu oturumun ağından engelli olduğu için Devpost bilgileri web aramasıyla toplandı; gönderiler ekran görüntüsünden okundu, projelerin kodu açılmadı. Hepsi kendi beyanları.

## Hackathon gerçekleri (Counterfoil'u etkileyenler)
- Teslim **12 Kas 2026, 12:00 PST** (Türkiye 23:00). Katılımcı 12.000+ (Channel3 gönderisi).
- Şart: PayPal geliştirici platformu (sandbox) + bir AI aracı/modeli, merkezi olarak. Braintree kurallarda uygun servisler arasında sayılıyor.
- Teslim: çalışan prototip (mockup kabul edilmiyor), lisanslı herkese açık repo, **3 dakikadan kısa video**, jürinin çalıştırabileceği kurulum talimatı veya canlı demo adresi.
- Kriterler: teknik uygulama, tasarım, potansiyel etki, yenilik, sunum. Sunum: "video projeyi uçtan uca çalışırken gösteriyor mu, problemi ve hedef kitleyi anlatıyor mu".
- Özel ödüller ($5.000): Most Creative, Most Impactful, Best Demo Delivery, Best Use of PayPal + AI, **Best Use of Agentic Commerce**.
- Doğrulanmamış: toplam havuz ($67.500 nakit / $69.750 toplam; eski gönderilerde $60.000+), jüri tarihleri, kriter ağırlıkları, proje başına ödül sınırı.

## Sponsor ödülleri ve Counterfoil'a uyum
| Sponsor | Ödül | Uyum |
|---|---|---|
| AG Grid | $5.000 / $2.000 / 3×$1.000 | **Hazır**: `dashboard/` `ag-grid-community`/`ag-grid-react` 36.2.0 ve AG Studio kullanıyor. Devpost metninde açıkça söylenmeli. |
| Bryntum | 3×$1.000 | **Doğal**: bekletilen ödemeler (`CHARGE_NEEDS_CONFIRMATION`) için Scheduler zaman çizelgesi. Bryntum ticari; MIT repoyla lisans uyumu önce kontrol edilmeli. |
| Render | $1.000 / $750 / $500 kredi | **Kolay**: `render.yaml` var; jürinin "çalıştırabilme" şartını da karşılar. |
| APIMatic | 3×$1.000 + 6 ay Business | **Şartlı**: APIMatic Context Plugins ile PayPal Server SDK kodu yazılırsa (ör. PayPal REST rail). Bugünkü kod Braintree Python SDK; Python desteği doğrulanmadı. |
| Channel3 | $1.500 | **Zorlama**: 100M+ ürünlük katalog API'si. Counterfoil'un doğruluk kaynağı mağazanın kendi kaydı; dış katalog daha zayıf kanıt. Önerilmiyor. |

Sponsor şeridindeki Postman, Zapier, Elastic, Kernel, Astropods için ayrı ödül bulunamadı (araç sponsoru gibi görünüyor).

## Rakipler
| Proje | Ne yapıyor | Koruma iddiası | Ölçüm | Counterfoil'a yakınlık |
|---|---|---|---|---|
| **Patrizia Giampà** (adı yok; Zapier + Claude + PayPal sandbox, "no-code"; teslim 9 Kas'ta) | Ajanın neye ödeyebileceğine karar veren kapı; ekranda "Emergency fund cap $500", "Trusted contact" alanları | "AI önerebilir, parayı yalnızca sabit kurallar hareket ettirir; her geri alınamaz adım insan onayı ister" | gönderide yok | **En yakın ilke.** Ama tüketici/aile tarafı görünüyor ve koruma büyük ölçüde tutar tavanı. |
| **ClipPay** (Ivan Petrov; PayPal + Gemini + Next.js + Cloudflare, tek kişi, 3 gün) | Hasarlı ürün fotoğrafından kısmi iade; ürün iade edilmiyor | "AI asla parayı belirlemez; yalnızca hasarı tarif eder, tutarı satıcı kurallarıyla test edilmiş kod belirler; AI kandırılıp fazla ödetilemez" | gönderide yok | Satıcı tarafı iade, aynı slogan. Ama AI'ın verdiği **hasar derecesi tutarın girdisi**: abartılmış/manipüle fotoğraf tutarı yükseltebilir. |
| **ScamShield** (Ajeet Gupta; teslim edildi, ~11 Eki; Gemini + PayPal Orders API, Webhooks, Agent Toolkit, JS SDK; Render) | Alıcıya gelen mesaj/link/faturayı ödemeden önce puanlar; güvenli görünürse PayPal checkout'u açar. Ajan yok, satıcı yok. Ayrıca Chrome eklentisi prototipi ve "Security Inspector" (Decision Log, Tamper Test, Webhook Stream, Attack Matrix) | "Check before you pay"; AI + kurallar, sandbox, para hareket etmiyor | **40 etiketli test isteği** (ekranda) | Düşük: insan alıcıyı insan dolandırıcıya karşı korur. Karar AI + kural puanında. Ama "test ettik" iddiası artık tek başına ayırt edici değil. |
| Jochen Schultz (rakip değil, şüpheci yorum) | — | "AI ajanına ödeme yetkisi = maymuna makineli tüfek; bunu mümkün kılan şey varsa AI'ın rolü kalmamıştır" | — | Videonun açılış kancası olarak kullanılabilir (aşağıda). |

## GitHub'da yayınlanmış hackathon repoları
Web aramasıyla bulundu (4 arama, 25 Eki); yalnızca arama özetleri okundu, **kod ve README'ler açılmadı**, iddialar repoların kendi beyanı. Bu oturumun GitHub erişimi Counterfoil reposuyla sınırlı olduğu için klonlanmadı. Yaklaşık 30 repo çıktı; Counterfoil'a göre gruplandı.

**En yakınlar: satıcı tarafı, işlem kayda karşı kontrol**
| Repo | Ne yapıyor | Counterfoil'a göre |
|---|---|---|
| [Fizzl13 fizzl-paypal-guard](https://github.com/Fizzl13/x402-examples/pull/261) (PR) | Ajan ile PayPal Agent Toolkit arasında kapı; iade kuralları: ödeyen eşleşmesi, ödemede kalan bakiye, iade başına tavan, günlük limit; üstü sahip onayı. 25 çevrimdışı test | **Kontrol kümesi en çok benzeyen.** Sahiplik + kalan iade edilebilir tutar bizdeki kurallarla örtüşüyor. Ölçüm (saldırı/model) görünmüyor. |
| [antonmareo10 supplora-pay](https://github.com/antonmareo10/supplora-pay) | Tedarikçi faturasını Claude okur, imzalı irsaliye ve fiyat geçmişine karşı doğrular, sahip onayından sonra öder; faturadaki talimatı veri sayar | **"Kayda karşı doğrula" + belgeye gizli talimat** aynı fikir, ama ödeme (alacaklı tarafı), iade değil. |
| [AR-dev804 paypal-pulse-ai](https://github.com/AR-dev804/paypal-pulse-ai) | Satıcıya dönük ödeme operasyonu; "the payment agent that can't be tricked"; AI önerir, kod kapısı uygular | Aynı slogan, satıcı tarafı. |
| [StuartYo subguard](https://github.com/StuartYo/subguard) | Abonelik chargeback'lerini önleyen ajan (PayPal + Claude); tutarı model değil koddan PayPal capture'ından hesaplar; günlük tavan, 30 $ üstü insan onayı | Tutarın kaynağı kayıt: aynı ilke. |
| [mohanprasath-dev returngate](https://github.com/mohanprasath-dev/returngate), [rosh2525 refundpilot](https://github.com/rosh2525/refundpilot), [klat58688-ui refundgpt](https://github.com/klat58688-ui/refundgpt), [morganwhite-dev recall-runner](https://github.com/morganwhite-dev/recall-runner), [icey4826 clippay](https://github.com/icey4826/clippay), [Josefusan payback.ai](https://github.com/Josefusan/payback.ai) | Satıcı tarafı iade/geri ödeme iş akışları; çoğunda tutarı kod belirler, satıcı onaylar | İade yapan ajan + onay; saldırı ölçümü görünmüyor (payback.ai bir injection iadesinin engellendiğini gösteriyor). |

**Saldırı seti / değerlendirme olanlar**
| Repo | Ne ölçüyor | Counterfoil'a göre |
|---|---|---|
| [Aniket-pd payproof](https://github.com/Aniket-pd/payproof) | İade ajanları için "release check"; tek modelle (Codex) 18 geçti / 0 kaldı / 2 belirsiz, 20 kayıtlı karar + 3 kontrol yeniden değerlendiriliyor; PayPal sandbox doğrulaması | **Ölçüm yaklaşımında en yakın.** Tek model, ayrılmış holdout görünmüyor. |
| [midas-png paypal-agent-firewall](https://github.com/midas-png/paypal-agent-firewall) | Alıcı tarafı ödeme güvenlik duvarı; Z3 ile yetkinin kuralları aşamayacağının ispatı; 6 saldırılı "attack lab"; Agent Toolkit + MCP | Biçimsel ispat güçlü bir teknik iddia; alıcı tarafı. |
| [OkyWoww aegismandate](https://github.com/OkyWoww/aegismandate) | Yetki belgesi (mandate) tabanlı kontrol; 12 senaryolu saldırı seti; "injection tespiti çözüldü demiyoruz" | Alıcı tarafı; dürüst sınır yazımı bizimkine benziyor. |
| [arc585 breakpoint](https://github.com/arc585/breakpoint) | Satıcının PayPal checkout'una ve AI asistanına saldıran kırmızı takım; her açık için tek satırlık düzeltme | Tamamlayıcı (saldırgan araç), rakip değil. |
| [nikolas-sapa scope-to-deposit](https://github.com/nikolas-sapa/scope-to-deposit-paypal-ai-2026) | GLM ile 20 standart + 2 düşmanca vaka, bağımsız incelemede 1/20 tam geçiş | Depozito akışı. |

**Alıcı tarafı yetki/tavan kapıları** (çok sayıda; aynı desen): [andreyalchin Mandate](https://github.com/andreyalchin/Mandate-Agentic-Ecommerce-PayPal-AI-Hackathon-2026), [Aditya251610 SafePayAI](https://github.com/Aditya251610/SafePayAI), [Zhiyilang paypilot](https://github.com/Zhiyilang/paypilot), [luongs3 agent-spend-gate](https://github.com/luongs3/agent-spend-gate), [rayhannajla-hash procure-agent](https://github.com/rayhannajla-hash/procure-agent) (Channel3 kullanıyor), [sanjaysaini383 paypal (CartPilot)](https://github.com/sanjaysaini383/paypal), [Bajiyadav paypal-ai-agent](https://github.com/Bajiyadav/paypal-ai-agent), [AndreSierraM payguard-agent](https://github.com/AndreSierraM/payguard-agent) (iskelet), [devjuneja789 agentic-commerce](https://github.com/devjuneja789/agentic-commerce).

**GitHub taramasının sonucu**
- **"Ajan ile PayPal arasında deterministik kod + insan onayı" bu hackathon'un baskın deseni**; en az 15 repo bunu söylüyor. Satıcı tarafında da yalnız değiliz (fizzl-paypal-guard, Supplora Pay, PayPal Pulse AI, SubGuard).
- Bulunamayan şey: **çok modelli, ayrılmış holdout'lu, girişim/zarar ayrımlı ve tavanla karşılaştırmalı bir ölçüm.** En yakını PayProof (tek model, 20 vaka). Bu, arama özetlerine dayanan bir "bulunamadı"; "yok" demek değil.
- Bu yüzden Counterfoil'un savunulabilir farkı daraldı ve netleşti: **ölçümün biçimi** (holdout, 9+ model, tekrar, tavan karşılaştırması, gerçek Braintree sandbox) ve **okuyucu/uygulayıcı ajan ayrımı üzerinden e-postaya gizlenmiş talimat**. "Kayda karşı kontrol" ve "AI parayı belirlemez" tek başına fark değil.
- Teslimden önce fizzl-paypal-guard, Supplora Pay ve PayProof'un README'lerine bir insan gözüyle bakmak değerli; README'de atıf yapılabilir (23 Ekim dosyasındaki "Atıf yapılması gerekenler" listesine eklenmeli).

## Ortaya çıkan tablo
- **"AI parayı belirlemez" bu hackathon'da yaygın bir slogan.** İki ayrı proje neredeyse aynı cümleyi kuruyor. Tek başına ayırt edici değil.
- Fark kanıtta ve tasarım ayrıntısında.
- **Ölçüm de tek başına yetmiyor:** ScamShield 40 etiketli istekle test ettiğini söylüyor. Ayırt eden, ölçümün biçimi: ayrılmış holdout, 9+ model ve tekrar, girişim/zarar ayrımı, tavanla karşılaştırma, gerçek sandbox.

## Çıta örneği: ScamShield'ın teslimi
Teslim şartlarını eksiksiz karşılayan bir giriş; jüri bunu görmüş olacak:
- 2:56 demo videosu (https://youtu.be/2HSRVaYXA7I), Render'da canlı demo (https://scam-shield-paypal.onrender.com/pay), açık repo (https://github.com/gajit9147-dev/scam-shield-paypal).
- "Honest limits" paragrafı ("sandbox only, no real money; a cleared result is guidance, not proof").
- Saldırı tablosu ürünün içinde ("Attack Matrix"), karar günlüğü görünür.
- PayPal'ı geniş kullanıyor (Orders, Webhooks, Agent Toolkit, JS SDK). Counterfoil yalnızca Braintree + mocked PayPal kullanıyor ve Agent Toolkit kullanmadığını README'de söylüyor. Devpost metninde tek cümleyle: Braintree bir PayPal servisi ve PayPal'ın onayıyla seçildi (ADR 0007); kapı rail'den bağımsız (in-memory ve Braintree rail'de aynı kapı).
- Gönderide PayPal Devpost, Jo Franchetti, Marco Podien, Eddie Jaoude etiketli; muhtemelen PayPal geliştirici ilişkileri / jüri (doğrulanmadı).

## Counterfoil'un farkları (bu iki rakibe karşı)
1. **Tutarın kaynağı modelin çıktısı değil, mağaza kaydı.** Model ne söylerse söylesin tutar RMA/sipariş kaydından gelir; modelin önerdiği tutar o kayda karşı kontrol edilir. (ClipPay'de AI'ın derecesi tutarı belirliyor; Patrizia'da tavan.)
2. **Tavanın işe yaramadığı ölçüldü.** README: "$200 cap (the kind of guard most agent-payment projects ship)… The cap blocked nothing." Saldırılar tavanın altında kalıyor.
3. **İddia değil ölçüm.** Dev + ayrılmış holdout, saldırı/meşru istek ayrı, 9+ model, tekrarlı koşular; senaryolu en kötü ajan gerçek Braintree sandbox'ında 0/14 zarar.
4. **Kör onay değil, kalemli onay.** Her ödeme alma işlemi insan onayına düşer, ama insan "6 × CUP @ 25.00 = 150.00 USD" gibi dökülmüş toplamı görür. "Her şeyi insana sor" itirazına cevap: meşru isteklerin tamamlanma/bekletilme oranı ayrıca ölçülüyor.
5. **Tek akış değil, herhangi bir ödeme ajanının önüne konan modelsiz kapı.** Model bağımsızlığı ölçümü bunu gösteriyor.
6. **Kendi hatasını raporluyor.** Eski kapıdaki qwen3 P7-01 zararı sonuçlarda duruyor ve kapı buna göre değişti (PR #8).

## Konumlandırma önerisi (video ve Devpost için)
- **Ana mesaj PayPal'ın güveni:** "Counterfoil, PayPal üzerinde satış yapan bir işletmenin AI ajanına iade ve ödeme yetkisi verebilmesini güvenli kılar. Ajan kandırılsa bile para ve müşteri verisi mağazanın kayıtlarının dışına çıkamaz." Müşteri verisi de korunuyor (P2: başka müşterinin siparişini okutma).
- PayPal'ın kendi zararını (chargeback vb.) azalttığımızı **iddia etmeyin**; ölçülmedi.
- **Açılış:** somut tek hikâye (gizli satır yüzünden 25 $ yerine 150 $ çekilen bardak, P7-01). ClipPay'in "$40 mug, arrived chipped" anlatımı bunun ne kadar hızlı anlaşıldığını gösteriyor.
- İsterseniz şüpheci cümleyle aç: "Ödeme yetkisi olan AI ajanı tehlikeli" → "Haklı; o yüzden parayı modele bırakmıyoruz" → sayılar.
- Sloganı kanıtla kur: "AI parayı belirlemez" yerine "ödeme ajanınız kandırılacak; ölçtük, tavan hiçbirini durdurmadı, Counterfoil hepsini durdurdu."
- **Jüri riski:** "AI'ın rolü yoksa Best Use of PayPal + AI nasıl?" Cevap: ajan e-postayı okuyor ve gerçek istekleri sonuçlandırıyor; Counterfoil altında da tamamlıyor (tablodaki "genuine requests" sütunu). Bunu sayıyla göstermek şart.

## Takip
- 10–11 Kas: Patrizia Giampà'nın projesi (9 Kas teslim) Devpost'ta görününce farkın Devpost metninde net yazıldığını kontrol et.
- LinkedIn'de başka rakip bulunursa bu tabloya ekle.

## Kaynaklar
- Devpost: https://paypalaihackathon.devpost.com/ · /rules · /resources (web aramasıyla)
- LinkedIn gönderileri (Sena'nın ekran görüntüleri, 25 Eki): PayPal Developer duyurusu; Alexander Schiff ve Channel3; Arsalan Khattak (Bryntum); APIMatic.io; Jochen Schultz; Patrizia Giampà; Ivan Petrov (ClipPay); Ajeet Gupta (ScamShield).
- İkincil: DevGrants Daily, The GenAI Magazine, Startup Grants India, Parsec AI Labs, Course Joiner (tarih ve ödül ayrıntılarında birbiriyle çelişiyorlar).
