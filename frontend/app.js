/* ==================================================================
   Scheme Saathi — frontend logic (v3, professional UI)
   ================================================================== */
"use strict";

const $ = (id) => document.getElementById(id);

const state = {
  sessionId: null,
  uiLang: "en",
  convoLang: "en",
  report: null,
  busy: false,
  view: "chat",
  schemes: [],
  libFilter: { q: "", cat: "All" },
};

/* ------------------------------- i18n ------------------------------- */
const S = {
  en: {
    navChat: "Assistant", navReport: "Eligibility Report", navSchemes: "Scheme Library",
    profileTitle: "Your profile", profileHint: "Answers appear here in real time as you chat.",
    newSession: "New session", privacy: "In-memory session — nothing is stored",
    viewTitles: { chat: ["Assistant", "Answer a few questions — get your scheme eligibility instantly"],
                  report: ["Eligibility Report", "Ranked matches, gap analysis, documents & apply links"],
                  schemes: ["Scheme Library", "Browse every scheme in the rule engine"] },
    placeholder: "Type your answer — or ask a doubt, e.g. “BPL kya hai?”…", chooseOpt: "Choose an option or type below",
    multiOpt: "Select all that apply — <b>reply like “1, 3” or tap one</b>",
    kicker: (n) => `ELIGIBILITY REPORT · ${n} SCHEMES CHECKED`,
    repTitle: (name) => `${name} — your personalized scheme report`,
    print: "Print / Save PDF", newProfile: "New profile",
    statEligible: "Fully eligible", statNear: "Near-miss", statChecked: "Schemes checked", statValue: "Top-5 benefit value",
    eligibleTitle: "Fully eligible — ranked for you",
    nearTitle: "Almost there — precise gap analysis",
    whyMatch: "WHY YOU QUALIFY", docs: "DOCUMENTS REQUIRED", gaps: "WHERE YOU FALL SHORT",
    tips: "HOW TO BECOME ELIGIBLE", apply: "Apply on official portal", match: "match",
    neTitle: (n) => `Not eligible right now (${n}) — click to see reasons`,
    rulesVerified: (n) => `${n} criteria verified`,
    searchPh: "Search schemes, ministries, benefits…", all: "All",
    sessionLost: "Session expired — starting a fresh one…",
    yesNo: (v) => (v ? "Yes" : "No"),
    themes: "Themes", themesTitle: "Choose a theme",
    themeLight: "Gov Light (default)", themeMidnight: "Midnight 🌙",
    themeKesari: "Kesari 🧡", themeEmerald: "Emerald 🌿", themeRoyal: "Royal 💜",
  },
  hi: {
    navChat: "सहायक", navReport: "पात्रता रिपोर्ट", navSchemes: "योजना सूची",
    profileTitle: "आपकी प्रोफ़ाइल", profileHint: "चैट करते हुए उत्तर यहाँ दिखने लगेंगे।",
    newSession: "नया सत्र", privacy: "इन-मेमोरी सत्र — कुछ भी सहेजा नहीं जाता",
    viewTitles: { chat: ["सहायक", "कुछ सवालों के जवाब दें — तुरंत योजना पात्रता पाएँ"],
                  report: ["पात्रता रिपोर्ट", "रैंक किए गए मैच, गैप विश्लेषण, दस्तावेज़ व लिंक"],
                  schemes: ["योजना सूची", "नियम-इंजन की हर योजना देखें"] },
    placeholder: "अपना जवाब लिखें — या अपना संदेह पूछें, जैसे “BPL क्या है?”…", chooseOpt: "कोई विकल्प चुनें या नीचे लिखें",
    multiOpt: "जो भी लागू हों चुनें — <b>“1, 3” लिखें या एक टैप करें</b>",
    kicker: (n) => `पात्रता रिपोर्ट · ${n} योजनाएँ जाँची गईं`,
    repTitle: (name) => `${name} — आपकी व्यक्तिगत योजना रिपोर्ट`,
    print: "प्रिंट / PDF सहेजें", newProfile: "नई प्रोफ़ाइल",
    statEligible: "पूरी तरह पात्र", statNear: "नियर-मिस", statChecked: "जाँची गई योजनाएँ", statValue: "शीर्ष-5 लाभ मूल्य",
    eligibleTitle: "पूरी तरह पात्र — आपके लिए रैंक किया गया",
    nearTitle: "बस थोड़ा सा रह गया — सटीक गैप विश्लेषण",
    whyMatch: "आप क्यों पात्र हैं", docs: "ज़रूरी दस्तावेज़", gaps: "कहाँ कमी रह गई",
    tips: "पात्र कैसे बनें", apply: "आधिकारिक पोर्टल पर आवेदन करें", match: "मैच",
    neTitle: (n) => `अभी पात्र नहीं (${n}) — कारण देखने के लिए क्लिक करें`,
    rulesVerified: (n) => `${n} मानदंड सत्यापित`,
    searchPh: "योजना, मंत्रालय, लाभ खोजें…", all: "सभी",
    sessionLost: "सत्र समाप्त — नया शुरू हो रहा है…",
    yesNo: (v) => (v ? "हाँ" : "नहीं"),
    themes: "थीम", themesTitle: "थीम चुनें",
    themeLight: "गव लाइट (डिफ़ॉल्ट)", themeMidnight: "मिडनाइट 🌙",
    themeKesari: "केसरी 🧡", themeEmerald: "एमराल्ड 🌿", themeRoyal: "रॉयल 💜",
  },
};
const t = () => S[state.uiLang];

