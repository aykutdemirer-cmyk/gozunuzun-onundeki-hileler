# Gözünüzün Önündeki Hileler — Shorts Otomasyonu

Konu yaz → Claude senaryoyu yazar → Ahmet sesiyle seslendirilir → 1080×1920 video render edilir → Telegram'a gönderilir.

## Kullanım
GitHub'da **Actions → Shorts Üret → Run workflow**:
- **topic:** Yeni konu (örn. "9,99 TL fiyat hilesi")
- **episode:** Hazır bir bölümü tekrar üretmek için (örn. `episodes/01_ekmek_sut.json`)

Video Telegram'a gelir, ayrıca çalıştırmanın **Artifacts** kısmından indirilebilir. Senaryolar `episodes/` klasörüne kaydedilir.

## Gerekli secrets (Settings → Secrets → Actions)
| Ad | Açıklama |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API anahtarı (console.anthropic.com) |
| `TELEGRAM_BOT_TOKEN` | @BotFather'dan alınan bot token |
| `TELEGRAM_CHAT_ID` | Videonun gideceği sohbet/kanal ID'si |

## Ayarlar (opsiyonel ortam değişkenleri)
`TTS_VOICE` (varsayılan `tr-TR-AhmetNeural`), `TTS_RATE` (varsayılan `+25%`), `CLAUDE_MODEL` (varsayılan `claude-sonnet-5-5`).

## Yerel çalıştırma
```
pip install pillow edge-tts imageio-ffmpeg requests
python render.py episodes/01_ekmek_sut.json short.mp4
```
Windows'ta `FONT_BOLD=C:\Windows\Fonts\arialbd.ttf` ayarla.
