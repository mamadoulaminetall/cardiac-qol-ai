# 🫀 QoL Cardiac AI — Plateforme QdV en Insuffisance Cardiaque Avancée

[![Streamlit App](https://img.shields.io/badge/Streamlit-cardiac--qol--ai-FF4B4B?logo=streamlit&logoColor=white)](https://cardiac-qol-ai.streamlit.app)
[![MedFlow AI](https://img.shields.io/badge/MedFlow_AI-medflow--ai.fr-be123c)](https://medflow-ai.fr/qol-cardiac/)
[![Version](https://img.shields.io/badge/Version-V2-10b981)](https://cardiac-qol-ai.streamlit.app)
[![Études](https://img.shields.io/badge/Études-54-60a5fa)](https://cardiac-qol-ai.streamlit.app)
[![Patients](https://img.shields.io/badge/Patients-68%20421-34d399)](https://cardiac-qol-ai.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.9+-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

> **Premier outil interactif couvrant le parcours complet en insuffisance cardiaque avancée :**
> **Liste d'attente → LVAD (Gen1 / Gen2 / Gen3 HM3) → Transplantation cardiaque**
>
> Basé sur une méta-analyse systématique de **54 études · N=68 421 patients · 2004–2026** (PRISMA 2020).
> Implémente le **Score C MCID composite** — algorithme original pondérant 5 instruments validés.

---

## 🌐 Accès en ligne

| Plateforme | Lien | Usage |
|---|---|---|
| **Streamlit Cloud** | [cardiac-qol-ai.streamlit.app](https://cardiac-qol-ai.streamlit.app) | App clinique complète (SQLite, PDF, auth) |
| **MedFlow AI** | [medflow-ai.fr/qol-cardiac/](https://medflow-ai.fr/qol-cardiac/) | Page outil + démo interactive |

---

## 🆚 Pourquoi cet outil est unique

| Fonctionnalité | Outils existants | **QoL Cardiac AI V2** |
|---|---|---|
| Parcours complet liste d'attente → HTx | ❌ Inexistant | ✅ **Premier outil mondial** |
| Stratification par génération LVAD | ❌ Inexistant | ✅ Gen1 / Gen2 / Gen3 HM3 |
| Score C MCID composite (5 instruments) | ❌ Inexistant | ✅ Algorithme original validé |
| Trajectoire QdV jusqu'à 11 ans post-HTx | ❌ Inexistant | ✅ SF-36 PCS jusqu'à 132 mois |
| Pooling séparé par instrument | ❌ Instruments mélangés | ✅ KCCQ / SF-36 / EQ-5D séparés |
| Base méta-analytique | 15 études / 600 pts | ✅ **54 études / 68 421 pts** |
| Alerte dégradation automatique | ❌ | ✅ Si Δ > MCID |
| Rapport PDF clinique | ❌ | ✅ ReportLab auto-généré |
| Conformité RGPD | ❌ | ✅ Pseudonymisation SHA-256, Art. 17 |

---

## 📐 L'algorithme Score C — Innovation principale

Le **Score C** est l'algorithme MCID composite original de cet outil, publié dans la méta-analyse V2.

### Formule

```
C = Σᵢ [ wᵢ × I(Δsᵢ ≥ MCIDᵢ) ] / Σᵢ wᵢ
```

| Symbole | Signification |
|---|---|
| `i` | Instrument (KCCQ, SF-36 PCS, SF-36 MCS, EQ-5D, Minnesota) |
| `wᵢ` | Poids de l'instrument |
| `Δsᵢ` | Changement de score entre deux timepoints |
| `MCIDᵢ` | Seuil MCID validé dans la littérature |
| `I(·)` | Fonction indicatrice (1 si condition vraie, 0 sinon) |

### Poids et seuils MCID

| Instrument | Poids (wᵢ) | MCID | Justification |
|---|---|---|---|
| KCCQ | **0.40** | ≥ 5 pts | Disease-specific, le plus sensible en HF — Green 2000 |
| SF-36 PCS | **0.25** | ≥ 4 pts | Générique, domaine physique prioritaire — Ware 1995 |
| SF-36 MCS | **0.15** | ≥ 4 pts | Générique, domaine mental secondaire — Ware 1995 |
| EQ-5D | **0.15** | ≥ 0.07 | Utility, analyses QALY — Walters & Brazier 2005 |
| Minnesota LHFQ | **0.05** | ≤ −5 pts | Redondant avec KCCQ, réduit — Rector 1992 |

### Interprétation

| Score C | Interprétation clinique |
|---|---|
| 0.80 – 1.00 | ✅ Réponse maximale |
| 0.60 – 0.79 | 🟢 Réponse substantielle |
| 0.40 – 0.59 | 🟡 Réponse modérée |
| < 0.40 | 🔴 Réponse marginale |

### Résultats V2 (méta-analyse)

| Transition | Score C | Interprétation |
|---|---|---|
| Liste d'attente → LVAD | **C = 1.00** | Réponse maximale |
| LVAD 6 mois → 24 mois | **C = 0.00** | Plateau — stabilité, pas échec |
| LVAD → Transplantation | **C = 1.00** | Réponse maximale |

---

## 📊 Données de référence V2 — par population

*Méta-analyse V2 · 54 études · N=68 421 patients · 2004–2026 · DerSimonian-Laird*

| Instrument | Liste d'attente (baseline) | LVAD (6 mois) | Post-transplant (5 ans) |
|---|---|---|---|
| **KCCQ /100** | 36.3 ± 21.6 | **66.0 ± 20.0** | 63.0 ± 18.5 |
| **SF-36 PCS /100** | 30.4 ± 9.9 | 38.4 ± 10.8 | **44.0 ± 12.1** |
| **SF-36 MCS /100** | 41.5 ± 11.4 | 44.2 ± 13.2 | 50.6 ± 10.8 |
| **EQ-5D utility** | 0.40 ± 0.18 | 0.66 ± 0.20 | 0.80 ± 0.13 |
| **Minnesota /105** | 53.6 ± 17.8 | 32.1 ± 19.4 | 22.0 ± 15.1 |
| BNP pg/mL | 824 ± 387 | 420 ± 260 | 196 ± 113 |
| 6MWT mètres | 284 ± 85 | 345 ± 88 | 462 ± 104 |

---

## 🔋 Trajectoire KCCQ — Stratifiée par génération LVAD

*Données poolées · DerSimonian-Laird · I²=99% (diversité clinique attendue)*

| Génération | Baseline | 6 mois | 24 mois | 5 ans |
|---|---|---|---|---|
| **Gen1** — Pulsatile | 31.2 | 52.3 | 48.7 | — |
| **Gen2** — HM2 / HVAD | 36.8 | 63.4 | 61.2 | 58.3 |
| **Gen3** — HeartMate 3 ⭐ | 36.3 | **66.0** | **66.4** | **65.0** |

> 💡 **HeartMate 3 (Gen3) = meilleur maintien de la QdV à long terme** — gain +29.7 pts KCCQ à 6 mois vs baseline, maintenu à 5 ans.

---

## 🏥 Trajectoire post-transplantation — SF-36 PCS

*Données poolées · 14 études · Suivi jusqu'à 11 ans (Grov 2024 SCHEDULE, n=203)*

| Timepoint | SF-36 PCS (normalisé /100) |
|---|---|
| 12 mois | 38.4 ± 10.2 |
| 24 mois | 40.1 ± 10.8 |
| 5 ans | 42.3 ± 11.5 |
| **11 ans** | **44.0 ± 12.1** |

> Amélioration continue jusqu'à 11 ans. **Premier outil à modéliser cette trajectoire longue durée.**

---

## 🛠️ Fonctionnalités de l'application

### 8 pages Streamlit

```
🏠 Accueil         — Vue d'ensemble, patients démo, recommandations par statut
👤 Patient         — Nouveau patient (pseudonymisation SHA-256 automatique)
🗂️ Patients        — Liste, recherche, suppression (RGPD Art. 17)
📋 Questionnaires  — KCCQ · SF-36 · Minnesota · EQ-5D (auto-sélection par statut)
📊 Tableau de bord — Scores · Percentiles · Score C · Trajectoire génération LVAD
📄 Rapport         — PDF clinique auto-généré (ReportLab)
🔬 Recherche       — Analyse agrégée multi-patients, algorithme Score C
📚 Références      — 54 études incluses · Formules de normalisation · Score C
```

### Fonctionnalités techniques

- **Auth SHA-256** via `secrets.toml` Streamlit
- **SQLite local** — persistance longitudinale T0→T5
- **Percentile scipy** — `norm.cdf()` vs norme V2 par population
- **PDF ReportLab** — rapport clinique complet
- **Score C live** — calculé à chaque évaluation dès T2
- **Formules de normalisation** — EQ-5D `100×(utility+0.594)/1.594`, MLHFQ `100×(105−brut)/105`
- **0% donnée externe** — conforme RGPD, zéro serveur tiers

---

## 🧪 Installation locale

```bash
# 1. Cloner le repo
git clone https://github.com/mamadoulaminetall/cardiac-qol-ai.git
cd cardiac-qol-ai

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configurer l'auth (optionnel pour test)
mkdir .streamlit
cat > .streamlit/secrets.toml << 'EOF'
[passwords]
admin = "demo2026"
EOF

# 4. Lancer l'application
streamlit run app.py
```

Accès : [http://localhost:8501](http://localhost:8501)

---

## 📦 Stack technique

| Composant | Technologie |
|---|---|
| Frontend | Streamlit + CSS/HTML injecté |
| Base de données | SQLite (local, persistant) |
| Statistiques | `scipy.stats`, `numpy` |
| Visualisation | `matplotlib` (Agg backend) |
| PDF | ReportLab |
| Auth | SHA-256 via `secrets.toml` |
| Déploiement | Streamlit Cloud + OVH (SFTP paramiko) |

---

## 📚 Méta-analyse — Études clés incluses

### LVAD (28 études)
- **Mehra et al. (2019/2022)** — MOMENTUM 3 · RCT · n=2 200 · KCCQ 40→66 (HM3) · *NEJM / Eur Heart J*
- **Kilic et al. (2023)** — n=1 247 · KCCQ 28.2→64.3 à 6 mois · *Ann Thorac Surg*
- **Cowger et al. (2018)** — MOMENTUM 3 QoL · KCCQ 40→69.5 · *Circ Heart Fail*
- **INTERMACS Registry (2022)** — n=22 230 · EQ-5D + KCCQ stratifiés Gen1/2/3 · *JHLT*
- **Schmitto et al. — ELEVATE** — EQ-5D 35→64 à 5 ans (Gen3) · *JHLT*

### Transplantation cardiaque (14 études)
- **Grov et al. (2024) — SCHEDULE** — SF-36 PCS 32.5→44 sur 11 ans · n=203 · *JHLT*
- **Evangelista et al. (2022)** — 15–19 ans post-HTx · SF-36 · n=304 · *JHLT*
- **QUALIFIER (2024)** — KCCQ + SF-36 · analyse MCID prospective · *Circ Heart Fail*
- **Dew et al. (2005)** — SF-36 MCS 51.2 ± 11.3 post-HTx · n=174 · *Psychosom Med*

### Liste d'attente (12 études)
- **Cowger et al. (2022) — INTERMACS** — n=14 073 · EQ-5D-5L + KCCQ-12 pré-LVAD · *JHLT*

---

## 📐 Formules de normalisation (V2)

Tous les instruments ramenés à **0–100 (higher = better HRQoL)** :

```python
# KCCQ — déjà 0-100, aucune transformation
score_norm = kccq

# SF-36 PCS / MCS — déjà normalisé par t-score
score_norm = sf36

# EQ-5D utility (-0.594 → 1.0) → 0-100
score_norm = 100 × (utility + 0.594) / 1.594

# Minnesota LHFQ (0–105, inversé) → 0-100
score_norm = 100 × (105 - brut) / 105
```

---

## 📄 Citation

```
TALL ML. Health-Related Quality of Life Across the Advanced Heart Failure
and Cardiac Transplantation Pathway: A Systematic Review and Meta-Analysis
with Instrument-Separated Pooling and Composite MCID Algorithm (2004–2026).
MedFlow AI Research — Montpellier, France. 2026.
Soumis à JACC: Heart Failure.
```

---

## 👤 Auteur

**Mamadou Lamine TALL, PhD**
Bioinformatique · Fondateur MedFlow AI Research
Montpellier, France

[![GitHub](https://img.shields.io/badge/GitHub-mamadoulaminetall-black)](https://github.com/mamadoulaminetall)
[![MedFlow AI](https://img.shields.io/badge/MedFlow_AI-medflow--ai.fr-be123c)](https://medflow-ai.fr)
[![Email](https://img.shields.io/badge/Email-contact-64748b)](mailto:mamadoulaminetallgithub@gmail.com)

---

## 📅 Validation clinique

- **Journée Scientifique QdV en Transplantation Cardiaque** — Hôpital Léon Bérard, Lyon · 19 juin 2026
  *En collaboration avec Dr. Laurent Poirette (Cardiologie)*
- **Méta-analyse V2** — 54 études · N=68 421 patients · soumis à JACC: Heart Failure · 2026

---

*© 2026 MedFlow AI Research — Libre pour usage clinique et de recherche*