/* profile display maps (bilingual) */
const MAPS = {
  gender: { male: ["Male", "पुरुष"], female: ["Female", "महिला"], other: ["Other", "अन्य"] },
  area_type: { rural: ["Rural", "ग्रामीण"], urban: ["Urban", "शहरी"] },
  occupation: {
    farmer: ["Farmer", "किसान"], student: ["Student", "छात्र/छात्रा"],
    business: ["Business owner", "व्यवसायी"], self_employed: ["Self-employed", "स्वरोज़गार"],
    artisan: ["Artisan", "कारीगर"], street_vendor: ["Street vendor", "स्ट्रीट वेंडर"],
    employee: ["Salaried", "नौकरीपेशा"], unemployed: ["Looking for work", "कार्य की तलाश"],
    homemaker: ["Homemaker", "गृहिणी"], retired: ["Retired", "सेवानिवृत्त"],
  },
  education_level: {
    none: ["No formal schooling", "कोई औपचारिक शिक्षा नहीं"], below_8th: ["Below 8th", "8वीं से कम"],
    "8th": ["8th pass", "8वीं पास"], "10th": ["10th pass", "10वीं पास"], "12th": ["12th pass", "12वीं पास"],
    graduate: ["Graduate", "स्नातक"], post_graduate: ["Post-graduate", "स्नातकोत्तर"],
  },
  category: { general: ["General", "सामान्य"], obc: ["OBC", "ओबीसी"], sc: ["SC", "एससी"], st: ["ST", "एसटी"] },
  business_sector: { manufacturing: ["Manufacturing", "विनिर्माण"], services: ["Services", "सेवाएँ"], trading: ["Trading", "व्यापार"], other: ["Other", "अन्य"] },
  special: {
    daughter_under_10: ["Daughter below 10", "10 से छोटी बेटी"],
    pregnant_or_new_mother: ["Pregnant / new mother", "गर्भवती / नई माँ"],
    traditional_artisan: ["Traditional craft", "पारंपरिक शिल्प"],
    willing_shg: ["Open to SHG", "SHG से जुड़ सकती हैं"],
    differently_abled: ["Differently-abled", "दिव्यांग"],
    ex_serviceman: ["Ex-serviceman", "भूतपूर्व सैनिक"],
  },
};
const mapVal = (field, v) => (MAPS[field] && MAPS[field][v]) ? MAPS[field][v][state.uiLang === "hi" ? 1 : 0] : v;

function inrJS(n) {
  n = Math.round(Number(n) || 0);
  const s = String(Math.abs(n));
  if (s.length <= 3) return "₹" + s;
  let head = s.slice(0, -3), tail = s.slice(-3);
  const parts = [];
  while (head.length > 2) { parts.unshift(head.slice(-2)); head = head.slice(0, -2); }
  if (head) parts.unshift(head);
  return "₹" + parts.join(",") + "," + tail;
}

