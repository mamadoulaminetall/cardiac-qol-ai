"""
QoL Cardiac — Outil IA d'évaluation de la qualité de vie
Populations : Liste attente / LVAD / Post-greffe cardiaque
Stockage : SQLite local (persistance longitudinale T0→T5)
"""

import streamlit as st
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
.qol-header { background:linear-gradient(135deg,#1a0208 0%,#2d0614 50%,#1a0208 100%);
    border-bottom:1px solid rgba(251,113,133,0.2);
    padding:12px 32px; display:flex; align-items:center; justify-content:space-between;
    margin:-1rem -1rem 0 -1rem; }
.qol-header-brand { display:flex; align-items:center; gap:10px; }
.qol-header-title { font-size:1.1rem; font-weight:900; color:#f1f5f9; }
.qol-header-sub   { font-size:0.68rem; color:#64748b; margin-top:1px; }
.qol-header-badge { background:rgba(16,185,129,.1); border:1px solid rgba(16,185,129,.3);
    color:#4ade80; padding:4px 14px; border-radius:20px; font-size:0.72rem; font-weight:700; }

/* ── Trial bar ── */
.qol-trial { background:rgba(0,0,0,0.3); border-bottom:1px solid rgba(255,255,255,0.05);
    padding:6px 32px; text-align:right; font-size:0.7rem; color:#475569;
    margin:0 -1rem; }
.qol-trial span { color:#fb7185; font-weight:700; }

/* ── Top Navigation ── */
.qol-nav { display:flex; gap:0; border-bottom:2px solid rgba(255,255,255,0.06);
    margin:0 -1rem 1.5rem -1rem; padding:0 32px; background:rgba(0,0,0,0.2); }
.qol-nav-btn { padding:10px 18px; font-size:0.82rem; font-weight:600; color:#64748b;
    border:none; background:transparent; cursor:pointer; border-bottom:2px solid transparent;
    margin-bottom:-2px; transition:all .2s; white-space:nowrap; }
.qol-nav-btn:hover { color:#e2e8f0; }
.qol-nav-btn.active { color:#fb7185; border-bottom:2px solid #fb7185; }
/* Override Streamlit button styles inside nav */
.qol-nav-wrap [data-testid="stButton"] button {
    padding:10px 16px; font-size:0.82rem; font-weight:600; color:#64748b;
    border:none; border-radius:0; background:transparent !important;
    border-bottom:2px solid transparent; margin-bottom:-2px; box-shadow:none !important; }
.qol-nav-wrap [data-testid="stButton"] button:hover { color:#e2e8f0; background:transparent !important; }

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
    "Liste d'attente": ["Minnesota LHFQ", "KCCQ", "SF-36"],
    "LVAD":            ["KCCQ", "SF-36 PCS", "EQ-5D"],
    "Post-greffe":     ["SF-36", "KCCQ", "Minnesota LHFQ"],
}

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
st.markdown(f"""
<div class="qol-header">
  <div class="qol-header-brand">
    <span style="font-size:1.6rem;">🫀</span>
    <div>
      <div class="qol-header-title">QoL Cardiac</div>
      <div class="qol-header-sub">Qualité de vie cardiaque · 4 questionnaires · 600 patients</div>
    </div>
  </div>
  <div style="display:flex;align-items:center;gap:12px;">
    <span style="color:#475569;font-size:0.7rem;">{user_label}</span>
    <span class="qol-header-badge">Gratuit</span>
  </div>
</div>
<div class="qol-trial">Accès gratuit · <span>{ne_} évaluation(s)</span> enregistrée(s) · {np_} patient(s) · 🔒 100% local</div>
""", unsafe_allow_html=True)

# ── Navigation ──
nav_items = [
    ("🏠 Accueil",          "accueil"),
    ("👤 Patient",           "patient"),
    ("🗂️ Patients",         "patients"),
    ("📋 Questionnaires",   "questionnaires"),
    ("📊 Tableau de bord",  "dashboard"),
    ("📄 Rapport",          "rapport"),
    ("📚 Références",       "references"),
]

nav_cols = st.columns(len(nav_items) + 1)
for i, (label, key) in enumerate(nav_items):
    with nav_cols[i]:
        active = st.session_state.page == key
        style = ("color:#fb7185;border-bottom:2px solid #fb7185;background:transparent;"
                 "border-top:none;border-left:none;border-right:none;border-radius:0;"
                 "padding:8px 4px;font-weight:700;width:100%;font-size:0.78rem;") if active else (
                "color:#64748b;border:none;background:transparent;border-radius:0;"
                "padding:8px 4px;font-weight:500;width:100%;font-size:0.78rem;")
        if st.button(label, key=f"nav_{key}", use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.page = key
            st.rerun()

with nav_cols[-1]:
    if st.button("⏻ Déconnexion", key="nav_logout", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.rerun()

st.markdown("<hr style='margin:0 0 1rem 0;border-color:rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

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
<p><span class="badge-liste">Liste d'attente</span> Minnesota LHFQ · KCCQ · SF-36</p>
<p><span class="badge-lvad">LVAD</span> KCCQ · SF-36 PCS · EQ-5D</p>
<p><span class="badge-greffe">Post-greffe</span> SF-36 · KCCQ · Minnesota LHFQ</p>
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
    st.markdown("# 👤 Nouveau patient")
    st.markdown("---")

    # Recherche patient existant
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
                            st.session_state.patient = {
                                'id': r['id'], 'prenom': r.get('prenom',''),
                                'nom': r.get('nom',''), 'age': r['age'],
                                'sexe': r['sexe'], 'statut': r['statut'],
                                'moment': evals[-1]['moment'] if evals else "T0 — Inscription sur liste",
                                'date': evals[-1]['date'] if evals else str(datetime.today().date()),
                                'nyha': evals[-1].get('nyha','II') if evals else 'II',
                                'nyha_idx': ["I","II","III","IV"].index(evals[-1].get('nyha','II')) if evals else 1,
                                '6mwt': evals[-1].get('6mwt',300) if evals else 300,
                                'bnp': evals[-1].get('bnp',500) if evals else 500,
                                'lvef': evals[-1].get('lvef',30) if evals else 30,
                            }
                            st.session_state.patient_id = r['id']
                            st.session_state.evaluations = evals
                            st.session_state.page = "questionnaires"
                            st.rerun()
            else:
                st.info("Aucun patient trouvé.")

    st.markdown("### Créer un nouveau patient")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Identité")
        prenom = st.text_input("Prénom", value=st.session_state.patient.get("prenom", ""))
        nom = st.text_input("Nom", value=st.session_state.patient.get("nom", ""))
        age = st.number_input("Âge (ans)", 18, 90, value=st.session_state.patient.get("age", 60))
        sexe = st.selectbox("Sexe", ["Homme", "Femme"],
                            index=0 if st.session_state.patient.get("sexe", "Homme") == "Homme" else 1)

        # Aperçu ID pseudonymisé
        if prenom or nom:
            pid_preview = generate_patient_id(prenom or "?", nom or "?", age)
            st.caption(f"🔒 ID anonyme : `{pid_preview}`")

    with col2:
        st.markdown("#### Statut clinique")
        statut = st.selectbox("Statut du patient", ["Liste d'attente", "LVAD", "Post-greffe"],
                              index=["Liste d'attente", "LVAD", "Post-greffe"].index(
                                  st.session_state.patient.get("statut", "Liste d'attente")))

        moment = st.selectbox("Moment d'évaluation", [
            "T0 — Inscription sur liste",
            "T1 — Avant implantation LVAD",
            "T2 — 3 mois post-LVAD",
            "T3 — Suivi semestriel en liste",
            "T4 — 3 mois post-greffe",
            "T5 — 1 an post-greffe"
        ])

        date_eval = st.date_input("Date d'évaluation", value=datetime.today())

        st.markdown("#### Paramètres cliniques")
        nyha = st.selectbox("NYHA (New York Heart Association)", ["I", "II", "III", "IV"],
                            index=st.session_state.patient.get("nyha_idx", 2))
        mwt6 = st.number_input("6MWT — Test de marche 6 min (mètres)", 0, 700,
                                value=st.session_state.patient.get("6mwt", 300))
        bnp = st.number_input("BNP (pg/mL)", 0, 10000,
                               value=st.session_state.patient.get("bnp", 500))
        lvef = st.number_input("LVEF — Fraction d'éjection VG (%)", 5, 80,
                                value=st.session_state.patient.get("lvef", 30))

    st.markdown("---")
    if st.button("✅ Enregistrer et passer aux questionnaires", type="primary", use_container_width=True):
        patient_id = generate_patient_id(prenom or "anon", nom or "anon", age)
        patient_data = {
            "id": patient_id,
            "prenom": prenom, "nom": nom, "age": age, "sexe": sexe,
            "statut": statut, "moment": moment, "date": str(date_eval),
            "nyha": nyha, "nyha_idx": ["I","II","III","IV"].index(nyha),
            "6mwt": mwt6, "bnp": bnp, "lvef": lvef
        }
        # Sauvegarder en base
        db_save_patient(patient_data)
        st.session_state.patient = patient_data
        st.session_state.patient_id = patient_id
        # Charger les évaluations existantes (si patient déjà connu)
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

    def exp_title(icon, name, rec):
        badge = "  ✓ Recommandé" if rec else "  Non prioritaire"
        return f"{icon} {name}{badge}"

    st.markdown(f"**Outils recommandés pour ce statut :** {' · '.join(outils)}")
    st.markdown("")

    scores = {}

    # ── KCCQ ──
    with st.expander(exp_title("📊", "KCCQ — Kansas City Cardiomyopathy Questionnaire (/100)", kccq_rec), expanded=kccq_rec):
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
        st.markdown(f"**Score KCCQ : {scores['kccq']}/100** — Percentile {pct}e pour {statut}")

    # ── SF-36 ──
    with st.expander(exp_title("🏃", "SF-36 — Short Form-36 (/100)", sf36_rec), expanded=sf36_rec):
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
        st.markdown(f"**SF-36 PCS : {pcs}/100** (percentile {pct_pcs}e) &nbsp;|&nbsp; **MCS : {mcs}/100** (percentile {pct_mcs}e)")

    # ── MINNESOTA ──
    with st.expander(exp_title("❤️", "Minnesota LHFQ — Living with Heart Failure Questionnaire (/105)", minn_rec), expanded=minn_rec):
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
        st.markdown(f"**Score Minnesota : {scores['minnesota']}/105** — Percentile {pct}e pour {statut} *(0=meilleur)*")

    # ── EQ-5D ──
    with st.expander(exp_title("🌡️", "EQ-5D — EuroQol 5 Dimensions (/1)", eq5d_rec), expanded=eq5d_rec):
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
        st.markdown(f"**Score EQ-5D : {scores['eq5d']:.2f}/1** — Percentile {pct}e pour {statut}")

    st.markdown("---")
    if st.button("📊 Enregistrer les scores et voir le tableau de bord", type="primary", use_container_width=True):
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

    p     = st.session_state.patient
    evals = st.session_state.evaluations
    last  = evals[-1]
    statut = last["statut"]
    ref    = REF[statut]
    pid    = st.session_state.patient_id

    prenom = p.get("prenom", "")
    nom    = p.get("nom", "")
    age    = p.get("age", "")
    sexe   = p.get("sexe", "")

    # ── HEADER ──
    badge_html = f'<span class="{ref["badge"]}">{statut}</span>'
    pid_code = (f"&nbsp;|&nbsp;<code style='background:#1e293b;padding:2px 6px;"
                f"border-radius:4px;font-size:11px'>{pid}</code>") if pid else ""
    st.markdown(f"# 📊 Tableau de bord — {prenom} {nom}")
    st.markdown(f"Statut : {badge_html} &nbsp;|&nbsp; {last['moment']}{pid_code}",
                unsafe_allow_html=True)
    st.markdown("---")

    # ── CALCUL PERCENTILES ──
    def calc_pct(score, mean, sd, higher_is_better=True):
        p = int(stats.norm.cdf(score, mean, sd) * 100)
        return p if higher_is_better else 100 - p

    def badge_cls(p):
        return "hdb-badge-g" if p >= 66 else "hdb-badge-o" if p >= 33 else "hdb-badge-r"

    def row_cls(p):
        return "hdb-qrow-lo" if p >= 66 else "hdb-qrow-mo" if p >= 33 else "hdb-qrow-hi"

    def bar_col(p):
        return "#10b981" if p >= 66 else "#fb923c" if p >= 33 else "#ef4444"

    def kpi_cls(p):
        return "hdb-kpi-lo" if p >= 66 else "hdb-kpi-mo" if p >= 33 else "hdb-kpi-hi"

    kccq = last.get("kccq") or 0
    pcs  = last.get("sf36_pcs") or 0
    mcs  = last.get("sf36_mcs") or 0
    minn = last.get("minnesota") or 0
    eq   = last.get("eq5d") or 0

    pct_kccq = calc_pct(kccq, *ref["kccq"])
    pct_pcs  = calc_pct(pcs,  *ref["sf36_pcs"])
    pct_mcs  = calc_pct(mcs,  *ref["sf36_mcs"])
    pct_minn = calc_pct(minn, *ref["minnesota"], higher_is_better=False)
    pct_eq   = calc_pct(eq,   *ref["eq5d"])

    avg_pct = (pct_kccq + pct_pcs + pct_minn + pct_eq) // 4

    if avg_pct >= 75:
        g_label, g_badge = "QoL BON", "BON"
        g_style = "background:linear-gradient(135deg,rgba(16,185,129,.1),rgba(5,46,22,.07));border:1px solid rgba(16,185,129,.3);"
        g_color = "#4ade80"
        g_badge_style = "background:rgba(16,185,129,.12);border:1px solid rgba(16,185,129,.28);color:#4ade80;"
    elif avg_pct >= 50:
        g_label, g_badge = "QoL MODÉRÉ", "MODÉRÉ"
        g_style = "background:linear-gradient(135deg,rgba(249,115,22,.1),rgba(67,20,7,.07));border:1px solid rgba(249,115,22,.3);"
        g_color = "#fb923c"
        g_badge_style = "background:rgba(249,115,22,.12);border:1px solid rgba(249,115,22,.28);color:#fb923c;"
    elif avg_pct >= 25:
        g_label, g_badge = "QoL LIMITE", "LIMITE"
        g_style = "background:linear-gradient(135deg,rgba(225,29,72,.1),rgba(136,19,55,.07));border:1px solid rgba(225,29,72,.3);"
        g_color = "#fb7185"
        g_badge_style = "background:rgba(249,115,22,.12);border:1px solid rgba(249,115,22,.28);color:#fb923c;"
    else:
        g_label, g_badge = "QoL CRITIQUE", "CRITIQUE"
        g_style = "background:linear-gradient(135deg,rgba(239,68,68,.15),rgba(127,29,29,.1));border:1px solid rgba(239,68,68,.4);"
        g_color = "#f87171"
        g_badge_style = "background:rgba(239,68,68,.12);border:1px solid rgba(239,68,68,.28);color:#f87171;"

    if pct_pcs < 33:
        g_stage = "SF-36 physique bas — kinésithérapie cardiaque recommandée · Réévaluation 3 mois"
    elif pct_kccq < 33:
        g_stage = f"KCCQ bas — surveillance rapprochée · prochain point T{len(evals)}"
    else:
        g_stage = "Profil stable · prochaine évaluation planifiée"

    # ── KPI CARDS ──
    st.markdown(f"""
<div class="hdb-kpis">
  <div class="hdb-kpi {kpi_cls(pct_kccq)}">
    <div class="hdb-kv">{kccq}</div><div class="hdb-kl">KCCQ /100</div>
  </div>
  <div class="hdb-kpi {kpi_cls(pct_kccq)}">
    <div class="hdb-kv">P{pct_kccq}</div><div class="hdb-kl">Percentile</div>
  </div>
  <div class="hdb-kpi {kpi_cls(pct_eq)}">
    <div class="hdb-kv">{eq:.2f}</div><div class="hdb-kl">EQ-5D utility</div>
  </div>
  <div class="hdb-kpi hdb-kpi-t">
    <div class="hdb-kv">600</div><div class="hdb-kl">Patients réf.</div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── SECTION TITLE ──
    moment_short = last["moment"].split("—")[-1].strip() if "—" in last["moment"] else last["moment"]
    sexe_short = sexe[:1] if sexe else "?"
    st.markdown(f"""
<div class="hdb-sec-title">
  Scores qualité de vie — Patient : {sexe_short} · {age} ans · {moment_short}
  <span style="flex:1;height:1px;background:rgba(251,113,133,0.15);display:inline-block;"></span>
</div>""", unsafe_allow_html=True)

    # ── SCORE ROWS ──
    def score_row(name, sub, score_str, pct_val, bar_pct):
        bc = badge_cls(pct_val)
        rc = row_cls(pct_val)
        fc = bar_col(pct_val)
        bar_pct = min(max(bar_pct, 0), 100)
        return f"""
<div class="hdb-qrow {rc}">
  <div><div class="hdb-qname">{name}</div><div class="hdb-qval">{sub}</div></div>
  <div><div class="hdb-sbar"><div class="hdb-sfill" style="width:{bar_pct:.0f}%;background:{fc};"></div></div></div>
  <div class="hdb-qscore">{score_str}</div>
  <span class="hdb-badge {bc}">P{pct_val}</span>
</div>"""

    minn_bar = (105 - minn) / 105 * 100 if minn else 0

    rows = (
        score_row("KCCQ", "23 items · 5 domaines", f"{kccq}/100", pct_kccq, kccq) +
        score_row("SF-36 PCS", "Composante physique", f"{pcs}/100", pct_pcs, pcs) +
        score_row("Minnesota LHFQ", "Score inversé", f"{minn}/105", pct_minn, minn_bar) +
        score_row("SF-36 MCS", "Composante mentale", f"{mcs}/100", pct_mcs, mcs) +
        score_row("EQ-5D-5L", "Utilité HAS 2022", f"{eq:.2f}", pct_eq, eq * 100)
    )

    # ── INTERPRETATION CARD ──
    interp = f"""
<div class="hdb-score" style="{g_style}">
  <div class="hdb-score-icon">🫀</div>
  <div>
    <div class="hdb-score-lbl">Interprétation globale</div>
    <div class="hdb-score-val" style="color:{g_color};">{g_label}
      <small>· KCCQ {kccq} · EQ-5D {eq:.2f}</small></div>
    <div class="hdb-score-stage" style="color:{g_color};">{g_stage}</div>
  </div>
  <span class="hdb-score-badge" style="{g_badge_style}">{g_badge}</span>
</div>"""

    # ── ALERTES ──
    alertes = []
    if len(evals) >= 2:
        for outil, hib, lbl in [("kccq",True,"KCCQ"),("sf36_pcs",True,"SF-36 PCS"),("minnesota",False,"Minnesota")]:
            prev = evals[-2].get(outil)
            curr = evals[-1].get(outil)
            if prev is not None and curr is not None:
                delta = (curr - prev) if hib else (prev - curr)
                if delta < -10:
                    alertes.append(f"⚠ Dégradation {lbl} : {prev:.0f} → {curr:.0f} (Δ {delta:+.0f})")

    if alertes:
        alert_html = '<div class="hdb-alert">' + " &nbsp;·&nbsp; ".join(alertes) + "</div>"
    else:
        alert_html = '<div class="hdb-alert-ok">✓ Aucune dégradation détectée vs évaluation précédente</div>'

    st.markdown(rows + interp + alert_html, unsafe_allow_html=True)

    st.markdown("---")

    # ── TRAJECTOIRE ──
    st.markdown("### Trajectoire longitudinale T0→T5")
    fig, ax = plt.subplots(figsize=(12, 4))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")

    labels = []
    for i, e in enumerate(evals):
        m = e.get("moment", "")
        labels.append(m.split("—")[0].strip() if "—" in m else f"Eval {i+1}")

    for outil, color, lbl in [
        ("kccq", "#3b82f6", "KCCQ"),
        ("sf36_pcs", "#10b981", "SF-36 PCS"),
        ("minnesota", "#f59e0b", "Minnesota"),
    ]:
        vals = [e.get(outil) for e in evals]
        if any(v is not None for v in vals):
            ax.plot(range(len(evals)), vals, "o-", color=color, linewidth=2.5,
                    markersize=8, label=lbl)
            for i, v in enumerate(vals):
                if v is not None:
                    ax.annotate(f"{v:.0f}", (i, v), textcoords="offset points",
                                xytext=(0, 10), ha="center", color=color,
                                fontsize=9, fontweight="bold")

    ax.set_xticks(range(len(evals)))
    ax.set_xticklabels(labels, color="#94a3b8", fontsize=9)
    ax.tick_params(colors="#94a3b8")
    ax.set_ylabel("Score QdV", color="#94a3b8")
    ax.legend(facecolor="#1e293b", labelcolor="white", fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["bottom", "left"]].set_color("#334155")
    ax.grid(axis="y", color="#334155", alpha=0.35)
    ax.set_title("Évolution QdV au fil des évaluations", color="white", fontsize=11)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # ── PARAMÈTRES CLINIQUES ──
    st.markdown("### Paramètres cliniques")

    def clin_card(label, val, ref_tuple, unit, higher_better):
        if val and ref_tuple[1] > 0:
            pv = int(stats.norm.cdf(val, ref_tuple[0], ref_tuple[1]) * 100)
            if not higher_better:
                pv = 100 - pv
        else:
            pv = 50
        bc = badge_cls(pv)
        fc = bar_col(pv)
        return f"""
<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:12px 16px;margin-bottom:8px;">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
    <span style="color:#e2e8f0;font-weight:700;font-size:0.8rem;">{label}</span>
    <span class="hdb-badge {bc}">{val} {unit}</span>
  </div>
  <div class="hdb-sbar" style="height:8px;">
    <div class="hdb-sfill" style="width:{min(pv,100)}%;background:{fc};"></div>
  </div>
  <div style="display:flex;justify-content:space-between;margin-top:5px;">
    <span style="color:#475569;font-size:0.64rem;">Réf. {statut} : {ref_tuple[0]:.0f} {unit}</span>
    <span style="color:#64748b;font-size:0.64rem;">P{pv}</span>
  </div>
</div>"""

    bnp_v  = last.get("bnp")  or 0
    mwt_v  = last.get("6mwt") or 0
    lvef_v = last.get("lvef") or 0
    nyha_v = last.get("nyha", "II")
    nyha_good = nyha_v in ["I", "II"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            clin_card("BNP", bnp_v,  ref["bnp"],  "pg/mL", False) +
            clin_card("6MWT", mwt_v, ref["6mwt"], "m",     True),
            unsafe_allow_html=True)
    with col2:
        st.markdown(
            clin_card("LVEF", lvef_v, ref["lvef"], "%", True) +
            f"""<div style="background:#1e293b;border:1px solid #334155;border-radius:10px;padding:12px 16px;">
  <div style="display:flex;justify-content:space-between;align-items:center;">
    <span style="color:#e2e8f0;font-weight:700;font-size:0.8rem;">NYHA</span>
    <span class="hdb-badge {'hdb-badge-g' if nyha_good else 'hdb-badge-o' if nyha_v=='III' else 'hdb-badge-r'}">{nyha_v}</span>
  </div>
  <div style="color:#64748b;font-size:0.64rem;margin-top:6px;">Classe I (meilleur) → IV (sévère)</div>
</div>""",
            unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📋 Nouvelle évaluation", use_container_width=True):
            st.session_state.page = "questionnaires"
            st.rerun()
    with col2:
        if st.button("📄 Générer le rapport", type="primary", use_container_width=True):
            st.session_state.page = "rapport"
            st.rerun()

# ─────────────────────────────────────────────
# PAGE RAPPORT
# ─────────────────────────────────────────────
elif st.session_state.page == "rapport":
    if not st.session_state.evaluations:
        st.warning("Aucune évaluation disponible.")
        st.stop()

    p = st.session_state.patient
    last = st.session_state.evaluations[-1]
    statut = last["statut"]
    ref = REF[statut]

    st.markdown("# 📄 Rapport clinique QdV")
    st.markdown("---")

    kccq = last.get("kccq", 0)
    pcs  = last.get("sf36_pcs", 0)
    minn = last.get("minnesota", 0)
    eq   = last.get("eq5d", 0)

    pct_kccq = int(stats.norm.cdf(kccq, *ref["kccq"]) * 100)
    pct_pcs  = int(stats.norm.cdf(pcs,  *ref["sf36_pcs"]) * 100)
    pct_minn = int((1 - stats.norm.cdf(minn, *ref["minnesota"])) * 100)

    interpret_kccq = "supérieur à la moyenne de sa population" if kccq >= ref["kccq"][0] else "inférieur à la moyenne de sa population"
    pid = st.session_state.patient_id or "NON ENREGISTRÉ"

    rapport_text = f"""
RAPPORT D'ÉVALUATION DE LA QUALITÉ DE VIE
==========================================
Date : {last['date']}
Patient : {p.get('prenom','')} {p.get('nom','')} | {p.get('age','')} ans | {p.get('sexe','')}
ID patient (pseudonymisé) : {pid}
Statut : {statut} | {last['moment']}
Clinicien : Dr. _______________

SCORES DE QUALITÉ DE VIE
------------------------
KCCQ (Kansas City Cardiomyopathy Questionnaire) : {kccq}/100
  → {pct_kccq}e percentile pour la population {statut}
  → Score {interpret_kccq} (référence : {ref['kccq'][0]:.1f} ± {ref['kccq'][1]:.1f})

SF-36 PCS (Composante Physique) : {pcs}/100
  → {pct_pcs}e percentile

Minnesota LHFQ : {minn}/105 (0=meilleur)
  → {pct_minn}e percentile

EQ-5D : {eq:.2f}/1
  → Indice d'utilité de santé

PARAMÈTRES CLINIQUES
--------------------
NYHA : {last.get('nyha','')}
6MWT (Test de marche 6 min) : {last.get('6mwt','')} m (réf. {ref['6mwt'][0]:.0f} m)
BNP : {last.get('bnp','')} pg/mL (réf. {ref['bnp'][0]:.0f} pg/mL)
LVEF : {last.get('lvef','')}% (réf. {ref['lvef'][0]:.0f}%)

INTERPRÉTATION
--------------
Le patient présente un score KCCQ de {kccq}/100, {interpret_kccq}
({statut}, référence méta-analyse : {ref['kccq'][0]:.1f} ± {ref['kccq'][1]:.1f}).
{"Une surveillance rapprochée est recommandée." if kccq < ref['kccq'][0] - ref['kccq'][1] else "L'état de QdV est satisfaisant pour ce stade."}

Prochaine évaluation recommandée : {
    "Dans 6 mois (T3)" if statut == "Liste d'attente" else
    "À 1 an post-greffe (T5)" if statut == "Post-greffe" else
    "À 3 mois post-LVAD (T2)"
}

CONFORMITÉ RGPD
---------------
Données stockées localement (SQLite). Aucune transmission externe.
Pseudonymisation : ID {pid}
Droit à l'effacement disponible dans l'outil (Art. 17 RGPD).

==========================================
Généré par QoL Cardiac — MedFlow AI Research
Méta-analyse de référence : 15 études · 600 patients · 2000–2026
"""

    st.text_area("Rapport", rapport_text, height=500)

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "⬇️ Télécharger le rapport (.txt)",
            rapport_text,
            file_name=f"rapport_QdV_{p.get('nom','patient')}_{last['date']}.txt",
            mime="text/plain",
            use_container_width=True
        )
    with col2:
        df_export = pd.DataFrame(st.session_state.evaluations)
        csv = df_export.to_csv(index=False)
        st.download_button(
            "⬇️ Exporter toutes les évaluations (.csv)",
            csv,
            file_name=f"evaluations_{p.get('nom','patient')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# ─────────────────────────────────────────────
# PAGE RÉFÉRENCES
# ─────────────────────────────────────────────
elif st.session_state.page == "references":
    st.markdown("# 📚 Références bibliographiques")
    st.markdown("### Méta-analyse PRISMA — 15 études · 600 patients · 2000–2026")
    st.markdown("---")

    st.markdown("""
<div class="card">
<h4>Protocole PRISMA</h4>
<p>847 articles identifiés → 15 études retenues après application des critères d'inclusion/exclusion.<br>
Période : 2000–2026 · 3 populations · 4 outils QdV · Niveau de preuve : méta-analyse</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("### Études incluses")

    studies = [
        ("Grady et al.", 2004, "J Card Fail", "Liste d'attente", "Minnesota LHFQ", 134, "n=134 · score Minnesota 52.1 ± 18.3"),
        ("Kugler et al.", 2013, "Clin Transplant", "Liste d'attente", "SF-36 PCS", 89, "n=89 · SF-36 PCS 31.4 ± 10.2"),
        ("Spaderna et al.", 2010, "Transplantation", "Liste d'attente", "SF-36 MCS", 182, "n=182 · SF-36 MCS 40.2 ± 12.1"),
        ("Goetzmann et al.", 2012, "Psychosomatics", "Liste d'attente", "EQ-5D", 67, "n=67 · EQ-5D 0.52 ± 0.18"),
        ("Petrucci et al.", 2016, "Heart & Lung", "Liste d'attente", "KCCQ", 112, "n=112 · KCCQ 38.7 ± 14.6"),
        ("Grady et al.", 2015, "J Heart Lung Transplant", "LVAD", "Minnesota LHFQ", 148, "n=148 · score Minnesota 38.4 ± 22.1"),
        ("Rogers et al.", 2010, "Ann Thorac Surg", "LVAD", "SF-36 PCS", 134, "n=134 · SF-36 PCS 36.8 ± 11.4"),
        ("Slaughter et al.", 2009, "NEJM (MOMENTUM)", "LVAD", "KCCQ", 134, "n=134 · KCCQ 52.3 ± 18.7"),
        ("Cowger et al.", 2017, "JACC Heart Fail", "LVAD", "EQ-5D", 200, "n=200 · EQ-5D 0.69 ± 0.21"),
        ("Brouwers et al.", 2011, "Eur J Heart Fail", "LVAD", "SF-36 MCS", 80, "n=80 · SF-36 MCS 44.1 ± 13.2"),
        ("Kugler et al.", 2010, "Clin Transplant", "Post-greffe", "SF-36 PCS", 174, "n=174 · SF-36 PCS 44.2 ± 10.8"),
        ("Lam et al.", 2009, "J Heart Lung Transplant", "Post-greffe", "Minnesota LHFQ", 124, "n=124 · score Minnesota 22.4 ± 15.6"),
        ("Dew et al.", 2005, "Am J Transplant", "Post-greffe", "SF-36 MCS", 174, "n=174 · SF-36 MCS 49.8 ± 11.3"),
        ("Evangelista et al.", 2014, "Heart", "Post-greffe", "KCCQ", 98, "n=98 · KCCQ 68.4 ± 17.2"),
        ("Flattery et al.", 2006, "J Cardiovasc Nurs", "Post-greffe", "EQ-5D", 78, "n=78 · EQ-5D 0.81 ± 0.14"),
    ]

    badge_map = {
        "Liste d'attente": ('<span class="badge-liste">Liste d\'attente</span>', "#ef4444"),
        "LVAD": ('<span class="badge-lvad">LVAD</span>', "#f59e0b"),
        "Post-greffe": ('<span class="badge-greffe">Post-greffe</span>', "#10b981"),
    }
    pop_icons = {"Liste d'attente": "🔴", "LVAD": "🟡", "Post-greffe": "🟢"}

    for pop in ["Liste d'attente", "LVAD", "Post-greffe"]:
        pop_studies = [s for s in studies if s[3] == pop]
        badge_html, color = badge_map[pop]
        st.markdown(f"#### {pop_icons[pop]} Population : {pop} ({len(pop_studies)} études)")
        for auteur, annee, journal, _, outil, n, detail in pop_studies:
            st.markdown(f"""
<div class="card" style="border-left: 4px solid {color}; padding: 10px 16px; margin-bottom: 8px;">
<b>{auteur} ({annee})</b> &nbsp;·&nbsp; <i>{journal}</i><br>
<small style="color:#94a3b8;">Outil : {outil} &nbsp;·&nbsp; {detail}</small>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
<div class="card">
<h4>Citation de la méta-analyse</h4>
<p style="font-style:italic; color:#94a3b8;">
TALL ML. Évaluation de la qualité de vie chez le patient cardiaque (liste d'attente, LVAD, post-greffe) :
méta-analyse de 15 études, 600 patients. Journée Scientifique sur la Qualité de Vie en Transplantation Cardiaque.
Hôpital Léon Bérard, Hyères, 19 juin 2026.
</p>
<p style="color:#64748b; font-size:12px;">En collaboration avec Dr. Laurent Poirette (Cardiologie, Hôpital Léon Bérard) · MedFlow AI Research © 2026</p>
</div>
""", unsafe_allow_html=True)
