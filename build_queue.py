"""konular.txt dosyasındaki senaryoları queue/ klasörüne bölüm JSON'u olarak yazar (zaten yayınlananları atlar)."""
import json, os, re, glob

PAL = [((180,20,30),(40,0,10)), ((20,30,60),(5,5,20)), ((60,20,90),(15,5,30)), ((20,80,50),(5,25,15)),
       ((200,90,0),(60,20,0)), ((150,0,60),(40,0,20)), ((0,70,120),(0,15,35)), ((230,190,0),(120,40,0))]
TAGS = "#shorts #tasarruf #pazarlama #psikoloji #tüketici #ilginçbilgiler #gözünüzünönündekihileler"
slug = lambda s: re.sub(r"[^a-z0-9]+", "_", s.replace("İ", "i").lower().translate(str.maketrans("çğıöşüâ", "cgiosua"))).strip("_")[:35]

published = {json.load(open(f, encoding="utf-8")).get("topic") for f in glob.glob("episodes/*.json")}
os.makedirs("queue", exist_ok=True)
eps, cur = [], None
for line in open("konular.txt", encoding="utf-8"):
    line = line.strip()
    if line.startswith("## "): cur = {"topic": line[3:], "scenes": []}; eps.append(cur)
    elif cur and line.count("|") == 2:
        cap, voice, kw = (x.strip() for x in line.split("|"))
        cur["scenes"].append({"caption": cap.replace("/", "\n"), "voice": voice, "keyword": kw})
n = 0
for i, e in enumerate(eps, 1):
    if e["topic"] in published: continue
    for j, s in enumerate(e["scenes"]):
        s["colors"] = [list(c) for c in PAL[(i + j) % len(PAL)]]
        s["graphic"] = "keyword"
    first = e["scenes"][0]["voice"]; last = e["scenes"][-1]["voice"]
    e["title"] = f'{e["topic"]} 😳 #shorts'
    e["description"] = f"{first}\n\n{e['scenes'][-2]['voice']}\n\n💬 {last}\n\n🔔 Gözünüzün Önündeki Hileler serisi için abone ol!\n\n{TAGS}"
    json.dump(e, open(f"queue/{i:03d}_{slug(e['topic'])}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1); n += 1
print(n, "bölüm kuyrukta")