const PROFILE_ROWS = [
  ["name", "Name", "नाम", (v) => v],
  ["age", "Age", "उम्र", (v) => v],
  ["gender", "Gender", "लिंग", (v) => mapVal("gender", v)],
  ["state", "State", "राज्य", (v) => v],
  ["area_type", "Area", "क्षेत्र", (v) => mapVal("area_type", v)],
  ["occupation", "Occupation", "पेशा", (v) => mapVal("occupation", v)],
  ["education_level", "Education", "शिक्षा", (v) => mapVal("education_level", v)],
  ["annual_income", "Annual income", "वार्षिक आय", (v) => inrJS(v)],
  ["category", "Category", "वर्ग", (v) => mapVal("category", v)],
  ["is_bpl", "BPL card", "बीपीएल", (v) => t().yesNo(v)],
  ["land_holding", "Agri land", "कृषि भूमि", (v) => `${v} ha`],
  ["business_age_years", "Business age", "व्यवसाय आयु", (v) => (v === 0 ? (state.uiLang === "hi" ? "नया / आइडिया" : "New / idea") : `${v} yr`)],
  ["business_sector", "Sector", "क्षेत्र", (v) => mapVal("business_sector", v)],
  ["owns_pucca_house", "Pucca house", "पक्का मकान", (v) => t().yesNo(v)],
  ["has_bank_account", "Bank account", "बैंक खाता", (v) => t().yesNo(v)],
  ["special", "Special", "विशेष", (v) => (Array.isArray(v) && v.length ? v.map((x) => mapVal("special", x)).join(", ") : "—")],
];

/* ------------------------------- helpers ------------------------------- */
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function api(path, opts = {}) {
  const res = await fetch(path, { headers: { "Content-Type": "application/json" }, ...opts });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch {}
    const err = new Error(detail); err.status = res.status; throw err;
  }
  return res.json();
}

const esc = (x) => String(x).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
function mdLite(text) {
  let html = esc(text);
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  html = html.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
  return html.replace(/\n/g, "<br>");
}
function toast(msg) {
  document.querySelectorAll(".toast").forEach((x) => x.remove());
  const el = document.createElement("div");
  el.className = "toast"; el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2400);
}
const stamp = () => new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

const CHAKRA_MINI = `<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="46" fill="none" stroke="#174a9f" stroke-width="8"/><circle cx="50" cy="50" r="10" fill="#174a9f"/><g stroke="#174a9f" stroke-width="6" stroke-linecap="round"><line x1="50" y1="10" x2="50" y2="90"/><line x1="10" y1="50" x2="90" y2="50"/><line x1="22" y1="22" x2="78" y2="78"/><line x1="22" y1="78" x2="78" y2="22"/></g></svg>`;

/* ------------------------------- views ------------------------------- */
function showView(view) {
  state.view = view;
  document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
  $("view-" + view).classList.add("active");
  document.querySelectorAll(".s-nav-item").forEach((n) => n.classList.toggle("active", n.dataset.view === view));
  const [title, sub] = t().viewTitles[view];
  $("view-title").textContent = title;
  $("view-sub").textContent = sub;
  closeSidebar();
}

/* sidebar (mobile drawer) */
function openSidebar() { $("sidebar").classList.add("open"); $("overlay").hidden = false; requestAnimationFrame(() => $("overlay").classList.add("show")); }
function closeSidebar() { $("sidebar").classList.remove("open"); $("overlay").classList.remove("show"); setTimeout(() => ($("overlay").hidden = true), 250); }

/* ------------------------------- profile sidebar ------------------------------- */
function renderProfile(profile, step, total) {
  const rows = $("profile-rows");
  rows.innerHTML = "";
  const prevFilled = state.profileFilled ?? 0;
  let filled = 0;
  PROFILE_ROWS.forEach(([field, en, hi, fmt]) => {
    const v = profile[field];
    if (v === null || v === undefined || field === "language") return;
    filled++;
    const row = document.createElement("div");
    row.className = "row" + (filled > prevFilled ? " new" : "");   // only NEW answers spring in
    row.innerHTML = `<dt>${state.uiLang === "hi" ? hi : en}</dt><dd>${esc(String(fmt(v)))}</dd>`;
    rows.appendChild(row);
  });
  state.profileFilled = filled;
  $("profile-hint").style.display = filled ? "none" : "";
  const pct = total ? Math.min(100, Math.round((step / total) * 100)) : 0;
  $("s-progress-fill").style.width = pct + "%";
  $("profile-pct").textContent = total ? `${pct}%` : "";
}

