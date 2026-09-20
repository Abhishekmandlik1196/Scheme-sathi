"""
Print-friendly HTML report — 'Download PDF' in the app opens this page;
Ctrl/Cmd+P → Save as PDF gives a professional shareable document
(exactly what an NGO worker prints for a beneficiary).
"""

from __future__ import annotations

from datetime import datetime
from html import escape as e


def _card(c: dict, lang: str, near_miss: bool = False) -> str:
    name = c["name_hi" if lang == "hi" else "name_en"]
    benefit = c["benefit_hi" if lang == "hi" else "benefit_en"]
    docs = c.get("documents_hi" if lang == "hi" else "documents_en", [])
    reasons = c.get("reasons_hi" if lang == "hi" else "reasons_en", [])
    gaps = c.get("gaps_hi" if lang == "hi" else "gaps_en", [])
    tips = c.get("tips_hi" if lang == "hi" else "tips_en", [])
    badge = "⚠️ ALMOST ELIGIBLE" if near_miss else f"✅ ELIGIBLE — {c.get('match_percent', 0)}% match"

    rows = []
    for r in reasons:
        rows.append(f'<li class="ok">{e(r)}</li>')
    for g in gaps:
        rows.append(f'<li class="gap"><b>Gap:</b> {e(g)}</li>')
    for t in tips:
        rows.append(f'<li class="tip">💡 {e(t)}</li>')
    reason_html = "<ul>" + "".join(rows) + "</ul>" if rows else ""
    doc_html = "".join(f"<li>{e(d)}</li>" for d in docs)

    return f"""
    <div class="card {'near' if near_miss else 'ok-card'}">
      <div class="card-head">
        <span class="scheme">{e(name)}</span>
        <span class="badge {'near-badge' if near_miss else ''}">{badge}</span>
      </div>
      <p class="benefit"><b>{'लाभ' if lang == 'hi' else 'Benefit'}:</b> {e(benefit)}</p>
      {reason_html}
      <p><b>{'दस्तावेज़' if lang == 'hi' else 'Documents'}:</b></p>
      <ul class="docs">{doc_html}</ul>
      <p class="apply">🔗 <b>{'आवेदन' if lang == 'hi' else 'Apply'}:</b> <a href="{e(c['apply_url'])}">{e(c['apply_url'])}</a></p>
    </div>"""


