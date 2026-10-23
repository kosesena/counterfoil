# Braintree sandbox ilk deneme (23 Eki 2026)

Betikler: `spikes/braintree_spike.py` (taklit PayPal), `spikes/braintree_card_refund_spike.py` (test kartı). SDK `braintree` 4.48.0. Ham çıktı aşağıda; işlem kimlikleri sandbox'a ait.

## Taklit PayPal (`fake-paypal-one-time-nonce`)
```
OK   sale 40.54 via mocked PayPal: status=settling instrument=paypal_account
OK   refund 25.00 (partial)
OK   refund 25.00 again (25+25 > original)
OK   refund 120.00 (> original)
OK   refund 15.54 (exactly the remainder)
OK   refund 1.00 after fully refunded
FIND status=settling amount=40.54 refund_ids=[5 iade]
OK   vault customer … method=PayPalAccount   (fake-paypal-billing-agreement-nonce)
OK   charge 120.54 on vaulted PayPal
OK   charge 1200.54 on vaulted PayPal (10x)
OK   second sale 80.54 → refund 30.00
```
İlk koşuda aynı tutarlı ikinci satış reddedildi: `Gateway Rejected: duplicate`.

## Test kartı (`fake-valid-nonce`)
```
OK   card sale 40.61: status=submitted_for_settlement
FAIL refund 10.00 before settlement: 91506 Cannot refund transaction unless it is settled.
OK   testing.settle_transaction → settled
OK   refund 25.00
FAIL refund 25.00 again (total > original): 91521 Refund amount is too large.
FAIL refund 120.00 (> original): 91521 Refund amount is too large.
OK   refund 15.61 (remainder)
FAIL refund 1.00 after fully refunded: 91512 already fully refunded; 91521
```

## Sonuçlar
1. **Taklit PayPal çalışıyor:** PayPal ödemesi, iade, sorgu ve kayıtlı PayPal'dan (vault) tahsilat sandbox'ta PayPal hesabı olmadan yapılabiliyor. Taslaktaki "doğrulanmadı" maddesi kapandı.
2. **Taklit PayPal iade sınırını uygulamıyor.** 40,54 $'lık işleme 186,54 $ iade kabul edildi. Kartta aynı istekler 91521 ile reddedildi. Bu, taklit modun bir eksikliği; gerçek ortamda PayPal iadelerinin de sınırlandığını varsaymalıyız. **Demo ya da ölçüm, taklit PayPal'ın bu eksikliğinden yararlanarak "geçit yakaladı" diyemez.**
3. **Ödeme servisi kendi başına şunları zaten durduruyor (kart):** işlem tutarını aşan iade, tamamen iade edilmiş işleme iade, kesinleşmemiş işleme iade, kısa sürede aynı tutarlı mükerrer satış. Yani taslaktaki "40 $'lık siparişe 120 $ iade" örneği **zaten Braintree'ye takılır**; bizim farkımız olarak gösterilemez.
4. **Ödeme servisinin göremediği, geçidin işi olanlar:**
   - Toplamın altında kalan ama müşterinin hak etmediği iade (3 kalemden 1'i iade edildi, gizli talimatla tamamı iade isteniyor).
   - Sahiplik: e-postayı gönderen, siparişin sahibi mi? (Braintree için iade isteği kimden gelirse gelsin geçerli.)
   - Toplamın altında kalan mükerrer iade (40 $'lık siparişe 20 + 20).
   - Mağaza kuralı: iade süresi, insan onayı sınırı.
   - Tahsilat tutarı ≠ katalog fiyatı × adet (1200 $ tahsilat kabul edildi).
5. **Tasarım sonucu:** İadenin dayanağı, mağaza kaydındaki **iade kaydı (RMA)** olmalı: hangi kalemler geri geldi, kaç para. Geçit iadeyi bu kayıtla karşılaştırır; işlem toplamı üst sınırını ödeme servisi zaten uyguluyor.