/* ------------------------------- chat ------------------------------- */
function addMsg(sender, text) {
  const row = document.createElement("div");
  row.className = `msg-row ${sender}`;
  const avatar = sender === "bot" ? `<div class="avatar">${CHAKRA_MINI}</div>` : "";
  row.innerHTML = `${avatar}<div class="msg-col"><div class="bubble">${mdLite(text)}</div><div class="stamp">${stamp()}</div></div>`;
  $("chat-scroll").appendChild(row);
  scrollChat();
}
function scrollChat(smooth) {
  // Wait 2 frames so flex layout/fonts settle (options panel height change
  // shrinks the scroll area — scrolling before that leaves the last
  // message hidden behind the buttons).
  const sc = $("chat-scroll");
  requestAnimationFrame(() => requestAnimationFrame(() => {
    sc.scrollTo({ top: sc.scrollHeight, behavior: smooth ? "smooth" : "auto" });
  }));
}

function showTyping() {
  const row = document.createElement("div");
  row.className = "msg-row bot"; row.id = "typing";
  row.innerHTML = `<div class="avatar">${CHAKRA_MINI}</div><div class="msg-col"><div class="bubble typing-b"><i></i><i></i><i></i></div></div>`;
  $("chat-scroll").appendChild(row); scrollChat();
}
const hideTyping = () => $("typing")?.remove();

function renderOptions(replies, inputType) {
  const panel = $("options-panel"), grid = $("opt-grid"), title = $("opt-title");
  grid.innerHTML = "";
  const list = replies || [];
  if (!list.length) { panel.hidden = true; return; }
  const multi = inputType === "multichoice";
  title.innerHTML = multi ? t().multiOpt : t().chooseOpt;
  const cols2 = !multi && list.length >= 2 && list.length <= 6 && list.every((r) => String(r.label).length <= 16);
  grid.className = "opt-grid" + (cols2 ? " cols2" : "");
  list.forEach((r, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "opt" + (multi ? " multi" : "");
    b.style.animationDelay = `${i * 45}ms`;
    b.innerHTML = `<span class="opt-key">${multi ? "✓" : i + 1}</span><span class="opt-label">${esc(r.label)}</span><span class="opt-arrow">→</span>`;
    b.onclick = () => sendMessage(r.label);
    grid.appendChild(b);
  });
  panel.hidden = false;
  scrollChat(true);  // panel just ate vertical space — pull the latest message back into view
}

function setBusy(busy) {
  state.busy = busy;
  $("send-btn").disabled = busy;
  $("msg-input").disabled = busy;
}

/* ------------------------------- session ------------------------------- */
async function startSession() {
  state.report = null;
  window.__reportSid = null;
  $("chat-scroll").innerHTML = "";
  renderOptions([], "text");
  $("report-count").hidden = true;
  $("nav-report").disabled = true;
  renderProfile({}, 0, 1);
  showView("chat");
  const data = await api("/api/session/new", { method: "POST", body: "{}" });
  state.sessionId = data.session_id;
  await sleep(250);
  for (const m of data.messages) addMsg("bot", m);
  renderOptions(data.quick_replies, "choice");
  $("msg-input").focus();
}

async function sendMessage(text) {
  text = (text || "").trim();
  if (!text || state.busy) return;
  $("msg-input").value = "";
  renderOptions([], "text");
  addMsg("user", text);
  // paper-plane take-off 🛩️
  const sb = $("send-btn");
  sb.classList.remove("fly"); void sb.offsetWidth; sb.classList.add("fly");
  setTimeout(() => sb.classList.remove("fly"), 620);
  setBusy(true); showTyping();
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: state.sessionId, message: text }),
    });
    hideTyping();
    for (const m of data.messages) { await sleep(360); addMsg("bot", m); }
    renderOptions(data.quick_replies, data.input_type);
    renderProfile(data.profile || {}, data.step, data.total_steps);
    if (data.language) state.convoLang = data.language;
    if (data.report) {
      const firstReport = !state.report;         // only the FIRST report auto-opens the dashboard;
      state.report = data.report;                // follow-up answers stay in chat where the user is
      window.__reportSid = state.sessionId;
      renderReport(data.report);
      if (firstReport) { await sleep(600); showView("report"); confettiBurst(); }
    }
  } catch (err) {
    hideTyping();
    if (err.status === 404) { toast(t().sessionLost); await startSession(); }
    else addMsg("bot", "⚠️ " + err.message);
  } finally { setBusy(false); }
}

