"""Telegram sohbet botu (GitHub Actions ile periyodik çalışır).
Konu al -> 3 fikir sun -> senaryo yaz -> düzelt/onayla -> episodes/ altına yaz (video aynı iş içinde render edilir)."""
import os, json, re, time, datetime, requests

TOKEN, CHAT = os.environ["TELEGRAM_BOT_TOKEN"], str(os.environ["TELEGRAM_CHAT_ID"])
GKEY, GMODEL = os.environ["GEMINI_API_KEY"], os.getenv("GEMINI_MODEL", "gemini-flash-latest")
STATE_F = "state/bot.json"
SERIES = '"Gözünüzün Önündeki Hileler" YouTube Shorts serisi (markaların, marketlerin, restoranların tüketiciye fark ettirmeden para harcatan psikolojik tuzakları)'

def options_prompt(topic):
    return f'''{SERIES} için kullanıcı şunu istedi: "{topic}".
Bu istekten 3 FARKLI video fikri öner (farklı açı/hile). SADECE JSON döndür:
{{"options":[{{"title":"kısa başlık (max 40 karakter)","hook":"ilk 3 saniyedeki kanca cümlesi"}}]}}'''

def script_prompt(topic, opt, feedback=None, prev=None):
    rev = f'Önceki taslak: {json.dumps(prev, ensure_ascii=False)}\nKullanıcının düzeltme isteği: "{feedback}". Buna göre yeniden yaz.' if prev else ""
    return f'''{SERIES} için Shorts senaryosu yaz.
İstek: "{topic}". Seçilen fikir: {opt["title"]} — kanca: {opt["hook"]}
{rev}
Kurallar: 40-50 saniye (toplam 110-130 kelime seslendirme), 8-9 sahne. İlk sahne şok edici kanca. Hızlı, samimi, dolgu kelimesiz Türkçe. Son sahne izleyiciyi ikiye bölen bir soruyla "Yorumlara yaz!" diye bitsin. Doğrulanamayan kesin istatistik uydurma.
SADECE şu JSON'u döndür:
{{"title":"YouTube başlığı, #shorts dahil, max 90 karakter","description":"YouTube açıklaması + 6-8 hashtag",
"scenes":[{{"caption":"BÜYÜK HARF 2-4 KELİME, satır için \\n","voice":"dış ses cümlesi, rakamları yazıyla yaz","colors":[[r,g,b],[r,g,b]],"graphic":"keyword","keyword":"1-2 kelimelik vurgu"}}]}}
colors: koyu ve doygun gradyan, her sahnede farklı. graphic genelde "keyword"; konuya uygunsa receipt, cart_big, cart_fill, shelf, list; son sahnede "split" kullanılabilir.'''

def gemini(prompt):
    r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{GMODEL}:generateContent",
                      headers={"x-goog-api-key": GKEY}, timeout=120,
                      json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9}})
    r.raise_for_status()
    t = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(t[t.index("{"): t.rindex("}") + 1])

def tg(method, **body):
    return requests.post(f"https://api.telegram.org/bot{TOKEN}/{method}", json=body, timeout=60).json()

def say(text, kb=None):
    b = {"chat_id": CHAT, "text": text[:4000]}
    if kb: b["reply_markup"] = {"inline_keyboard": kb}
    tg("sendMessage", **b)

def show_options(st, head):
    txt = head + "\n\n" + "\n\n".join(f'{i+1}️⃣ {o["title"]}\n   "{o["hook"]}"' for i, o in enumerate(st["options"]))
    kb = [[{"text": f'{i+1}. {o["title"]}'[:60], "callback_data": f"opt:{i}"}] for i, o in enumerate(st["options"])]
    kb.append([{"text": "🔄 Başka fikirler", "callback_data": "more"}])
    say(txt, kb)

