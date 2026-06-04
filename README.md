# 🫀 Cardiac QoL AI — Quality of Life Assessment Platform

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://cardiac-qol-ai.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

> **The only platform covering all 3 cardiac populations — waiting list, LVAD, and post-transplant — with real-time percentile comparison, automatic degradation alerts, and longitudinal T0→T5 tracking.**

---

## 🆚 Why Cardiac QoL AI is better

| Feature | Standard tools | **Cardiac QoL AI** |
|---------|---------------|-------------------|
| Questionnaire auto-selection by status | ❌ Manual | ✅ Automatic |
| Comparison to reference cohort | ❌ None | ✅ Percentile vs 600 patients |
| Automatic degradation alert | ❌ None | ✅ Alert if Δ > 10 points |
| 3 populations on one platform | ❌ Separate tools | ✅ Waiting list · LVAD · Post-transplant |
| Longitudinal trajectory T0→T5 | ❌ Static | ✅ Full timeline |
| Clinical PDF report | ❌ Manual | ✅ Auto-generated |
| Language | English only | ✅ French (for clinicians) |
| Cost | Paid / institutional | ✅ Free |

---

## 📊 Clinical Tools Included

| Tool | Full Name | Questions | Time | Score | Best for |
|------|-----------|-----------|------|-------|----------|
| **KCCQ** | Kansas City Cardiomyopathy Questionnaire | 23 | 5 min | /100 ↑ | All 3 populations |
| **SF-36** | Short Form-36 | 36 | 10 min | /100 ↑ | Post-transplant comparison |
| **Minnesota LHFQ** | Living with Heart Failure Questionnaire | 21 | 5 min | /105 ↓ | Waiting list · Post-transplant |
| **EQ-5D** | EuroQol 5 Dimensions | 5 | 2 min | /1 ↑ | Health economics (QALYs) |

---

## 🎯 3 Populations — Reference Values (meta-analysis, 600 patients, 15 studies)

| Parameter | Waiting list | LVAD | Post-transplant |
|-----------|------------|------|-----------------|
| KCCQ /100 | 40.1 ± 15.4 | 53.5 ± 19.8 | 66.7 ± 16.6 |
| SF-36 PCS /100 | 30.4 ± 9.9 | 37.4 ± 10.6 | 43.4 ± 11.2 |
| Minnesota /105 | 53.6 ± 17.8 | 37.6 ± 21.8 | 22.0 ± 15.1 |
| EQ-5D /1 | 0.54 ± 0.18 | 0.68 ± 0.21 | 0.80 ± 0.13 |
| BNP pg/mL | 824 ± 387 | 474 ± 276 | 196 ± 113 |
| 6MWT meters | 284 ± 85 | 332 ± 87 | 462 ± 104 |
| LVEF % | 24 ± 8 | 30 ± 10 | 58 ± 8 |

---

## ⏱️ 6 Key Assessment Timepoints

```
T0 — Listing          ← MANDATORY baseline (most important)
T1 — Before LVAD      ← Pre-implantation reference
T2 — 3 months LVAD    ← First QoL gain visible
T3 — Every 6 months   ← Detect degradation before BNP rises
T4 — 3 months post-Tx ← Early recovery
T5 — 1 year post-Tx   ← Stabilization (long-term reference)
```

**Practical rule:**
- 1 assessment only → **T0**
- 2 assessments → **T0 + T5**

---

## 🚀 Features

- **Auto-selects questionnaires** based on patient status
- **Real-time percentile** vs reference cohort (600 patients, 15 published studies) — `scipy.stats.norm.cdf`
- **MCID composite algorithm** — identifies the optimal assessment moment per population
- **Automatic degradation alert** if MCID threshold crossed (KCCQ ≥5 pts · SF-36 ≥3 pts · Minnesota ≤−5 pts · EQ-5D ≥0.05)
- **Longitudinal trajectory** T0→T5 across all evaluations
- **Clinical PDF report** auto-generated with ReportLab
- **100% in French** — designed for French-speaking clinicians

---

## 🧮 MCID Composite Algorithm (🔬 Analyse page)

Identifies the **optimal QoL assessment moment** per cardiac population using a composite responder score:

```
C = (1/n) × Σ rᵢ
rᵢ = % patients with |Δᵢ| ≥ MCIDᵢ at transition Tₐ → Tₐ₊₁
```

**Simulation results (n=60 patients per population):**

| Population | Optimal transition | C score | Clinical insight |
|---|---|---|---|
| 🔴 Waiting list | T0 → T3 | **C = 4%** | KCCQ −3.5 pts → early alert, clinical-only monitoring |
| 🟡 LVAD | T1 → T2 | **C = 95%** | KCCQ +14.2 · SF-36 +13.3 → peak at 3 months |
| 🟢 Post-transplant | T0 → T4 | **C = 88%** | SF-36 +26.4 · KCCQ +31.2 → peak at 3 months (9 months earlier than T5) |

Population sequences: Waiting list `T0→T3` · LVAD `T1→T2→T3` · Post-transplant `T0→T4→T5`

---

## 📱 Platform Pages

```
🏠 Accueil        — Overview & recommended tools by status
👤 Patient        — New patient profile (NYHA, BNP, LVEF, 6MWT)
🗂️ Patients       — Patient list & search
📋 Questionnaires — KCCQ · SF-36 · Minnesota · EQ-5D
📊 Tableau de bord — Scores · Percentiles · Alerts · Longitudinal charts
📄 Rapport        — Clinical PDF report + CSV export
🔬 Analyse        — MCID composite algorithm · KPI cards · Population comparison
📚 Références     — Meta-analysis references & MCID sources
```

---

## 🛠️ Installation

```bash
git clone https://github.com/mamadoulaminetall/cardiac-qol-ai.git
cd cardiac-qol-ai
pip install -r requirements.txt
streamlit run app.py
```

---

## 📚 Meta-analysis References

Studies included (PRISMA protocol, 2000–2026):

- Grady et al. *J Card Fail* 2004
- Slaughter et al. *NEJM* 2009 (MOMENTUM)
- Dew et al. *Am J Transplant* 2005
- Kugler et al. *Clin Transplant* 2010, 2013
- Cowger et al. *JACC Heart Fail* 2017
- Rogers et al. *Ann Thorac Surg* 2010
- Evangelista et al. *Heart* 2014
- *(+ 8 additional studies)*

---

## 👤 Author

**Dr. Mamadou Lamine TALL, PhD**
Bioinformatics · MedFlow AI Research

[![GitHub](https://img.shields.io/badge/GitHub-mamadoulaminetall-black)](https://github.com/mamadoulaminetall)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-MedFlow_AI-blue)](https://www.linkedin.com/in/medflow-ia-350531401/)

---

## 📅 Clinical Validation

Presented at the **Scientific Day on QoL in Cardiac Transplantation**
Hôpital Léon Bérard, Lyon — June 19, 2026
*In collaboration with Dr. Laurent Poirette (Cardiology)*

---

*© 2026 MedFlow AI Research — Free for clinical and research use*
