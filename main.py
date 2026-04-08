from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import random

app = FastAPI(title="Rural EPR System")

# ---------------- DATABASE ---------------- #
conn = sqlite3.connect("epr.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS patients (
    upid TEXT PRIMARY KEY,
    name TEXT,
    age INTEGER,
    gender TEXT,
    fbs REAL,
    rbs REAL,
    bp_sys REAL,
    bp_dia REAL,
    weight REAL,
    risk TEXT,
    score REAL,
    timestamp TEXT
)
""")
conn.commit()

# ---------------- MODELS ---------------- #
class PatientData(BaseModel):
    name: str
    age: int
    gender: str
    fbs: float
    rbs: float
    bp_sys: float
    bp_dia: float
    weight: float

# ---------------- UPID GENERATION ---------------- #
def generate_upid():
    date = datetime.now().strftime("%Y%m%d")
    rand = random.randint(1000, 9999)
    return f"SKD-{date}-{rand}"

# ---------------- RISK CLASSIFICATION ---------------- #
def classify_risk(fbs, rbs):
    if fbs >= 126 or rbs >= 200:
        return "Diabetic"
    elif 100 <= fbs < 126 or 140 <= rbs < 200:
        return "Pre-diabetic"
    else:
        return "Normal"

# ---------------- RISK SCORE (SIMULATED ML) ---------------- #
def risk_score(age, bp_sys, weight):
    score = (age * 0.01) + (bp_sys * 0.005) + (weight * 0.002)
    return min(score, 1.0)

def risk_level(score):
    if score < 0.3:
        return "Low"
    elif score < 0.7:
        return "Medium"
    else:
        return "High"

# ---------------- REGISTER PATIENT ---------------- #
@app.post("/register")
def register_patient(data: PatientData):
    upid = generate_upid()
    risk = classify_risk(data.fbs, data.rbs)
    score = risk_score(data.age, data.bp_sys, data.weight)
    level = risk_level(score)

    cursor.execute("""
    INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        upid,
        data.name,
        data.age,
        data.gender,
        data.fbs,
        data.rbs,
        data.bp_sys,
        data.bp_dia,
        data.weight,
        risk,
        score,
        datetime.now().isoformat()
    ))
    conn.commit()

    return {
        "UPID": upid,
        "risk_category": risk,
        "risk_score": round(score, 2),
        "risk_level": level,
        "message": "Patient registered successfully"
    }

# ---------------- GET PATIENT ---------------- #
@app.get("/patient/{upid}")
def get_patient(upid: str):
    cursor.execute("SELECT * FROM patients WHERE upid=?", (upid,))
    result = cursor.fetchone()

    if not result:
        return {"error": "Patient not found"}

    return {
        "UPID": result[0],
        "name": result[1],
        "age": result[2],
        "gender": result[3],
        "FBS": result[4],
        "RBS": result[5],
        "BP": f"{result[6]}/{result[7]}",
        "weight": result[8],
        "risk": result[9],
        "score": result[10],
        "timestamp": result[11]
    }

# ---------------- REFERRAL ---------------- #
@app.get("/referral/{upid}")
def generate_referral(upid: str):
    cursor.execute("SELECT * FROM patients WHERE upid=?", (upid,))
    result = cursor.fetchone()

    if not result:
        return {"error": "Patient not found"}

    risk = result[9]

    if risk == "Diabetic":
        priority = "Immediate"
    elif risk == "Pre-diabetic":
        priority = "Moderate"
    else:
        priority = "Routine"

    return {
        "UPID": upid,
        "risk": risk,
        "priority": priority,
        "referral": "Visit nearest PHC for further evaluation"
    }

# ---------------- DASHBOARD ---------------- #
@app.get("/dashboard")
def dashboard():
    cursor.execute("SELECT risk, COUNT(*) FROM patients GROUP BY risk")
    data = cursor.fetchall()

    return {risk: count for risk, count in data}