def preview(s):
    lines = "\n".join(f'{i+1}. {x["voice"]}' for i, x in enumerate(s["scenes"]))
    say(f'📝 {s["title"]}\n\n{lines}'[:3800] + '\n\n✏️ Değişiklik için yaz (ör. "kancayı daha şok edici yap")',
        [[{"text": "✅ Videoyu üret", "callback_data": "go"}],
         [{"text": "🔁 Yeniden yaz", "callback_data": "redo"}, {"text": "❌ İptal", "callback_data": "cancel"}]])

def handle(u, st):
    """st: bu sohbetin durumu (dict veya None). Yeni durumu ve üretilecek bölüm yolunu döndürür."""
    msg, cb = u.get("message"), u.get("callback_query")
    chat = str((msg or {}).get("chat", {}).get("id") or (cb or {}).get("message", {}).get("chat", {}).get("id") or "")
    if chat != CHAT: return st, None
    if msg and msg.get("text"):
        t = msg["text"].strip()
        if t in ("/start", "/yardim"):
            say('Merhaba! 🎬 Bana bir konu yaz (ör. "restoran menü hileleri"), sana 3 video fikri sunayım.\n\n'
                "Taslak gelince düzeltme isteğini yazabilir ya da ✅ ile videoyu üretebilirsin. Yeni konu için /yeni\n\n"
                "⏱ Not: Mesajlarını birkaç dakikada bir kontrol ediyorum, cevabım biraz gecikebilir.")
            return st, None
        if t == "/yeni": say("Tamam, yeni konuyu yaz 👇"); return None, None
        if st and st.get("stage") == "review":
            st["script"] = gemini(script_prompt(st["topic"], st["opt"], t, st["script"])); preview(st["script"]); return st, None
        st = {"stage": "choose", "topic": t, "options": gemini(options_prompt(t))["options"][:3]}
        show_options(st, "Hangisini hazırlayayım?"); return st, None
    if not cb: return st, None
    tg("answerCallbackQuery", callback_query_id=cb["id"])
    d = cb.get("data", "")
    if not st: say("Oturum bulunamadı, konuyu tekrar yaz."); return None, None
    if d == "more":
        prev = ", ".join(o["title"] for o in st["options"])
        st["options"] = gemini(options_prompt(f'{st["topic"]} (öncekilerden farklı: {prev})'))["options"][:3]
        show_options(st, "Yeni fikirler:"); return st, None
    if d.startswith("opt:"):
        st["opt"] = st["options"][int(d[4:])]
        st["script"] = gemini(script_prompt(st["topic"], st["opt"])); st["stage"] = "review"
        preview(st["script"]); return st, None
    if d == "redo":
        st["script"] = gemini(script_prompt(st["topic"], st["opt"], "Tamamen farklı ve daha çarpıcı yaz", st["script"]))
        preview(st["script"]); return st, None
    if d == "cancel": say("❌ İptal edildi. Yeni konu yazabilirsin."); return None, None
    if d == "go" and st.get("script"):
        now = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y%m%d%H%M")
        slug = re.sub(r"[^a-z0-9]+", "_", st["opt"]["title"].lower().translate(str.maketrans("çğıöşü", "cgiosu")))[:30]
        path = f"episodes/{now}_{slug}.json"
        json.dump(st["script"], open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        say("🎬 Video üretiliyor! Birkaç dakika içinde burada olacak."); return None, path
    return st, None

def main():
    os.makedirs("state", exist_ok=True)
    S = json.load(open(STATE_F, encoding="utf-8")) if os.path.exists(STATE_F) else {"offset": 0, "chat": None}
    tg("deleteWebhook")
    upd = tg("getUpdates", offset=S["offset"], timeout=0).get("result", [])
    out = []
    for u in upd:
        S["offset"] = u["update_id"] + 1
        try:
            S["chat"], path = handle(u, S["chat"])
            if path: out.append(path)
        except Exception as e:
            say("⚠️ Hata: " + str(e)[:300])
        json.dump(S, open(STATE_F, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(S, open(STATE_F, "w", encoding="utf-8"), ensure_ascii=False)
    open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a").write(f"episodes={' '.join(out)}\n")
    print(f"{len(upd)} mesaj, {len(out)} video")

if __name__ == "__main__":
    main()