/* --------------------------- delight fx --------------------------- */
const REDUCED_MOTION = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

function countUp(el, target, fmt = (x) => String(x), ms = 900) {
  if (!el) return;
  if (REDUCED_MOTION) { el.textContent = fmt(target); return; }
  const t0 = performance.now();
  (function step(now) {
    const k = Math.min(1, (now - t0) / ms);
    const e = 1 - Math.pow(1 - k, 3);
    el.textContent = fmt(Math.round(target * e));
    if (k < 1) requestAnimationFrame(step);
  })(t0);
}

function confettiBurst() {
  if (REDUCED_MOTION) return;
  const c = $("confetti-canvas");
  if (!c) return;
  const ctx = c.getContext("2d");
  c.width = window.innerWidth; c.height = window.innerHeight;
  c.hidden = false;
  const COLORS = ["#e2680f", "#1b5bb5", "#167d4f", "#f3b61f", "#5c8ef2", "#fff"];
  const parts = Array.from({ length: 170 }, () => ({
    x: window.innerWidth / 2 + (Math.random() - .5) * 160,
    y: window.innerHeight * .30,
    vx: (Math.random() - .5) * 14,
    vy: -4.5 - Math.random() * 9.5,
    g: .21 + Math.random() * .13,
    s: 5 + Math.random() * 7,
    r: Math.random() * Math.PI,
    vr: (Math.random() - .5) * .32,
    col: COLORS[(Math.random() * COLORS.length) | 0],
    circ: Math.random() < .3,
    life: 0,
  }));
  (function tick() {
    ctx.clearRect(0, 0, c.width, c.height);
    let alive = 0;
    for (const p of parts) {
      p.life++; p.x += p.vx; p.y += p.vy; p.vy += p.g; p.vx *= .985; p.r += p.vr;
      if (p.y < c.height + 40 && p.life < 260) alive++;
      ctx.save();
      ctx.translate(p.x, p.y); ctx.rotate(p.r);
      ctx.globalAlpha = Math.max(0, 1 - p.life / 250);
      ctx.fillStyle = p.col;
      if (p.circ) { ctx.beginPath(); ctx.arc(0, 0, p.s / 2, 0, 7); ctx.fill(); }
      else ctx.fillRect(-p.s / 2, -p.s / 2, p.s, p.s * .62);
      ctx.restore();
    }
    if (alive) requestAnimationFrame(tick);
    else { c.hidden = true; ctx.clearRect(0, 0, c.width, c.height); }
  })();
}

/* ------------------------------- report ------------------------------- */
function L(obj, base) { return obj[`${base}_${state.uiLang}`] ?? obj[`${base}_en`] ?? ""; }

const li = (items, cls) => (items || []).map((x) => `<li class="${cls}">${esc(x)}</li>`).join("");

