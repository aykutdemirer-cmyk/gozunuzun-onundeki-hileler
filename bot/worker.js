// Telegram sohbet botu: konu al -> seçenek sun -> senaryo yaz -> onayla -> GitHub'a bölüm ekle (video otomatik üretilir)
const SERIES = '"Gözünüzün Önündeki Hileler" YouTube Shorts serisi (markaların, marketlerin, restoranların tüketiciye fark ettirmeden para harcatan psikolojik tuzakları)';

const OPTIONS_PROMPT = (topic) => `${SERIES} için kullanıcı şunu istedi: "${topic}".
Bu istekten 3 FARKLI video fikri öner (farklı açı/hile). SADECE JSON döndür:
{"options":[{"title":"kısa başlık (max 40 karakter)","hook":"ilk 3 saniyedeki kanca cümlesi"}]}`;

const SCRIPT_PROMPT = (topic, opt, feedback, prev) => `${SERIES} için Shorts senaryosu yaz.
İstek: "${topic}". Seçilen fikir: ${opt.title} — kanca: ${opt.hook}
${prev ? `Önceki taslak: ${JSON.stringify(prev)}\nKullanıcının düzeltme isteği: "${feedback}". Buna göre yeniden yaz.` : ""}
Kurallar: 40-50 saniye (toplam 110-130 kelime seslendirme), 8-9 sahne. İlk sahne şok edici kanca. Hızlı, samimi, dolgu kelimesiz Türkçe. Son sahne izleyiciyi ikiye bölen bir soruyla "Yorumlara yaz!" diye bitsin. Doğrulanamayan kesin istatistik uydurma.
SADECE şu JSON'u döndür:
{"title":"YouTube başlığı, #shorts dahil, max 90 karakter","description":"YouTube açıklaması + 6-8 hashtag",
"scenes":[{"caption":"BÜYÜK HARF 2-4 KELİME, satır için \\n","voice":"dış ses cümlesi, rakamları yazıyla yaz","colors":[[r,g,b],[r,g,b]],"graphic":"keyword","keyword":"1-2 kelimelik vurgu"}]}
colors: koyu ve doygun gradyan, her sahnede farklı. graphic genelde "keyword"; konuya uygunsa receipt, cart_big, cart_fill, shelf, list; son sahnede "split" kullanılabilir.`;

export default {
  async fetch(req, env, ctx) {
    if (req.method !== "POST" || req.headers.get("X-Telegram-Bot-Api-Secret-Token") !== env.WEBHOOK_SECRET)
      return new Response("ok");
    const u = await req.json();
    ctx.waitUntil(handle(u, env).catch((e) => {
      const chat = u.message?.chat.id || u.callback_query?.message.chat.id;
      if (chat) tg(env, "sendMessage", { chat_id: chat, text: "⚠️ Hata: " + String(e).slice(0, 300) });
    }));
    return new Response("ok");
  },
};

