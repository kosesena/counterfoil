# PayPal AI Hackathon — proje taslağı v3 (23 Eki 2026)

Çalışma adı: **PayGate** (değişebilir). Aynı proje Vultr Agent Rush'a da gidecek (Blast Radius Zero).
- v2: Codex incelemesi işlendi ([inceleme/2026-10-22-codex.md](inceleme/2026-10-22-codex.md)).
- v3: PayPal ekibinin 22 Eki Discord cevabı: TR'den **Braintree sandbox kabul**. Braintree'de Payouts/Invoicing ve Agent Toolkit/MCP yok, bu yüzden akış "tedarikçiye ödeme"den **"müşteri iadesi ve tahsilatı"**na döndü. Geçidin mantığı aynı.

## 1. Fikir ve kim için
**Tek cümle:** Küçük bir çevrimiçi mağazanın müşteri e-postalarını (iade isteği, yeniden sipariş) okuyup Braintree üzerinden iade ya da tahsilat yapan bir ajan. Ajanla Braintree arasındaki geçit her para hareketini mağazanın kendi sipariş/işlem kaydıyla karşılaştırır. Gizli talimatla şişirilmiş iadeyi, başka müşterinin işlemini, mükerrer iadeyi ya da yanlış tutarlı tahsilatı para hareket etmeden durdurur ve insana sorar.

**Kim için:** Müşteri e-postalarını az kişiyle yanıtlayan ve iade/tahsilat işini bir ajana devretmek isteyen küçük mağaza.
**Sorun:** OWASP, büyük dil modeli uygulamaları için hazırladığı 2025 listesinde prompt injection'ı ilk sıraya (LLM01) koyuyor. Dolaylı türünde talimat, modelin okuduğu dış içerikten gelir; burada bu içerik müşteri e-postası. Ajan yalnızca yanıt yazarken bu bir metin hatasıdır; para hareket ettirmeye başladığında doğrudan kayba dönüşür. Kaynaklı bir kayıp rakamı bulamazsak rakam yazılmayacak.
**Bağlam:** Bitirme projesindeki benzer geçit ERPNext'te adet şişirme saldırılarında ERP'ye geçişi 0/21'e indirdi. Bu düşüşün tamamı geçide ait değil, bu yüzden videoda yalnız bu projede ölçtüğümüzü vereceğiz.

