from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import sqlite3
import pandas as pd
import io

from database import init_db, get_db_connection
from models import RegistrationCreate

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    init_db()
    yield

app = FastAPI(title="Event Registration API", lifespan=lifespan)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Event Registration API is online!", "status": "active"}

@app.post("/register")
def register(data: RegistrationCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO registrations (full_name, email, phone, university, department, semester, experience, motivation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.full_name, data.email, data.phone, data.university,
            data.department, data.semester, data.experience, data.motivation
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email is already registered.")
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    
    conn.close()
    return {"message": "Registration successful"}

@app.get("/responses")
def get_responses():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM registrations")
    rows = cursor.fetchall()
    conn.close()
    
    return {"data": [dict(row) for row in rows]}

@app.delete("/registration/{id}")
def delete_registration(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM registrations WHERE id = ?", (id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Registration not found")
    return {"message": "Registration deleted successfully"}

@app.get("/export/excel")
def export_excel():
    conn = get_db_connection()
    query = "SELECT * FROM registrations"
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    output = io.BytesIO()
    # Write to BytesIO using openpyxl engine
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Registrations')
    
    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="registrations.xlsx"'
    }
    
    return StreamingResponse(
        output,
        headers=headers,
        media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
