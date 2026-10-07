"""Konudan sahne JSON'u üretir (Claude API). Kullanım: python write_script.py "konu" episodes/xx.json"""
import os, sys, json, re, urllib.request

PROMPT = """"Gözünüzün Önündeki Hileler" YouTube Shorts serisi için senaryo yaz. Konu: {topic}

Kurallar: 40-50 saniye (toplam ~110-130 kelime seslendirme), 8-9 sahne. İlk sahne şok edici kanca sorusu. Hızlı, samimi, dolgu kelimesiz Türkçe. Son sahne izleyiciyi ikiye bölen bir soruyla "Yorumlara yaz!" diye bitsin. Doğrulanamayan kesin istatistik uydurma.
SADECE şu JSON'u döndür:
{{"title": "YouTube başlığı (#shorts dahil, max 90 karakter)",
 "description": "YouTube açıklaması + hashtagler",
 "scenes": [{{"caption": "BÜYÜK HARF 2-4 KELİME, satır için \\n", "voice": "dış ses cümlesi (rakamları yazıyla yaz)", "colors": [[r,g,b],[r,g,b]], "graphic": "keyword", "keyword": "1-2 kelimelik vurgulu ifade"}}]}}
colors: koyu, doygun gradyan; sahneden sahneye değişsin. graphic: "keyword" kullan; sadece konuya uygunsa şunlardan biri: receipt, cart_big, cart_fill, shelf, list, split (son sahne için split uygundur)."""

topic, out = sys.argv[1], sys.argv[2]
req = urllib.request.Request("https://api.anthropic.com/v1/messages", headers={
    "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01", "content-type": "application/json"},
    data=json.dumps({"model": os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"), "max_tokens": 2500,
                     "messages": [{"role": "user", "content": PROMPT.format(topic=topic)}]}).encode())
text = json.load(urllib.request.urlopen(req))["content"][0]["text"]
ep = json.loads(re.search(r"\{.*\}", text, re.S).group())
os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
json.dump(ep, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(ep["title"])
