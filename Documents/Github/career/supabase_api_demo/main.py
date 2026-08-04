import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Job Data API")

# Define the Pydantic model for incoming JSON data
class JobRecord(BaseModel):
    email: str
    type: str
    date: str  # Expected format: DD-MM-YY

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            # Validate that it matches DD-MM-YY
            datetime.strptime(v, "%d-%m-%y")
            return v
        except ValueError:
            raise ValueError("Date must be in DD-MM-YY format")


@app.post("/store_record")
async def store_record(record: JobRecord):
    """
    API 1: Takes JSON data (email, type, date in DD-MM-YY format) and stores it in Supabase.
    """
    try:
        data, count = supabase.table('job_records').insert({
            "email": record.email,
            "type": record.type,
            "date": record.date
        }).execute()
        
        return {"message": "Record stored successfully", "data": data[1]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fetch_by_date")
async def fetch_by_date(date: str):
    """
    API 2: Takes a date argument (DD-MM-YY) and fetches all matching records.
    Example: /fetch_by_date?date=15-07-26
    """
    try:
        # Validate the date format first
        datetime.strptime(date, "%d-%m-%y")
        
        # Query Supabase for matching records
        response = supabase.table('job_records').select("*").eq("date", date).execute()
        
        records = response.data
        if not records:
            return {"message": "No records found for this date", "data": []}
            
        return {"message": f"Found {len(records)} records", "data": records}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Must be DD-MM-YY")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
