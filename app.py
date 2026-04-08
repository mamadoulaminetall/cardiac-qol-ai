"""
QoL Cardiac — Outil IA d'évaluation de la qualité de vie
Populations : Liste attente / LVAD / Post-greffe cardiaque
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats
import io
import os
from datetime import datetime

st.set_page_config(
    page_title="QoL Cardiac — MedFlow AI",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0f172a; }
[data-testid="stSidebar"] { background-color: #1e293b; }
[data-testid="stHeader"] { background-color: #0f172a; }
h1, h2, h3, h4 { color: #f1f5f9 !important; }
p, li, label { color: #cbd5e1 !important; }
.stSelectbox label, .stSlider label, .stNumberInput label { color: #94a3b8 !important; }
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
</style>
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
# SESSION STATE
# ─────────────────────────────────────────────
if "evaluations" not in st.session_state:
    st.session_state.evaluations = []
if "patient" not in st.session_state:
    st.session_state.patient = {}
if "page" not in st.session_state:
    st.session_state.page = "accueil"

# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🫀 QoL Cardiac")
    st.markdown("*Évaluation de la qualité de vie*")
    st.markdown("---")

    pages = {
        "🏠 Accueil": "accueil",
        "👤 Nouveau patient": "patient",
        "📋 Questionnaires": "questionnaires",
        "📊 Tableau de bord": "dashboard",
        "📄 Rapport PDF": "rapport",
    }

    for label, key in pages.items():
        active = st.session_state.page == key
        if st.button(label, use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state.page = key
            st.rerun()

    st.markdown("---")
    if st.session_state.patient:
        p = st.session_state.patient
        st.markdown(f"**Patient actif**")
        st.markdown(f"*{p.get('prenom', '')} {p.get('nom', '')}*")
        badge = {"Liste d'attente": "🔴", "LVAD": "🟡", "Post-greffe": "🟢"}
        st.markdown(f"{badge.get(p.get('statut',''), '')} {p.get('statut', '')}")

    st.markdown("---")
    st.caption("MedFlow AI Research © 2026")

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
    if st.button("👤 Commencer — Nouveau patient", type="primary", use_container_width=True):
        st.session_state.page = "patient"
        st.rerun()

# ─────────────────────────────────────────────
# PAGE NOUVEAU PATIENT
# ─────────────────────────────────────────────
elif st.session_state.page == "patient":
    st.markdown("# 👤 Nouveau patient")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Identité")
        prenom = st.text_input("Prénom", value=st.session_state.patient.get("prenom", ""))
        nom = st.text_input("Nom", value=st.session_state.patient.get("nom", ""))
        age = st.number_input("Âge (ans)", 18, 90, value=st.session_state.patient.get("age", 60))
        sexe = st.selectbox("Sexe", ["Homme", "Femme"],
                            index=0 if st.session_state.patient.get("sexe", "Homme") == "Homme" else 1)

    with col2:
        st.markdown("### Statut clinique")
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

        st.markdown("### Paramètres cliniques")
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
        st.session_state.patient = {
            "prenom": prenom, "nom": nom, "age": age, "sexe": sexe,
            "statut": statut, "moment": moment, "date": str(date_eval),
            "nyha": nyha, "nyha_idx": ["I","II","III","IV"].index(nyha),
            "6mwt": mwt6, "bnp": bnp, "lvef": lvef
        }
        st.success("Patient enregistré !")
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
    st.markdown(f"**Outils recommandés pour ce statut :** {' · '.join(outils)}")
    st.markdown("")

    scores = {}

    # ── KCCQ ──
    with st.expander("📊 KCCQ — Kansas City Cardiomyopathy Questionnaire (/100)", expanded=True):
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
    with st.expander("🏃 SF-36 — Short Form-36 (/100)", expanded=False):
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
    with st.expander("❤️ Minnesota LHFQ — Living with Heart Failure Questionnaire (/105)", expanded=False):
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
        st.markdown(f"**Score Minnesota : {scores['minnesota']}/105** — Percentile {pct}e pour {statut} *(0=meilleur)*")

    # ── EQ-5D ──
    with st.expander("🌡️ EQ-5D — EuroQol 5 Dimensions (/1)", expanded=False):
        st.caption("5 questions · 2 min · Score élevé = meilleure QdV")
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

    p = st.session_state.patient
    evals = st.session_state.evaluations
    last = evals[-1]
    statut = last["statut"]
    ref = REF[statut]

    st.markdown(f"# 📊 Tableau de bord — {p.get('prenom','')} {p.get('nom','')}")
    badge_html = f'<span class="{ref["badge"]}">{statut}</span>'
    st.markdown(f"Statut : {badge_html} &nbsp;|&nbsp; {last['moment']}", unsafe_allow_html=True)
    st.markdown("---")

    # ── ALERTES ──
    def check_alert(score, outil, higher_is_better=True):
        if len(evals) < 2:
            return None
        prev = evals[-2].get(outil)
        curr = evals[-1].get(outil)
        if prev is None or curr is None:
            return None
        delta = curr - prev if higher_is_better else prev - curr
        if delta < -10:
            return f"⚠️ Dégradation détectée sur {outil.upper()} : {prev:.0f} → {curr:.0f} (Δ {delta:+.0f})"
        return None

    alertes = [
        check_alert(last.get("kccq"), "kccq"),
        check_alert(last.get("sf36_pcs"), "sf36_pcs"),
        check_alert(last.get("minnesota"), "minnesota", higher_is_better=False),
    ]
    alertes = [a for a in alertes if a]

    if alertes:
        for a in alertes:
            st.markdown(f'<div class="alert-danger">{a}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert-success">✅ Aucune dégradation détectée</div>', unsafe_allow_html=True)

    st.markdown("---")

    # ── SCORES ACTUELS ──
    st.markdown("### Scores actuels vs cohorte de référence")
    col1, col2, col3, col4 = st.columns(4)

    def percentile_label(score, mean, sd, higher_is_better=True):
        pct = stats.norm.cdf(score, mean, sd) * 100
        if not higher_is_better:
            pct = 100 - pct
        return int(pct)

    with col1:
        kccq = last.get("kccq", 0)
        pct = percentile_label(kccq, *ref["kccq"])
        delta_color = "normal" if pct >= 50 else "inverse"
        st.metric("KCCQ", f"{kccq}/100", f"{pct}e percentile")

    with col2:
        pcs = last.get("sf36_pcs", 0)
        pct = percentile_label(pcs, *ref["sf36_pcs"])
        st.metric("SF-36 PCS", f"{pcs}/100", f"{pct}e percentile")

    with col3:
        minn = last.get("minnesota", 0)
        pct = percentile_label(minn, *ref["minnesota"], higher_is_better=False)
        st.metric("Minnesota", f"{minn}/105", f"{pct}e percentile ↓ mieux")

    with col4:
        eq = last.get("eq5d", 0)
        pct = percentile_label(eq, *ref["eq5d"])
        st.metric("EQ-5D", f"{eq:.2f}/1", f"{pct}e percentile")

    st.markdown("---")

    # ── GRAPHIQUES ──
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Profil QdV vs cohorte")
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor("#0f172a")
        ax.set_facecolor("#1e293b")

        outils_graph = ["KCCQ", "SF-36 PCS", "SF-36 MCS", "EQ-5D×100"]
        scores_patient = [
            last.get("kccq", 0),
            last.get("sf36_pcs", 0),
            last.get("sf36_mcs", 0),
            last.get("eq5d", 0) * 100
        ]
        ref_moyennes = [
            ref["kccq"][0],
            ref["sf36_pcs"][0],
            ref["sf36_mcs"][0],
            ref["eq5d"][0] * 100
        ]

        x = np.arange(len(outils_graph))
        w = 0.35
        ax.bar(x - w/2, ref_moyennes, w, label=f"Référence {statut}", color=ref["color"], alpha=0.5)
        ax.bar(x + w/2, scores_patient, w, label="Patient", color="#3b82f6", alpha=0.9)

        ax.set_xticks(x)
        ax.set_xticklabels(outils_graph, color="#94a3b8", fontsize=9)
        ax.tick_params(colors="#94a3b8")
        ax.set_ylabel("Score (/100)", color="#94a3b8")
        ax.legend(facecolor="#1e293b", labelcolor="white", fontsize=9)
        ax.spines[["top","right"]].set_visible(False)
        ax.spines[["bottom","left"]].set_color("#334155")
        ax.set_title("Patient vs cohorte de référence", color="white", fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col2:
        st.markdown("### Paramètres cliniques")
        fig, axes = plt.subplots(2, 2, figsize=(7, 4))
        fig.patch.set_facecolor("#0f172a")

        params = [
            ("BNP (pg/mL)", last.get("bnp", 0), ref["bnp"], False, "#ef4444"),
            ("6MWT (m)", last.get("6mwt", 0), ref["6mwt"], True, "#10b981"),
            ("LVEF (%)", last.get("lvef", 0), ref["lvef"], True, "#3b82f6"),
            ("NYHA", ["I","II","III","IV"].index(last.get("nyha","II"))+1, (2.5, 1), False, "#f59e0b"),
        ]

        for ax, (label, val, ref_vals, higher_better, color) in zip(axes.flat, params):
            ax.set_facecolor("#1e293b")
            ref_m, ref_sd = ref_vals
            ax.barh([0], [ref_m], color="#334155", height=0.4, label="Référence")
            ax.barh([0.5], [val], color=color, height=0.4, label="Patient", alpha=0.9)
            ax.set_yticks([0, 0.5])
            ax.set_yticklabels(["Réf.", "Patient"], color="#94a3b8", fontsize=8)
            ax.set_title(label, color="white", fontsize=9, fontweight="bold")
            ax.tick_params(colors="#94a3b8", labelsize=8)
            ax.spines[["top","right","left"]].set_visible(False)
            ax.spines["bottom"].set_color("#334155")

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # ── TRAJECTOIRE (si plusieurs évaluations) ──
    if len(evals) >= 2:
        st.markdown("---")
        st.markdown("### Trajectoire longitudinale")
        fig, ax = plt.subplots(figsize=(12, 4))
        fig.patch.set_facecolor("#0f172a")
        ax.set_facecolor("#1e293b")

        moments = [e["moment"].split("—")[0].strip() for e in evals]
        for outil, color, label in [
            ("kccq", "#3b82f6", "KCCQ"),
            ("sf36_pcs", "#10b981", "SF-36 PCS"),
        ]:
            vals = [e.get(outil, None) for e in evals]
            if any(v is not None for v in vals):
                ax.plot(range(len(evals)), vals, "o-", color=color, linewidth=2.5,
                        markersize=8, label=label)
                for i, v in enumerate(vals):
                    if v:
                        ax.annotate(f"{v:.0f}", (i, v), textcoords="offset points",
                                    xytext=(0, 10), ha="center", color=color, fontsize=9)

        ax.set_xticks(range(len(evals)))
        ax.set_xticklabels(moments, color="#94a3b8", fontsize=9, rotation=10)
        ax.tick_params(colors="#94a3b8")
        ax.set_ylabel("Score QdV", color="#94a3b8")
        ax.legend(facecolor="#1e293b", labelcolor="white", fontsize=9)
        ax.spines[["top","right"]].set_visible(False)
        ax.spines[["bottom","left"]].set_color("#334155")
        ax.set_title("Évolution QdV au fil des évaluations", color="white", fontsize=11)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

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

    # Génération du rapport texte
    kccq = last.get("kccq", 0)
    pcs  = last.get("sf36_pcs", 0)
    minn = last.get("minnesota", 0)
    eq   = last.get("eq5d", 0)

    pct_kccq = int(stats.norm.cdf(kccq, *ref["kccq"]) * 100)
    pct_pcs  = int(stats.norm.cdf(pcs,  *ref["sf36_pcs"]) * 100)
    pct_minn = int((1 - stats.norm.cdf(minn, *ref["minnesota"])) * 100)

    if kccq >= ref["kccq"][0]:
        interpret_kccq = "supérieur à la moyenne de sa population"
    else:
        interpret_kccq = "inférieur à la moyenne de sa population"

    rapport_text = f"""
RAPPORT D'ÉVALUATION DE LA QUALITÉ DE VIE
==========================================
Date : {last['date']}
Patient : {p.get('prenom','')} {p.get('nom','')} | {p.get('age','')} ans | {p.get('sexe','')}
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

==========================================
Généré par QoL Cardiac — MedFlow AI Research
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
