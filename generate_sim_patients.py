"""
Génère 57 patients simulés réalistes (3 populations) et les insère dans la DB.
Basé sur les valeurs de référence des méta-analyses publiées.
"""
import sqlite3, random, hashlib, uuid
from datetime import datetime, timedelta
import numpy as np

DB_PATH = "/Users/tall/Claude Code/Research/QoL-Cardiac/app/qol_cardiac.db"
random.seed(42)
np.random.seed(42)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def rnd(mean, sd, lo, hi, digits=0):
    v = np.random.normal(mean, sd)
    v = clamp(v, lo, hi)
    return round(v, digits) if digits > 0 else int(round(v))

def pid():
    return "SIM-" + uuid.uuid4().hex[:8].upper()

def date_str(base, days_offset):
    return (base + timedelta(days=days_offset)).strftime("%Y-%m-%d")

BASE_DATE = datetime(2025, 6, 1)

# ─── DONNÉES RÉALISTES PAR POPULATION ET MOMENT T ────────────────────────────
#
# Liste d'attente
#   T0 : inscription — état dégradé baseline
#   T3 : 6 mois — stable ou léger déclin
#
# LVAD
#   T1 : pré-implantation — état très dégradé
#   T2 : 3 mois post-LVAD — pic d'amélioration
#   T3 : 6 mois post-LVAD — plateau (70% des patients)
#
# Post-greffe
#   T0 : baseline sur liste (60% des patients ont cette éval)
#   T4 : 3 mois post-greffe — pic, mais 20% rejet aigu
#   T5 : 1 an post-greffe — stabilisation haute
# ─────────────────────────────────────────────────────────────────────────────

def gen_liste_patient(i):
    """20 patients Liste d'attente — T0 tous, T3 pour 14 d'entre eux"""
    pid_v = pid()
    age   = rnd(55, 9, 35, 75)
    sexe  = "Homme" if random.random() < 0.72 else "Femme"
    prenom = random.choice(["Jean","Pierre","Michel","François","Alain","Bruno",
                             "Marc","Luc","André","Paul","Henri","Serge",
                             "Marie","Claire","Anne","Sylvie","Isabelle","Nathalie"])
    nom    = random.choice(["Martin","Dupont","Bernard","Moreau","Simon","Laurent",
                             "Leroy","Roux","David","Petit","Richard","Garnier",
                             "Blanc","Faure","Girard","Bonnet","Lemaire","Rousseau"])
    created = (BASE_DATE - timedelta(days=random.randint(10,60))).isoformat()

    # T0 — baseline inscription
    t0_kccq   = rnd(36, 10, 18, 56)
    t0_pcs    = rnd(28, 7,  14, 44)
    t0_mcs    = rnd(38, 9,  20, 58)
    t0_minn   = rnd(68, 12, 42, 95)    # Minnesota : élevé = mauvais
    t0_eq5d   = round(rnd(0.51, 0.09, 0.28, 0.68, 2), 2)
    t0_nyha   = random.choices(["III","IV"], weights=[0.65,0.35])[0]
    t0_6mwt   = rnd(268, 58, 140, 380)
    t0_bnp    = rnd(820, 280, 350, 1800)
    t0_lvef   = rnd(28, 6,  14, 38)
    t0_date   = date_str(BASE_DATE, -random.randint(30, 120))

    evals = [(pid_v, t0_date, "T0 — Inscription sur liste", "Liste d'attente",
              t0_kccq, t0_pcs, t0_mcs, t0_minn, t0_eq5d, t0_nyha, t0_6mwt, t0_bnp, t0_lvef)]

    # T3 — 6 mois : 70% des patients (déclin léger)
    if i < 14:
        t3_kccq = clamp(t0_kccq + rnd(-4, 6, -18, 8), 12, 60)
        t3_pcs  = clamp(t0_pcs  + rnd(-3, 5, -14, 6), 10, 48)
        t3_mcs  = clamp(t0_mcs  + rnd(-2, 6, -10, 8), 18, 60)
        t3_minn = clamp(t0_minn + rnd( 4, 7, -8, 20), 38, 105)
        t3_eq5d = round(clamp(t0_eq5d + rnd(-0.04, 0.06, -0.15, 0.08, 2), 0.20, 0.72), 2)
        t3_nyha = random.choices(["III","IV"], weights=[0.55,0.45])[0]
        t3_6mwt = clamp(t0_6mwt + rnd(-18, 30, -80, 40), 100, 400)
        t3_bnp  = clamp(t0_bnp  + rnd(90, 120, -100, 500), 300, 2200)
        t3_lvef = clamp(t0_lvef + rnd(-1, 3, -6, 4), 12, 40)
        t3_date = date_str(BASE_DATE, -random.randint(0, 30))
        evals.append((pid_v, t3_date, "T3 — Suivi semestriel", "Liste d'attente",
                      t3_kccq, t3_pcs, t3_mcs, t3_minn, t3_eq5d, t3_nyha, t3_6mwt, t3_bnp, t3_lvef))

    return (pid_v, prenom, nom, age, sexe, "Liste d'attente", created), evals