def render_html_report(report: dict, lang: str = "en") -> str:
    p = report.get("profile", {})
    summary = report.get("summary_llm") or (report.get("summary_hi") if lang == "hi" else report.get("summary_en")) or ""
    eligible = report.get("eligible", [])
    near = report.get("near_miss", [])
    hi = lang == "hi"

    profile_rows = "".join(
        f"<tr><th>{e(label)}</th><td>{e(str(value))}</td></tr>"
        for label, value in [
            ("नाम / Name", p.get("name", "—")),
            ("उम्र / Age", p.get("age", "—")),
            ("लिंग / Gender", p.get("gender", "—")),
            ("राज्य / State", p.get("state", "—")),
            ("क्षेत्र / Area", "ग्रामीण / Rural" if p.get("area_type") == "rural" else "शहरी / Urban"),
            ("पेशा / Occupation", p.get("occupation", "—")),
            ("वार्षिक आय / Annual income", f"₹{int(p.get('annual_income', 0)):,}"),
            ("वर्ग / Category", str(p.get("category", "—")).upper()),
        ]
    )

    eligible_html = "".join(_card(c, lang) for c in eligible)
    near_html = "".join(_card(c, lang, near_miss=True) for c in near)

    near_section = (
        f'<h2 class="near-title">⚠️ {"आप इन योजनाओं के बहुत करीब हैं" if hi else "You are ALMOST eligible for these"} ({len(near)})</h2>{near_html}'
        if near else ""
    )

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<title>Scheme Saathi — Eligibility Report</title>
<style>
  * {{ box-sizing: border-box; font-family: 'Segoe UI', 'Noto Sans', sans-serif; }}
  body {{ max-width: 800px; margin: 0 auto; padding: 24px; color: #1a1a2e; background: #fff; }}
  .header {{ background: linear-gradient(135deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
            padding: 3px; border-radius: 14px; margin-bottom: 20px; }}
  .header-inner {{ background: #fff; border-radius: 12px; padding: 18px 22px; }}
  h1 {{ font-size: 22px; margin: 0 0 4px; color: #0a3d91; }}
  .sub {{ color: #666; font-size: 13px; margin: 0; }}
  .summary {{ background: #f0f7ff; border-left: 4px solid #0a6cff; padding: 12px 16px;
             border-radius: 8px; margin: 16px 0; line-height: 1.6; }}
  table {{ width: 100%; border-collapse: collapse; margin: 12px 0 20px; font-size: 14px; }}
  th, td {{ border: 1px solid #dde; padding: 7px 10px; text-align: left; }}
  th {{ background: #f4f6fb; width: 40%; }}
  h2 {{ font-size: 18px; margin: 22px 0 10px; color: #137a3f; }}
  .near-title {{ color: #b26a00; }}
  .card {{ border: 1px solid #d5e8db; border-left: 5px solid #1f9d4d; border-radius: 10px;
          padding: 14px 18px; margin: 12px 0; page-break-inside: avoid; }}
  .card.near {{ border-color: #f2e3c6; border-left-color: #e69b00; background: #fffdf7; }}
  .card-head {{ display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .scheme {{ font-weight: 700; font-size: 16px; }}
  .badge {{ background: #e2f6e9; color: #137a3f; font-size: 12px; font-weight: 700;
           padding: 4px 10px; border-radius: 20px; white-space: nowrap; }}
  .badge.near-badge {{ background: #fff0d6; color: #a66a00; }}
  .benefit {{ color: #333; margin: 8px 0; }}
  ul {{ margin: 6px 0; padding-left: 20px; }}
  li {{ margin: 4px 0; line-height: 1.5; }}
  li.ok::marker {{ color: #1f9d4d; }}
  li.gap {{ color: #b25e00; }}
  li.tip {{ color: #0a5a8a; }}
  .docs {{ columns: 2; font-size: 13px; }}
  .apply {{ font-size: 13px; }}
  .footer {{ margin-top: 28px; padding-top: 12px; border-top: 2px dashed #ccc;
            font-size: 12px; color: #777; }}
  .print-btn {{ position: fixed; top: 14px; right: 14px; background: #0a6cff; color: #fff;
               border: 0; padding: 10px 18px; border-radius: 8px; font-size: 14px;
               cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,.2); }}
  @media print {{ .print-btn {{ display: none; }} body {{ padding: 0; }} }}
</style>
</head>
<body>
<button class="print-btn" onclick="window.print()">🖨️ {"प्रिंट / पीडीएफ सहेजें" if hi else "Print / Save as PDF"}</button>
<div class="header"><div class="header-inner">
  <h1>🇮🇳 स्कीम साथी — Scheme Saathi</h1>
  <p class="sub">{"व्यक्तिगत सरकारी योजना पात्रता रिपोर्ट" if hi else "Personal Government Scheme Eligibility Report"} · {datetime.now().strftime('%d %b %Y, %I:%M %p')}</p>
</div></div>

<div class="summary">{e(summary)}</div>

<table>{profile_rows}</table>

<h2>✅ {"आप इन योजनाओं के लिए पूरी तरह पात्र हैं" if hi else "You are FULLY eligible for these schemes"} ({len(eligible)})</h2>
{eligible_html}
{near_section}

<div class="footer">
  Generated by Scheme Saathi · {report.get('n_checked', 25)} schemes checked with a transparent rule engine.<br>
  {"यह रिपोर्ट सूचना के लिए है — अंतिम पात्रता संबंधित विभाग/पोर्टल पर सत्यापित करें।" if hi else "This report is indicative — please verify final eligibility with the concerned department / official portal."}
</div>
</body></html>"""