function cardHtml(card, rank, near, delay) {
  const pick = (b) => (state.uiLang === "hi" ? card[`${b}_hi`] : card[`${b}_en`]) || [];
  const docs = pick("documents");
  const pct = near ? 50 : card.match_percent;
  const bodyWhy = near
    ? `<div class="mini-h">${t().gaps}</div><ul class="tick-list">${li(pick("reasons"), "gap")}${li(pick("gaps"), "gap")}</ul>
       ${pick("tips").length ? `<div class="mini-h" style="margin-top:14px">${t().tips}</div><ul class="tick-list">${li(pick("tips"), "tip")}</ul>` : ""}`
    : `<div class="mini-h">${t().whyMatch}</div><ul class="tick-list">${li(pick("reasons"))}</ul>`;
  return `
  <article class="sc-card card rise ${near ? "near" : ""}" style="animation-delay:${delay}ms" data-card>
    <div class="sc-head" role="button" tabindex="0" aria-expanded="false">
      <div class="rank-badge">${near ? "≈" : "#" + rank}</div>
      <div class="sc-t">
        <div class="sc-name">${esc(L(card, "name"))}</div>
        <div class="sc-meta">${esc(L(card, "category"))}${card.ministry_en ? " · " + esc(L(card, "ministry")) : ""}</div>
      </div>
      <div class="sc-mp">
        ${near
          ? `<div class="mp-top"><b>${t().match}</b><span>gap</span></div><div class="mp-bar"><span data-w="62"></span></div>`
          : `<div class="mp-top"><b>${card.match_percent}%</b><span>${t().match}</span></div><div class="mp-bar"><span data-w="${pct}"></span></div>`}
      </div>
      <button class="chev" aria-label="expand">▾</button>
    </div>
    <div class="sc-body"><div class="sc-body-in"><div class="sc-body-pad">
      <div style="margin-bottom:14px"><span class="benefit-line"><span class="rupee">₹</span><span>${esc(L(card, "benefit"))}</span></span></div>
      <div class="sc-cols">
        <div>${bodyWhy}</div>
        <div><div class="mini-h">${t().docs}</div><div class="doc-chips">${docs.map((d) => `<span class="doc-chip">${esc(d)}</span>`).join("")}</div></div>
      </div>
      <div class="sc-actions">
        <a class="btn btn-primary sm" href="${esc(card.apply_url)}" target="_blank" rel="noopener">${t().apply} ↗</a>
        ${!near && card.apply_mode_en ? `<span class="apply-mode">${esc(L(card, "apply_mode"))}</span>` : ""}
      </div>
    </div></div></div>
  </article>`;
}

function renderReport(report) {
  const lang = state.uiLang;
  const summary = report.summary_llm || (lang === "hi" ? report.summary_hi : report.summary_en);
  const llmTag = report.summary_llm ? `<span class="llm-tag">✨ GEMINI</span>` : "";
  const v = report.top_benefit_estimate || 0;
  const fmtValue = (n) => n >= 10000000 ? "₹" + (n / 10000000).toFixed(2).replace(/\.?0+$/, "") + " Cr+"
    : n >= 100000 ? "₹" + (n / 100000).toFixed(1).replace(/\.0$/, "") + " L+"
    : "₹" + Math.round(n / 1000) + "K+";
  const value = fmtValue(v);

  const eligibleHtml = (report.eligible || []).map((c, i) => cardHtml(c, i + 1, false, 60 + i * 70)).join("");
  const nearHtml = (report.near_miss || []).map((c, i) => cardHtml(c, 0, true, 60 + i * 70)).join("");
  const neItems = (report.not_eligible || [])
    .map((c) => `<li><b>${esc(L(c, "name"))}</b> — ${esc(((lang === "hi" ? c.reasons_hi : c.reasons_en) || [""])[0])}</li>`)
    .join("");

  $("report-root").innerHTML = `
    <div class="rep-head card rise">
      <div>
        <div class="rep-kicker">${t().kicker(report.n_checked)}</div>
        <h3>${esc(t().repTitle(report.profile.name || ""))}</h3>
        <p class="rep-summary">${mdLite(summary)} ${llmTag}</p>
      </div>
      <div class="rep-actions">
        <button class="btn btn-outline sm" id="btn-print">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
          ${t().print}</button>
        <button class="btn btn-ghost sm" id="btn-new">${t().newProfile}</button>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat card rise" style="animation-delay:40ms"><div class="stat-ico g">✓</div><div><b>${report.n_eligible}</b><span>${t().statEligible}</span></div></div>
      <div class="stat card rise" style="animation-delay:90ms"><div class="stat-ico a">≈</div><div><b>${report.n_near_miss}</b><span>${t().statNear}</span></div></div>
      <div class="stat card rise" style="animation-delay:140ms"><div class="stat-ico b">▤</div><div><b>${report.n_checked}</b><span>${t().statChecked}</span></div></div>
      <div class="stat card rise" style="animation-delay:190ms"><div class="stat-ico r">₹</div><div><b>${value}</b><span>${t().statValue}</span></div></div>
    </div>

    <h4 class="sec-h rise" style="animation-delay:220ms"><span class="marker g"></span>${t().eligibleTitle}<span class="count-chip g">${report.n_eligible}</span></h4>
    <div>${eligibleHtml}</div>

    ${report.near_miss?.length ? `
      <h4 class="sec-h rise" style="animation-delay:260ms"><span class="marker a"></span>${t().nearTitle}<span class="count-chip a">${report.n_near_miss}</span></h4>
      <div>${nearHtml}</div>` : ""}

    ${report.not_eligible?.length ? `
      <details class="ne-list rise" style="animation-delay:300ms"><summary>${t().neTitle(report.not_eligible.length)}</summary><ul>${neItems}</ul></details>` : ""}

    <div class="rep-bottom">
      <button class="btn btn-primary" id="btn-print2">
        <svg viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/></svg>
        ${t().print}</button>
      <button class="btn btn-outline" id="btn-new2">${t().newProfile}</button>
    </div>
  `;

  $("report-count").textContent = report.n_eligible;
  $("report-count").hidden = false;
  $("nav-report").disabled = false;

  // count-up delight on the hero stats 🔢
  const statB = document.querySelectorAll(".stat b");
  countUp(statB[0], report.n_eligible);
  countUp(statB[1], report.n_near_miss);
  countUp(statB[2], report.n_checked);
  countUp(statB[3], v, fmtValue, 1150);

  const openPrint = () => window.open(`/api/report/${window.__reportSid}/html?lang=${lang}`, "_blank");
  $("btn-print").onclick = openPrint;
  $("btn-print2").onclick = openPrint;
  $("btn-new").onclick = $("btn-new2").onclick = () => startSession();

  // expand/collapse + animate match bars
  document.querySelectorAll("[data-card] .sc-head").forEach((h) => {
    const toggle = () => h.parentElement.classList.toggle("expanded");
    h.addEventListener("click", (e) => { if (e.target.closest("a")) return; toggle(); });
    h.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggle(); } });
  });
  requestAnimationFrame(() => requestAnimationFrame(() => {
    document.querySelectorAll(".mp-bar span").forEach((s) => (s.style.width = s.dataset.w + "%"));
  }));
  // auto-expand the #1 card for instant readability
  const first = document.querySelector("[data-card]");
  if (first) first.classList.add("expanded");
}