def gen_lvad_patient(i):
    """19 patients LVAD — T1 tous, T2 tous, T3 pour 13 d'entre eux"""
    pid_v = pid()
    age   = rnd(58, 9, 38, 76)
    sexe  = "Homme" if random.random() < 0.78 else "Femme"
    prenom = random.choice(["Claude","Patrick","Gilles","Denis","Thierry","Yves",
                             "Robert","Christian","Daniel","Didier","Olivier","Eric",
                             "Martine","Véronique","Christine","Monique","Brigitte"])
    nom    = random.choice(["Chevalier","Morin","Fontaine","Durand","Legrand","Renard",
                             "Perrin","Colin","Gauthier","Masson","Marchand","Nicolas",
                             "Thomas","Garcia","Robin","Muller","Henry","Bourgeois"])
    created = (BASE_DATE - timedelta(days=random.randint(60, 180))).isoformat()

    # T1 — pré-implantation
    t1_kccq = rnd(30, 9,  14, 50)
    t1_pcs  = rnd(24, 7,  10, 40)
    t1_mcs  = rnd(32, 9,  16, 52)
    t1_minn = rnd(74, 11, 48, 98)
    t1_eq5d = round(rnd(0.43, 0.09, 0.22, 0.64, 2), 2)
    t1_nyha = random.choices(["III","IV"], weights=[0.45,0.55])[0]
    t1_6mwt = rnd(210, 52, 80,  320)
    t1_bnp  = rnd(1350, 380, 600, 2800)
    t1_lvef = rnd(19, 5,  8,  30)
    t1_date = date_str(BASE_DATE, -random.randint(120, 200))

    evals = [(pid_v, t1_date, "T1 — Avant implantation LVAD", "LVAD",
              t1_kccq, t1_pcs, t1_mcs, t1_minn, t1_eq5d, t1_nyha, t1_6mwt, t1_bnp, t1_lvef)]

    # T2 — 3 mois post-LVAD : amélioration significative ~75%
    improvement = random.random() < 0.76
    d_kccq = rnd(16, 7, 4, 28)  if improvement else rnd(3, 5, -4, 10)
    t2_kccq = clamp(t1_kccq + d_kccq, 20, 76)
    t2_pcs  = clamp(t1_pcs  + rnd(13, 5,  3, 22), 18, 62)
    t2_mcs  = clamp(t1_mcs  + rnd( 8, 6,  0, 18), 20, 62)
    t2_minn = clamp(t1_minn + rnd(-20, 8,-38, -4), 28, 88)
    t2_eq5d = round(clamp(t1_eq5d + rnd(0.17, 0.07, 0.04, 0.30, 2), 0.32, 0.82), 2)
    t2_nyha = random.choices(["I","II","III"], weights=[0.15,0.68,0.17])[0]
    t2_6mwt = clamp(t1_6mwt + rnd(110, 38, 40, 200), 150, 480)
    t2_bnp  = clamp(t1_bnp  * rnd(0.38, 0.10, 0.20, 0.58), 80, 1200)
    t2_lvef = clamp(t1_lvef + rnd(2, 4, -2, 8), 8, 36)
    t2_date = date_str(BASE_DATE, -random.randint(30, 90))

    evals.append((pid_v, t2_date, "T2 — 3 mois post-LVAD", "LVAD",
                  t2_kccq, t2_pcs, t2_mcs, t2_minn, t2_eq5d, t2_nyha,
                  t2_6mwt, int(t2_bnp), t2_lvef))

    # T3 — 6 mois : plateau (68% des patients)
    if i < 13:
        t3_kccq = clamp(t2_kccq + rnd(3, 5, -4, 12), 22, 82)
        t3_pcs  = clamp(t2_pcs  + rnd(2, 4, -3, 10), 18, 68)
        t3_mcs  = clamp(t2_mcs  + rnd(2, 4, -3, 10), 20, 68)
        t3_minn = clamp(t2_minn + rnd(-4, 6,-14,  4), 22, 90)
        t3_eq5d = round(clamp(t2_eq5d + rnd(0.04, 0.05,-0.04,0.12, 2), 0.30, 0.88), 2)
        t3_nyha = random.choices(["I","II","III"], weights=[0.22,0.64,0.14])[0]
        t3_6mwt = clamp(t2_6mwt + rnd(22, 28, -20, 70), 160, 520)
        t3_bnp  = clamp(t2_bnp  * rnd(0.86, 0.12, 0.60, 1.05), 60, 1000)
        t3_lvef = clamp(t2_lvef + rnd(1, 3, -3, 6), 8, 40)
        t3_date = date_str(BASE_DATE, random.randint(0, 30))
        evals.append((pid_v, t3_date, "T3 — Suivi semestriel", "LVAD",
                      t3_kccq, t3_pcs, t3_mcs, t3_minn, t3_eq5d, t3_nyha,
                      t3_6mwt, int(t3_bnp), t3_lvef))

    return (pid_v, prenom, nom, age, sexe, "LVAD", created), evals


