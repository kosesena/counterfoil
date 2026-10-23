# Kasa tasarımı devir notu (Claude → Codex, 23 Eki 21:50)

Sena kararı: kasa tasarımı Codex'in. Codex'in önerdiği akış (HOMI self-servis iade noktası, müdür tableti, amber "İnceleme gerekiyor") uygulanacak. Claude bu dosyaya (counterfoil-magaza.blend) artık dokunmuyor.

Son commit: 022c19b (main, github.com/kosesena/counterfoil, private).

## Dosya ve sahne
- docs/gorseller/counterfoil-magaza.blend, sahne `Counterfoil_Market_Composite`.
- Sena'nın izleme penceresi açık (eski sürüm). Ona kaydettirme; iki pencere aynı anda kaydetmesin.

## Kasa alanı (Kat 1, sol ön)
- 3 kasa `SE_Till0/1/2_*`: gövdeler x -16.7 / -13.5 / -10.2, y -9.6..-7.2. Her birinde POS terminali, PayPal çıkartması, QR standı var.
- Sahne Till1'de geçiyor. Bant üstünde `SE_Till1_Item_*` ürünleri ve `SE_Till1_Receipt*` var.

## Karakterler
- `Inst_<Role>` empty'leri ve `Cast_<Role>` koleksiyonları.
- İskeletler `tools/rig_and_animate.py` ile kuruluyor:
  - END=720, WALK_END=590.
  - Müşteride 'pay' kol hareketi var, müdürde tablet tutma pozu var.
- Kaideler (Plinth) ve isim etiketleri gizli. Inst'ler z=-0.16'da.
- Müşteri:
  - 1–170: dışarıda araba alıp giriyor.
  - 170–590: güvenlik kapılarından (`SE_GateEntry*`, `SE_GateExit*`) geçip Till1'in müşteri tarafına (x -12.3, y -8.75) yürüyor.
  - 604: -x yönüne dönüyor.
- Reader_Agent ve Transaction_Agent robota çevrildi:
  - İnsan yüz parçaları gizli.
  - Eklenen parçalar: `<Role>_HeadScreen`, `EyeLED*`, `MouthLED`, `HeadAntenna*`, `EarCap*`, `ChestAI`.
  - Yerleri: Transaction_Agent (-14.45, -9.25), Reader (-15.35, -8.05).
  - Codex'in tasarımında bunlar ekran içi karakter ya da tarayıcı yanında küçük yardımcı olacaksa, iki büyük figür kaldırılıp değiştirilebilir.
- Müdür tabletli, cam "STORE OFFICE" kabininde (`SE_Office_*`, Inst (-17.85, -11.05)).

## Mağazanın diğer yeni parçaları
- Sepet standı (`tools/basket_stand.py`, `SE_BStand_*`).
- Giriş ve çıkış güvenlik kapıları.

## Senaryo
- Sipariş 90 $, 3 kalem: tepsi, kâse, vazo.
- İade kaydı (RMA) 30 $, tepsi için.
- Saldırıda ajan 90 $ ister.
- Müdür isteği reddeder. 30 $ yeniden oluşturulur ve geçitten tekrar geçer. Fiş ancak ödeme servisi başarıyı doğruladıktan sonra çıkar.

## Kurallar
- Commit etme. Bitince ne değiştirdiğini ve render yollarını yaz; Claude gözden geçirip commit'ler.
- Videoda üçüncü taraf markası yok (IKEA yok). PayPal logoları `marka-dis/` klasöründe (gitignore'da).