/* ------------------------------- scheme library ------------------------------- */
function renderLib() {
  const lang = state.uiLang;
  const cats = ["All", ...new Set(state.schemes.map((s) => s.category_en))];
  const pills = $("lib-pills");
  pills.innerHTML = "";
  cats.forEach((c) => {
    const b = document.createElement("button");
    b.className = "lib-pill" + (state.libFilter.cat === c ? " active" : "");
    b.textContent = c === "All" ? t().all : c;
    b.onclick = () => { state.libFilter.cat = c; renderLib(); };
    pills.appendChild(b);
  });

  const q = state.libFilter.q.toLowerCase();
  const filtered = state.schemes.filter((s) => {
    const inCat = state.libFilter.cat === "All" || s.category_en === state.libFilter.cat;
    if (!inCat) return false;
    if (!q) return true;
    return [s.name_en, s.name_hi, s.ministry_en, s.benefit_en, s.benefit_hi, s.category_en]
      .join(" ").toLowerCase().includes(q);
  });

  const grid = $("lib-grid");
  grid.innerHTML = filtered.length ? "" : `<div class="lib-empty">—</div>`;
  filtered.forEach((s, i) => {
    const el = document.createElement("article");
    el.className = "lib-card card rise";
    el.style.animationDelay = `${Math.min(i, 10) * 40}ms`;
    el.innerHTML = `
      <span class="lib-cat">${esc(lang === "hi" ? s.category_hi : s.category_en)}</span>
      <div class="lib-name">${esc(lang === "hi" ? s.name_hi : s.name_en)}</div>
      ${lang === "en" ? `<div class="lib-hi">${esc(s.name_hi)}</div>` : ""}
      <div class="lib-benefit">${esc(lang === "hi" ? s.benefit_hi : s.benefit_en)}</div>
      <div class="lib-foot">
        <span class="lib-crit">${t().rulesVerified(s.n_rules)}</span>
        <a class="btn btn-outline sm" href="${esc(s.apply_url)}" target="_blank" rel="noopener">${state.uiLang === "hi" ? "पोर्टल खोलें" : "Open portal"} ↗</a>
      </div>`;
    grid.appendChild(el);
  });
}