async function handle(u, env) {
  const msg = u.message, cb = u.callback_query;
  const chat = String(msg?.chat.id || cb?.message.chat.id || "");
  if (!chat || (env.ALLOWED_CHAT_ID && chat !== String(env.ALLOWED_CHAT_ID))) return;
  const key = "s:" + chat;
  let st = JSON.parse((await env.STATE.get(key)) || "null");

  if (msg?.text) {
    const t = msg.text.trim();
    if (t === "/start" || t === "/yardim")
      return say(env, chat, "Merhaba! 🎬 Bana bir konu yaz (ör. \"restoran menü hileleri\"), sana 3 video fikri sunayım.\n\nTaslak gelince düzeltme isteğini yazabilir ya da ✅ ile videoyu üretebilirsin. Yeni konu için /yeni");
    if (t === "/yeni") { await env.STATE.delete(key); return say(env, chat, "Tamam, yeni konuyu yaz 👇"); }
    if (st?.stage === "review") {
      await say(env, chat, "✏️ Düzeltiyorum...");
      st.script = await gemini(env, SCRIPT_PROMPT(st.topic, st.opt, t, st.script));
      await env.STATE.put(key, JSON.stringify(st), { expirationTtl: 86400 });
      return preview(env, chat, st.script);
    }
    await say(env, chat, "💡 Fikirler hazırlanıyor...");
    const { options } = await gemini(env, OPTIONS_PROMPT(t));
    st = { stage: "choose", topic: t, options: options.slice(0, 3) };
    await env.STATE.put(key, JSON.stringify(st), { expirationTtl: 86400 });
    const text = "Hangisini hazırlayayım?\n\n" + st.options.map((o, i) => `${i + 1}️⃣ ${o.title}\n   "${o.hook}"`).join("\n\n");
    const kb = st.options.map((o, i) => [{ text: `${i + 1}. ${o.title}`.slice(0, 60), callback_data: "opt:" + i }]);
    kb.push([{ text: "🔄 Başka fikirler", callback_data: "more" }]);
    return tg(env, "sendMessage", { chat_id: chat, text, reply_markup: { inline_keyboard: kb } });
  }

  if (!cb) return;
  await tg(env, "answerCallbackQuery", { callback_query_id: cb.id });
  const d = cb.data;
  if (!st) return say(env, chat, "Oturum süresi doldu, konuyu tekrar yaz.");

  if (d === "more") {
    await say(env, chat, "🔄 Yeni fikirler...");
    const { options } = await gemini(env, OPTIONS_PROMPT(st.topic + " (öncekilerden farklı: " + st.options.map((o) => o.title).join(", ") + ")"));
    st.options = options.slice(0, 3); await env.STATE.put(key, JSON.stringify(st), { expirationTtl: 86400 });
    const kb = st.options.map((o, i) => [{ text: `${i + 1}. ${o.title}`.slice(0, 60), callback_data: "opt:" + i }]);
    kb.push([{ text: "🔄 Başka fikirler", callback_data: "more" }]);
    return tg(env, "sendMessage", { chat_id: chat, text: st.options.map((o, i) => `${i + 1}️⃣ ${o.title}\n   "${o.hook}"`).join("\n\n"), reply_markup: { inline_keyboard: kb } });
  }
  if (d.startsWith("opt:")) {
    st.opt = st.options[+d.slice(4)];
    await say(env, chat, `✍️ "${st.opt.title}" senaryosu yazılıyor...`);
    st.script = await gemini(env, SCRIPT_PROMPT(st.topic, st.opt));
    st.stage = "review"; await env.STATE.put(key, JSON.stringify(st), { expirationTtl: 86400 });
    return preview(env, chat, st.script);
  }
  if (d === "redo") {
    await say(env, chat, "🔁 Yeniden yazılıyor...");
    st.script = await gemini(env, SCRIPT_PROMPT(st.topic, st.opt, "Tamamen farklı ve daha çarpıcı yaz", st.script));
    await env.STATE.put(key, JSON.stringify(st), { expirationTtl: 86400 });
    return preview(env, chat, st.script);
  }
  if (d === "cancel") { await env.STATE.delete(key); return say(env, chat, "❌ İptal edildi. Yeni konu yazabilirsin."); }
  if (d === "go" && st.script) {
    const now = new Date(Date.now() + 3 * 3600e3).toISOString().replace(/\D/g, "").slice(0, 12);
    const slug = st.opt.title.toLowerCase().replace(/[çğıöşü]/g, (c) => "cgiosu"["çğıöşü".indexOf(c)]).replace(/[^a-z0-9]+/g, "_").slice(0, 30);
    const path = `episodes/${now}_${slug}.json`;
    const bytes = new TextEncoder().encode(JSON.stringify(st.script, null, 1));
    const b64 = btoa(Array.from(bytes, (b) => String.fromCharCode(b)).join(""));
    const r = await fetch(`https://api.github.com/repos/${env.GITHUB_REPO}/contents/${path}`, {
      method: "PUT",
      headers: { Authorization: "Bearer " + env.GITHUB_TOKEN, "User-Agent": "shorts-bot", Accept: "application/vnd.github+json" },
      body: JSON.stringify({ message: "Yeni bölüm: " + st.opt.title, content: b64 }),
    });
    if (!r.ok) throw new Error("GitHub " + r.status + " " + (await r.text()).slice(0, 200));
    await env.STATE.delete(key);
    return say(env, chat, "🎬 Video üretiliyor! Yaklaşık 3 dakika içinde burada olacak.");
  }
}

function preview(env, chat, s) {
  const lines = s.scenes.map((x, i) => `${i + 1}. ${x.voice}`).join("\n");
  const text = `📝 ${s.title}\n\n${lines}`.slice(0, 3900) + "\n\n✏️ Değişiklik için yaz (ör. \"kancayı daha şok edici yap\")";
  return tg(env, "sendMessage", { chat_id: chat, text, reply_markup: { inline_keyboard: [
    [{ text: "✅ Videoyu üret", callback_data: "go" }],
    [{ text: "🔁 Yeniden yaz", callback_data: "redo" }, { text: "❌ İptal", callback_data: "cancel" }],
  ] } });
}

async function gemini(env, prompt) {
  const model = env.GEMINI_MODEL || "gemini-flash-latest";
  const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-goog-api-key": env.GEMINI_API_KEY },
    body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }], generationConfig: { responseMimeType: "application/json", temperature: 0.9 } }),
  });
  if (!r.ok) throw new Error("Gemini " + r.status + " " + (await r.text()).slice(0, 200));
  const t = (await r.json()).candidates[0].content.parts[0].text;
  return JSON.parse(t.slice(t.indexOf("{"), t.lastIndexOf("}") + 1));
}

const say = (env, chat, text) => tg(env, "sendMessage", { chat_id: chat, text });
const tg = (env, m, body) => fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${m}`, {
  method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body),
});
