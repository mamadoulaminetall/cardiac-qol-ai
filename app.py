"""
QoL Cardiac — Outil IA d'évaluation de la qualité de vie
Populations : Liste attente / LVAD / Post-greffe cardiaque
Stockage : SQLite local (persistance longitudinale T0→T5)
"""

import streamlit as st
import streamlit.components.v1 as _components
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
import sqlite3
import hashlib
import io
import os
from datetime import datetime

st.set_page_config(
    page_title="QoL Cardiac — MedFlow AI",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset & Base ── */
[data-testid="stAppViewContainer"] { background-color: #0f172a; }
[data-testid="stSidebar"] { display:none; }
[data-testid="stHeader"] { display:none; }
[data-testid="collapsedControl"] { display:none; }
section[data-testid="stMain"] > div:first-child { padding-top: 0 !important; }
.block-container { padding-top: 0 !important; max-width: 1200px; }
h1, h2, h3, h4 { color: #f1f5f9 !important; }
p, li, label { color: #cbd5e1 !important; }
.stSelectbox label, .stSlider label, .stNumberInput label { color: #94a3b8 !important; }

/* ── Top Header ── */
.qol-header { background:linear-gradient(135deg,#450a0a 0%,#881337 50%,#450a0a 100%);
    border-bottom:1px solid rgba(251,113,133,0.2);
    padding:12px 24px; display:flex; align-items:center; justify-content:space-between;
    margin:-1rem -1rem 0 -1rem; }
.qol-header-brand { display:flex; align-items:center; gap:10px; }
.qol-header-icon  { font-size:1.5rem; color:#fff; line-height:1; }
.qol-header-texts { display:flex; flex-direction:column; gap:1px; }
.qol-header-title { font-size:1.05rem; font-weight:900; color:#ffffff; line-height:1.2; }
.qol-header-sub   { font-size:0.66rem; color:rgba(255,255,255,0.45); }
.qol-header-badge { background:transparent; border:1px solid rgba(255,255,255,0.35);
    color:#ffffff; padding:4px 14px; border-radius:20px; font-size:0.72rem; font-weight:600; }

/* ── Trial bar ── */
.qol-trial { background:rgba(0,0,0,0.3); border-bottom:1px solid rgba(255,255,255,0.05);
    padding:5px 24px; text-align:right; font-size:0.68rem; color:#475569;
    margin:0 -1rem; }
.qol-trial span { color:#f59e0b; font-weight:700; }

/* ── Top Navigation — stylé via JS (voir injection _components.html) ── */
#qol-nav-marker { display: none; }

/* ── Aligner les colonnes en haut (fix décalage Streamlit) ── */
[data-testid="stHorizontalBlock"] { align-items: flex-start !important; }

/* ── Expander badge styling ── */
details summary p { display:flex; align-items:center; gap:8px; }
div[data-testid="metric-container"] {
    background: #1e293b; border-radius: 12px; padding: 16px;
    border: 1px solid #334155;
}
.card {
    background: #1e293b; border-radius: 12px; padding: 20px;
    border: 1px solid #334155; margin-bottom: 16px;
}
.alert-danger { background: #450a0a; border-left: 4px solid #ef4444;
    padding: 12px 16px; border-radius: 8px; margin: 8px 0; color: #fca5a5 !important; }
.alert-warning { background: #451a03; border-left: 4px solid #f59e0b;
    padding: 12px 16px; border-radius: 8px; margin: 8px 0; color: #fcd34d !important; }
.alert-success { background: #052e16; border-left: 4px solid #10b981;
    padding: 12px 16px; border-radius: 8px; margin: 8px 0; color: #6ee7b7 !important; }
.badge-liste { background:#ef4444; color:white; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:bold; }
.badge-lvad  { background:#f59e0b; color:white; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:bold; }
.badge-greffe{ background:#10b981; color:white; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:bold; }
.patient-row { background:#1e293b; border-radius:10px; padding:12px 16px;
    border:1px solid #334155; margin-bottom:8px; }

/* ── Dashboard hdb-* (matching HTML landing page) ── */
.hdb-kpis { display:grid; grid-template-columns:repeat(4,1fr);
    border:1px solid rgba(255,255,255,0.06); background:rgba(0,0,0,0.25);
    border-radius:14px; overflow:hidden; margin-bottom:18px; }
.hdb-kpi { padding:16px 8px; text-align:center; border-right:1px solid rgba(255,255,255,0.05); }
.hdb-kpi:last-child { border-right:none; }
.hdb-kv { font-size:2rem; font-weight:900; line-height:1; margin-bottom:4px; }
.hdb-kl { font-size:0.62rem; text-transform:uppercase; letter-spacing:0.06em; color:#475569; }
.hdb-kpi-hi .hdb-kv { color:#f87171; }
.hdb-kpi-mo .hdb-kv { color:#fb923c; }
.hdb-kpi-lo .hdb-kv { color:#4ade80; }
.hdb-kpi-t  .hdb-kv { color:#fb7185; }
.hdb-sec-title { font-size:0.67rem; font-weight:800; text-transform:uppercase;
    letter-spacing:0.09em; color:#fb7185; margin-bottom:10px;
    display:flex; align-items:center; gap:7px; }
.hdb-qrow { display:grid; grid-template-columns:120px 1fr 60px auto;
    align-items:center; gap:8px; padding:8px 14px;
    border-radius:8px; margin-bottom:4px; }
.hdb-qrow-hi { background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.16); }
.hdb-qrow-mo { background:rgba(249,115,22,0.05); border:1px solid rgba(249,115,22,0.14); }
.hdb-qrow-lo { background:rgba(16,185,129,0.04); border:1px solid rgba(16,185,129,0.12); }
.hdb-qname  { font-weight:700; color:#e2e8f0; font-size:0.76rem; }
.hdb-qval   { color:#64748b; font-size:0.64rem; }
.hdb-qscore { font-weight:700; font-size:0.70rem; color:#fb7185; text-align:right; }
.hdb-sbar   { height:6px; border-radius:3px; background:rgba(255,255,255,.07); overflow:hidden; }
.hdb-sfill  { height:100%; border-radius:3px; }
.hdb-badge  { font-size:0.64rem; font-weight:700; padding:3px 8px; border-radius:4px; white-space:nowrap; }
.hdb-badge-r { background:rgba(239,68,68,0.12); color:#f87171; border:1px solid rgba(239,68,68,0.22); }
.hdb-badge-o { background:rgba(249,115,22,0.12); color:#fb923c; border:1px solid rgba(249,115,22,0.22); }
.hdb-badge-g { background:rgba(16,185,129,0.12); color:#4ade80; border:1px solid rgba(16,185,129,0.22); }
.hdb-score { display:flex; align-items:center; gap:14px; margin-top:14px; padding:12px 16px;
    border-radius:10px; }
.hdb-score-icon  { font-size:1.6rem; flex-shrink:0; }
.hdb-score-lbl   { font-size:0.62rem; color:#6b7280; margin-bottom:2px; }
.hdb-score-val   { font-size:1.2rem; font-weight:900; line-height:1; }
.hdb-score-val small { font-size:0.62rem; font-weight:500; color:#475569; }
.hdb-score-stage { font-size:0.63rem; margin-top:3px; font-weight:700; }
.hdb-score-badge { margin-left:auto; font-size:0.63rem; font-weight:800; padding:5px 13px;
    border-radius:20px; letter-spacing:0.08em; flex-shrink:0; }
.hdb-alert    { margin-top:10px; padding:9px 14px; background:rgba(239,68,68,0.07);
    border:1px solid rgba(239,68,68,0.22); border-radius:8px; font-size:0.72rem; color:#f87171; }
.hdb-alert-ok { margin-top:10px; padding:9px 14px; background:rgba(16,185,129,0.07);
    border:1px solid rgba(16,185,129,0.2); border-radius:8px; font-size:0.72rem; color:#4ade80; }

/* ── Timeline stepper ── */
.tl-wrap { display:flex; align-items:center; }
.tl-step { display:flex; flex-direction:column; align-items:center; flex-shrink:0; }
.tl-circle { width:28px; height:28px; border-radius:50%; border:2px solid #334155;
    display:flex; align-items:center; justify-content:center;
    font-size:0.68rem; font-weight:700; color:#475569; background:#1e293b; }
.tl-circle.done { background:#10b981; border-color:#10b981; color:white; }
.tl-label { font-size:0.58rem; color:#475569; margin-top:4px; text-align:center; white-space:nowrap; }
.tl-line { flex:1; height:2px; background:#334155; margin:0 4px; margin-bottom:14px; min-width:16px; }
.tl-line.done { background:#10b981; }

/* ── Score dual-bar card ── */
.sc-card { background:#1e293b; border:1px solid #334155; border-radius:12px; padding:18px; }
.sc-card-title { font-size:0.76rem; font-weight:700; color:#e2e8f0; margin-bottom:2px; }
.sc-card-sub { font-size:0.63rem; color:#475569; margin-bottom:14px; }
.sc-row { display:flex; align-items:center; gap:8px; margin-bottom:10px; }
.sc-name { font-size:0.72rem; font-weight:700; color:#e2e8f0; min-width:86px; flex-shrink:0; }
.sc-bar-outer { flex:1; height:10px; background:rgba(255,255,255,0.06);
    border-radius:5px; position:relative; overflow:hidden; }
.sc-bar-patient { height:100%; border-radius:5px; }
.sc-ref-mark { position:absolute; top:0; width:3px; height:100%;
    background:rgba(255,255,255,0.85); z-index:2; }
.sc-val { font-size:0.68rem; font-weight:700; color:#fb7185;
    min-width:128px; text-align:right; white-space:nowrap; flex-shrink:0; }

/* ── Trajectory table ── */
.traj-table { width:100%; border-collapse:collapse; font-size:0.76rem; }
.traj-table th { padding:8px 12px; text-align:left; color:#94a3b8;
    border-bottom:1px solid #334155; font-weight:600; font-size:0.68rem;
    text-transform:uppercase; letter-spacing:0.04em; }
.traj-table td { padding:9px 12px; border-bottom:1px solid rgba(255,255,255,0.04); color:#cbd5e1; }
.traj-table td.kccq-val { color:#3b82f6; font-weight:700; }
.traj-table td.sf36-val { color:#10b981; font-weight:700; }
.traj-table td.moment-val { color:#94a3b8; font-size:0.72rem; }
.traj-table tr:last-child td { border-bottom:none; }

/* ── Patient header strip ── */
.pat-header { background:#1e293b; border:1px solid #334155; border-radius:10px;
    padding:10px 16px; display:flex; align-items:center; gap:10px; margin-bottom:12px; }

/* ── Report side panels ── */
.rpt-side-panel { background:#1e293b; border:1px solid #334155; border-radius:10px;
    padding:14px 16px; margin-bottom:10px; }
.rpt-side-title { font-size:0.62rem; font-weight:800; text-transform:uppercase;
    letter-spacing:0.08em; color:#fb7185; margin-bottom:10px; }
.rpt-side-row { display:flex; justify-content:space-between; align-items:center;
    padding:5px 0; border-bottom:1px solid rgba(255,255,255,0.04); font-size:0.74rem; }
.rpt-side-key { color:#94a3b8; }
.rpt-side-val { color:#f59e0b; font-weight:700; }

/* ── Report interpretation block ── */
.rpt-interp { background:rgba(59,130,246,0.06); border:1px solid rgba(59,130,246,0.18);
    border-radius:10px; padding:14px 16px; margin-top:10px; }
.rpt-interp-title { font-size:0.68rem; font-weight:800; text-transform:uppercase;
    letter-spacing:0.06em; color:#60a5fa; margin-bottom:8px; }

/* ── Expander badge overlay ── */
.exp-badge-wrap { display:flex; justify-content:flex-end; margin-bottom:-30px;
    position:relative; z-index:10; pointer-events:none; padding-right:44px; }
.exp-badge-rec { background:#064e3b; color:#6ee7b7;
    border:1px solid #10b981; padding:3px 12px;
    border-radius:20px; font-size:0.72rem; font-weight:700; pointer-events:none;
    letter-spacing:0.01em; }
.exp-badge-not { background:#1e293b; color:#64748b;
    border:1px solid #334155; padding:3px 12px;
    border-radius:20px; font-size:0.72rem; pointer-events:none; }

/* ── Remove badge text from expander label ── */
details summary p { font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# AUTHENTIFICATION
# ─────────────────────────────────────────────
USERS = {
    "admin":    "01d1c301414e623552058e3fdd3c0b77df9d591533c39ebb2fa6c3d901ec86ce",  # MedFlow2026!
    "demo":     "43c27b4e263fa191a6a7ec198cd4d5b47d17413c49d77dc533a01720707e3202",  # demo2026
    "poirette": "2e68a3ab6888456228888db5089d0ed9d3698ae3a488975226a7851516049aa4",  # QoLCardiac2026
    "stolpe":   "2e68a3ab6888456228888db5089d0ed9d3698ae3a488975226a7851516049aa4",  # QoLCardiac2026
}

USER_LABELS = {
    "admin":    "Administrateur — MedFlow AI",
    "demo":     "Démo",
    "poirette": "Dr. Laurent Poirette — HLB Hyères",
    "stolpe":   "Dr. Stolpe — La Timone, Marseille",
}

def hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

def show_login():
    st.markdown("""
    <div style='max-width:420px; margin:80px auto 0 auto;'>
      <div style='text-align:center; margin-bottom:32px;'>
        <div style='font-size:48px;'>🫀</div>
        <h1 style='color:#f1f5f9; font-size:28px; margin:8px 0 4px;'>QoL Cardiac</h1>
        <p style='color:#64748b; font-size:14px; margin:0;'>MedFlow AI — Accès sécurisé</p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Identifiant", placeholder="ex: poirette")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Connexion", use_container_width=True)

            if submitted:
                if username in USERS and USERS[username] == hash_pwd(password):
                    st.session_state.authenticated = True
                    st.session_state.current_user = username
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")

        st.markdown("""
        <p style='text-align:center; color:#475569; font-size:12px; margin-top:24px;'>
        Accès réservé aux professionnels de santé autorisés<br>
        Données patients — Conformité RGPD
        </p>
        """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# RÉFÉRENCES MÉTA-ANALYSE (600 patients)
# ─────────────────────────────────────────────
REF = {
    "Liste d'attente": {
        "kccq": (40.1, 15.4), "sf36_pcs": (30.4, 9.9),
        "sf36_mcs": (41.5, 11.4), "minnesota": (53.6, 17.8),
        "eq5d": (0.54, 0.18), "6mwt": (284, 85),
        "bnp": (824, 387), "lvef": (24, 8),
        "color": "#ef4444", "badge": "badge-liste"
    },
    "LVAD": {
        "kccq": (53.5, 19.8), "sf36_pcs": (37.4, 10.6),
        "sf36_mcs": (42.7, 13.5), "minnesota": (37.6, 21.8),
        "eq5d": (0.68, 0.21), "6mwt": (332, 87),
        "bnp": (474, 276), "lvef": (30, 10),
        "color": "#f59e0b", "badge": "badge-lvad"
    },
    "Post-greffe": {
        "kccq": (66.7, 16.6), "sf36_pcs": (43.4, 11.2),
        "sf36_mcs": (50.6, 10.8), "minnesota": (22.0, 15.1),
        "eq5d": (0.80, 0.13), "6mwt": (462, 104),
        "bnp": (196, 113), "lvef": (58, 8),
        "color": "#10b981", "badge": "badge-greffe"
    }
}

OUTILS_RECOMMANDES = {
    "Liste d'attente": ["Minnesota LHFQ", "KCCQ"],
    "LVAD":            ["KCCQ", "SF-36 PCS"],
    "Post-greffe":     ["SF-36", "KCCQ", "EQ-5D"],
}

# ─────────────────────────────────────────────
# GÉNÉRATION PDF
# ─────────────────────────────────────────────
def _gen_pdf_report(p, last, evals, statut, ref, pid,
                    kccq, pcs, mcs, minn, eq, bnp_v, mwt_v, lvef_v, nyha_v,
                    pct_kccq, pct_pcs, pct_mcs, rpt_sf36, rpt_minn, rpt_eq5d):
    from reportlab.pdfgen import canvas as _c
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.utils import simpleSplit

    buf = io.BytesIO()
    _W, _H = A4
    cv = _c.Canvas(buf, pagesize=A4)

    def mm(v): return v * 2.8346
    ML = mm(18); MR = _W - mm(18); PW = MR - ML

    C = {
        'red':    HexColor('#ef4444'), 'blue':   HexColor('#3b82f6'),
        'green':  HexColor('#10b981'), 'orange': HexColor('#f59e0b'),
        'purple': HexColor('#8b5cf6'), 'navy':   HexColor('#0f172a'),
        'card':   HexColor('#f1f5f9'), 'border': HexColor('#cbd5e1'),
        'dark':   HexColor('#1e293b'), 'mid':    HexColor('#475569'),
        'light':  HexColor('#94a3b8'), 'white':  white,
    }
    STAT_C = {"Liste d'attente": C['red'], "LVAD": C['orange'], "Post-greffe": C['green']}[statut]

    def fy(top): return _H - top

    def rct(x, top, w, h, fill=None, stroke=None, r=3):
        cv.setLineWidth(0.5)
        if fill:   cv.setFillColor(fill)
        if stroke: cv.setStrokeColor(stroke)
        cv.roundRect(x, fy(top + h), w, h, r, fill=bool(fill), stroke=bool(stroke))

    def txt(s, x, top, size=8, color=None, bold=False, align='left'):
        if color: cv.setFillColor(color)
        cv.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
        rl = fy(top)
        if align == 'center': cv.drawCentredString(x, rl, str(s))
        elif align == 'right': cv.drawRightString(x, rl, str(s))
        else: cv.drawString(x, rl, str(s))

    def hln(top, x1=None, x2=None, col=None, lw=0.5):
        cv.setStrokeColor(col or C['border']); cv.setLineWidth(lw)
        cv.line(x1 or ML, fy(top), x2 or MR, fy(top))

    def pc(v): return C['green'] if v >= 66 else (C['orange'] if v >= 33 else C['red'])

    pct_minn = int(stats.norm.cdf(minn, *ref["minnesota"]) * 100)
    pct_minn = 100 - pct_minn
    pct_eq   = int(stats.norm.cdf(eq,   *ref["eq5d"])      * 100)

    kccq_interp = ("significativement altérée" if pct_kccq < 25 else
                   "altérée" if pct_kccq < 50 else
                   "proche de la norme" if pct_kccq < 75 else "bonne")
    _mc = last.get('moment', '').split('—')[0].strip()
    _next_map = {'T0': "Dans 6 mois (T3 — Suivi semestriel)",
                 'T1': "À 3 mois post-LVAD (T2)",
                 'T2': "Dans 6 mois (T3 — Suivi semestriel)",
                 'T3': "Dans 6 mois (T3 — Suivi semestriel)",
                 'T4': "À 1 an post-greffe (T5)",
                 'T5': "Bilan annuel de suivi"}
    next_eval = _next_map.get(_mc,
                 "Dans 6 mois (T3 — Suivi semestriel)" if statut == "Liste d'attente" else
                 "À 1 an post-greffe (T5)" if statut == "Post-greffe" else
                 "À 3 mois post-LVAD (T2)")
    delta_str = ""
    if len(evals) >= 2:
        prev = evals[-2].get("kccq")
        if prev is not None:
            d = kccq - prev
            evol = "stable" if abs(d) < 5 else ("en amélioration" if d > 0 else "en dégradation")
            delta_str = f"QdV {evol} vs évaluation précédente (Δ KCCQ : {d:+.0f} pts)."

    now_str = datetime.now().strftime("%-d %B %Y à %H:%M")
    cur = 0

    # ── 1. HEADER ───────────────────────────────────────────────
    hh = mm(22)
    rct(0, cur, _W, hh, fill=C['navy'], r=0)
    cv.setFillColor(C['red']);  cv.setFont('Helvetica-Bold', 13)
    cv.drawString(ML, fy(cur + mm(10)), "MedFlow")
    cv.setFillColor(C['white']); cv.setFont('Helvetica-Bold', 13)
    cv.drawString(ML + mm(27), fy(cur + mm(10)), "AI")
    txt("QoL Cardiac — Rapport d'évaluation de la qualité de vie",
        ML, cur + mm(16), size=7, color=C['light'])
    bw = mm(38); bx = MR - bw
    rct(bx, cur + mm(3), bw, mm(9), fill=STAT_C, r=4)
    txt(statut, bx + bw/2, cur + mm(9), size=7.5, bold=True, color=C['white'], align='center')
    txt(last.get('moment','—'), MR, cur + mm(15), size=7, color=C['light'], align='right')
    txt(now_str, MR, cur + mm(20), size=6.5, color=HexColor('#64748b'), align='right')
    cur += hh + mm(5)

    # ── 2. PATIENT KPI ROW ──────────────────────────────────────
    kh = mm(18)
    rct(ML, cur, PW, kh, fill=C['card'], stroke=C['border'], r=5)
    txt("Patient", ML + mm(4), cur + mm(6), size=9, bold=True, color=C['dark'])
    txt(f"{p.get('age','—')} ans · {p.get('sexe','—')}",
        ML + mm(4), cur + mm(11.5), size=7, color=C['mid'])
    kpis = [(str(kccq),"KCCQ/100",C['blue']),(f"{mwt_v} m","6MWT",C['green']),
            (str(nyha_v),"NYHA",C['orange']),(f"{lvef_v}%","LVEF",C['orange']),
            (str(bnp_v),"BNP pg/mL",C['orange'])]
    pw_ = mm(21.5); px_ = ML + mm(37)
    for vs,ls,cs in kpis:
        rct(px_, cur+mm(2), pw_, mm(14), fill=HexColor('#e8efff'), stroke=C['border'], r=4)
        txt(vs, px_+pw_/2, cur+mm(8), size=10, bold=True, color=cs, align='center')
        txt(ls, px_+pw_/2, cur+mm(13.5), size=6, color=C['light'], align='center')
        px_ += pw_ + mm(2)
    cur += kh + mm(4)

    # ── 3. SECTION TITLE ────────────────────────────────────────
    rct(ML, cur, PW, mm(7), fill=HexColor('#eff6ff'), stroke=HexColor('#bfdbfe'), r=4)
    txt(f"SCORES DE QUALITÉ DE VIE vs COHORTE DE RÉFÉRENCE ({statut.upper()})",
        ML+mm(5), cur+mm(4.8), size=7, bold=True, color=C['blue'])
    cur += mm(7) + mm(3)

    # ── 4. SCORES (60%) + SIDE PANEL (38%) ──────────────────────
    sw = PW*0.60 - mm(4); sdw = PW*0.39; sdx = MR - sdw
    sc_top = cur

    def draw_bar(top, name, val, max_v, ref_m, pct_v, val_str, bar_c):
        bh = mm(20)
        rct(ML, top, sw, bh, fill=C['card'], stroke=C['border'], r=5)
        txt(name, ML+mm(4), top+mm(5.5), size=8.5, bold=True, color=C['dark'])
        txt(val_str, ML+sw-mm(35), top+mm(5.5), size=8.5, bold=True, color=C['dark'])
        txt(f"{pct_v}e pct.", ML+sw-mm(4), top+mm(5.5), size=7.5, bold=True, color=pc(pct_v), align='right')
        bx0=ML+mm(4); bar_w=sw-mm(10); bar_top=top+mm(10)
        rct(bx0, bar_top, bar_w, mm(5), fill=HexColor('#e2e8f0'), r=2)
        fw = min(val/max_v,1.0)*bar_w if max_v else 0
        if fw > 0: rct(bx0, bar_top, fw, mm(5), fill=bar_c, r=2)
        rx = bx0 + min(ref_m/max_v,1.0)*bar_w if max_v else bx0
        cv.setStrokeColor(HexColor('#64748b')); cv.setLineWidth(1.5)
        cv.line(rx, fy(bar_top - mm(1.5)), rx, fy(bar_top + mm(5)))
        txt(f"Réf. cohorte : {ref_m:.1f}", bx0, top+mm(18), size=6, color=C['light'])
        return bh + mm(2)

    s_list = [("KCCQ",kccq,100,ref["kccq"][0],pct_kccq,f"{kccq}/100",C['blue'])]
    if rpt_sf36:
        s_list += [("SF-36 PCS",pcs,100,ref["sf36_pcs"][0],pct_pcs,f"{pcs}/100",C['green']),
                   ("SF-36 MCS",mcs,100,ref["sf36_mcs"][0],pct_mcs,f"{mcs}/100",C['purple'])]
    if rpt_minn:
        s_list.append(("Minnesota",minn,105,ref["minnesota"][0],pct_minn,f"{minn}/105",C['orange']))
    if rpt_eq5d:
        s_list.append(("EQ-5D",eq,1,ref["eq5d"][0],pct_eq,f"{eq:.2f}/1",C['green']))

    sc = cur
    for args in s_list: sc += draw_bar(sc, *args)

    # Side panel — clinical params
    pc_ = cur
    cph = mm(28)
    rct(sdx, pc_, sdw, cph, fill=C['card'], stroke=C['border'], r=5)
    txt("PARAMÈTRES CLINIQUES", sdx+mm(4), pc_+mm(5.5), size=6.5, bold=True, color=C['dark'])
    nyha_c = C['green'] if nyha_v in ["I","II"] else (C['orange'] if nyha_v=="III" else C['red'])
    RV = MR - mm(4)   # right-align x with inner padding
    for i,(k,v,col) in enumerate([("6MWT",f"{mwt_v} m",C['green']),("BNP",f"{bnp_v} pg/mL",C['orange']),
                                   ("LVEF",f"{lvef_v}%",C['orange']),("NYHA",str(nyha_v),nyha_c)]):
        ry = pc_+mm(9.5)+i*mm(4.5)
        txt(k, sdx+mm(4), ry, size=7.5, color=C['mid'])
        txt(v, RV, ry, size=7.5, bold=True, color=col, align='right')
    pc_ += cph + mm(3)

    # Side panel — meta-analysis refs
    rfh = mm(37)
    rct(sdx, pc_, sdw, rfh, fill=C['card'], stroke=C['border'], r=5)
    txt("REFERENCES META-ANALYSE", sdx+mm(4), pc_+mm(5.5), size=6.5, bold=True, color=C['dark'])
    ref_rows = [("KCCQ",f"{ref['kccq'][0]:.1f} +/- {ref['kccq'][1]:.1f}"),
                ("SF-36 PCS",f"{ref['sf36_pcs'][0]:.1f} +/- {ref['sf36_pcs'][1]:.1f}"),
                ("SF-36 MCS",f"{ref['sf36_mcs'][0]:.1f} +/- {ref['sf36_mcs'][1]:.1f}"),
                ("Minnesota",f"{ref['minnesota'][0]:.1f} +/- {ref['minnesota'][1]:.1f}"),
                ("EQ-5D",f"{ref['eq5d'][0]:.2f} +/- {ref['eq5d'][1]:.2f}"),
                ("6MWT",f"{ref['6mwt'][0]:.0f} +/- {ref['6mwt'][1]:.0f} m"),
                ("BNP",f"{ref['bnp'][0]:.0f} +/- {ref['bnp'][1]:.0f}")]
    for i,(k,v) in enumerate(ref_rows):
        ry = pc_+mm(9.5)+i*mm(3.7)
        txt(k, sdx+mm(4), ry, size=7, color=C['mid'])
        txt(v, RV, ry, size=6.5, color=C['light'], align='right')
    txt("15 etudes · 600 patients · 2000-2026",
        sdx+mm(4), pc_+rfh-mm(3), size=5.5, color=C['light'])
    cur = max(sc, pc_+rfh) + mm(5)

    # ── 5. TRAJECTOIRE LONGITUDINALE ────────────────────────────
    traj_rh = mm(6)
    # traj_h: titre(6) + stepper(13+8.5=21.5) + gap(4.5) + header(6) + rows + padding(4)
    traj_h = mm(42) + len(evals) * traj_rh
    rct(ML, cur, PW, traj_h, fill=C['card'], stroke=C['border'], r=7)
    txt(f"TRAJECTOIRE LONGITUDINALE  —  {len(evals)} évaluation(s)",
        ML+mm(5), cur+mm(6), size=8, bold=True, color=C['dark'])

    eval_ts = set()
    for ev in evals:
        m_ = ev.get("moment","")
        if m_[:2] in ["T0","T1","T2","T3","T4","T5"]: eval_ts.add(m_[:2])

    T_S = [("T0","Inscr."),("T1","Pré-LVAD"),("T2","3m LVAD"),
           ("T3","Suivi 6m"),("T4","3m gref."),("T5","1an gref.")]
    st_w = PW/6; s_y = cur+mm(13); cr = mm(3)
    for i,(tk,tlbl) in enumerate(T_S):
        cx = ML+st_w*i+st_w/2; done = tk in eval_ts
        if i < 5:
            cv.setStrokeColor(C['green'] if done else C['border']); cv.setLineWidth(1.5)
            cv.line(cx+cr, fy(s_y), cx+st_w-cr, fy(s_y))
        cv.setFillColor(C['green'] if done else HexColor('#e2e8f0'))
        cv.setStrokeColor(C['green'] if done else C['border']); cv.setLineWidth(1)
        cv.circle(cx, fy(s_y), cr, fill=1, stroke=1)
        cv.setFillColor(C['white'] if done else C['light'])
        cv.setFont('Helvetica-Bold', 5)
        cv.drawCentredString(cx, fy(s_y)-2, "v" if done else str(i))
        txt(tk, cx, s_y+mm(5), size=6, bold=done, color=C['dark'] if done else C['light'], align='center')
        txt(tlbl, cx, s_y+mm(8.5), size=5.5, color=C['light'], align='center')

    # Table header starts below the deepest stepper label (cur+mm(21.5)) + gap
    t_y = cur + mm(27)
    col_x = [ML+mm(4),ML+mm(42),ML+mm(79),ML+mm(112),ML+mm(137)]
    for h_,cx_,hc_ in zip(["MOMENT","KCCQ","SF-36 PCS","NYHA","6MWT"],col_x,
                           [C['dark'],C['blue'],C['green'],C['dark'],C['dark']]):
        txt(h_, cx_, t_y, size=7, bold=True, color=hc_)
    hln(t_y+mm(2), x1=ML+mm(2), x2=MR-mm(2))
    for i,ev in enumerate(evals):
        ry = t_y+mm(6)+i*traj_rh
        ms = ev.get("moment","—").split("—")[0].strip()
        row_v = [ms, str(ev.get("kccq","—") or "—"), str(ev.get("sf36_pcs","—") or "—"),
                 ev.get("nyha","—"), f"{ev.get('6mwt','—')} m"]
        row_c = [C['dark'],C['blue'],C['green'],C['dark'],C['dark']]
        for v_,cx_,vc_ in zip(row_v,col_x,row_c):
            txt(v_, cx_, ry, size=7.5, bold=(vc_ in [C['blue'],C['green']]), color=vc_)
        if i < len(evals)-1: hln(ry+mm(3), x1=ML+mm(2), x2=MR-mm(2), lw=0.3)
    cur += traj_h + mm(4)

    # ── 6. INTERPRÉTATION CLINIQUE (dark card — style app) ───────
    interp = (
        f"Patient ({p.get('age','—')} ans, {p.get('sexe','—')}), en {statut}, "
        f"présente une qualité de vie {kccq_interp} (score composite {pct_kccq}e pct.). "
        f"KCCQ : {kccq}/100 — {pct_kccq}e pct. (ref. {ref['kccq'][0]:.1f}/100). "
        f"SF-36 PCS : {pcs}/100 ({pct_pcs}e pct.)  MCS : {mcs}/100 ({pct_mcs}e pct.)."
        f"{(' ' + delta_str) if delta_str else ''} "
        f"Prochaine evaluation recommandee : {next_eval}."
    )
    lines = simpleSplit(interp, 'Helvetica', 7.5, PW - mm(16))
    ih = mm(13) + len(lines)*mm(4.5) + mm(10)
    rct(ML, cur, PW, ih, fill=HexColor('#1e293b'), stroke=HexColor('#334155'), r=7)
    # Colored left accent bar
    rct(ML, cur, mm(3), ih, fill=HexColor('#fb923c'), r=2)
    txt("INTERPRETATION CLINIQUE", ML+mm(6), cur+mm(6.5), size=8, bold=True, color=HexColor('#fb923c'))
    cv.setFillColor(HexColor('#e2e8f0')); cv.setFont('Helvetica', 7.5)
    for i,l in enumerate(lines):
        cv.drawString(ML+mm(6), fy(cur+mm(12)+i*mm(4.5)), l)
    txt("Outil d'aide clinique — Ne remplace pas l'avis medical. Meta-analyse 15 etudes, 600 patients.",
        ML+mm(6), cur+ih-mm(4), size=6, color=HexColor('#64748b'))
    cur += ih + mm(4)

    # ── 7. FOOTER ────────────────────────────────────────────────
    hln(cur)
    txt("Clinicien : Dr. _______________", ML, cur+mm(5.5), size=7.5, color=C['mid'])
    txt("medflow-ai.fr/qol-cardiac", MR, cur+mm(5.5), size=7.5, color=C['mid'], align='right')

    cv.save(); buf.seek(0)
    return buf.getvalue()


# ─────────────────────────────────────────────
# SQLITE — BASE DE DONNÉES LOCALE
# ─────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "qol_cardiac.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS patients (
        id TEXT PRIMARY KEY,
        prenom TEXT DEFAULT '',
        nom TEXT DEFAULT '',
        age INTEGER,
        sexe TEXT,
        statut TEXT,
        created_at TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id TEXT,
        date TEXT,
        moment TEXT,
        statut TEXT,
        kccq REAL, sf36_pcs REAL, sf36_mcs REAL,
        minnesota REAL, eq5d REAL,
        nyha TEXT, mwt6 INTEGER, bnp INTEGER, lvef INTEGER,
        FOREIGN KEY (patient_id) REFERENCES patients(id)
    )''')
    conn.commit()
    # Patients démo si DB vide (Streamlit Cloud ou premier lancement)
    c.execute("SELECT COUNT(*) FROM patients")
    if c.fetchone()[0] == 0:
        from datetime import datetime
        now = datetime.now().isoformat()
        demo_patients = [
            ("DEMO-001", "Paul",   "Martin", 58, "Homme",  "Liste d'attente", now),
            ("DEMO-002", "Michel", "Dubois", 60, "Homme",  "LVAD",            now),
            ("DEMO-003", "Marie",  "Leroy",  54, "Femme",  "Post-greffe",     now),
        ]
        c.executemany("INSERT INTO patients VALUES (?,?,?,?,?,?,?)", demo_patients)
        demo_evals = [
            ("DEMO-001", "2026-01-10", "T0 — Inscription sur liste",      "Liste d'attente", 49,  32, 40,  52, 0.55, "III", 280, 850, 22),
            ("DEMO-002", "2026-02-15", "T1 — Avant implantation LVAD",    "LVAD",            52,  38, 42,  38, 0.67, "II",  320, 490, 28),
            ("DEMO-002", "2026-05-20", "T2 — 3 mois post-LVAD",           "LVAD",            61,  42, 45,  30, 0.72, "II",  365, 380, 32),
            ("DEMO-003", "2025-12-05", "T0 — Inscription sur liste",      "Post-greffe",     38,  28, 38,  58, 0.50, "III", 260, 920, 20),
            ("DEMO-003", "2026-03-10", "T4 — 3 mois post-greffe",         "Post-greffe",     65,  42, 50,  23, 0.79, "I",   450, 200, 57),
        ]
        c.executemany(
            "INSERT INTO evaluations (patient_id,date,moment,statut,kccq,sf36_pcs,sf36_mcs,minnesota,eq5d,nyha,mwt6,bnp,lvef) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            demo_evals
        )
        conn.commit()
    conn.close()

init_db()

def generate_patient_id(prenom, nom, age):
    """Pseudonymisation automatique — ID anonyme irréversible."""
    raw = f"{prenom.strip().lower()}{nom.strip().lower()}{age}"
    return "PT-" + hashlib.sha256(raw.encode()).hexdigest()[:8].upper()

def db_save_patient(p):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT OR REPLACE INTO patients
                 (id, prenom, nom, age, sexe, statut, created_at)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
              (p['id'], p.get('prenom',''), p.get('nom',''),
               p['age'], p['sexe'], p['statut'],
               p.get('created_at', datetime.now().isoformat())))
    conn.commit()
    conn.close()

def db_save_evaluation(patient_id, ev):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''INSERT INTO evaluations
                 (patient_id, date, moment, statut, kccq, sf36_pcs, sf36_mcs,
                  minnesota, eq5d, nyha, mwt6, bnp, lvef)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
              (patient_id, ev['date'], ev['moment'], ev['statut'],
               ev.get('kccq'), ev.get('sf36_pcs'), ev.get('sf36_mcs'),
               ev.get('minnesota'), ev.get('eq5d'), ev.get('nyha'),
               ev.get('6mwt'), ev.get('bnp'), ev.get('lvef')))
    conn.commit()
    conn.close()

def db_load_evaluations(patient_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT date, moment, statut, kccq, sf36_pcs, sf36_mcs,
                        minnesota, eq5d, nyha, mwt6, bnp, lvef
                 FROM evaluations WHERE patient_id=? ORDER BY date''', (patient_id,))
    rows = c.fetchall()
    conn.close()
    cols = ['date','moment','statut','kccq','sf36_pcs','sf36_mcs',
            'minnesota','eq5d','nyha','6mwt','bnp','lvef']
    return [dict(zip(cols, row)) for row in rows]

def db_list_patients():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''SELECT id, prenom, nom, age, sexe, statut, created_at
                 FROM patients ORDER BY created_at DESC''')
    rows = c.fetchall()
    conn.close()
    return [{'id':r[0],'prenom':r[1],'nom':r[2],'age':r[3],
             'sexe':r[4],'statut':r[5],'created_at':r[6]} for r in rows]

def db_search_patients(query):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    q = f"%{query.lower()}%"
    c.execute('''SELECT id, prenom, nom, age, sexe, statut FROM patients
                 WHERE lower(nom) LIKE ? OR lower(prenom) LIKE ? OR lower(id) LIKE ?
                 ORDER BY created_at DESC LIMIT 10''', (q, q, q))
    rows = c.fetchall()
    conn.close()
    return [{'id':r[0],'prenom':r[1],'nom':r[2],'age':r[3],
             'sexe':r[4],'statut':r[5]} for r in rows]

def db_delete_patient(patient_id):
    """Droit à l'effacement — Art. 17 RGPD."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM evaluations WHERE patient_id=?', (patient_id,))
    c.execute('DELETE FROM patients WHERE id=?', (patient_id,))
    conn.commit()
    conn.close()

def db_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM patients')
    np_ = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM evaluations')
    ne_ = c.fetchone()[0]
    conn.close()
    return np_, ne_

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

if not st.session_state.authenticated:
    show_login()
    st.stop()

if "evaluations" not in st.session_state:
    st.session_state.evaluations = []
if "patient" not in st.session_state:
    st.session_state.patient = {}
if "patient_id" not in st.session_state:
    st.session_state.patient_id = None
if "page" not in st.session_state:
    st.session_state.page = "accueil"

# ─────────────────────────────────────────────
# DONNÉES DÉMO
# ─────────────────────────────────────────────
DEMO_PATIENTS = {
    "Liste d'attente": {
        "patient": {
            "prenom": "Jean", "nom": "Dupont", "age": 58, "sexe": "Homme",
            "statut": "Liste d'attente", "moment": "T0 — Inscription sur liste",
            "date": "2026-01-15", "nyha": "III", "nyha_idx": 2,
            "6mwt": 265, "bnp": 890, "lvef": 22
        },
        "evaluations": [
            {"date": "2026-01-15", "moment": "T0 — Inscription sur liste",
             "statut": "Liste d'attente",
             "kccq": 36, "sf36_pcs": 28, "sf36_mcs": 39, "minnesota": 58, "eq5d": 0.49,
             "nyha": "III", "6mwt": 265, "bnp": 890, "lvef": 22},
        ]
    },
    "LVAD": {
        "patient": {
            "prenom": "Michel", "nom": "Bernard", "age": 62, "sexe": "Homme",
            "statut": "LVAD", "moment": "T2 — 3 mois post-LVAD",
            "date": "2026-03-10", "nyha": "II", "nyha_idx": 1,
            "6mwt": 340, "bnp": 420, "lvef": 28
        },
        "evaluations": [
            {"date": "2025-11-20", "moment": "T0 — Inscription sur liste",
             "statut": "LVAD",
             "kccq": 34, "sf36_pcs": 26, "sf36_mcs": 38, "minnesota": 62, "eq5d": 0.45,
             "nyha": "III", "6mwt": 240, "bnp": 950, "lvef": 20},
            {"date": "2025-12-15", "moment": "T1 — Avant implantation LVAD",
             "statut": "LVAD",
             "kccq": 32, "sf36_pcs": 25, "sf36_mcs": 36, "minnesota": 65, "eq5d": 0.43,
             "nyha": "IV", "6mwt": 210, "bnp": 1100, "lvef": 18},
            {"date": "2026-03-10", "moment": "T2 — 3 mois post-LVAD",
             "statut": "LVAD",
             "kccq": 54, "sf36_pcs": 38, "sf36_mcs": 44, "minnesota": 38, "eq5d": 0.69,
             "nyha": "II", "6mwt": 340, "bnp": 420, "lvef": 28},
        ]
    },
    "Post-greffe": {
        "patient": {
            "prenom": "Marie", "nom": "Leroy", "age": 54, "sexe": "Femme",
            "statut": "Post-greffe", "moment": "T5 — 1 an post-greffe",
            "date": "2026-04-01", "nyha": "I", "nyha_idx": 0,
            "6mwt": 490, "bnp": 165, "lvef": 62
        },
        "evaluations": [
            {"date": "2024-12-10", "moment": "T0 — Inscription sur liste",
             "statut": "Post-greffe",
             "kccq": 38, "sf36_pcs": 29, "sf36_mcs": 40, "minnesota": 56, "eq5d": 0.51,
             "nyha": "III", "6mwt": 270, "bnp": 810, "lvef": 23},
            {"date": "2025-04-05", "moment": "T4 — 3 mois post-greffe",
             "statut": "Post-greffe",
             "kccq": 58, "sf36_pcs": 40, "sf36_mcs": 47, "minnesota": 28, "eq5d": 0.74,
             "nyha": "II", "6mwt": 410, "bnp": 220, "lvef": 56},
            {"date": "2026-04-01", "moment": "T5 — 1 an post-greffe",
             "statut": "Post-greffe",
             "kccq": 68, "sf36_pcs": 45, "sf36_mcs": 52, "minnesota": 20, "eq5d": 0.82,
             "nyha": "I", "6mwt": 490, "bnp": 165, "lvef": 62},
        ]
    }
}

# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# HEADER + TOP NAVIGATION
# ─────────────────────────────────────────────
user_label = USER_LABELS.get(st.session_state.current_user, st.session_state.current_user)
np_, ne_ = db_count()

# ── Header ──
_trial_days = max(0, 90 - (datetime.now() - datetime(2026, 4, 1)).days)
st.markdown(f"""
<div class="qol-header">
  <div class="qol-header-brand">
    <span class="qol-header-icon">♡</span>
    <div class="qol-header-texts">
      <span class="qol-header-title">QoL Cardiac</span>
      <span class="qol-header-sub">Qualité de vie cardiaque · 4 questionnaires · 600 patients</span>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:10px;">
    <span style="color:rgba(255,255,255,0.4);font-size:0.68rem;">{user_label}</span>
    <span class="qol-header-badge">Gratuit</span>
  </div>
</div>
<div class="qol-trial">Accès gratuit · <span>{_trial_days} jours</span> restants (sur 90) · {ne_} évaluation(s) · 🔒 100% local</div>
""", unsafe_allow_html=True)

# ── Navigation (boutons Streamlit — session préservée) ──
_pg = st.session_state.page
nav_items = [
    ("🏠 Accueil",         "accueil"),
    ("👤 Patient",          "patient"),
    ("🗂️ Patients",        "patients"),
    ("📋 Questionnaires",  "questionnaires"),
    ("📊 Tableau de bord", "dashboard"),
    ("📄 Rapport",         "rapport"),
    ("🔬 Recherche",       "recherche"),
    ("📚 Références",      "references"),
]

st.markdown('<div id="qol-nav-marker" style="display:none"></div>', unsafe_allow_html=True)
_nav_cols = st.columns([0.85,0.85,0.95,1.25,1.4,0.85,1.05,1.15,0.6])
for i, (lbl, k) in enumerate(nav_items):
    with _nav_cols[i]:
        _btn_type = "primary" if _pg == k else "secondary"
        if st.button(lbl, key=f"nav_{k}", use_container_width=True, type=_btn_type):
            st.session_state.page = k
            st.session_state.pop("_prev_page", None)
            st.rerun()
with _nav_cols[-1]:
    if st.button("⏻ Déco", key="nav_logout", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()

# JS injection — style les boutons comme des onglets plats (même session, sans navigation)
_components.html("""
<script>
(function() {
  function styleNav() {
    var doc = window.parent.document;
    // trouver le bloc horizontal avec >=7 boutons (la nav)
    var navBlock = null;
    doc.querySelectorAll('[data-testid="stHorizontalBlock"]').forEach(function(b) {
      if (b.querySelectorAll('button').length >= 7) navBlock = b;
    });
    if (!navBlock) { setTimeout(styleNav, 100); return; }

    // Conteneur tab-bar
    navBlock.style.cssText =
      'background:rgba(0,0,0,0.15)!important;' +
      'border-bottom:1px solid rgba(255,255,255,0.05)!important;' +
      'padding:8px 18px 0 18px!important;overflow-x:auto!important;' +
      'display:flex!important;align-items:flex-end!important;gap:2px!important;' +
      'scrollbar-width:none!important;margin:0 -1rem!important;';

    // Colonnes — laisser la taille s'adapter au contenu
    navBlock.querySelectorAll('[data-testid="stColumn"]').forEach(function(c) {
      c.style.cssText = 'padding:0!important;flex:0 0 auto!important;min-width:0!important;';
    });

    // Boutons individuels
    navBlock.querySelectorAll('button').forEach(function(btn) {
      var active = btn.getAttribute('kind') === 'primary';
      btn.style.cssText = active
        ? 'background:transparent!important;border:none!important;' +
          'border-bottom:2px solid #fb7185!important;border-radius:0!important;' +
          'color:#fb7185!important;font-size:0.76rem!important;font-weight:700!important;' +
          'padding:6px 13px!important;min-height:auto!important;height:auto!important;' +
          'box-shadow:none!important;white-space:nowrap!important;width:auto!important;'
        : 'background:transparent!important;border:none!important;' +
          'border-radius:6px 6px 0 0!important;color:#475569!important;' +
          'font-size:0.76rem!important;font-weight:600!important;' +
          'padding:6px 13px!important;min-height:auto!important;height:auto!important;' +
          'box-shadow:none!important;white-space:nowrap!important;width:auto!important;';
    });
  }

  styleNav();
  var _t = null;
  new MutationObserver(function() {
    clearTimeout(_t); _t = setTimeout(styleNav, 80);
  }).observe(window.parent.document.body, {childList:true, subtree:true});
})();
</script>
""", height=0)
st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE ACCUEIL
# ─────────────────────────────────────────────
if st.session_state.page == "accueil":
    st.markdown("# 🫀 QoL Cardiac")
    st.markdown("### Plateforme d'évaluation de la qualité de vie chez le patient cardiaque")
    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Populations", "3", "Liste · LVAD · Greffe")
    with col2:
        st.metric("Questionnaires", "4", "SF-36 · KCCQ · Minnesota · EQ-5D")
    with col3:
        st.metric("Moments clés", "6", "T0 → T5")
    with col4:
        st.metric("Études de référence", "15", "600 patients")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
<div class="card">
<h4>📋 Comment utiliser cet outil</h4>
<ol>
<li><b>Nouveau patient</b> — saisissez le profil et le statut clinique</li>
<li><b>Questionnaires</b> — remplissez les outils recommandés pour ce statut</li>
<li><b>Tableau de bord</b> — visualisez les scores, la trajectoire et les alertes</li>
<li><b>Rapport PDF</b> — exportez pour le dossier médical</li>
</ol>
<p style="font-size:12px;color:#64748b;margin-top:8px">
💾 Toutes les données sont sauvegardées automatiquement (SQLite local).
Le patient est retrouvé à la prochaine session.
</p>
</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown("""
<div class="card">
<h4>🎯 Outils recommandés par statut</h4>
<p><span class="badge-liste">Liste d'attente</span> Minnesota LHFQ · KCCQ &nbsp;<span style="color:#475569;font-size:.85em">| SF-36 : Non prioritaire</span></p>
<p><span class="badge-lvad">LVAD</span> KCCQ · SF-36 PCS &nbsp;<span style="color:#475569;font-size:.85em">| EQ-5D : Non prioritaire</span></p>
<p><span class="badge-greffe">Post-greffe</span> SF-36 · KCCQ · EQ-5D &nbsp;<span style="color:#475569;font-size:.85em">| Minnesota LHFQ : Non prioritaire</span></p>
<br>
<p><b>Règle pratique :</b> si 1 seul choix → T0 (baseline)<br>
Si 2 choix → T0 + T5 (1 an post-greffe)</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎬 Mode démo — Charger un patient exemple")
    st.markdown("*Explorez la plateforme avec des données réalistes issues de la méta-analyse*")

    dcol1, dcol2, dcol3 = st.columns(3)

    with dcol1:
        st.markdown("""
<div class="card" style="border-color:#ef4444; min-height:210px;">
<h4>🔴 Liste d'attente</h4>
<p><b>Jean Dupont</b>, 58 ans · NYHA III<br>
BNP 890 pg/mL · 6MWT 265 m · LVEF 22%<br>
<b>1 évaluation — T0 baseline</b></p>
<hr style="border-color:#334155; margin:8px 0">
<p style="font-size:12px; color:#fca5a5;">
⚠ KCCQ 36/100 — 30<sup>e</sup> percentile<br>
Tous les paramètres sous la référence.<br>
Surveillance rapprochée recommandée.
</p>
</div>
""", unsafe_allow_html=True)
        if st.button("Charger démo Liste d'attente", use_container_width=True, key="demo_liste"):
            demo = DEMO_PATIENTS["Liste d'attente"]
            st.session_state.patient = demo["patient"]
            st.session_state.patient_id = None
            st.session_state.evaluations = demo["evaluations"]
            st.session_state.page = "dashboard"
            st.rerun()

    with dcol2:
        st.markdown("""
<div class="card" style="border-color:#f59e0b; min-height:210px;">
<h4>🟡 LVAD</h4>
<p><b>Michel Bernard</b>, 62 ans · NYHA II<br>
BNP 420 pg/mL · 6MWT 340 m · LVEF 28%<br>
<b>3 évaluations — T0 → T1 → T2</b></p>
<hr style="border-color:#334155; margin:8px 0">
<p style="font-size:12px; color:#fcd34d;">
✓ KCCQ : 32 → 54/100 — gain +22 pts<br>
Seuil significativité clinique : +5 pts.<br>
Amélioration nette après implantation LVAD.
</p>
</div>
""", unsafe_allow_html=True)
        if st.button("Charger démo LVAD", use_container_width=True, key="demo_lvad"):
            demo = DEMO_PATIENTS["LVAD"]
            st.session_state.patient = demo["patient"]
            st.session_state.patient_id = None
            st.session_state.evaluations = demo["evaluations"]
            st.session_state.page = "dashboard"
            st.rerun()

    with dcol3:
        st.markdown("""
<div class="card" style="border-color:#10b981; min-height:210px;">
<h4>🟢 Post-greffe</h4>
<p><b>Marie Leroy</b>, 54 ans · NYHA I<br>
BNP 165 pg/mL · 6MWT 490 m · LVEF 62%<br>
<b>3 évaluations — T0 → T4 → T5</b></p>
<hr style="border-color:#334155; margin:8px 0">
<p style="font-size:12px; color:#6ee7b7;">
✓ KCCQ : 38 → 68/100 — gain +30 pts<br>
79<sup>e</sup> percentile · SF-36 PCS : 45/100<br>
Retour quasi-normal à la vie quotidienne.
</p>
</div>
""", unsafe_allow_html=True)
        if st.button("Charger démo Post-greffe", use_container_width=True, key="demo_greffe"):
            demo = DEMO_PATIENTS["Post-greffe"]
            st.session_state.patient = demo["patient"]
            st.session_state.patient_id = None
            st.session_state.evaluations = demo["evaluations"]
            st.session_state.page = "dashboard"
            st.rerun()

    st.markdown("""
<div class="card" style="border-color:#3b82f6; margin-top:16px;">
<h4>💡 Ce que la démo illustre</h4>
<table style="width:100%; border-collapse:collapse; font-size:13px;">
<tr>
<td style="padding:6px 12px; color:#ef4444; font-weight:bold; width:18%;">Liste d'attente</td>
<td style="padding:6px 12px; color:#cbd5e1;">QdV très dégradée, sous le 30e percentile → mesurer dès T0 est indispensable comme baseline</td>
</tr>
<tr style="background:#0f172a;">
<td style="padding:6px 12px; color:#f59e0b; font-weight:bold;">LVAD</td>
<td style="padding:6px 12px; color:#cbd5e1;">Gain +22 pts KCCQ en 4 mois → le LVAD améliore objectivement la QdV, ce n'est pas qu'un pont</td>
</tr>
<tr>
<td style="padding:6px 12px; color:#10b981; font-weight:bold;">Post-greffe</td>
<td style="padding:6px 12px; color:#cbd5e1;">79e percentile à 1 an → la greffe est transformatrice, la QdV rejoint quasi la population générale</td>
</tr>
</table>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤 Nouveau patient", type="primary", use_container_width=True):
            st.session_state.page = "patient"
            st.rerun()
    with col2:
        if st.button("🗂️ Mes patients enregistrés", use_container_width=True):
            st.session_state.page = "patients"
            st.rerun()

# ─────────────────────────────────────────────
# PAGE MES PATIENTS
# ─────────────────────────────────────────────
elif st.session_state.page == "patients":
    st.markdown("# 🗂️ Mes patients")
    st.markdown("---")

    patients = db_list_patients()

    if not patients:
        st.info("Aucun patient enregistré. Créez votre premier patient.")
        if st.button("👤 Nouveau patient", type="primary"):
            st.session_state.page = "patient"
            st.rerun()
        st.stop()

    # Barre de recherche
    search = st.text_input("🔍 Rechercher par nom, prénom ou ID", placeholder="Dupont, Jean, PT-3A7F...")
    if search:
        patients = db_search_patients(search)
        if not patients:
            st.warning("Aucun résultat.")

    st.markdown(f"**{len(patients)} patient(s)**")
    st.markdown("---")

    badge_map = {"Liste d'attente": "🔴", "LVAD": "🟡", "Post-greffe": "🟢"}

    for pat in patients:
        evals = db_load_evaluations(pat['id'])
        nb_evals = len(evals)
        derniere = evals[-1]['date'] if evals else "—"
        dernier_moment = evals[-1]['moment'] if evals else "—"

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            b = badge_map.get(pat['statut'], '⚪')
            nom_display = f"{pat.get('prenom','')} {pat.get('nom','')}".strip() or pat['id']
            st.markdown(f"""
<div class="patient-row">
<b style="color:#f1f5f9">{b} {nom_display}</b>
&nbsp;·&nbsp; <span style="color:#94a3b8">{pat['age']} ans · {pat['sexe']}</span>
&nbsp;·&nbsp; <span style="color:#64748b;font-size:12px">{pat['statut']}</span><br>
<span style="color:#64748b;font-size:12px">
{nb_evals} évaluation(s) · Dernière : {derniere} ({dernier_moment.split('—')[0].strip() if '—' in dernier_moment else dernier_moment})
&nbsp;·&nbsp; ID : <code style="background:#0f172a;padding:1px 4px;border-radius:4px">{pat['id']}</code>
</span>
</div>
""", unsafe_allow_html=True)
        with col2:
            if st.button("📊 Charger", key=f"load_{pat['id']}", use_container_width=True):
                # Charger patient et ses évaluations en session
                st.session_state.patient = {
                    'id': pat['id'],
                    'prenom': pat.get('prenom',''),
                    'nom': pat.get('nom',''),
                    'age': pat['age'],
                    'sexe': pat['sexe'],
                    'statut': pat['statut'],
                    'moment': evals[-1]['moment'] if evals else "T0 — Inscription sur liste",
                    'date': evals[-1]['date'] if evals else str(datetime.today().date()),
                    'nyha': evals[-1].get('nyha','II') if evals else 'II',
                    'nyha_idx': ["I","II","III","IV"].index(evals[-1].get('nyha','II')) if evals else 1,
                    '6mwt': evals[-1].get('6mwt', 300) if evals else 300,
                    'bnp': evals[-1].get('bnp', 500) if evals else 500,
                    'lvef': evals[-1].get('lvef', 30) if evals else 30,
                }
                st.session_state.patient_id = pat['id']
                st.session_state.evaluations = evals
                st.session_state.page = "dashboard"
                st.rerun()
        with col3:
            if st.button("🗑️ Supprimer", key=f"del_{pat['id']}", use_container_width=True):
                st.session_state[f"confirm_del_{pat['id']}"] = True
                st.rerun()

        # Confirmation suppression
        if st.session_state.get(f"confirm_del_{pat['id']}", False):
            st.warning(f"⚠️ Supprimer définitivement {nom_display} et toutes ses évaluations ?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Confirmer la suppression", key=f"yes_{pat['id']}", type="primary"):
                    db_delete_patient(pat['id'])
                    if st.session_state.patient_id == pat['id']:
                        st.session_state.patient = {}
                        st.session_state.patient_id = None
                        st.session_state.evaluations = []
                    st.session_state.pop(f"confirm_del_{pat['id']}", None)
                    st.success("Patient supprimé (Art. 17 RGPD)")
                    st.rerun()
            with c2:
                if st.button("❌ Annuler", key=f"no_{pat['id']}"):
                    st.session_state.pop(f"confirm_del_{pat['id']}", None)
                    st.rerun()

    st.markdown("---")
    if st.button("👤 Nouveau patient", type="primary", use_container_width=True):
        st.session_state.page = "patient"
        st.rerun()

# ─────────────────────────────────────────────
# PAGE NOUVEAU PATIENT
# ─────────────────────────────────────────────
elif st.session_state.page == "patient":
    # Force un rerun au premier rendu pour corriger le décalage de colonnes Streamlit
    if st.session_state.get("_prev_page") != "patient":
        st.session_state._prev_page = "patient"
        st.rerun()

    st.markdown("# 👤 Nouveau patient")

    with st.expander("🔍 Rechercher un patient existant", expanded=False):
        search_q = st.text_input("Nom, prénom ou ID patient", key="search_patient")
        if search_q:
            results = db_search_patients(search_q)
            if results:
                for r in results:
                    evals = db_load_evaluations(r['id'])
                    b = {"Liste d'attente":"🔴","LVAD":"🟡","Post-greffe":"🟢"}.get(r['statut'],'⚪')
                    nom_d = f"{r.get('prenom','')} {r.get('nom','')}".strip() or r['id']
                    col_a, col_b = st.columns([4,1])
                    with col_a:
                        st.markdown(f"{b} **{nom_d}** · {r['age']} ans · {r['statut']} · {len(evals)} éval.")
                    with col_b:
                        if st.button("Charger", key=f"srch_{r['id']}"):
                            evals2 = db_load_evaluations(r['id'])
                            st.session_state.patient = {
                                'id': r['id'], 'prenom': r.get('prenom',''),
                                'nom': r.get('nom',''), 'age': r['age'],
                                'sexe': r['sexe'], 'statut': r['statut'],
                                'moment': evals2[-1]['moment'] if evals2 else "T0 — Inscription sur liste",
                                'date': evals2[-1]['date'] if evals2 else str(datetime.today().date()),
                                'nyha': evals2[-1].get('nyha','II') if evals2 else 'II',
                                'nyha_idx': ["I","II","III","IV"].index(evals2[-1].get('nyha','II')) if evals2 else 1,
                                '6mwt': evals2[-1].get('6mwt',300) if evals2 else 300,
                                'bnp': evals2[-1].get('bnp',500) if evals2 else 500,
                                'lvef': evals2[-1].get('lvef',30) if evals2 else 30,
                            }
                            st.session_state.patient_id = r['id']
                            st.session_state.evaluations = evals2
                            st.session_state.page = "questionnaires"
                            st.rerun()
            else:
                st.info("Aucun patient trouvé.")

    _LBL_S = ("font-size:0.72rem;font-weight:700;text-transform:uppercase;"
              "letter-spacing:0.09em;color:#64748b;margin:0 0 2px 0")

    # ── Ligne 0 : en-têtes de colonnes ──────────────────────────────────────
    h1, h2 = st.columns(2)
    with h1:
        st.markdown(f'<p style="{_LBL_S}">IDENTITÉ</p>', unsafe_allow_html=True)
    with h2:
        st.markdown(f'<p style="{_LBL_S}">STATUT CLINIQUE</p>', unsafe_allow_html=True)

    # ── Ligne 1 : Prénom / Statut ────────────────────────────────────────────
    r1l, r1r = st.columns(2)
    with r1l:
        prenom = st.text_input("Prénom", value=st.session_state.patient.get("prenom", ""))
    with r1r:
        statut = st.selectbox("Statut", ["Liste d'attente", "LVAD", "Post-greffe"],
                              index=["Liste d'attente", "LVAD", "Post-greffe"].index(
                                  st.session_state.patient.get("statut", "Liste d'attente")))

    # ── Ligne 2 : Nom / Moment d'évaluation ─────────────────────────────────
    r2l, r2r = st.columns(2)
    with r2l:
        nom = st.text_input("Nom", value=st.session_state.patient.get("nom", ""))
    with r2r:
        moment = st.selectbox("Moment d'évaluation", [
            "T0 — Inscription sur liste",
            "T1 — Avant implantation LVAD",
            "T2 — 3 mois post-LVAD",
            "T3 — Suivi semestriel en liste",
            "T4 — 3 mois post-greffe",
            "T5 — 1 an post-greffe",
        ])

    # ── Ligne 3 : Âge / Date d'évaluation ───────────────────────────────────
    r3l, r3r = st.columns(2)
    with r3l:
        age = st.number_input("Âge (ans)", 18, 90,
                              value=st.session_state.patient.get("age", 60))
    with r3r:
        date_eval = st.date_input("Date d'évaluation", value=datetime.today())

    # ── Ligne 4 : Sexe / label + NYHA groupés ────────────────────────────────
    r4l, r4r = st.columns(2)
    with r4l:
        sexe = st.selectbox("Sexe", ["Homme", "Femme"],
                            index=0 if st.session_state.patient.get("sexe", "Homme") == "Homme" else 1)
    with r4r:
        st.markdown(f'<p style="{_LBL_S};margin-top:8px">PARAMÈTRES CLINIQUES</p>',
                    unsafe_allow_html=True)
        nyha = st.selectbox("NYHA", ["I", "II", "III", "IV"],
                            index=st.session_state.patient.get("nyha_idx", 2))

    # ── Ligne 5 : ID anonyme / 6MWT ──────────────────────────────────────────
    r5l, r5r = st.columns(2)
    with r5l:
        pid_preview = generate_patient_id(prenom or "?", nom or "?", age)
        if prenom or nom:
            st.caption(f"🔒 ID anonyme : `{pid_preview}`")
        else:
            st.caption("🔒 ID anonyme : sera généré après saisie")
    with r5r:
        mwt6 = st.number_input("6MWT — Test de marche 6 min (mètres)", 0, 700,
                                value=st.session_state.patient.get("6mwt", 300))

    # ── Lignes 6-7 : colonnes droite seulement ───────────────────────────────
    _, r6r = st.columns(2)
    with r6r:
        bnp = st.number_input("BNP (pg/mL)", 0, 10000,
                               value=st.session_state.patient.get("bnp", 500))
    _, r7r = st.columns(2)
    with r7r:
        lvef = st.number_input("LVEF — Fraction d'éjection VG (%)", 5, 80,
                                value=st.session_state.patient.get("lvef", 30))

    st.markdown("---")
    if st.button("✅ Enregistrer et passer aux questionnaires →", type="primary", use_container_width=True):
        patient_id = generate_patient_id(prenom or "anon", nom or "anon", age)
        patient_data = {
            "id": patient_id,
            "prenom": prenom, "nom": nom, "age": age, "sexe": sexe,
            "statut": statut, "moment": moment, "date": str(date_eval),
            "nyha": nyha, "nyha_idx": ["I","II","III","IV"].index(nyha),
            "6mwt": mwt6, "bnp": bnp, "lvef": lvef
        }
        db_save_patient(patient_data)
        st.session_state.patient    = patient_data
        st.session_state.patient_id = patient_id
        existing_evals = db_load_evaluations(patient_id)
        st.session_state.evaluations = existing_evals
        st.success(f"✅ Patient enregistré · ID : {patient_id}")
        st.session_state.page = "questionnaires"
        st.rerun()

# ─────────────────────────────────────────────
# PAGE QUESTIONNAIRES
# ─────────────────────────────────────────────
elif st.session_state.page == "questionnaires":
    if not st.session_state.patient:
        st.warning("Veuillez d'abord créer un patient.")
        if st.button("👤 Aller à Nouveau patient"):
            st.session_state.page = "patient"
            st.rerun()
        st.stop()

    p = st.session_state.patient
    statut = p["statut"]
    ref = REF[statut]

    badge_html = f'<span class="{ref["badge"]}">{statut}</span>'
    st.markdown(f"# 📋 Questionnaires — {p.get('prenom','')} {p.get('nom','')}")
    st.markdown(f"Statut : {badge_html} &nbsp;|&nbsp; {p['moment']}", unsafe_allow_html=True)
    st.markdown("---")

    outils = OUTILS_RECOMMANDES[statut]

    def reco(key):
        return any(key.lower() in o.lower() for o in outils)

    kccq_rec = reco("KCCQ")
    sf36_rec = reco("SF-36")
    minn_rec = reco("Minnesota")
    eq5d_rec = reco("EQ-5D")

    def exp_title(icon, name):
        return f"{icon} {name}"

    def exp_badge(rec):
        if rec:
            return '<div class="exp-badge-wrap"><span class="exp-badge-rec">✓ Recommandé</span></div>'
        else:
            return '<div class="exp-badge-wrap"><span class="exp-badge-not">Non prioritaire</span></div>'

    st.markdown(f"**Outils recommandés pour ce statut :** {' · '.join(outils)}")
    st.markdown("")

    scores = {}

    # ── KCCQ ──
    st.markdown(exp_badge(kccq_rec), unsafe_allow_html=True)
    with st.expander(exp_title("📊", "KCCQ — Kansas City Cardiomyopathy Questionnaire (/100)"), expanded=kccq_rec):
        st.caption("23 questions · 5 min · Score élevé = meilleure QdV")
        col1, col2 = st.columns(2)
        with col1:
            kccq_fonc = st.slider("Limitation physique (activités quotidiennes)", 0, 100, 50)
            kccq_symp = st.slider("Fréquence des symptômes (essoufflement, fatigue)", 0, 100, 50)
            kccq_qual = st.slider("Qualité de vie globale", 0, 100, 50)
        with col2:
            kccq_soc  = st.slider("Limitation sociale", 0, 100, 50)
            kccq_auto = st.slider("Auto-efficacité (confiance en soi)", 0, 100, 50)
        scores["kccq"] = round((kccq_fonc + kccq_symp + kccq_qual + kccq_soc + kccq_auto) / 5)
        m, sd = ref["kccq"]
        pct = round(stats.norm.cdf(scores["kccq"], m, sd) * 100)
        st.markdown(f"<span style='color:#fb7185;font-weight:700;'>Score KCCQ : {scores['kccq']}/100</span> — Percentile {pct}e", unsafe_allow_html=True)

    # ── SF-36 ──
    st.markdown(exp_badge(sf36_rec), unsafe_allow_html=True)
    with st.expander(exp_title("🏃", "SF-36 — Short Form-36 (/100)"), expanded=sf36_rec):
        st.caption("36 questions · 10 min · Score élevé = meilleure QdV")
        col1, col2 = st.columns(2)
        with col1:
            pcs = st.slider("PCS — Composante Physique", 0, 100, 40)
        with col2:
            mcs = st.slider("MCS — Composante Mentale", 0, 100, 45)
        scores["sf36_pcs"] = pcs
        scores["sf36_mcs"] = mcs
        m_pcs, sd_pcs = ref["sf36_pcs"]
        m_mcs, sd_mcs = ref["sf36_mcs"]
        pct_pcs = round(stats.norm.cdf(pcs, m_pcs, sd_pcs) * 100)
        pct_mcs = round(stats.norm.cdf(mcs, m_mcs, sd_mcs) * 100)
        st.markdown(f"<span style='color:#fb7185;font-weight:700;'>SF-36 PCS : {pcs}/100</span> ({pct_pcs}e percentile) &nbsp;|&nbsp; <span style='color:#fb7185;font-weight:700;'>MCS : {mcs}/100</span> ({pct_mcs}e percentile)", unsafe_allow_html=True)

    # ── MINNESOTA ──
    st.markdown(exp_badge(minn_rec), unsafe_allow_html=True)
    with st.expander(exp_title("❤️", "Minnesota LHFQ — Living with Heart Failure Questionnaire (/105)"), expanded=minn_rec):
        st.caption("21 questions · 5 min · Score bas = meilleure QdV (0 = parfait)")
        col1, col2 = st.columns(2)
        with col1:
            minn_phys = st.slider("Impact physique (essoufflement, fatigue, œdèmes)", 0, 40, 20)
        with col2:
            minn_emot = st.slider("Impact émotionnel et social", 0, 25, 12)
        minn_autre = st.slider("Autres limitations (médicaments, hospitalisations...)", 0, 40, 15)
        scores["minnesota"] = minn_phys + minn_emot + minn_autre
        m, sd = ref["minnesota"]
        pct = round((1 - stats.norm.cdf(scores["minnesota"], m, sd)) * 100)
        if not minn_rec:
            st.info("Non prioritaire pour ce statut — score pris en compte si renseigné.")
        st.markdown(f"<span style='color:#fb7185;font-weight:700;'>Score Minnesota : {scores['minnesota']}/105</span> — Percentile {pct}e <span style='color:#64748b;font-size:0.8em'>(0=meilleur)</span>", unsafe_allow_html=True)

    # ── EQ-5D ──
    st.markdown(exp_badge(eq5d_rec), unsafe_allow_html=True)
    with st.expander(exp_title("🌡️", "EQ-5D — EuroQol 5 Dimensions (/1)"), expanded=eq5d_rec):
        st.caption("5 questions · 2 min · Score élevé = meilleure QdV")
        if not eq5d_rec:
            st.info("Non prioritaire pour ce statut — utile si étude pharmaco-économique (calcul QALYs).")
        col1, col2 = st.columns(2)
        with col1:
            eq_mob   = st.select_slider("Mobilité", [1,2,3], 2)
            eq_soins = st.select_slider("Autonomie personnelle", [1,2,3], 2)
            eq_act   = st.select_slider("Activités courantes", [1,2,3], 2)
        with col2:
            eq_doul  = st.select_slider("Douleur / Gêne", [1,2,3], 2)
            eq_anx   = st.select_slider("Anxiété / Dépression", [1,2,3], 2)
        eq5d_raw = 1 - ((eq_mob + eq_soins + eq_act + eq_doul + eq_anx - 5) / 10) * 0.6
        scores["eq5d"] = round(eq5d_raw, 3)
        m, sd = ref["eq5d"]
        pct = round(stats.norm.cdf(scores["eq5d"], m, sd) * 100)
        st.markdown(f"<span style='color:#fb7185;font-weight:700;'>Score EQ-5D : {scores['eq5d']:.2f}/1</span> — Percentile {pct}e", unsafe_allow_html=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("📊 Enregistrer les scores et voir le tableau de bord →", type="primary", use_container_width=True):
        evaluation = {
            "date": p["date"],
            "moment": p["moment"],
            "statut": statut,
            **scores,
            "nyha": p["nyha"],
            "6mwt": p["6mwt"],
            "bnp": p["bnp"],
            "lvef": p["lvef"],
        }
        # Sauvegarder en SQLite si patient enregistré
        if st.session_state.patient_id:
            db_save_evaluation(st.session_state.patient_id, evaluation)
        st.session_state.evaluations.append(evaluation)
        st.session_state.page = "dashboard"
        st.rerun()

# ─────────────────────────────────────────────
# PAGE TABLEAU DE BORD
# ─────────────────────────────────────────────
elif st.session_state.page == "dashboard":
    if not st.session_state.evaluations:
        st.warning("Aucune évaluation enregistrée.")
        if st.button("📋 Aller aux questionnaires"):
            st.session_state.page = "questionnaires"
            st.rerun()
        st.stop()

    p      = st.session_state.patient
    evals  = st.session_state.evaluations
    last   = evals[-1]
    statut = last["statut"]
    ref    = REF[statut]

    prenom = p.get("prenom", "")
    nom    = p.get("nom", "")

    # ── SETUP ──

    # ── PERCENTILES ──
    def calc_pct(score, mean, sd, higher_is_better=True):
        v = int(stats.norm.cdf(score, mean, sd) * 100)
        return v if higher_is_better else 100 - v

    def badge_cls(v):
        return "hdb-badge-g" if v >= 66 else "hdb-badge-o" if v >= 33 else "hdb-badge-r"

    def bar_col(v):
        return "#10b981" if v >= 66 else "#fb923c" if v >= 33 else "#ef4444"

    kccq   = last.get("kccq") or 0
    pcs    = last.get("sf36_pcs") or 0
    mcs    = last.get("sf36_mcs") or 0
    minn   = last.get("minnesota") or 0
    eq     = last.get("eq5d") or 0
    bnp_v  = last.get("bnp") or 0
    mwt_v  = last.get("6mwt") or 0
    lvef_v = last.get("lvef") or 0
    nyha_v = last.get("nyha", "II")

    pct_kccq = calc_pct(kccq, *ref["kccq"])
    pct_pcs  = calc_pct(pcs,  *ref["sf36_pcs"])
    pct_mcs  = calc_pct(mcs,  *ref["sf36_mcs"])
    pct_mwt  = calc_pct(mwt_v, *ref["6mwt"])
    pct_bnp  = calc_pct(bnp_v, *ref["bnp"], higher_is_better=False)
    pct_lvef = calc_pct(lvef_v, *ref["lvef"])

    # ── TIMELINE STEPPER ──
    T_DEFS = [
        ("T0","Inscription"),("T1","Pré-LVAD"),("T2","3m LVAD"),
        ("T3","Suivi 6m"),  ("T4","3m greffe"),("T5","1an greffe"),
    ]
    eval_ts = set()
    for ev in evals:
        m = ev.get("moment","")
        if m[:2] in [t[0] for t in T_DEFS]:
            eval_ts.add(m[:2])

    tl_html = ""
    for i, (tk, tlbl) in enumerate(T_DEFS):
        circ_cls = "done" if tk in eval_ts else ""
        circ_txt = "✓" if tk in eval_ts else str(i)
        step = (f'<div class="tl-step">'
                f'<div class="tl-circle {circ_cls}">{circ_txt}</div>'
                f'<div class="tl-label">{tk}<br>{tlbl}</div>'
                f'</div>')
        if i < len(T_DEFS) - 1:
            line_cls = "tl-line done" if tk in eval_ts else "tl-line"
            step += f'<div class="{line_cls}"></div>'
        tl_html += step

    st.markdown(f"""
<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px 24px;margin-bottom:14px;">
  <div class="tl-wrap">{tl_html}</div>
</div>""", unsafe_allow_html=True)

    # ── PATIENT HEADER ──
    badge_html = f'<span class="{ref["badge"]}">{statut}</span>'
    st.markdown(f"""
<div class="pat-header">
  <span style="font-size:1.1rem;">📊</span>
  <span style="color:#e2e8f0;font-weight:700;font-size:0.9rem;">Patient</span>
  <span style="color:#475569;">—</span>
  {badge_html}
</div>""", unsafe_allow_html=True)

    # ── ALERT BANNER ──
    alertes = []
    if len(evals) >= 2:
        for outil, hib, lbl in [("kccq",True,"KCCQ"),("sf36_pcs",True,"SF-36 PCS"),("minnesota",False,"Minnesota")]:
            prev = evals[-2].get(outil)
            curr = evals[-1].get(outil)
            if prev is not None and curr is not None:
                delta = (curr - prev) if hib else (prev - curr)
                if delta < -10:
                    alertes.append(f"Dégradation {lbl} : {prev:.0f}→{curr:.0f} (Δ{delta:+.0f})")

    if alertes:
        st.markdown(f'<div class="alert-danger">⚠️ {" &nbsp;·&nbsp; ".join(alertes)}</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-success">✅ Aucune dégradation détectée depuis la dernière évaluation</div>',
                    unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    # ── TWO-COL CARDS ──
    def dual_row(name, val, max_val, ref_mean, pct_val, val_str):
        patient_pct = min(val / max_val * 100, 100) if max_val else 0
        ref_pct     = min(ref_mean / max_val * 100, 100) if max_val else 0
        bc = badge_cls(pct_val); fc = bar_col(pct_val)
        return (f'<div class="sc-row">'
                f'<span class="sc-name">{name}</span>'
                f'<div class="sc-bar-outer">'
                f'<div class="sc-bar-patient" style="width:{patient_pct:.1f}%;background:{fc};"></div>'
                f'<div class="sc-ref-mark" style="left:{ref_pct:.1f}%;"></div>'
                f'</div>'
                f'<span class="sc-val">{val_str} '
                f'<span class="hdb-badge {bc}" style="font-size:0.6rem;padding:2px 6px;">'
                f'{pct_val}e pct.</span></span>'
                f'</div>')

    sf36_shown = any("SF-36" in o or "sf-36" in o.lower() for o in OUTILS_RECOMMANDES[statut])
    eq5d_shown = any("EQ-5D" in o or "eq-5d" in o.lower() for o in OUTILS_RECOMMANDES[statut])
    minn_shown = any("Minnesota" in o for o in OUTILS_RECOMMANDES[statut])

    col_l, col_r = st.columns(2)

    with col_l:
        rows_qol = dual_row("KCCQ", kccq, 100, ref["kccq"][0], pct_kccq, f"{kccq}/100")
        if sf36_shown:
            rows_qol += (
                dual_row("SF-36 PCS", pcs, 100, ref["sf36_pcs"][0], pct_pcs, f"{pcs}/100") +
                dual_row("SF-36 MCS", mcs, 100, ref["sf36_mcs"][0], pct_mcs, f"{mcs}/100")
            )
        if minn_shown:
            rows_qol += dual_row("Minnesota", minn, 105, ref["minnesota"][0],
                                 calc_pct(minn, *ref["minnesota"], higher_is_better=False),
                                 f"{minn}/105")
        st.markdown(f"""
<div class="sc-card">
  <div class="sc-card-title">Scores de qualité de vie</div>
  <div class="sc-card-sub">Barre grise = référence méta-analyse</div>
  {rows_qol}
</div>""", unsafe_allow_html=True)

    with col_r:
        nyha_good = nyha_v in ["I","II"]
        nyha_bc = "hdb-badge-g" if nyha_good else ("hdb-badge-o" if nyha_v=="III" else "hdb-badge-r")
        rows_clin = (
            dual_row("6MWT", mwt_v, 600,  ref["6mwt"][0], pct_mwt,  f"{mwt_v} m")       +
            dual_row("BNP",  bnp_v, 1500, ref["bnp"][0],  pct_bnp,  f"{bnp_v} pg/mL")   +
            dual_row("LVEF", lvef_v, 80,  ref["lvef"][0], pct_lvef, f"{lvef_v}%")
        )
        nyha_row = (f'<div class="sc-row">'
                    f'<span class="sc-name">NYHA</span>'
                    f'<div style="flex:1;"></div>'
                    f'<span class="hdb-badge {nyha_bc}" style="font-size:0.72rem;padding:4px 12px;">{nyha_v}</span>'
                    f'</div>')
        st.markdown(f"""
<div class="sc-card">
  <div class="sc-card-title">Paramètres cliniques</div>
  <div class="sc-card-sub">Barre grise = référence méta-analyse</div>
  {rows_clin}{nyha_row}
</div>""", unsafe_allow_html=True)

    # ── TRAJECTORY TABLE ──
    traj_rows = ""
    for ev in evals:
        m      = ev.get("moment","—")
        m_s    = m.split("—")[0].strip() if "—" in m else m
        kccq_e = ev.get("kccq","—")
        pcs_e  = ev.get("sf36_pcs","—")
        nyha_e = ev.get("nyha","—")
        mwt_e  = ev.get("6mwt","—")
        mwt_s  = f"{mwt_e} m" if mwt_e != "—" and mwt_e is not None else "—"
        traj_rows += (f'<tr><td class="moment-val">{m_s}</td>'
                      f'<td class="kccq-val">{kccq_e if kccq_e is not None else "—"}</td>'
                      f'<td class="sf36-val">{pcs_e if pcs_e is not None else "—"}</td>'
                      f'<td>{nyha_e}</td><td>{mwt_s}</td></tr>')

    st.markdown(f"""
<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:20px;margin-top:14px;">
  <div style="font-size:0.8rem;font-weight:700;color:#e2e8f0;margin-bottom:14px;">
    📝 Trajectoire longitudinale
    <span style="color:#64748b;font-weight:400;font-size:0.72rem;margin-left:6px;">{len(evals)} évaluation(s)</span>
  </div>
  <table class="traj-table"><thead><tr>
    <th>Moment</th>
    <th style="color:#3b82f6;">KCCQ</th>
    <th style="color:#10b981;">SF-36 PCS</th>
    <th>NYHA</th><th>6MWT</th>
  </tr></thead><tbody>{traj_rows}</tbody></table>
</div>""", unsafe_allow_html=True)

    # ── BUTTONS ──
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Nouvelle évaluation", use_container_width=True):
            st.session_state.page = "questionnaires"
            st.rerun()
    with col2:
        if st.button("📄 Générer le rapport", type="primary", use_container_width=True):
            st.session_state.page = "rapport"
            st.rerun()

    # ── RGPD FOOTER ──
    st.markdown("""
<div style="background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.15);
    border-radius:10px;padding:12px 18px;margin-top:14px;font-size:0.72rem;color:#64748b;">
  <span style="color:#4ade80;margin-right:6px;">🛡</span>
  <b style="color:#94a3b8;">Confidentialité & RGPD</b> — QoL Cardiac est un outil 100% local.
  Aucune donnée patient n'est transmise à un serveur externe.
  <b>Version clinique :</b> base SQLite locale · pseudonymisation automatique HDS · droit à l'effacement intégré (Art. 17 RGPD).
</div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PAGE RAPPORT
# ─────────────────────────────────────────────
elif st.session_state.page == "rapport":
    if not st.session_state.evaluations:
        st.warning("Aucune évaluation disponible.")
        st.stop()

    p      = st.session_state.patient
    evals  = st.session_state.evaluations
    last   = evals[-1]
    statut = last["statut"]
    ref    = REF[statut]
    pid    = st.session_state.patient_id or "NON ENREGISTRÉ"

    kccq   = last.get("kccq", 0) or 0
    pcs    = last.get("sf36_pcs", 0) or 0
    mcs    = last.get("sf36_mcs", 0) or 0
    minn   = last.get("minnesota", 0) or 0
    eq     = last.get("eq5d", 0) or 0
    bnp_v  = last.get("bnp", 0) or 0
    mwt_v  = last.get("6mwt", 0) or 0
    lvef_v = last.get("lvef", 0) or 0
    nyha_v = last.get("nyha", "—")
    age_v  = p.get("age","—")
    sexe_v = p.get("sexe","—")

    def cpct(score, mean, sd, hib=True):
        v = int(stats.norm.cdf(score, mean, sd) * 100)
        return v if hib else 100 - v

    pct_kccq = cpct(kccq, *ref["kccq"])
    pct_pcs  = cpct(pcs,  *ref["sf36_pcs"])
    pct_mcs  = cpct(mcs,  *ref["sf36_mcs"])
    pct_minn = cpct(minn, *ref["minnesota"], hib=False)
    pct_eq   = cpct(eq,   *ref["eq5d"])
    pct_mwt  = cpct(mwt_v, *ref["6mwt"])
    pct_bnp  = cpct(bnp_v, *ref["bnp"], hib=False)
    pct_lvef = cpct(lvef_v, *ref["lvef"])

    def pct_color(v):
        return "#4ade80" if v >= 66 else ("#fb923c" if v >= 33 else "#f87171")

    # ── RAPPORT HEADER ──
    now_str = datetime.now().strftime("%-d %B %Y à %H:%M")
    badge_html = f'<span class="{ref["badge"]}">{statut}</span>'
    st.markdown(f"""
<div style="background:linear-gradient(135deg,#0f172a,#1a2744);border:1px solid #334155;
    border-radius:12px;padding:16px 22px;margin-bottom:12px;
    display:flex;justify-content:space-between;align-items:center;">
  <div>
    <div style="color:#fb7185;font-weight:900;font-size:1.05rem;">MedFlow <span style="color:#f1f5f9;">AI</span></div>
    <div style="color:#64748b;font-size:0.7rem;margin-top:2px;">QoL Cardiac — Rapport d'évaluation de la qualité de vie</div>
  </div>
  <div style="text-align:right;">
    {badge_html}
    <div style="color:#94a3b8;font-size:0.7rem;margin-top:3px;">{last['moment']}</div>
    <div style="color:#64748b;font-size:0.63rem;">{now_str}</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── PATIENT KPI ROW ──
    st.markdown(f"""
<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;
    padding:12px 18px;margin-bottom:14px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
  <div style="margin-right:8px;">
    <div style="color:#e2e8f0;font-weight:700;font-size:0.82rem;">Patient</div>
    <div style="color:#64748b;font-size:0.7rem;">{age_v} ans · {sexe_v}</div>
  </div>
  <div style="display:flex;gap:6px;flex-wrap:wrap;margin-left:auto;">
    <span style="background:#1a2744;border:1px solid #334155;border-radius:8px;padding:5px 10px;text-align:center;">
      <div style="color:#3b82f6;font-weight:900;font-size:1rem;">{kccq}</div>
      <div style="color:#64748b;font-size:0.58rem;">KCCQ/100</div>
    </span>
    <span style="background:#1a2744;border:1px solid #334155;border-radius:8px;padding:5px 10px;text-align:center;">
      <div style="color:#10b981;font-weight:900;font-size:1rem;">{mwt_v} m</div>
      <div style="color:#64748b;font-size:0.58rem;">6MWT</div>
    </span>
    <span style="background:#1a2744;border:1px solid #334155;border-radius:8px;padding:5px 10px;text-align:center;">
      <div style="color:#f59e0b;font-weight:900;font-size:1rem;">{nyha_v}</div>
      <div style="color:#64748b;font-size:0.58rem;">NYHA</div>
    </span>
    <span style="background:#1a2744;border:1px solid #334155;border-radius:8px;padding:5px 10px;text-align:center;">
      <div style="color:#f59e0b;font-weight:900;font-size:1rem;">{lvef_v}%</div>
      <div style="color:#64748b;font-size:0.58rem;">LVEF</div>
    </span>
    <span style="background:#1a2744;border:1px solid #334155;border-radius:8px;padding:5px 10px;text-align:center;">
      <div style="color:#f59e0b;font-weight:900;font-size:1rem;">{bnp_v}</div>
      <div style="color:#64748b;font-size:0.58rem;">BNP pg/mL</div>
    </span>
  </div>
</div>""", unsafe_allow_html=True)

    # ── SECTION TITLE ──
    st.markdown(f"""
<div style="background:rgba(59,130,246,0.07);border:1px solid rgba(59,130,246,0.18);
    border-radius:8px;padding:9px 16px;margin-bottom:14px;">
  <span style="color:#60a5fa;font-weight:800;font-size:0.7rem;text-transform:uppercase;
      letter-spacing:0.08em;">📊 Scores de qualité de vie vs cohorte de référence ({statut})</span>
</div>""", unsafe_allow_html=True)

    # ── SCORES LEFT + SIDE RIGHT ──
    def rpt_score_bar(name, val, max_val, ref_mean, pct_val, ref_label):
        pp  = min(val / max_val * 100, 100) if max_val else 0
        rp  = min(ref_mean / max_val * 100, 100) if max_val else 0
        pc  = pct_color(pct_val)
        mv  = int(max_val)
        return (f'<div style="margin-bottom:16px;padding:13px 16px;background:#1a2744;border-radius:10px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">'
                f'<span style="color:#e2e8f0;font-weight:700;font-size:0.82rem;">{name}</span>'
                f'<div style="display:flex;align-items:center;gap:10px;">'
                f'<span style="color:#f1f5f9;font-weight:900;">{val:.0f}/{mv}</span>'
                f'<span style="color:{pc};font-weight:700;font-size:0.72rem;">{pct_val}e pct.</span>'
                f'</div></div>'
                f'<div style="height:12px;background:rgba(255,255,255,0.06);border-radius:6px;position:relative;overflow:hidden;">'
                f'<div style="height:100%;border-radius:6px;background:{pc};width:{pp:.1f}%;"></div>'
                f'<div style="position:absolute;top:0;left:{rp:.1f}%;width:3px;height:100%;background:rgba(255,255,255,0.85);z-index:2;"></div>'
                f'</div>'
                f'<div style="margin-top:8px;font-size:0.63rem;color:#475569;">Réf. cohorte : {ref_label}</div>'
                f'</div>')

    col_main, col_side = st.columns([2, 1])

    rpt_sf36 = any("SF-36" in o or "sf-36" in o.lower() for o in OUTILS_RECOMMANDES[statut])
    rpt_minn = any("Minnesota" in o for o in OUTILS_RECOMMANDES[statut])
    rpt_eq5d = any("EQ-5D" in o or "eq-5d" in o.lower() for o in OUTILS_RECOMMANDES[statut])

    with col_main:
        score_bars = rpt_score_bar("KCCQ", kccq, 100, ref["kccq"][0], pct_kccq, f"{ref['kccq'][0]:.1f}/100")
        if rpt_sf36:
            score_bars += (
                rpt_score_bar("SF-36 PCS", pcs, 100, ref["sf36_pcs"][0], pct_pcs, f"{ref['sf36_pcs'][0]:.1f}/100") +
                rpt_score_bar("SF-36 MCS", mcs, 100, ref["sf36_mcs"][0], pct_mcs, f"{ref['sf36_mcs'][0]:.1f}/100")
            )
        if rpt_minn:
            score_bars += rpt_score_bar("Minnesota", minn, 105, ref["minnesota"][0],
                                        cpct(minn, *ref["minnesota"], hib=False), f"{ref['minnesota'][0]:.1f}/105")
        if rpt_eq5d:
            score_bars += rpt_score_bar("EQ-5D", eq, 1, ref["eq5d"][0],
                                        cpct(eq, *ref["eq5d"]), f"{ref['eq5d'][0]:.2f}/1")
        st.markdown(score_bars, unsafe_allow_html=True)
        if kccq < ref["kccq"][0] - ref["kccq"][1]:
            st.markdown("""
<div style="background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.25);
    border-radius:8px;padding:9px 14px;">
  <span style="color:#f87171;font-size:0.74rem;">⚠️ Surveillance rapprochée recommandée — KCCQ en dessous de 1 ET de la cohorte de référence</span>
</div>""", unsafe_allow_html=True)

    with col_side:
        nyha_c = "#4ade80" if nyha_v in ["I","II"] else ("#fb923c" if nyha_v=="III" else "#f87171")
        st.markdown(f"""
<div class="rpt-side-panel">
  <div class="rpt-side-title">Paramètres cliniques</div>
  <div class="rpt-side-row"><span class="rpt-side-key">6MWT</span><span class="rpt-side-val">{mwt_v} m</span></div>
  <div class="rpt-side-row"><span class="rpt-side-key">BNP</span><span class="rpt-side-val">{bnp_v} pg/mL</span></div>
  <div class="rpt-side-row"><span class="rpt-side-key">LVEF</span><span class="rpt-side-val">{lvef_v}%</span></div>
  <div class="rpt-side-row" style="border-bottom:none;">
    <span class="rpt-side-key">NYHA</span>
    <span style="color:{nyha_c};font-weight:700;">{nyha_v}</span>
  </div>
</div>
<div class="rpt-side-panel">
  <div class="rpt-side-title">Références méta-analyse</div>
  <div class="rpt-side-row"><span class="rpt-side-key">KCCQ</span><span style="color:#64748b;font-size:0.7rem;">{ref['kccq'][0]:.1f} ± {ref['kccq'][1]:.1f}</span></div>
  <div class="rpt-side-row"><span class="rpt-side-key">SF-36 PCS</span><span style="color:#64748b;font-size:0.7rem;">{ref['sf36_pcs'][0]:.1f} ± {ref['sf36_pcs'][1]:.1f}</span></div>
  <div class="rpt-side-row"><span class="rpt-side-key">SF-36 MCS</span><span style="color:#64748b;font-size:0.7rem;">{ref['sf36_mcs'][0]:.1f} ± {ref['sf36_mcs'][1]:.1f}</span></div>
  <div class="rpt-side-row"><span class="rpt-side-key">Minnesota</span><span style="color:#64748b;font-size:0.7rem;">{ref['minnesota'][0]:.1f} ± {ref['minnesota'][1]:.1f}</span></div>
  <div class="rpt-side-row"><span class="rpt-side-key">EQ-5D</span><span style="color:#64748b;font-size:0.7rem;">{ref['eq5d'][0]:.2f} ± {ref['eq5d'][1]:.2f}</span></div>
  <div class="rpt-side-row"><span class="rpt-side-key">6MWT</span><span style="color:#64748b;font-size:0.7rem;">{ref['6mwt'][0]:.0f} ± {ref['6mwt'][1]:.0f} m</span></div>
  <div class="rpt-side-row"><span class="rpt-side-key">BNP</span><span style="color:#64748b;font-size:0.7rem;">{ref['bnp'][0]:.0f} ± {ref['bnp'][1]:.0f}</span></div>
  <div class="rpt-side-row" style="border-bottom:none;"><span class="rpt-side-key">LVEF</span><span style="color:#64748b;font-size:0.7rem;">{ref['lvef'][0]:.0f} ± {ref['lvef'][1]:.0f}%</span></div>
  <div style="margin-top:8px;font-size:0.6rem;color:#334155;font-style:italic;">15 études · 600 patients · 2000–2026</div>
</div>""", unsafe_allow_html=True)

    # ── TRAJECTOIRE ──
    T_DEFS = [
        ("T0","Inscription"),("T1","Pré-LVAD"),("T2","3m LVAD"),
        ("T3","Suivi 6m"),  ("T4","3m greffe"),("T5","1an greffe"),
    ]
    eval_ts = set()
    for ev in evals:
        m = ev.get("moment","")
        if m[:2] in [t[0] for t in T_DEFS]:
            eval_ts.add(m[:2])

    tl_html = ""
    for i, (tk, tlbl) in enumerate(T_DEFS):
        circ_cls = "done" if tk in eval_ts else ""
        circ_txt = "✓" if tk in eval_ts else str(i)
        step = (f'<div class="tl-step">'
                f'<div class="tl-circle {circ_cls}">{circ_txt}</div>'
                f'<div class="tl-label">{tk}<br>{tlbl}</div></div>')
        if i < len(T_DEFS) - 1:
            line_cls = "tl-line done" if tk in eval_ts else "tl-line"
            step += f'<div class="{line_cls}"></div>'
        tl_html += step

    traj_rows = ""
    for ev in evals:
        m     = ev.get("moment","—")
        m_s   = m.split("—")[0].strip() if "—" in m else m
        kccq_e = ev.get("kccq","—"); pcs_e = ev.get("sf36_pcs","—")
        nyha_e = ev.get("nyha","—"); mwt_e  = ev.get("6mwt","—")
        mwt_s  = f"{mwt_e} m" if mwt_e not in ("—", None) else "—"
        traj_rows += (f'<tr><td class="moment-val">{m_s}</td>'
                      f'<td class="kccq-val">{kccq_e if kccq_e is not None else "—"}</td>'
                      f'<td class="sf36-val">{pcs_e if pcs_e is not None else "—"}</td>'
                      f'<td>{nyha_e}</td><td>{mwt_s}</td></tr>')

    st.markdown(f"""
<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:18px;margin-top:16px;">
  <div style="font-size:0.8rem;font-weight:700;color:#e2e8f0;margin-bottom:12px;">
    📝 Trajectoire longitudinale
    <span style="color:#64748b;font-weight:400;font-size:0.7rem;margin-left:6px;">{len(evals)} évaluation(s)</span>
  </div>
  <div style="background:#0f172a;border-radius:8px;padding:12px 18px;margin-bottom:12px;">
    <div class="tl-wrap">{tl_html}</div>
  </div>
  <table class="traj-table"><thead><tr>
    <th>Moment</th>
    <th style="color:#3b82f6;">KCCQ</th>
    <th style="color:#10b981;">SF-36 PCS</th>
    <th>NYHA</th><th>6MWT</th>
  </tr></thead><tbody>{traj_rows}</tbody></table>
</div>""", unsafe_allow_html=True)

    # ── INTERPRÉTATION ──
    delta_str = ""
    if len(evals) >= 2:
        prev_kccq = evals[-2].get("kccq")
        if prev_kccq is not None:
            delta = kccq - prev_kccq
            evol = "stable" if abs(delta) < 5 else ("en amélioration" if delta > 0 else "en dégradation")
            delta_str = f" La QdV est {evol} par rapport à l'évaluation précédente (Δ KCCQ : {delta:+.0f} pts)."

    _mc = last.get('moment', '').split('—')[0].strip()
    _next_map = {
        'T0': "Dans 6 mois (T3 — Suivi semestriel)",
        'T1': "À 3 mois post-LVAD (T2)",
        'T2': "Dans 6 mois (T3 — Suivi semestriel)",
        'T3': "Prochain suivi dans 6 mois (T3) ou T4 si greffe imminente",
        'T4': "À 1 an post-greffe (T5)",
        'T5': "Bilan annuel de suivi",
    }
    next_eval = _next_map.get(_mc,
                 "Dans 6 mois (T3 — Suivi semestriel)" if statut == "Liste d'attente" else
                 "À 1 an post-greffe (T5)" if statut == "Post-greffe" else
                 "À 3 mois post-LVAD (T2)")

    kccq_interp = ("significativement altérée" if pct_kccq < 25 else
                   "altérée" if pct_kccq < 50 else
                   "proche de la norme" if pct_kccq < 75 else "bonne")
    diff_kccq = ref["kccq"][0] - kccq
    diff_str = (f"inférieur de <b>{diff_kccq:.1f} pts</b>" if diff_kccq > 0
                else f"supérieur de <b>{-diff_kccq:.1f} pts</b>")

    st.markdown(f"""
<div class="rpt-interp">
  <div class="rpt-interp-title">🧠 Interprétation clinique</div>
  <p style="color:#cbd5e1;font-size:0.78rem;line-height:1.7;margin:0;">
    Patient ({age_v} ans, {sexe_v}), en <b style="color:#f1f5f9;">{statut}</b>, présente une qualité de vie
    <span style="color:#fb7185;font-weight:700;">{kccq_interp}</span>
    (score composite {pct_kccq}e percentile).
    Le KCCQ de {kccq}/100 est {diff_str} à la moyenne de la cohorte de référence
    ({ref['kccq'][0]:.1f}/100 — {pct_kccq}e percentile).
    La composante physique SF-36 PCS est à {pcs}/100 ({pct_pcs}e percentile)
    et la composante mentale MCS à {mcs}/100 ({pct_mcs}e percentile).{delta_str}
    <b style="color:#60a5fa;">Prochaine évaluation recommandée : {next_eval}.</b>
  </p>
  <p style="color:#475569;font-size:0.63rem;margin:8px 0 0 0;">
    ⚠ Outil d'aide clinique — Ne remplace pas l'avis médical. Valeurs issues méta-analyse 15 études, 600 patients.
  </p>
</div>""", unsafe_allow_html=True)

    # ── FOOTER ──
    st.markdown(f"""
<div style="display:flex;justify-content:space-between;margin-top:12px;
    padding-top:8px;border-top:1px solid #334155;font-size:0.67rem;color:#475569;">
  <span>Clinicien : Dr. _______________</span>
  <span>medflow-ai.fr/qol-cardiac</span>
</div>""", unsafe_allow_html=True)

    # ── BUTTONS ──
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    rapport_text = f"""RAPPORT D'ÉVALUATION DE LA QUALITÉ DE VIE
==========================================
Date : {last['date']}  |  Généré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}
Patient : {age_v} ans | {sexe_v}
ID : {pid}  |  Statut : {statut} | {last['moment']}
Clinicien : Dr. _______________

SCORES DE QUALITÉ DE VIE
KCCQ : {kccq}/100 → {pct_kccq}e pct  (réf. {ref['kccq'][0]:.1f}±{ref['kccq'][1]:.1f})
SF-36 PCS : {pcs}/100 → {pct_pcs}e pct  (réf. {ref['sf36_pcs'][0]:.1f}±{ref['sf36_pcs'][1]:.1f})
SF-36 MCS : {mcs}/100 → {pct_mcs}e pct  (réf. {ref['sf36_mcs'][0]:.1f}±{ref['sf36_mcs'][1]:.1f})
Minnesota LHFQ : {minn}/105 → {cpct(minn, *ref['minnesota'], hib=False)}e pct
EQ-5D : {eq:.2f}/1 → {pct_eq}e pct

PARAMÈTRES CLINIQUES
NYHA : {nyha_v}  |  6MWT : {mwt_v} m  |  BNP : {bnp_v} pg/mL  |  LVEF : {lvef_v}%

Prochaine évaluation recommandée : {next_eval}
==========================================
QoL Cardiac — MedFlow AI Research · 15 études · 600 patients · 2000–2026
"""

    col1, col2, col3 = st.columns(3)
    with col1:
        pdf_bytes = _gen_pdf_report(
            p, last, evals, statut, ref, pid,
            kccq, pcs, mcs, minn, eq, bnp_v, mwt_v, lvef_v, nyha_v,
            pct_kccq, pct_pcs, pct_mcs, rpt_sf36, rpt_minn, rpt_eq5d
        )
        st.download_button("⬇️ Télécharger (.pdf)", pdf_bytes,
            file_name=f"rapport_QdV_{p.get('nom','patient')}_{last['date']}.pdf",
            mime="application/pdf", use_container_width=True, type="primary")
    with col2:
        df_export = pd.DataFrame(evals)
        csv = df_export.to_csv(index=False)
        st.download_button("📊 Export données (.csv)", csv,
            file_name=f"evaluations_{p.get('nom','patient')}.csv",
            mime="text/csv", use_container_width=True)
    with col3:
        if st.button("🖨 Imprimer", use_container_width=True):
            st.info("Utilisez Ctrl+P / Cmd+P dans votre navigateur.")

# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# PAGE RECHERCHE
# ─────────────────────────────────────────────
elif st.session_state.page == "recherche":

    st.markdown("""
<div style="background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid #334155;
            border-radius:14px;padding:20px 24px;margin-bottom:20px;">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
    <div>
      <div style="font-size:0.68rem;font-weight:700;color:#94a3b8;letter-spacing:1px;
                  text-transform:uppercase;margin-bottom:6px;">MedFlow AI · QoL Cardiac</div>
      <div style="font-size:1.3rem;font-weight:900;color:#f1f5f9;">🔬 Analyse de recherche</div>
      <div style="font-size:0.78rem;color:#64748b;margin-top:4px;">
        Meilleurs moments du parcours pour évaluer la QdV</div>
    </div>
    <div style="background:#1e3a5f;border:1px solid #3b82f6;border-radius:8px;
                padding:8px 16px;text-align:center;">
      <div style="font-size:0.62rem;color:#60a5fa;font-weight:700;letter-spacing:1px;">ÉTUDE PROSPECTIVE</div>
      <div style="font-size:0.68rem;color:#94a3b8;margin-top:2px;">Multi-site · Données réelles</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

    all_patients = db_list_patients()
    all_evals_r  = []
    for _pt in all_patients:
        for _ev in db_load_evaluations(_pt['id']):
            _ev['patient_id'] = _pt['id']
            _ev['age']        = _pt['age']
            _ev['sexe']       = _pt['sexe']
            all_evals_r.append(_ev)

    df_r = pd.DataFrame(all_evals_r) if all_evals_r else pd.DataFrame()
    n_pts  = len(all_patients)
    n_evs  = len(all_evals_r)
    sc     = {}
    for _p in all_patients: sc[_p['statut']] = sc.get(_p['statut'], 0) + 1
    n_li   = sc.get("Liste d'attente", 0)
    n_lv   = sc.get("LVAD", 0)
    n_gr   = sc.get("Post-greffe", 0)
    n_mom  = len(df_r['moment'].unique()) if not df_r.empty else 0

    st.markdown(f"""
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
  <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;text-align:center;">
    <div style="font-size:2rem;font-weight:900;color:#60a5fa;">{n_pts}</div>
    <div style="font-size:0.78rem;font-weight:600;color:#e2e8f0;">Patients</div>
    <div style="font-size:0.68rem;color:#64748b;">Base locale</div>
  </div>
  <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;text-align:center;">
    <div style="font-size:2rem;font-weight:900;color:#a78bfa;">{n_evs}</div>
    <div style="font-size:0.78rem;font-weight:600;color:#e2e8f0;">Évaluations</div>
    <div style="font-size:0.68rem;color:#64748b;">T0→T5 enregistrés</div>
  </div>
  <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px;text-align:center;">
    <div style="font-size:1rem;font-weight:900;margin-top:4px;">
      <span style="color:#ef4444;">{n_li}</span>
      <span style="color:#475569;"> · </span>
      <span style="color:#f59e0b;">{n_lv}</span>
      <span style="color:#475569;"> · </span>
      <span style="color:#10b981;">{n_gr}</span>
    </div>
    <div style="font-size:0.78rem;font-weight:600;color:#e2e8f0;margin-top:4px;">Liste · LVAD · Greffe</div>
    <div style="font-size:0.68rem;color:#64748b;">Répartition statuts</div>
  </div>
  <div style="background:#1e293b;border:1px solid #10b981;border-radius:12px;padding:16px;text-align:center;">
    <div style="font-size:2rem;font-weight:900;color:#34d399;">{n_mom}</div>
    <div style="font-size:0.78rem;font-weight:600;color:#e2e8f0;">Moments T utilisés</div>
    <div style="font-size:0.68rem;color:#64748b;">Sur 6 possibles</div>
  </div>
</div>""", unsafe_allow_html=True)

    T_ORDER  = ['T0','T1','T2','T3','T4','T5']
    C_STAT   = {'T0':'#ef4444','T1':'#f59e0b','T2':'#f59e0b',
                'T3':'#f59e0b','T4':'#10b981','T5':'#10b981'}

    if df_r.empty or n_pts < 2:
        st.markdown("""
<div style="background:#1e293b;border:1px dashed #334155;border-radius:12px;
            padding:48px 24px;text-align:center;margin:12px 0 24px;">
  <div style="font-size:2.4rem;margin-bottom:12px;">📊</div>
  <div style="color:#94a3b8;font-size:0.9rem;font-weight:700;">Données insuffisantes pour l'analyse</div>
  <div style="color:#64748b;font-size:0.76rem;margin-top:8px;line-height:1.6;">
    Minimum 3 patients avec plusieurs évaluations requis<br>
    Saisissez des patients pour activer les graphiques automatiquement
  </div>
</div>""", unsafe_allow_html=True)
    else:
        df_r['t_code'] = df_r['moment'].apply(
            lambda x: x.split('—')[0].strip() if isinstance(x, str) else '')

        col_g1, col_g2 = st.columns(2)

        with col_g1:
            kbt = (df_r[df_r['kccq'].notna()]
                   .groupby('t_code')['kccq']
                   .agg(['mean','count','std'])
                   .reindex(T_ORDER).dropna(subset=['mean']).reset_index())
            fig1, ax1 = plt.subplots(figsize=(5.5, 3.6))
            fig1.patch.set_facecolor('#0f172a')
            ax1.set_facecolor('#1e293b')
            if not kbt.empty:
                bars1 = ax1.bar(range(len(kbt)), kbt['mean'],
                                color=[C_STAT.get(t,'#3b82f6') for t in kbt['t_code']],
                                alpha=0.85, width=0.6, zorder=3)
                ax1.errorbar(range(len(kbt)), kbt['mean'],
                             yerr=kbt['std'].fillna(0),
                             fmt='none', color='white', alpha=0.35, capsize=3, linewidth=1)
                for ref_v, ref_c, ref_l in [(40.1,'#ef4444','Réf. liste'),
                                             (53.5,'#f59e0b','Réf. LVAD'),
                                             (66.7,'#10b981','Réf. greffe')]:
                    ax1.axhline(ref_v, color=ref_c, linestyle='--', alpha=0.4,
                                linewidth=0.9, label=ref_l)
                for bar, (_, row) in zip(bars1, kbt.iterrows()):
                    ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1.5,
                             f"{row['mean']:.0f}\n(n={int(row['count'])})",
                             ha='center', va='bottom', color='white', fontsize=7)
                ax1.set_xticks(range(len(kbt)))
                ax1.set_xticklabels(kbt['t_code'], color='#94a3b8', fontsize=9)
            ax1.set_ylim(0, 110)
            ax1.set_ylabel('KCCQ moyen (/100)', color='#94a3b8', fontsize=8.5)
            ax1.set_title("KCCQ par moment d'évaluation", color='#e2e8f0',
                          fontsize=10, fontweight='bold', pad=10)
            for sp in ['top','right']: ax1.spines[sp].set_visible(False)
            for sp in ['bottom','left']: ax1.spines[sp].set_color('#334155')
            ax1.tick_params(colors='#64748b', labelsize=8)
            ax1.yaxis.grid(True, color='#334155', alpha=0.4, linewidth=0.5)
            ax1.set_axisbelow(True)
            ax1.legend(fontsize=6.5, facecolor='#1e293b', labelcolor='#94a3b8',
                       edgecolor='#334155', loc='upper left')
            plt.tight_layout()
            st.pyplot(fig1); plt.close()

        with col_g2:
            mom_counts = (df_r['t_code'].value_counts()
                          .reindex(T_ORDER, fill_value=0))
            fig2, ax2 = plt.subplots(figsize=(5.5, 3.6))
            fig2.patch.set_facecolor('#0f172a')
            ax2.set_facecolor('#1e293b')
            bar_c2 = ['#3b82f6' if v > 0 else '#334155' for v in mom_counts.values]
            bars2  = ax2.bar(T_ORDER, mom_counts.values, color=bar_c2,
                             alpha=0.85, width=0.6, zorder=3)
            for bar, val in zip(bars2, mom_counts.values):
                if val > 0:
                    ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                             str(int(val)), ha='center', va='bottom',
                             color='white', fontsize=9, fontweight='bold')
            ax2.set_ylim(0, mom_counts.max()+2 if mom_counts.max() > 0 else 3)
            ax2.set_ylabel("Nb d'évaluations", color='#94a3b8', fontsize=8.5)
            ax2.set_title('Distribution des moments utilisés', color='#e2e8f0',
                          fontsize=10, fontweight='bold', pad=10)
            for sp in ['top','right']: ax2.spines[sp].set_visible(False)
            for sp in ['bottom','left']: ax2.spines[sp].set_color('#334155')
            ax2.tick_params(colors='#94a3b8', labelsize=9)
            ax2.yaxis.grid(True, color='#334155', alpha=0.4, linewidth=0.5)
            ax2.set_axisbelow(True)
            plt.tight_layout()
            st.pyplot(fig2); plt.close()

        # Δ KCCQ entre T consécutifs
        st.markdown("""<div style="font-size:0.72rem;font-weight:700;color:#94a3b8;
            letter-spacing:1px;text-transform:uppercase;margin:20px 0 10px;">
            Δ KCCQ entre moments consécutifs — valeur ajoutée de chaque évaluation
            </div>""", unsafe_allow_html=True)
        t_means_r = {}
        for _t in T_ORDER:
            _vals = df_r[(df_r['t_code']==_t) & df_r['kccq'].notna()]['kccq'].tolist()
            if _vals: t_means_r[_t] = float(np.mean(_vals))
        t_pres = [t for t in T_ORDER if t in t_means_r]
        if len(t_pres) >= 2:
            d_cols = st.columns(len(t_pres)-1)
            for _i,(t1,t2) in enumerate(zip(t_pres[:-1], t_pres[1:])):
                _d = t_means_r[t2] - t_means_r[t1]
                _col = '#10b981' if _d > 0 else '#ef4444'
                _sgn = '+' if _d > 0 else ''
                with d_cols[_i]:
                    st.markdown(f"""
<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;
            padding:12px 8px;text-align:center;">
  <div style="font-size:0.62rem;color:#64748b;">{t1} → {t2}</div>
  <div style="font-size:1.4rem;font-weight:900;color:{_col};">{_sgn}{_d:.1f}</div>
  <div style="font-size:0.6rem;color:#94a3b8;">pts KCCQ</div>
</div>""", unsafe_allow_html=True)

    # Export CSV recherche
    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    _exp_rows = []
    for _pt in all_patients:
        for _ev in db_load_evaluations(_pt['id']):
            _exp_rows.append({
                'patient_id': _pt['id'], 'age': _pt['age'], 'sexe': _pt['sexe'],
                'statut': _ev.get('statut', _pt['statut']),
                'moment': _ev.get('moment','').split('—')[0].strip(),
                'date': _ev.get('date'),
                'kccq': _ev.get('kccq'), 'sf36_pcs': _ev.get('sf36_pcs'),
                'sf36_mcs': _ev.get('sf36_mcs'), 'minnesota': _ev.get('minnesota'),
                'eq5d': _ev.get('eq5d'), 'nyha': _ev.get('nyha'),
                '6mwt': _ev.get('6mwt'), 'bnp': _ev.get('bnp'), 'lvef': _ev.get('lvef'),
            })
    df_exp_all = pd.DataFrame(_exp_rows)
    csv_all = df_exp_all.to_csv(index=False) if not df_exp_all.empty else \
              "patient_id,age,sexe,statut,moment,date,kccq,sf36_pcs,sf36_mcs,minnesota,eq5d,nyha,6mwt,bnp,lvef\n"

    _ec1, _ec2 = st.columns([2.5, 1])
    with _ec1:
        st.markdown(f"""
<div style="background:#1e293b;border:1px solid #334155;border-radius:12px;padding:16px 20px;">
  <div style="font-size:0.78rem;font-weight:700;color:#e2e8f0;margin-bottom:4px;">
    📦 Export recherche — données anonymisées</div>
  <div style="font-size:0.72rem;color:#64748b;line-height:1.6;">
    {n_pts} patients · {n_evs} évaluations · patient_id pseudonyme · statut · moment T ·
    KCCQ · SF-36 · Minnesota · EQ-5D · 6MWT · BNP · LVEF<br>
    <span style="color:#475569;">Identité supprimée — Conforme RGPD</span>
  </div>
</div>""", unsafe_allow_html=True)
    with _ec2:
        from datetime import date as _date_cls
        st.download_button("📊 Export CSV recherche", csv_all,
            file_name=f"qol_cardiac_recherche_{_date_cls.today().isoformat()}.csv",
            mime="text/csv", use_container_width=True, type="primary")

# ─────────────────────────────────────────────
# PAGE RÉFÉRENCES
# ─────────────────────────────────────────────
elif st.session_state.page == "references":
    st.markdown("""
<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:20px;">
  <div style="background:#1e293b;border-radius:12px;padding:20px 16px;border:1px solid #334155;text-align:center;">
    <div style="font-size:2.2rem;font-weight:900;color:#60a5fa;line-height:1;">15</div>
    <div style="font-size:0.82rem;font-weight:600;color:#e2e8f0;margin-top:4px;">Études incluses</div>
    <div style="font-size:0.72rem;color:#64748b;">Sélection PRISMA</div>
  </div>
  <div style="background:#1e293b;border-radius:12px;padding:20px 16px;border:1px solid #334155;text-align:center;">
    <div style="font-size:2.2rem;font-weight:900;color:#34d399;line-height:1;">600</div>
    <div style="font-size:0.82rem;font-weight:600;color:#e2e8f0;margin-top:4px;">Patients</div>
    <div style="font-size:0.72rem;color:#64748b;">3 populations</div>
  </div>
  <div style="background:#1e293b;border-radius:12px;padding:20px 16px;border:1px solid #334155;text-align:center;">
    <div style="font-size:2.2rem;font-weight:900;color:#fbbf24;line-height:1;">4</div>
    <div style="font-size:0.82rem;font-weight:600;color:#e2e8f0;margin-top:4px;">Outils QdV</div>
    <div style="font-size:0.72rem;color:#64748b;">2000 – 2026</div>
  </div>
</div>

<div style="background:#1e293b;border-radius:12px;padding:18px 20px;border:1px solid #334155;border-left:4px solid #6366f1;margin-bottom:20px;">
  <div style="font-size:0.95rem;font-weight:700;color:#e2e8f0;margin-bottom:8px;">📋 Protocole PRISMA</div>
  <p style="color:#cbd5e1;margin:0 0 6px 0;font-size:0.85rem;">847 articles identifiés → <strong>15 études retenues</strong> après critères d'inclusion/exclusion.</p>
  <p style="color:#94a3b8;margin:0;font-size:0.82rem;">Période : 2000–2026 · 3 populations · 4 outils QdV · Niveau de preuve : méta-analyse</p>
</div>

<div style="font-size:1rem;font-weight:700;color:#f1f5f9;margin:0 0 14px 0;">Études incluses</div>

<div style="color:#ef4444;font-weight:600;font-size:0.85rem;margin-bottom:10px;">🔴 Population : Liste d'attente (5 études)</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:18px;">
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #ef4444;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Grady et al. (2004)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">Heart &amp; Lung</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Cohorte · n=134 · KCCQ 38.5 ± 18.4</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #ef4444;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Kugler et al. (2013)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">J Heart Lung Transplant</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Cohorte · n=89 · SF-36 PCS 30.2 ± 10.2</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #ef4444;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Spaderna et al. (2010)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">J Am Coll Cardiol</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Cohorte · n=182 · SF-36 MCS 42.1 ± 12.1</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #ef4444;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Goetzmann et al. (2012)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">Transplant Proc.</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Observationnelle · n=67 · KCCQ 41.2 ± 20.1</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #ef4444;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Petrucci et al. (2016)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">J Cardiovasc Nurs.</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Observationnelle · n=112 · SF-36 PCS 31.8 ± 9.8</div>
  </div>
</div>

<div style="color:#f59e0b;font-weight:600;font-size:0.85rem;margin-bottom:10px;">🟡 Population : LVAD (5 études)</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:18px;">
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #f59e0b;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Grady et al. (2015)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">J Cardiovasc Nurs.</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Cohorte · n=148 · KCCQ +18 pts à 12 mois</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #f59e0b;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Rogers et al. (2010)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">NEJM</div>
    <div style="color:#94a3b8;font-size:0.78rem;">RCT · n=134 · KCCQ HM-I vs HM-II</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #f59e0b;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Slaughter et al. (2009)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">NEJM (MOMENTUM)</div>
    <div style="color:#94a3b8;font-size:0.78rem;">RCT · n=134 · KCCQ +20 pts (HeartMate II)</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #f59e0b;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Cowger et al. (2017)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">Ann Thorac Surg.</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Registre INTERMACS · n=200 · Vie réelle</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #f59e0b;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Brouwers et al. (2011)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">Eur J Heart Fail</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Registre INTERMACS Europe · n=80</div>
  </div>
</div>

<div style="color:#10b981;font-weight:600;font-size:0.85rem;margin-bottom:10px;">🟢 Population : Post-greffe (5 études)</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:24px;">
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #10b981;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Kugler et al. (2010)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">J Heart Lung Transplant</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Cohorte · n=174 · SF-36 PCS 43.2 ± 10.8</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #10b981;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Lam et al. (2009)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">Circulation</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Registre · n=124 · KCCQ 67.4 ± 16.8</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #10b981;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Dew et al. (2005)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">Psychosom Med.</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Cohorte · n=174 · SF-36 MCS 51.2 ± 11.3</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #10b981;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Evangelista et al. (2014)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">J Heart Lung Transplant</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Observationnelle · n=98 · EQ-5D 0.78 ± 0.14</div>
  </div>
  <div style="background:#1e293b;border-radius:10px;padding:12px 14px;border:1px solid #334155;border-left:4px solid #10b981;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.85rem;">Flattery et al. (2006)</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin:2px 0;">Prog Cardiovasc Nurs.</div>
    <div style="color:#94a3b8;font-size:0.78rem;">Observationnelle · n=78 · Mn.LHFQ 22.3 ± 15.6</div>
  </div>
</div>

<div style="font-size:1rem;font-weight:700;color:#f1f5f9;margin:0 0 14px 0;">Outils QdV — Références de validation</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px;">
  <div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.9rem;margin-bottom:4px;">KCCQ</div>
    <div style="color:#94a3b8;font-size:0.82rem;margin-bottom:4px;">Kansas City Cardiomyopathy Questionnaire</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin-bottom:6px;">Green CP et al. J Am Coll Cardiol 2000;35:1245–1255</div>
    <div style="color:#cbd5e1;font-size:0.8rem;">Validé insuffisance cardiaque · 23 items · /100 · 5 min</div>
  </div>
  <div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.9rem;margin-bottom:4px;">SF-36</div>
    <div style="color:#94a3b8;font-size:0.82rem;margin-bottom:4px;">Short Form Health Survey</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin-bottom:6px;">Ware JE, Sherbourne CD. Med Care 1992;30:473–483</div>
    <div style="color:#cbd5e1;font-size:0.8rem;">Générique · 36 items · /100 · 10 min · norme population générale</div>
  </div>
  <div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.9rem;margin-bottom:4px;">Minnesota LHFQ</div>
    <div style="color:#94a3b8;font-size:0.82rem;margin-bottom:4px;">Living With Heart Failure Questionnaire</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin-bottom:6px;">Rector TS et al. Heart Fail 1987;1:198–209</div>
    <div style="color:#cbd5e1;font-size:0.8rem;">Spécifique IC · 21 items · /105 · 0 = meilleur · 5 min</div>
  </div>
  <div style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;">
    <div style="font-weight:700;color:#e2e8f0;font-size:0.9rem;margin-bottom:4px;">EQ-5D</div>
    <div style="color:#94a3b8;font-size:0.82rem;margin-bottom:4px;">EuroQol 5 Dimensions</div>
    <div style="color:#64748b;font-style:italic;font-size:0.78rem;margin-bottom:6px;">EuroQol Group. Health Policy 1990;16:199–208</div>
    <div style="color:#cbd5e1;font-size:0.8rem;">Médico-économique · 5 items · /1 · calcul QALYs · 2 min</div>
  </div>
</div>

<div style="background:#1e293b;border-radius:12px;padding:18px 20px;border:1px solid #334155;border-left:4px solid #3b82f6;">
  <div style="font-size:0.9rem;font-weight:700;color:#e2e8f0;margin-bottom:8px;">Citation de la méta-analyse</div>
  <p style="font-style:italic;color:#94a3b8;font-size:0.84rem;margin:0 0 8px 0;">
    TALL ML. Évaluation de la qualité de vie chez le patient cardiaque (liste d'attente, LVAD, post-greffe) :
    méta-analyse de 15 études, 600 patients. Journée Scientifique sur la Qualité de Vie en Transplantation Cardiaque.
    Hôpital Léon Bérard, Hyères, 19 juin 2026.
  </p>
  <p style="color:#475569;font-size:0.76rem;margin:0;">En collaboration avec Dr. Laurent Poirette (Cardiologie, Hôpital Léon Bérard) · MedFlow AI Research © 2026</p>
</div>
""", unsafe_allow_html=True)
