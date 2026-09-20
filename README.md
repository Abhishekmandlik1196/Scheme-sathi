# 🇮🇳 Scheme Saathi — स्कीम साथी

> **AI agent that tells every citizen exactly which government schemes they deserve — and why.**
> Conversational profile intake → transparent rule engine → ranked eligibility report with **near-miss gap analysis**, in **English + हिंदी**.

![status](https://img.shields.io/badge/tests-26%20passed-brightgreen) ![schemes](https://img.shields.io/badge/schemes-25-orange) ![stack](https://img.shields.io/badge/stack-FastAPI%20%2B%20LangGraph%20%2B%20Gemini-blue)

---

## 😤 The Problem

India has **700+ government schemes**, but the people who need them most — a farmer in UP, a street vendor in Delhi, a student in a village — **don't know what they're eligible for**. Portals are scattered, criteria are buried in PDFs, and most beneficiaries find out *by accident*.

## 💡 The Solution

Scheme Saathi asks a few **adaptive** questions (a farmer gets land questions, a student gets education questions — never a 20-field form), then instantly checks **25 curated central schemes** with a **transparent rule engine** and produces:

- ✅ **Eligible schemes** — ranked by value & relevance, with the *exact criteria you satisfy* and **why**
- ⚠️ **Near-miss gap analysis** — *"Your income ₹3,75,000 vs limit ₹3,00,000 — ₹75,000 over. You may still qualify under LIG."* + actionable **tips to become eligible**
- 📄 Documents checklist + 🔗 apply links + 🖨️ **printable PDF report** (an NGO worker can print it for a beneficiary)
- 🌐 Full **Hindi + English** support with auto language detection
- 💬 **Ask anything, anytime** — stuck on a question? Just type your doubt (*"BPL kya hai?"*, *"samajh nahi aaya"*) and the assistant explains in plain words and gently re-asks. Works **fully offline** (curated explanations per question); with a Gemini key the explanations become conversational — **grounded in the curated text so it can never invent scheme rules**.
- 🎤 Voice input (Web Speech API)

---

## 🏆 Why this wins — differentiators

| Feature | Typical team | Scheme Saathi |
|---|---|---|
| Profile intake | Static form | **Adaptive conversational flow** (LangGraph state machine) |
| Confused users | Error, or bot breaks | **Ask-anytime help**: doubts answered mid-flow, question re-asked, flow never lost — offline-safe |
| Eligibility | Black-box if-else / LLM guessing | **Deterministic rule engine** — every verdict traceable to a rule, bilingual |
| Near-miss | Not implemented | **Precise gap math** (₹ amounts, years, hectares) + cross-scheme tips |
| Language | English only | Hindi-first design, auto-detect, full demo in Hindi |
| Demo flow | Nervous live typing | **Quick-reply buttons** drive a full persona in ~10 seconds of taps; sidebar shows the profile building live |
| LLM dependency | Demo dies without API | **Graceful degradation**: Gemini enhances, templates guarantee output |

---

## 🧠 Architecture

```
┌──────────────────────── Frontend (vanilla JS, glass UI) ────────────────────────┐
│  WhatsApp-style chat · quick-replies · instant persona demos · report dashboard  │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │ REST (JSON)
┌──────────────────────────────────▼──────────────────────────────────────────────┐
│                              FastAPI  (app/api/routes.py)                        │
│  /api/session/new · /api/chat · /api/report/{id}(.html) · /api/schemes · /demo   │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │ per message
┌──────────────────────────────────▼──────────────────────────────────────────────┐
│                     LangGraph orchestration (app/graph/main_graph.py)            │
│                                                                                  │
│   START ──► intake ──┬─► (more questions) ───────────────► END                   │
│                      ├─► pipeline (match→rank→reason) ──► END                    │
│                      └─► followup (report Q&A) ─────────► END                    │
│        (sequential fallback if langgraph missing — identical behaviour)          │
└──────────┬───────────────────────────────────┬──────────────────────────────────┘
           ▼                                   ▼
┌───────────────────────┐          ┌──────────────────────────────────────────────┐
│ Adaptive intake agent │          │ Eligibility engine (app/engine)               │
│ app/agents/intake.py  │          │ matcher.py  — rule groups (ALL/ANY) per scheme│
│ prompts.py (EN/HI)    │          │ near_miss.py— precise gap analysis + tips     │
│ tolerant parsers      │          │ ranker.py   — benefit/criteria/fit/popularity │
│ (₹lakh, हाँ, indexes) │          │ reasoner.py — bilingual explained report      │
└───────────────────────┘          └──────────────┬───────────────────────────────┘
                                                  ▼
                          ┌──────────────────────────────────┐    ┌───────────────┐
                          │ data/schemes.json                │    │ Gemini (opt.) │
                          │ 25 schemes · bilingual rules     │    │ summary polish│
                          │ docs · benefits · apply links    │    │ + follow-up Q │
                          └──────────────────────────────────┘    └───────────────┘
```

---

## 🚀 Quickstart

```bash
pip install -r requirements.txt

# optional — without a key, everything still works (offline mode)
cp .env.example .env        # add GEMINI_API_KEY (free: aistudio.google.com/apikey)

python run.py               # → http://localhost:8000
```

Run the verification suite (all 4 demo personas + engine tests):

```bash
pytest tests/ -v
```

---

## 🎬 For the demo (important!)

Drive the chat live — quick-reply buttons make each persona ~10–15 seconds of tapping. Keep these cheat-cards next to you:

| Persona | Profile (answers to give) | Headline result |
|---|---|---|
| 🌾 **Ramesh** (run fully in **Hindi**) | 45 · पुरुष · ग्रामीण UP · किसान · ₹1–2.5 लाख · एससी · BPL हाँ · 1–2 हे. · पक्का नहीं · बैंक हाँ | PM-KISAN, Fasal Bima, KUSUM, PMAY-G, Ayushman, **Stand-Up India (SC!)** ✅ — MUDRA & APY as near-misses |
| 🎓 **Priya** | 20 · Female · Urban MH · Student · 12th · ₹1–2.5L · OBC · BPL No · pucca Yes · bank Yes | NSP + Post-Matric OBC scholarships ✅, Ayushman near-miss |
| 💼 **Amit** | 28 · Male · Delhi · Urban · Business · Graduate · ₹2.5–5L · General · new idea · services · pucca No · bank Yes | MUDRA + PMEGP + CGTMSE + Seed Fund ✅; **Stand-Up India near-miss with partnership tip**, PMAY-U gap **₹75,000** precise |
| 👩‍👧 **Sunita** | 35 · Female · Rural MP · Homemaker · <₹1L · ST · BPL Yes · pucca No · bank **No** · daughter+SHG | 8 schemes ✅ incl. **Jan Dhan**; insurance/pension become **near-misses that point back to Jan Dhan** (cross-scheme reasoning!) |

*(The same personas also exist as API fixtures — `POST /api/demo/ramesh` returns the full transcript + report, used by the test suite.)*

**Judges' moment** — midway through Ramesh's flow, when the BPL question appears, type **"BPL kya hai?"** instead of answering: the assistant explains BPL in simple Hindi (ration card, SECC list) and gently re-asks — the flow never breaks, and it works even with **internet off**.

Then show: the near-miss (amber) cards → Print/Save PDF → language toggle → sidebar Scheme Library.
Full script: **[demo/demo_script.md](demo/demo_script.md)** · Deploy & submission: **[demo/HACKATHON_SUBMISSION_GUIDE.md](demo/HACKATHON_SUBMISSION_GUIDE.md)** (GitHub push → Render free live link → demo video → form checklist).

---

## 🛠️ Tech stack

| Layer | Choice | Why |
|---|---|---|
| Backend | FastAPI + Uvicorn | required, instant, auto OpenAPI docs at `/docs` |
| Orchestration | LangGraph `StateGraph` | required by the problem statement; real graph per message |
| Eligibility | Custom deterministic rule engine | **correctness + explainability** > LLM improvisation |
| LLM | Gemini 2.0 Flash (optional) | free tier; summary polish + follow-up Q&A with hard fallback |
| Data | 25-scheme curated JSON (bilingual) | editable without touching code; add schemes in minutes |
| Frontend | Vanilla HTML/CSS/JS, glass UI | zero build step, runs anywhere |

## 📁 Layout

```
scheme-saathi/
├── data/schemes.json        # 25 schemes, structured bilingual eligibility rules
├── app/
│   ├── main.py              # FastAPI entry (+ static hosting)
│   ├── api/                 # routes, sessions, demo runner, printable report
│   ├── graph/               # LangGraph state machine + state schema
│   ├── agents/              # adaptive intake + bilingual prompts/parsers
│   ├── engine/              # rules · matcher · near-miss · ranker · reasoner
│   └── core/                # config (.env) + Gemini client (offline-safe)
├── frontend/                # chat UI + report dashboard
├── demo/                    # personas.json (one-click demos) + demo_script.md
└── tests/test_engine.py     # 26 tests — personas, gaps, ranking, adaptivity
```

## 🌐 Extending

- **Add a scheme** → append one JSON object to `data/schemes.json` (no code changes; tests validate the format).
- **Add a state scheme** → same JSON pattern; the engine already supports `any`/`all` groups.
- **More languages** → add `*_mr`/`*_ta` fields; prompts module is centralized.
- **RAG over scheme PDFs** → the rule engine gives the *verdict*; drop guidelines into ChromaDB and let Gemini cite them in explanations (planned; hooks exist in `core/llm.py`).

## ⚠️ Disclaimer

Scheme data is curated from official public criteria (Dec 2024) and simplified for the demo — final eligibility is always verified by the concerned department/portal.
