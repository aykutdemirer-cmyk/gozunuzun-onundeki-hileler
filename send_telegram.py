"""Videoyu başlık ve açıklamayla Telegram'a gönderir. Kullanım: python send_telegram.py video.mp4 episodes/xx.json"""
import os, sys, json, requests

video, ep = sys.argv[1], json.load(open(sys.argv[2], encoding="utf-8"))
caption = f"{ep.get('title', '')}\n\n{ep.get('description', '')}"[:1024]
r = requests.post(f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendVideo",
                  data={"chat_id": os.environ["TELEGRAM_CHAT_ID"], "caption": caption, "supports_streaming": True},
                  files={"video": open(video, "rb")}, timeout=300)
r.raise_for_status(); print("Telegram'a gönderildi")