def gen_greffe_patient(i):
    """18 patients Post-greffe — T0 baseline (11 patients), T4 tous, T5 tous"""
    pid_v = pid()
    age   = rnd(52, 10, 30, 72)
    sexe  = "Homme" if random.random() < 0.70 else "Femme"
    prenom = random.choice(["Laurent","Frédéric","Nicolas","Emmanuel","Julien","Antoine",
                             "Thomas","Maxime","Alexandre","Benjamin","Sébastien","Romain",
                             "Céline","Amélie","Julie","Sophie","Laure","Camille","Emma"])
    nom    = random.choice(["Meyer","Weber","Klein","Schneider","Wolf","Braun",
                             "Hoffmann","Fischer","Wagner","Bauer","Koch","Richter",
                             "Berger","Jung","Krause","Müller","Schäfer","Walter"])
    created = (BASE_DATE - timedelta(days=random.randint(200, 400))).isoformat()

    evals = []

    # T0 baseline — 61% des patients (ceux qui avaient une éval sur liste)
    if i < 11:
        t0_kccq = rnd(34, 11, 16, 54)
        t0_pcs  = rnd(27, 7,  13, 42)
        t0_mcs  = rnd(36, 9,  18, 56)
        t0_minn = rnd(70, 12, 44, 98)
        t0_eq5d = round(rnd(0.49, 0.10, 0.26, 0.68, 2), 2)
        t0_nyha = random.choices(["III","IV"], weights=[0.60,0.40])[0]
        t0_6mwt = rnd(258, 60, 120, 370)
        t0_bnp  = rnd(880, 300, 380, 1900)
        t0_lvef = rnd(26, 6,  12, 36)
        t0_date = date_str(BASE_DATE, -random.randint(280, 420))
        evals.append((pid_v, t0_date, "T0 — Inscription sur liste", "Post-greffe",
                      t0_kccq, t0_pcs, t0_mcs, t0_minn, t0_eq5d, t0_nyha,
                      t0_6mwt, t0_bnp, t0_lvef))

    # T4 — 3 mois post-greffe : 80% bonne réponse, 20% rejet
    rejet = random.random() < 0.20
    if rejet:
        t4_kccq = rnd(40, 10, 22, 58)
        t4_pcs  = rnd(32, 8,  18, 48)
        t4_mcs  = rnd(36, 9,  20, 54)
        t4_minn = rnd(50, 12, 28, 76)
        t4_eq5d = round(rnd(0.56, 0.09, 0.34, 0.72, 2), 2)
        t4_nyha = random.choices(["II","III"], weights=[0.40,0.60])[0]
        t4_6mwt = rnd(320, 60, 180, 430)
        t4_bnp  = rnd(680, 220, 300, 1200)
        t4_lvef = rnd(40, 8,  24, 54)
    else:
        t4_kccq = rnd(66, 12, 42, 86)
        t4_pcs  = rnd(52, 10, 32, 70)
        t4_mcs  = rnd(54, 10, 34, 72)
        t4_minn = rnd(22, 10,  4, 44)
        t4_eq5d = round(rnd(0.78, 0.09, 0.56, 0.94, 2), 2)
        t4_nyha = random.choices(["I","II"], weights=[0.55,0.45])[0]
        t4_6mwt = rnd(428, 65, 280, 560)
        t4_bnp  = rnd(138, 68,  28, 320)
        t4_lvef = rnd(58, 6,  42, 70)
    t4_date = date_str(BASE_DATE, -random.randint(60, 150))
    evals.append((pid_v, t4_date, "T4 — 3 mois post-greffe", "Post-greffe",
                  t4_kccq, t4_pcs, t4_mcs, t4_minn, t4_eq5d, t4_nyha,
                  t4_6mwt, t4_bnp, t4_lvef))

    # T5 — 1 an post-greffe : stabilisation haute
    t5_kccq = clamp(t4_kccq + rnd(5, 7,  -4, 18), 30, 92)
    t5_pcs  = clamp(t4_pcs  + rnd(4, 6,  -3, 14), 26, 78)
    t5_mcs  = clamp(t4_mcs  + rnd(3, 6,  -4, 12), 28, 80)
    t5_minn = clamp(t4_minn + rnd(-4, 6,-14,  4),  2, 50)
    t5_eq5d = round(clamp(t4_eq5d + rnd(0.05, 0.06,-0.04,0.14, 2), 0.28, 0.98), 2)
    t5_nyha = random.choices(["I","II"], weights=[0.68,0.32])[0]
    t5_6mwt = clamp(t4_6mwt + rnd(35, 30, -20, 90), 200, 600)
    t5_bnp  = clamp(t4_bnp  * rnd(0.76, 0.14, 0.40, 0.98), 18, 380)
    t5_lvef = clamp(t4_lvef + rnd(2, 4,  -2, 8), 36, 74)
    t5_date = date_str(BASE_DATE, random.randint(60, 180))
    evals.append((pid_v, t5_date, "T5 — 1 an post-greffe", "Post-greffe",
                  t5_kccq, t5_pcs, t5_mcs, t5_minn, t5_eq5d, t5_nyha,
                  int(t5_6mwt), int(t5_bnp), int(t5_lvef)))

    return (pid_v, prenom, nom, age, sexe, "Post-greffe", created), evals


