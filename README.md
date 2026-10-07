# Gözünüzün Önündeki Hileler — Shorts Otomasyonu

Yapay zekâ servisi gerektirmez. Senaryolar `konular.txt` içinde yazılı; `queue/` klasörü üretim sırasını tutar.

## Nasıl çalışır
- **Her gün ~09:47:** kuyruktaki ilk bölüm videoya dönüşür ve Telegram'a gönderilir.
- **Telegram botu:** bota herhangi bir mesaj yaz → sıradaki 5 konu buton olarak gelir → seçtiğin üretilir (bot ~5 dakikada bir kontrol eder).
- Kuyrukta 5 bölüm kalınca bot uyarır.

## Yeni bölüm eklemek
`konular.txt` dosyasına aynı formatta yeni bölümler ekle ve çalıştır:
```
python build_queue.py
```

## Secrets
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`

## Yerel render
```
pip install pillow edge-tts imageio-ffmpeg requests
python render.py queue/001_9_99_fiyat_hilesi.json short.mp4
```
Windows'ta `FONT_BOLD=C:\Windows\Fonts\arialbd.ttf` ayarla.
