"""Generate 3 synthetic HR datasets for People Analytics practice."""

import csv
import os
import random
from datetime import date, timedelta

random.seed(42)
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

DEPARTMENTS = ["Technology", "Sales", "HR", "Finance", "Marketing", "Operations", "Legal", "R&D"]
CHANNELS = ["LinkedIn", "Campus", "Referral", "HeadHunter", "JobBoard", "Internal"]
STAGES = ["Resume Screen", "Phone Screen", "Technical Interview", "Final Interview", "Offer"]


def gen_employees(n=500):
    rows = []
    base_date = date(2018, 1, 1)
    for i in range(1, n + 1):
        dept = random.choice(DEPARTMENTS)
        hire_date = base_date + timedelta(days=random.randint(0, 2500))
        left = random.random() < 0.25
        leave_date = (hire_date + timedelta(days=random.randint(180, 1500))) if left else ""
        salary = random.randint(5000, 30000)
        performance = round(random.gauss(3.5, 0.8), 1)
        performance = max(1.0, min(5.0, performance))
        training_hours = random.randint(0, 120)
        satisfaction = round(random.gauss(3.8, 0.9), 1)
        satisfaction = max(1.0, min(5.0, satisfaction))
        rows.append({
            "employee_id": f"EMP{i:04d}",
            "department": dept,
            "hire_date": hire_date.isoformat(),
            "leave_date": leave_date if left else "",
            "salary": salary,
            "performance_score": performance,
            "training_hours": training_hours,
            "satisfaction_score": satisfaction,
            "age": random.randint(22, 55),
            "gender": random.choice(["M", "F"]),
            "education": random.choice(["Bachelor", "Master", "PhD", "High School"]),
        })
    path = os.path.join(OUT_DIR, "hr_employees.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Generated {path} ({len(rows)} rows)")


def gen_recruitment(n=200):
    rows = []
    base_date = date(2024, 1, 1)
    for i in range(1, n + 1):
        channel = random.choice(CHANNELS)
        final_stage_idx = random.randint(0, len(STAGES) - 1)
        hired = final_stage_idx == len(STAGES) - 1 and random.random() < 0.6
        days_in_process = sum(random.randint(2, 10) for _ in range(final_stage_idx + 1))
        cost = random.randint(500, 8000) if channel in ("HeadHunter", "LinkedIn") else random.randint(0, 2000)
        rows.append({
            "candidate_id": f"CAND{i:04d}",
            "channel": channel,
            "apply_date": (base_date + timedelta(days=random.randint(0, 365))).isoformat(),
            "final_stage": STAGES[final_stage_idx],
            "days_in_process": days_in_process,
            "result": "Hired" if hired else "Rejected",
            "cost_yuan": cost,
            "department": random.choice(DEPARTMENTS),
        })
    path = os.path.join(OUT_DIR, "hr_recruitment.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Generated {path} ({len(rows)} rows)")


def gen_survey(n=300):
    """Generate UWES-9 + PLS-7 + LMX-7 survey data."""
    rows = []
    for i in range(1, n + 1):
        row = {"employee_id": f"EMP{random.randint(1, 500):04d}"}
        # UWES-9 (0-6 scale)
        uwes_base = random.gauss(4.0, 1.2)
        for q in range(1, 10):
            score = round(max(0, min(6, uwes_base + random.gauss(0, 0.8))))
            row[f"uwes_{q}"] = int(score)
        # PLS-7 (1-5 scale)
        pls_base = random.gauss(3.5, 0.9)
        for q in range(1, 8):
            score = round(max(1, min(5, pls_base + random.gauss(0, 0.6))))
            row[f"pls_{q}"] = int(score)
        # LMX-7 (1-5 scale)
        lmx_base = random.gauss(3.8, 0.8)
        for q in range(1, 8):
            score = round(max(1, min(5, lmx_base + random.gauss(0, 0.5))))
            row[f"lmx_{q}"] = int(score)
        rows.append(row)
    path = os.path.join(OUT_DIR, "hr_survey.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Generated {path} ({len(rows)} rows)")


if __name__ == "__main__":
    gen_employees()
    gen_recruitment()
    gen_survey()
    print("All datasets generated.")
