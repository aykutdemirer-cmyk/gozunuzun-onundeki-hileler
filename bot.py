"""Telegram botu (yapay zekâsız). Mesaj gelince kuyruktaki sıradaki konuları buton olarak sunar; seçileni üretime alır.
Kullanım: python bot.py         -> mesajları işler
          python bot.py daily   -> günlük: kuyruğun ilk bölümünü üretime alır"""
import os, sys, json, glob, shutil, requests

TOKEN, CHAT = os.environ["TELEGRAM_BOT_TOKEN"], str(os.environ["TELEGRAM_CHAT_ID"])
STATE_F, LOW = "state/bot.json", 5

def tg(method, **body):
    return requests.post(f"https://api.telegram.org/bot{TOKEN}/{method}", json=body, timeout=60).json()

def say(text, kb=None):
    b = {"chat_id": CHAT, "text": text[:4000]}
    if kb: b["reply_markup"] = {"inline_keyboard": kb}
    tg("sendMessage", **b)

def queue(): return sorted(glob.glob("queue/*.json"))
def topic(f): return json.load(open(f, encoding="utf-8")).get("topic", os.path.basename(f))

def take(f):
    """Bölümü kuyruktan episodes/ klasörüne taşır ve yolunu döndürür."""
    dst = "episodes/" + os.path.basename(f); shutil.move(f, dst); return dst

def menu():
    q = queue()
    if not q: return say("📭 Kuyrukta bölüm kalmadı. Claude'a 'yeni bölümler yaz' de, kuyruğu doldursun.")
    kb = [[{"text": f"🎬 {topic(f)}"[:60], "callback_data": "ep:" + os.path.basename(f)}] for f in q[:5]]
    kb.append([{"text": "🎲 Rastgele", "callback_data": "rnd"}])
    say(f"Hangi videoyu hazırlayayım? (Kuyrukta {len(q)} bölüm var)", kb)

def low_warning():
    n = len(queue())
    if n <= LOW: say(f"⚠️ Kuyrukta {n} bölüm kaldı. Claude'a 'yeni bölümler yaz' diyerek kuyruğu doldurabilirsin.")

def main():
    out = []
    if len(sys.argv) > 1 and sys.argv[1] == "daily":
        q = queue()
        if q: out.append(take(q[0]))
        else: say("📭 Bugünkü video için kuyrukta bölüm kalmadı.")
    else:
        os.makedirs("state", exist_ok=True)
        S = json.load(open(STATE_F)) if os.path.exists(STATE_F) else {"offset": 0}
        tg("deleteWebhook"); want_menu = False
        for u in tg("getUpdates", offset=S["offset"], timeout=0).get("result", []):
            S["offset"] = u["update_id"] + 1
            msg, cb = u.get("message"), u.get("callback_query")
            chat = str((msg or {}).get("chat", {}).get("id") or (cb or {}).get("message", {}).get("chat", {}).get("id") or "")
            if chat != CHAT: continue
            if msg: want_menu = True; continue
            if not cb: continue
            tg("answerCallbackQuery", callback_query_id=cb["id"])
            d, q = cb.get("data", ""), queue()
            f = f"queue/{d[3:]}" if d.startswith("ep:") else (__import__("random").choice(q) if q and d == "rnd" else None)
            if f and os.path.exists(f):
                say(f"🎬 \"{topic(f)}\" hazırlanıyor! Birkaç dakika içinde burada."); out.append(take(f))
            else: say("Bu bölüm zaten üretildi ya da bulunamadı."); want_menu = True
        if want_menu: menu()
        json.dump(S, open(STATE_F, "w"))
    open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a").write(f"episodes={' '.join(out)}\n")
    if out: low_warning()
    print(len(out), "bölüm üretime alındı")

if __name__ == "__main__":
    main()
