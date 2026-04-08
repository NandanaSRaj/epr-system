from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime
import random

app = FastAPI(title="RuralCare AI")

templates = Jinja2Templates(directory="templates")

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

# ---------------- LOGIC ---------------- #

def generate_upid():
    return f"RC-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

def calculate_risk(fbs, rbs, bp_sys, bp_dia):
    score = 0

    if fbs > 126:
        score += 0.4
    elif fbs > 100:
        score += 0.2

    if rbs > 200:
        score += 0.4
    elif rbs > 140:
        score += 0.2

    if bp_sys > 140 or bp_dia > 90:
        score += 0.2

    if score < 0.3:
        return "Low", score
    elif score < 0.6:
        return "Pre-diabetic", score
    else:
        return "High", score


def get_diet_plan(risk):
    if risk == "Low":
        return [
            "Maintain balanced diet",
            "Eat fruits & vegetables",
            "Exercise regularly"
        ]
    elif risk == "Pre-diabetic":
        return [
            "Reduce sugar intake",
            "Eat whole grains",
            "Avoid processed food",
            "Walk 30 mins daily"
        ]
    else:
        return [
            "Strict low sugar diet",
            "Avoid sweets & rice",
            "High fiber foods",
            "Consult doctor",
            "Daily monitoring required"
        ]

# ---------------- ROUTES ---------------- #

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    fbs: float = Form(...),
    rbs: float = Form(...),
    bp_sys: float = Form(...),
    bp_dia: float = Form(...),
    weight: float = Form(...)
):
    upid = generate_upid()
    risk, score = calculate_risk(fbs, rbs, bp_sys, bp_dia)
    diet = get_diet_plan(risk)

    cursor.execute("""
    INSERT INTO patients VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        upid, name, age, gender, fbs, rbs,
        bp_sys, bp_dia, weight,
        risk, score, datetime.now().isoformat()
    ))
    conn.commit()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "result": {
            "upid": upid,
            "risk": risk,
            "score": round(score, 2),
            "diet": diet
        }
    })


@app.get("/patient/{upid}")
def get_patient(upid: str):
    cursor.execute("SELECT * FROM patients WHERE upid = ?", (upid,))
    row = cursor.fetchone()

    if not row:
        return {"error": "Patient not found"}

    risk = row[9]

    return {
        "UPID": row[0],
        "name": row[1],
        "age": row[2],
        "gender": row[3],
        "FBS": row[4],
        "RBS": row[5],
        "BP_sys": row[6],
        "BP_dia": row[7],
        "weight": row[8],
        "risk": risk,
        "score": row[10],
        "diet_plan": get_diet_plan(risk),
        "timestamp": row[11]
    }
