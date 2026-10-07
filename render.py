"""Sahne JSON'undan seslendirmeli 1080x1920 Shorts videosu üretir.
Kullanım: python render.py episodes/xx.json cikti.mp4"""
import subprocess, math, os, re, sys, json, asyncio, tempfile, edge_tts, imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
VOICE, RATE = os.getenv("TTS_VOICE", "tr-TR-AhmetNeural"), os.getenv("TTS_RATE", "+0%")
EP = json.load(open(sys.argv[1], encoding="utf-8")); OUTF = sys.argv[2]; A = tempfile.mkdtemp()
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
B = os.getenv("FONT_BOLD", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
f = lambda p, s: ImageFont.truetype(p, s)

WORDS = {}
async def tts():
    for i, sc in enumerate(EP["scenes"]):
        try: c = edge_tts.Communicate(sc["voice"], VOICE, rate=RATE, boundary="WordBoundary")
        except TypeError: c = edge_tts.Communicate(sc["voice"], VOICE, rate=RATE)
        ws = []
        with open(os.path.join(A, f"s{i}.mp3"), "wb") as fh:
            async for ch in c.stream():
                if ch["type"] == "audio": fh.write(ch["data"])
                elif ch["type"] == "WordBoundary": ws.append((ch["offset"] / 1e7, ch["text"]))
        WORDS[i] = ws
asyncio.run(tts())

GAP = 0.08
def dur(p):
    o = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    h, m, x = re.search(r"Duration: (\d+):(\d+):([\d.]+)", o).groups(); return int(h)*3600+int(m)*60+float(x)
S, L, t0 = [], [], 0
for i, sc in enumerate(EP["scenes"]):
    l = dur(os.path.join(A, f"s{i}.mp3")) + GAP; L.append(l)
    S.append((t0, t0 + l, sc["caption"], sc["voice"], tuple(tuple(c) for c in sc["colors"]), sc.get("graphic", "keyword"), sc.get("keyword", "")))
    t0 += l
TOTAL = t0
for i, sc in enumerate(S):
    ws = WORDS.get(i) or []
    if not ws:  # yedek: kelimeleri süreye eşit dağıt
        toks = sc[3].split(); span = (sc[1] - sc[0] - GAP) / max(len(toks), 1)
        ws = [(k * span, w) for k, w in enumerate(toks)]
    WORDS[i] = ws
YEL, WHT = (255, 214, 0), (255, 255, 255)

def ease(t): return 1 - (1 - min(max(t, 0), 1)) ** 3
def pop(t): t = min(max(t, 0), 1); return 1 + 0.25 * math.sin(t * math.pi) if t < 1 else 1

def grad(c1, c2, shift):
    im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
    for y in range(0, H, 8):
        k = (y / H + shift) % 1; k = abs(k * 2 - 1)
        d.rectangle([0, y, W, y + 8], fill=tuple(int(c1[i] * (1 - k) + c2[i] * k) for i in range(3)))
    return im

def wrap(d, text, font, maxw):
    out = []
    for para in text.split("\n"):
        line = ""
        for w in para.split():
            tst = (line + " " + w).strip()
            if d.textlength(tst, font=font) > maxw and line: out.append(line); line = w
            else: line = tst
        out.append(line)
    return out

def cart(d, x, y, s, fill=0):
    d.line([(x - 60*s, y - 120*s), (x - 20*s, y - 120*s), (x + 20*s, y + 60*s), (x + 240*s, y + 60*s)], fill=WHT, width=int(14*s))
    d.polygon([(x, y - 80*s), (x + 280*s, y - 80*s), (x + 240*s, y + 40*s), (x + 25*s, y + 40*s)], outline=WHT, width=int(12*s))
    if fill:
        h = 120 * s * fill
        d.polygon([(x + 25*s, y + 40*s - h), (x + 255*s, y + 40*s - h), (x + 240*s, y + 40*s), (x + 25*s, y + 40*s)], fill=YEL)
    for cx in (x + 50*s, x + 220*s):
        d.ellipse([cx - 22*s, y + 80*s, cx + 22*s, y + 124*s], fill=WHT)

def graphic(d, kind, t, lt, kw=""):
    cx, cy = W // 2, 1080
    if kind == "keyword":
        r = int(300 * (0.55 + 0.45 * ease(lt / 0.4)) + 14 * math.sin(lt * 6)); d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=YEL, width=14)
        R = r + 46
        for q in range(12):  # dönen kesik halka
            a0 = q * 30 + lt * 60; d.arc([cx - R, cy - R, cx + R, cy + R], a0, a0 + 14, fill=WHT, width=10)
        fs = 150
        while kw and d.textlength(kw, font=f(B, fs)) > 560: fs -= 6
        d.text((cx, cy), kw, font=f(B, fs), fill=WHT, anchor="mm"); return
    if kind == "receipt":
        h = int(ease(lt / 2.5) * 520)
        d.rectangle([cx - 170, cy - 260, cx + 170, cy - 260 + h], fill=(245, 245, 235))
        for i in range(0, h - 40, 45):
            d.rectangle([cx - 130, cy - 230 + i, cx + 60, cy - 214 + i], fill=(180, 180, 180))
        d.text((cx, cy - 300), "EKMEK x1", font=f(B, 60), fill=WHT, anchor="mm")
    elif kind == "map":
        d.rectangle([cx - 380, cy - 300, cx + 380, cy + 300], outline=WHT, width=8)
        for i in range(4): d.rectangle([cx - 300 + i * 160, cy - 200, cx - 240 + i * 160, cy + 220], fill=(90, 100, 140))
        d.rectangle([cx + 200, cy - 290, cx + 370, cy - 200], fill=YEL)
        d.text((cx + 285, cy - 245), "SÜT", font=f(B, 40), fill=(0, 0, 0), anchor="mm")
        d.text((cx - 300, cy + 260), "GİRİŞ", font=f(B, 36), fill=WHT, anchor="mm")
        pts = [(cx - 300, cy + 230), (cx - 160, cy + 230), (cx - 160, cy - 240), (cx, cy - 240), (cx, cy + 240), (cx + 160, cy + 240), (cx + 160, cy - 245), (cx + 200, cy - 245)]
        p = ease(lt / 4.5) * (len(pts) - 1); n = int(p)
        path = pts[:n + 1]
        if n < len(pts) - 1:
            a, b = pts[n], pts[n + 1]; k = p - n
            path.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
        d.line(path, fill=(255, 40, 40), width=14, joint="curve")
    elif kind == "aisles":
        off = (lt * 900) % 360
        for row in range(-1, 4):
            y = cy - 300 + row * 180 + off * 0.5
            for side in (-1, 1):
                d.rectangle([cx + side * 380 - 90, y, cx + side * 380 + 90, y + 140], fill=[(255, 90, 90), (90, 200, 255), (255, 200, 60)][row % 3])
        d.text((cx, cy), "%  İNDİRİM  %", font=f(B, 64), fill=YEL, anchor="mm")
    elif kind == "shelf":
        for i, (lab, col) in enumerate([("₺₺₺", YEL), ("₺₺", (200, 200, 200)), ("₺", (120, 120, 120))]):
            y = cy - 260 + i * 220
            d.rectangle([cx - 400, y + 150, cx + 400, y + 165], fill=(200, 160, 100))
            k = ease((lt - i * 0.4) / 0.8)
            for j in range(4): d.rectangle([cx - 360 + j * 200, y + 150 - int(130 * k), cx - 220 + j * 200, y + 150], fill=col)
            d.text((cx + 470, y + 90), lab, font=f(B, 48), fill=col, anchor="mm")
        d.text((cx - 470, cy - 170), "GÖZ", font=f(B, 34), fill=WHT, anchor="mm")
    elif kind == "cart_big":
        s = 0.6 + ease(lt / 1.5) * 1.3; cart(d, cx - 140 * s, cy, s)
    elif kind == "cart_fill":
        cart(d, cx - 230, cy - 40, 1.6, fill=ease(lt / 5))
    elif kind == "fridge":
        d.rectangle([cx - 300, cy - 300, cx + 300, cy + 300], outline=(150, 220, 255), width=10)
        d.line([(cx, cy - 300), (cx, cy + 300)], fill=(150, 220, 255), width=8)
        d.text((cx, cy), "❄", font=f(B, 220), fill=(200, 240, 255), anchor="mm")
        if lt > 2.5: d.text((cx, cy + 360), "AMA SONUÇ: +HARCAMA", font=f(B, 56), fill=YEL, anchor="mm")
    elif kind == "list":
        d.rectangle([cx - 260, cy - 320, cx + 260, cy + 320], fill=(250, 248, 230))
        for i in range(5):
            y = cy - 250 + i * 110
            d.rectangle([cx - 200, y, cx + 160, y + 20], fill=(120, 120, 120))
            if lt > 0.5 + i * 0.6: d.text((cx - 230, y + 10), "✓", font=f(B, 60), fill=(0, 150, 60), anchor="mm")
    elif kind == "split":
        d.rectangle([0, cy - 260, cx - 8, cy + 260], fill=(20, 120, 70))
        d.rectangle([cx + 8, cy - 260, W, cy + 260], fill=(170, 20, 40))
        [d.rectangle([cx//2-60, cy-240+k*35, cx//2+60, cy-228+k*35], fill=WHT) for k in range(4)]
        d.text((cx // 2, cy + 50), "LİSTE", font=f(B, 80), fill=WHT, anchor="mm")
        d.text((cx + cx // 2, cy + 50), "ARABA", font=f(B, 80), fill=WHT, anchor="mm")
        cart(d, cx + cx // 2 - 110, cy - 180, 0.75, fill=1)
        a = int(abs(math.sin(lt * 5)) * 30)
        d.text((cx, cy + 330 + a), "YORUMA YAZ!", font=f(B, 70), fill=YEL, anchor="mm")

def frame(t):
    sc = next(s for s in S if s[0] <= t < s[1]) if t < TOTAL else S[-1]
    st, en, cap, vo, cols, kind, kw = sc; lt = t - st
    im = grad(cols[0], cols[1], t * 0.05); d = ImageDraw.Draw(im)
    for p in range(26):  # süzülen parçacıklar
        px = (p * 397 + t * (20 + p % 5 * 12)) % W; py = (H - (p * 733 + t * (60 + p % 7 * 18))) % H; r = 4 + p % 4 * 3
        c = tuple(min(255, int(v * 0.6 + 100)) for v in cols[0]); d.ellipse([px - r, py - r, px + r, py + r], fill=c)
    # series tag + progress bar
    d.text((W // 2, 130), "GÖZÜNÜZÜN ÖNÜNDEKİ HİLELER", font=f(B, 40), fill=(255, 255, 255, 180), anchor="mm")
    d.rectangle([0, 0, int(W * t / TOTAL), 14], fill=YEL)
    # big caption with pop
    lines = cap.split("\n"); base = 118
    while max(d.textlength(l, font=f(B, base)) for l in lines) > W - 100: base -= 4
    sz = int(base * pop(lt / 0.35)); fnt = f(B, sz); lh = sz * 1.15; y0 = 470 - (len(lines) - 1) * lh / 2
    for i, ln in enumerate(lines):
        col = YEL if i == 0 else WHT
        d.text((W // 2, y0 + i * lh), ln, font=fnt, fill=col, anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0))
    graphic(d, kind, t, lt, kw)
    # karaoke altyazı: 3'lü kelime grupları, konuşulan kelime sarı
    ws = WORDS[S.index(sc)]; k = max([j for j, (o, _) in enumerate(ws) if o <= lt] or [0])
    g0 = (k // 3) * 3; grp = ws[g0:g0 + 3]
    if grp:
        fs = 92
        while d.textlength(" ".join(w for _, w in grp), font=f(B, fs)) > W - 120: fs -= 4
        x = W // 2 - d.textlength(" ".join(w for _, w in grp), font=f(B, fs)) / 2
        for j, (o, w) in enumerate(grp):
            cur = g0 + j == k
            fz = int(fs * (1 + 0.12 * max(0, 1 - (lt - o) / 0.15))) if cur else fs
            d.text((x, 1600), w, font=f(B, fz), fill=YEL if cur else WHT, anchor="lm", stroke_width=9, stroke_fill=(0, 0, 0))
            x += d.textlength(w, font=f(B, fz)) + d.textlength(" ", font=f(B, fs))
    z = 1 + 0.07 * max(0, 1 - lt / 0.3)  # punch-in yakınlaşma
    if z > 1.001:
        cw, ch = int(W / z), int(H / z); im = im.crop(((W - cw) // 2, (H - ch) // 2, (W + cw) // 2, (H + ch) // 2)).resize((W, H))
    if lt < 0.06 and st > 0: im = Image.blend(im, Image.new("RGB", (W, H), WHT), 0.35)  # geçiş flaşı
    return im

cmd = [FF, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
for i in range(len(S)): cmd += ["-i", os.path.join(A, f"s{i}.mp3")]
cuts = [sc[0] for sc in S[1:]]
cmd += ["-f", "lavfi", "-i", "anoisesrc=d=0.4:c=pink:a=0.5"]
wh = f"[{len(S)+1}:a]highpass=f=900,lowpass=f=6000,afade=t=in:d=0.12,afade=t=out:st=0.15:d=0.25,volume=0.35,asplit={max(len(cuts),1)}" + "".join(f"[w{j}]" for j in range(max(len(cuts),1))) + ";"
wh += "".join(f"[w{j}]adelay={int(max(c - 0.15, 0) * 1000)}:all=1[d{j}];" for j, c in enumerate(cuts))
fl = wh + "".join(f"[{i+1}:a]apad=whole_dur={L[i]:.3f}[a{i}];" for i in range(len(S))) + "".join(f"[a{i}]" for i in range(len(S))) + f"concat=n={len(S)}:v=0:a=1[v];" + "[v]" + "".join(f"[d{j}]" for j in range(len(cuts))) + f"amix=inputs={len(cuts)+1}:normalize=0,loudnorm=I=-14[a]"
cmd += ["-filter_complex", fl, "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "fast", "-c:a", "aac", "-b:a", "192k", "-t", f"{TOTAL:.3f}", OUTF]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
for i in range(int(TOTAL * FPS)): p.stdin.write(frame(i / FPS).tobytes())
p.stdin.close(); p.wait(); print(OUTF, round(TOTAL, 1))
