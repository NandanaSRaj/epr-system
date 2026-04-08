# -------------------- IMPORTS --------------------
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
from datetime import datetime
import random

# -------------------- APP --------------------
app = FastAPI(title="Rural EPR System")

# -------------------- DATABASE --------------------
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

# -------------------- MODEL --------------------
class PatientData(BaseModel):
    name: str
    age: int
    gender: str
    fbs: float
    rbs: float
    bp_sys: float
    bp_dia: float
    weight: float

# -------------------- HELPERS --------------------
def generate_upid():
    return f"SKD-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000,9999)}"

def calculate_risk(data: PatientData):
    score = 0

    if data.fbs > 110:
        score += 0.3
    if data.rbs > 160:
        score += 0.3
    if data.bp_sys > 130 or data.bp_dia > 85:
        score += 0.2
    if data.weight > 70:
        score += 0.2

    if score < 0.3:
        risk = "Low"
    elif score < 0.7:
        risk = "Pre-diabetic"
    else:
        risk = "High"

    return risk, round(score, 2)

# -------------------- BEAUTIFUL HOME PAGE --------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <head>
        <title>Rural EPR System</title>
    </head>

    <body style="
        font-family: Arial;
        background: linear-gradient(to right, #4facfe, #00f2fe);
        margin:0;
        padding:0;
    ">

        <div style="
            width:400px;
            margin:50px auto;
            background:white;
            padding:25px;
            border-radius:15px;
            box-shadow:0px 5px 20px rgba(0,0,0,0.2);
        ">

        <h2 style="text-align:center; color:#2c3e50;">
            🩺 Rural EPR System
        </h2>

        <p style="text-align:center; color:gray;">
            Patient Registration
        </p>

        <form action="/register_form" method="post">

            <label>👤 Name</label><br>
            <input type="text" name="name" style="width:100%;padding:8px;"><br><br>

            <label>🎂 Age</label><br>
            <input type="number" name="age" style="width:100%;padding:8px;"><br><br>

            <label>⚧ Gender</label><br>
            <input type="text" name="gender" style="width:100%;padding:8px;"><br><br>

            <label>🧪 FBS</label><br>
            <input type="number" name="fbs" style="width:100%;padding:8px;"><br><br>

            <label>🧪 RBS</label><br>
            <input type="number" name="rbs" style="width:100%;padding:8px;"><br><br>

            <label>💓 BP Sys</label><br>
            <input type="number" name="bp_sys" style="width:100%;padding:8px;"><br><br>

            <label>💓 BP Dia</label><br>
            <input type="number" name="bp_dia" style="width:100%;padding:8px;"><br><br>

            <label>⚖ Weight</label><br>
            <input type="number" name="weight" style="width:100%;padding:8px;"><br><br>

            <button style="
                width:100%;
                padding:12px;
                background:#27ae60;
                color:white;
                border:none;
                border-radius:8px;
                font-size:16px;
                cursor:pointer;
            ">
                ✅ Register Patient
            </button>

        </form>

        </div>

        <p style="text-align:center; color:white;">
            Built for Rural Healthcare 💙
        </p>

    </body>
    </html>
    """

# -------------------- FORM SUBMIT --------------------
@app.post("/register_form", response_class=HTMLResponse)
def register_form(
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    fbs: float = Form(...),
    rbs: float = Form(...),
    bp_sys: float = Form(...),
    bp_dia: float = Form(...),
    weight: float = Form(...)
):
    data = PatientData(
        name=name,
        age=age,
        gender=gender,
        fbs=fbs,
        rbs=rbs,
        bp_sys=bp_sys,
        bp_dia=bp_dia,
        weight=weight
    )

    result = register(data)

    return f"""
    <html>
    <body style="
        font-family: Arial;
        background: linear-gradient(to right, #43e97b, #38f9d7);
        text-align:center;
        padding-top:80px;
    ">

    <div style="
        background:white;
        width:350px;
        margin:auto;
        padding:20px;
        border-radius:15px;
        box-shadow:0px 5px 20px rgba(0,0,0,0.2);
    ">

    <h2>✅ Patient Registered</h2>

    <p><b>🆔 UPID:</b> {result['UPID']}</p>
    <p><b>⚠ Risk:</b> {result['risk_category']}</p>
    <p><b>📊 Score:</b> {result['risk_score']}</p>

    <br>

    <a href="/" style="
        text-decoration:none;
        background:#3498db;
        color:white;
        padding:10px 15px;
        border-radius:8px;
    ">
        ⬅ Register Another
    </a>

    </div>

    </body>
    </html>
    """

# -------------------- API --------------------
@app.post("/register")
def register(data: PatientData):
    upid = generate_upid()
    risk, score = calculate_risk(data)

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
        "risk_score": score,
        "message": "Patient registered successfully"
    }

# -------------------- GET PATIENT --------------------
@app.get("/patient/{upid}")
def get_patient(upid: str):
    cursor.execute("SELECT * FROM patients WHERE upid=?", (upid,))
    row = cursor.fetchone()

    if not row:
        return {"error": "Patient not found"}

    return {
        "UPID": row[0],
        "name": row[1],
        "age": row[2],
        "gender": row[3],
        "FBS": row[4],
        "RBS": row[5],
        "BP": f"{row[6]}/{row[7]}",
        "weight": row[8],
        "risk": row[9],
        "score": row[10],
        "timestamp": row[11]
    }
