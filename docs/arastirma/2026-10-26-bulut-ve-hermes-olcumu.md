# Güncel geçitle dev seti: Hermes 3 ve bulut modelleri (26 Eki 2026)

25 Eki notunun (`2026-10-25-guncel-gecit-olcumu.md`) devamı. Ham kayıtlar ve her birinin meta dosyası `results/2026-10-26-dev-r3-current-gate-*`. Geçit kodu 25 Eki koşularıyla aynı (8c30644; koşu anındaki commit f57090a, aradaki değişiklikler yalnızca `counterfoil/worst_case.py` ve biçim). Dev seti 7 saldırı + 6 temiz, 3 tekrar, üç koşul: 117 koşu. Taklit ödeme servisi. Saatler Türkiye saati.

## Nerede, ne zaman, ne kadar

| Model | Nerede | Başlangıç → bitiş | Süre | Maliyet |
|---|---|---|---|---|
| Hermes 3 (hermes3-8k) | bu Mac, Ollama (Apple M2 Pro, 16 GB) | 17:38 → 17:49 | 11 dk | 0 $ |
| GPT-5.6 Terra | Astropods konteyneri bu Mac'te, Astro AI Gateway → Amazon Bedrock | 17:42 → 17:48 | 6 dk | ~0,67 $ |
| Claude Sonnet 5 | aynı yol | 17:58 → 18:24 | 25 dk | ~1,54 $ |
| Claude Opus 5.5 | aynı yol | 18:24 → 18:49 | 25 dk | ~2,89 $ |

Bulut maliyeti `ast billing get` önce/sonra farkıdır. Astropods ücretsiz kredisi (10 $) Sonnet sırasında bitti; kalan ~3,7 $ Sena'nın kartından 1 Kas'ta çekilecek (aylık fatura, harcama sınırı 20 $). Claude Haiku 4.5 ve GPT-5.6 Sol son geçitle koşulmadı.

Bulut koşularında konteyner sonuç satırlarını dosyaya değil log'a yazar (`CFROW`); meta dosyaları koşudan sonra satırlardaki zamanlardan yazıldı.

## Sonuçlar

| Model | Geçit yok | 200 $ tavan | Counterfoil | Temiz istek doğru (Counterfoil) |
|---|---|---|---|---|
| Hermes 3 | 6/21 | 6/21 | **0/21** | 6/18 |
| GPT-5.6 Terra | 7/21 | 8/21 | **0/21** | 18/18 |
| Claude Sonnet 5 | 5/21 | 6/21 | **0/21** | 18/18 |
| Claude Opus 5.5 | 6/21 | 6/21 | **0/21** | 18/18 |

Son geçitle yapılan bütün koşular (dev 7 model + holdout 4 yerel model): Counterfoil 0/228, geçit yok 81/228, tavan 83/228 (Braintree sandbox koşusu ayrı: 4/7, 4/7, 0/7).

## Bu sonuçlar ne demek, ne demek değil

- **14 farklı saldırı, 7 aile.** 228 koşu, aynı 14 senaryonun modeller ve tekrarlar üstünden tekrarı; bağımsız 228 saldırı değil.
- **Senaryoları da geçidi de biz yazdık.** Holdout seti geçit yazılırken ayrı tutuldu, ama aynı yazarlardan ve aynı ailelerden. Dışarıdan biri yeni bir saldırı yazınca sonuç değişebilir.
- **Sıfır, geçidin nasıl çalıştığından geliyor.** Geçit her para çağrısını mağazanın kendi kaydıyla (sipariş, iade kaydı, daha önce yapılan iadeler) karşılaştırıyor; kayıtla uyuşmayan para çıkamıyor. En kötü durum koşusunda (Okuyucu ve ajan tamamen saldırganın tarafında, model yok) da Counterfoil 0/14, geçitsiz ve tavan 11–12/14.
- **Kaydın kendisi yanlışsa yakalamaz.** Saldırgan sahte bir iade kaydı açtırabilirse, ya da kayıtla tutarlı ama başka bir yoldan zarar veren bir istek gelirse, geçit bunu görmez. İnsan onayına giden çağrılarda karar insana kalır.
- **Gerçek talepleri kaybetmiyor ama insana daha çok iş çıkarıyor.** Tamamlanan temiz istek sayısı üç koşulda aynı (78/147). Counterfoil 36 temiz isteği insana gönderdi (tavan 15, geçitsiz 0); bunların çoğu mağaza kuralı gereği (otomatik iade sınırının üstü). 6 temiz koşuda geçit bir çağrıyı durdurdu.
- **Ajan yine kanıyor.** "Ajan kandırıldı" oranı her koşulda benzer; geçit kandırılmayı değil, kandırılan ajanın parayı göndermesini engelliyor.