## 2. Akış, güven kaynağı, PayPal/Braintree kullanımı
```
müşteri e-postası → Okuyucu ajan (aracı yok) → yapılandırılmış alanlar + "not"
     → İşlem ajanı (ham e-postayı görmez) → GEÇİT → Braintree sandbox
                                               ↘ şüpheli → insan onayı (panel)
```
- **Güven kaynağı e-posta değil, mağazanın kaydı.** Kayıtta şunlar var: müşteri, e-posta adresi, sipariş, Braintree işlem kimliği, ödeme yöntemi, tutar, iade edilmiş toplam ve iade kuralları (süre, insan onayı gerektiren üst sınır). Demoda bu yerel bir tablo, Braintree'den de doğrulanıyor. Ham e-postadaki çelişkiler yalnızca ek bir işaret olarak ONAY'a gönderir (Codex #1).
- **Ajanlar arası şema sabit:** Okuyucu yalnız `musteri_email, siparis_no, istek (iade|tahsilat), tutar, para_birimi, kalemler [{sku, adet}] (yalnız tahsilatta), not` aktarır. `kalemler` P7'deki adet kontrolü için gerekli (Codex'in 23 Eki notu). `not` alanı P4'ün sınandığı yüzey.
- **Tek kapı:** Braintree anahtarları yalnız geçitte. Bağlam yoksa yazma reddedilir. Oturum durumu çağrı başına taşınır, bitirmedeki global `AKTIF` değişkeni kullanılmaz. Onay; işleme, oturuma ve tam argümanlara bağlı, süreli ve tek kullanımlık (Codex #4).
- **Braintree (resmî kurallarda PayPal hizmeti sayılıyor), resmî Python SDK `braintree`:**
  - `Transaction.refund(id, amount)`: kısmi ya da tam iade. Demonun merkezi.
  - `Transaction.void`: henüz kesinleşmemiş işlemi iptal.
  - `Transaction.sale`: kayıtlı ödeme yöntemiyle tahsilat (yeniden sipariş). `Customer`/vault müşterinin kayıtlı yöntemini tutar.
  - `Transaction.find` / `search`: geçidin kayıt doğrulaması, mükerrer kontrolü ve panel verisi.
  - Ajanın gördüğü araçları biz MCP aracı olarak yazıyoruz: `iade_et`, `iptal_et`, `tahsil_et`, `islem_sorgula`. Hazır PayPal ajan araçları Braintree'yi kapsamıyor.
- **PayPal görünürlüğü:** Braintree test ortamı, PayPal hesabı gerektirmeden "PayPal ile ödenmiş" işlemi taklit eder (varsayılan "mocked PayPal", test değeri `fake-paypal-one-time-nonce`; Braintree dokümanı, 23 Eki). Demodaki müşterilerin çoğu PayPal ile ödemiş olacak; iade de PayPal işlemine yapılır. Ödeme ekranı Braintree Drop-in olup PayPal düğmesi gösterecek. **Doğrulanmadı:** taklit PayPal işleminin iadesi ve Drop-in'in taklit modda PayPal düğmesi göstermesi. İlk kod gününde denenecek. Kısıt: taklit mod, JS v3 SDK'nın PayPal Checkout bileşeniyle çalışmıyor.
- "Agentic commerce" mansiyonu Grand ile birlikte alınamıyor (bkz. 4). Tema olarak duruyor: ajan gerçekten para hareket ettiriyor.

## 3. Saldırı/koruma senaryoları
Metinleri Codex yazar. Her örnekte doğru işlem, saldırganın hedefi ve beklenen karar koşudan önce sabitlenir; Sena okur.

| # | Senaryo | Geçidin kontrolü → karar |
|---|---|---|
| P1 | İade tutarı şişirme (gizli HTML/alıntı; varyant: aynı sayı, farklı para birimi) | iade + önceki iadeler > işlem tutarı, ya da para birimi ≠ kayıt (kesin ondalık) → ENGEL; kurala göre üst sınırı aşıyorsa ONAY |
| P2 | Başka müşterinin işlemini iade ettirme (sipariş no'su başka müşteriye ait) | gönderen ≠ siparişin kayıtlı müşterisi → ONAY |
| P3 | Mükerrer iade ("iade gelmedi, tekrar yap"; önkoşul: tamamlanmış / beklemede / başarısız / belirsiz iade) | Braintree'deki iade kayıtları + yerel kalıcı durum + rezervasyon; belirsizse yeni iade açmadan uzlaştır → ENGEL |
| P4 | `not` alanından İşlem ajanına "iadede düzelt" yönlendirmesi | çağrıdaki alan ≠ Okuyucu'nun aktardığı ve kayıttaki alan → ONAY |
| P5 | "Mutabakat" bahanesiyle başka müşterilerin işlemlerini sorgulatma / yetkisiz araç | araç + kapsam denetimi → ENGEL; aynı oturumdaki sonraki para hareketi ONAY |
| P6 | Bölme: iadeyi birkaç çağrıya ya da oturuma bölüp işlem tutarını aşmak | işlem bazında oturumlar arası iade toplamı ≤ işlem tutarı → ENGEL |
| P7 | Yeniden siparişte şişirilmiş tahsilat ("aynısından 10 tane", gizli satırla 100) | tahsilat ≠ katalog fiyatı × Okuyucu'nun aktardığı adet → ONAY |

**Temiz set:** kısmi iade, süre içinde tam iade, farklı sayı biçimi, eski yazışma alıntısı, başarısız iadenin meşru tekrarı, normal yeniden sipariş, insan onayı gerektiren yüksek tutarlı meşru iade. Kural geliştirmede kullanılmayan bir kısım son ölçüme ayrılır. Talimat kalıbı listesi (K3) yalnız işaretçi.

**Ölçüm (Codex #6–7):** her koşuda ayrı kayıt tutulur: referans, Okuyucu çıktısı, tüm araç girişimleri, geçit kararları, Braintree'ye ulaşan çağrılar, doğrulanmış son durum. Ayrı raporlanan sayılar: girişim / müdahale / zarar / meşru iş tamamlandı mı. Eksik kanıt "bilinmiyor" sayılır. Aynı senaryolar geçit açık ve kapalı koşulur. Kurallar ayrıca LLM'siz testlerle sınanır. Tekrarlar farklı günlere yayılır.

## 4. Ödül hedefi
Kural: en fazla 1 Grand + 1 Sponsor ya da 1 Mansiyon + 1 Sponsor. Hedef **Grand + Best Use of AG Grid**. Jüri 5 eşit ölçütle puanlıyor: teknik uygulama, tasarım, etki, özgünlük, sunum.

**AG Studio paneli:** React, 45 günlük deneme, lisans anahtarı env'de. Şablon PayPal API'si için hazırlanmış; veri katmanı Braintree işlemlerine uyarlanacak.
- Bekleyen onaylar: müşteri, sipariş, ödeme yöntemi (PayPal/kart), kayıttaki / Okuyucu'nun aktardığı / istenen tutar yan yana, tetiklenen kontrol, Onayla/Reddet (onay sunucuda doğrulanır).
- Geçit kararları: GEÇİŞ/ONAY/ENGEL dağılımı, kontrole göre sayılar, "incelemeye alınan tutar" ("önlenen kayıp" denmeyecek).
- İşlemler ve iadeler (Braintree `search`). Özel widget (üç değer yan yana fark kutusu) + tema.

**Studio Agent Framework:** geçit şüpheli işlem yakalayınca kendi ajanımız Studio'nun ajanlarıyla konuşur ve panele o işleme özel bir widget kurar (ör. "bu müşterinin bu siparişteki tüm iadeleri + bu istek"). Bu, AG Grid'in "anomaly-alert agent" örneğinin bizim alana uyarlaması. Widget yalnız izinli veriden kurulur; e-posta içeriği widget'a talimat veremez; ajan onay veremez.

## 5. Demo videosu (< 3 dk, İngilizce)
1. **0:00–0:20 Sorun:** müşteri e-postalarını ajana devreden mağaza; OWASP LLM01 kaynağıyla.
2. **0:20–0:40 Mimari:** iki ajan, mağaza kaydı, geçit, Braintree sandbox (PayPal hizmeti).
3. **0:40–1:05 Temiz akış:** PayPal ile ödenmiş siparişe iade isteği → GEÇİŞ → Braintree panelinde iade görünür.
4. **1:05–1:40 Containment moment:** aynı müşteri, gizli satırla iade 3 kat + başka bir sipariş. Ajan kandırılıp çağrıyı yapar, geçit durdurur. Kanıt: geçit izindeki istek + Braintree'de o işlem için yeni iade olmadığı.
5. **1:40–2:05 Panel:** geçit ajanının kurduğu widget; insan reddeder.
6. **2:05–2:25 Mükerrer iade + şişirilmiş tahsilat:** ENGEL ve ONAY.
7. **2:25–2:45 Ölçüm:** geçit açık/kapalı tablosu, gereksiz müdahale ayrı.
8. **2:45–2:58 Kapanış:** repo, MIT, nasıl çalıştırılır.

## 6. Takvim
- **23 Eki–2 Kas — çekirdek:** yeni public MIT repo. Mağaza kaydı + iki ajan + geçit + P1–P7 + temiz set + LLM'siz testler. Ödeme katmanı ayrı bir arayüz: önce taklit Braintree, sonra gerçek sandbox. **İlk denemeler:** Braintree sandbox hesabı; taklit PayPal işlemi → iade → sorgu uçtan uca; Drop-in'de PayPal düğmesi; AG Studio şablonunda tek widget.
- **3–8 Kas — Vultr (Blast Radius Zero):** Vultr VM + web uygulaması, LLM çağrıları Serverless Inference. Okuyucu ajan e-posta ekindeki PDF'den alan çıkaran kodu kendisi yazar, kod Docker sandbox'ta (ağ kapalı, salt-okuma) çalışır. İki durdurma katmanı: sandbox kodun dosya/ağ girişimini, geçit kandırılmış para hareketini durdurur. README'de "çekirdek 22 Eki'den beri, Vultr katmanı 3–8 Kas'ta" yazılır.
- **9–12 Kas — PayPal'a özgü:** panel cilası, ölçüm, video, Devpost formu. **Teslim 12 Kas 23:00 TR** (12:00 PT); hedef öğlen.
- Bitirme raporları Perşembe: 29 Eki, 5 Kas, 12 Kas (bu, 11 Kas'ta hazır olmalı).

## 7. Açık riskler
- **Braintree sandbox kaydı TR'den:** formda Turkey var, ama hesap henüz açılmadı. İlk iş.
- **"PayPal merkezde mi?"** Kurallar Braintree'yi PayPal hizmeti sayıyor ve PayPal ekibi yazılı olarak "Braintree works" dedi (Discord, 22 Eki 18:40). Jürinin "PayPal'ı ne kadar iyi kullandın" puanı yine de doğrulanmadı; PayPal'ı ödeme yöntemi olarak görünür tutmak bunun için.
- **Taklit PayPal'ın sınırları:** iade ve Drop-in davranışı doğrulanmadı (bkz. 2). Çalışmazsa PayPal işlemleri yerine kart işlemleriyle devam edilir ve bu açıkça yazılır.
- **Vultr:** lablab ön-kod kuralı belirsiz; Rule Book okunacak, kickoff'ta sorulacak.
- **AG Studio lisansı 45 gün:** erken başlarsa jüri döneminden (1–15 Ara) önce biter; #ag-grid'de sorulacak.
- **Zaman:** Meta Global kabul gelirse (≤26 Eki) 26 Eki–4 Kas çakışır. Model davranışı günden güne değişiyor; sabit model, birden çok gün.
