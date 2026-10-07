# Gözünüzün Önündeki Hileler — Shorts Otomasyonu

`episodes/` klasörüne yeni bölüm JSON'u eklenince → Ahmet sesiyle seslendirilir → 1080×1920 video render edilir → Telegram'a gönderilir.

## Kullanım
- `episodes/` klasörüne yeni `.json` eklemek/güncellemek videoyu **otomatik** üretir.
- Elle tekrar üretmek için: **Actions → Shorts Üret → Run workflow** ve bölüm dosyasını yaz.

Video Telegram'a gelir, ayrıca çalıştırmanın **Artifacts** kısmından indirilebilir.

## Gerekli secrets (Settings → Secrets → Actions)
| Ad | Açıklama |
|---|---|
| `TELEGRAM_BOT_TOKEN` | @BotFather'dan alınan bot token |
| `TELEGRAM_CHAT_ID` | Videonun gideceği sohbet/kanal ID'si |

## Ayarlar
`TTS_VOICE` (varsayılan `tr-TR-AhmetNeural`), `TTS_RATE` (varsayılan `+25%`).
## Yerel çalıştırma
```
pip install pillow edge-tts imageio-ffmpeg requests
python render.py episodes/01_ekmek_sut.json short.mp4
```
Windows'ta `FONT_BOLD=C:\Windows\Fonts\arialbd.ttf` ayarla.