# ─── INSERTION EN DB ─────────────────────────────────────────────────────────

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Vérifier les patients démo existants
c.execute("SELECT COUNT(*) FROM patients WHERE id LIKE 'DEMO-%'")
n_demo = c.fetchone()[0]
print(f"Patients DEMO existants : {n_demo}")

# Supprimer les anciens patients simulés si présents
c.execute("DELETE FROM patients WHERE id LIKE 'SIM-%'")
c.execute("DELETE FROM evaluations WHERE patient_id LIKE 'SIM-%'")
conn.commit()
print("Anciens patients SIM supprimés")

patients_all = []
evals_all    = []

# 20 Liste d'attente
for i in range(20):
    pt, evs = gen_liste_patient(i)
    patients_all.append(pt)
    evals_all.extend(evs)

# 19 LVAD
for i in range(19):
    pt, evs = gen_lvad_patient(i)
    patients_all.append(pt)
    evals_all.extend(evs)

# 18 Post-greffe
for i in range(18):
    pt, evs = gen_greffe_patient(i)
    patients_all.append(pt)
    evals_all.extend(evs)

# Insérer patients
c.executemany("INSERT INTO patients VALUES (?,?,?,?,?,?,?)", patients_all)

# Insérer évaluations
eval_rows = []
for ev in evals_all:
    # ev = (patient_id, date, moment, statut, kccq, sf36_pcs, sf36_mcs, minnesota, eq5d, nyha, 6mwt, bnp, lvef)
    eval_rows.append(ev)

c.executemany("""INSERT INTO evaluations
    (patient_id, date, moment, statut, kccq, sf36_pcs, sf36_mcs, minnesota,
     eq5d, nyha, mwt6, bnp, lvef)
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""", eval_rows)

conn.commit()
conn.close()

print(f"\n✓ {len(patients_all)} patients simulés insérés")
print(f"  - Liste d'attente : 20 (T0 tous · T3 pour 14)")
print(f"  - LVAD            : 19 (T1+T2 tous · T3 pour 13)")
print(f"  - Post-greffe     : 18 (T0 pour 11 · T4+T5 tous)")
print(f"  → {len(eval_rows)} évaluations au total")

# Vérification rapide des deltas LVAD
conn2 = sqlite3.connect(DB_PATH)
c2 = conn2.cursor()
c2.execute("""
    SELECT e1.patient_id,
           e1.kccq as kccq_t1,
           e2.kccq as kccq_t2,
           e2.kccq - e1.kccq as delta
    FROM evaluations e1
    JOIN evaluations e2 ON e1.patient_id = e2.patient_id
    WHERE e1.moment LIKE 'T1%' AND e2.moment LIKE 'T2%'
    AND e1.patient_id LIKE 'SIM-%'
    LIMIT 5
""")
rows = c2.fetchall()
print("\nVérification LVAD T1→T2 (5 premiers patients) :")
for r in rows:
    print(f"  {r[0]} : KCCQ T1={r[1]:.0f} → T2={r[2]:.0f} → Δ{r[3]:+.0f}")
conn2.close()