/* ------------------------------- voice ------------------------------- */
function initMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) return;
  const mic = $("mic-btn");
  mic.hidden = false;
  let rec = null;
  mic.onclick = () => {
    if (rec) { rec.stop(); return; }
    rec = new SR();
    rec.lang = state.convoLang === "hi" ? "hi-IN" : "en-IN";
    rec.interimResults = false;
    mic.classList.add("rec");
    rec.onresult = (e2) => { const text = e2.results[0][0].transcript; $("msg-input").value = text; sendMessage(text); };
    rec.onend = rec.onerror = () => { mic.classList.remove("rec"); rec = null; };
    rec.start();
  };
}

/* ------------------------------- boot ------------------------------- */
function applyUiLang() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (t()[key]) el.textContent = t()[key];
  });
  $("msg-input").placeholder = t().placeholder;
  $("scheme-search").placeholder = t().searchPh;
  $("lang-seg").classList.toggle("hi", state.uiLang === "hi");
  document.querySelectorAll("#lang-seg .seg-btn").forEach((b) => b.classList.toggle("active", b.dataset.lang === state.uiLang));
  showView(state.view);
  if (state.report) renderReport(state.report);
  if (state.schemes.length) renderLib();
}

async function boot() {
  try {
    const meta = await api("/api/meta");
    $("scheme-count").textContent = meta.total_schemes;
    $("engine-badge").textContent = meta.llm_enabled ? "rules + Gemini" : "rule-engine";
  } catch {}
  try {
    state.schemes = await api("/api/schemes");
    renderLib();
  } catch {}
  await startSession();
}

$("composer").addEventListener("submit", (e) => { e.preventDefault(); sendMessage($("msg-input").value); });
document.querySelectorAll(".s-nav-item[data-view]").forEach((n) => {
  n.addEventListener("click", () => { if (!n.disabled) showView(n.dataset.view); });
});

/* ------------------------------- themes ------------------------------- */
const THEMES = ["light", "midnight", "kesari", "emerald", "royal"];

function applyTheme(id, save = true) {
  if (!THEMES.includes(id)) id = "light";
  const root = document.documentElement;
  root.classList.add("theme-anim");                       // 0.35s cross-fade between palettes
  root.dataset.theme = id;
  clearTimeout(root.__ta);
  root.__ta = setTimeout(() => root.classList.remove("theme-anim"), 450);
  document.querySelectorAll(".theme-opt").forEach((b) =>
    b.classList.toggle("active", b.dataset.theme === id));
  if (save) { try { localStorage.setItem("ss-theme", id); } catch {} }
}
try { applyTheme(localStorage.getItem("ss-theme") || "light", false); } catch {}

$("themes-btn").addEventListener("click", (e) => {
  e.stopPropagation();
  const panel = $("themes-panel"), open = panel.hidden;
  panel.hidden = !open;
  $("themes-btn").classList.toggle("open", open);
  $("themes-btn").setAttribute("aria-expanded", String(open));
});
document.querySelectorAll(".theme-opt").forEach((b) =>
  b.addEventListener("click", () => {
    applyTheme(b.dataset.theme);
    $("themes-panel").hidden = true;
    $("themes-btn").classList.remove("open");
    $("themes-btn").setAttribute("aria-expanded", "false");
  }));
document.addEventListener("click", (e) => {
  if (!e.target.closest(".s-themes")) {
    $("themes-panel").hidden = true;
    $("themes-btn").classList.remove("open");
    $("themes-btn").setAttribute("aria-expanded", "false");
  }
});
$("restart-btn").onclick = () => startSession();
$("hamb").onclick = openSidebar;
$("overlay").onclick = closeSidebar;
$("scheme-search").addEventListener("input", (e) => { state.libFilter.q = e.target.value; renderLib(); });
document.querySelectorAll("#lang-seg .seg-btn").forEach((b) => {
  b.addEventListener("click", () => { state.uiLang = b.dataset.lang; applyUiLang(); });
});

initMic();
boot();
