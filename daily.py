"""Her gün yeni bir konu seçip bölüm JSON'u üretir (önceki bölümleri tekrarlamaz)."""
import os, json, glob, re, datetime
from bot import gemini, script_prompt, SERIES

done = []
for f in sorted(glob.glob("episodes/*.json")):
    try: done.append(json.load(open(f, encoding="utf-8")).get("title", ""))
    except Exception: pass

pick = gemini(f'''{SERIES} için bugünün videosunun konusunu seç.
Daha önce işlenenler (TEKRARLAMA, benzerini de seçme): {json.dumps(done[-60:], ensure_ascii=False)}
Market, restoran, kafe, e-ticaret, abonelik, banka, akaryakıt, giyim, kozmetik, teknoloji, otel/seyahat gibi farklı alanlardan dönüşümlü seç; herkesin hayatından tanıdığı, şaşırtıcı ve gerçek bir hile olsun.
SADECE JSON: {{"topic":"konu açıklaması","title":"kısa başlık (max 40 karakter)","hook":"ilk 3 saniyedeki kanca cümlesi"}}''')
ep = gemini(script_prompt(pick["topic"], pick))
now = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y%m%d%H%M")
slug = re.sub(r"[^a-z0-9]+", "_", pick["title"].lower().translate(str.maketrans("çğıöşü", "cgiosu")))[:30]
path = f"episodes/{now}_{slug}.json"
json.dump(ep, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a").write(f"episode={path}\n")
print(path, ep["title"])
