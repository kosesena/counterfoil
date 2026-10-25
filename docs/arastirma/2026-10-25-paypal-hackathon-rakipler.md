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
