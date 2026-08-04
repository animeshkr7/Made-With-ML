import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from module directory's .env file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY in .env file")

# Initialize Supabase Client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = FastAPI(title="Job URL Tracker API")

# Enable CORS for frontend UI interaction
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for incoming JSON data
class JobUrlRecord(BaseModel):
    url: str
    date: str  # Expected format: DD-MM-YY
    status: str

    @field_validator('date')
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%d-%m-%y")
            return v
        except ValueError:
            raise ValueError("Date must be in DD-MM-YY format")


class JobUrlUpdate(BaseModel):
    url: str | None = None
    date: str | None = None
    status: str | None = None


class CareerLinkRequest(BaseModel):
    url: str
    date: str | None = None  # Format: DD-MM-YY (defaults to current date if omitted)
    status: str | None = "Pending"


@app.get("/link")
async def get_link_page():
    """
    Serve the career link submission UI page.
    """
    html_path = os.path.join(BASE_DIR, "link.html")
    if os.path.exists(html_path):
        return FileResponse(html_path)
    raise HTTPException(status_code=404, detail="link.html page not found")


@app.post("/link")
async def save_career_link(record: CareerLinkRequest):
    """
    Save a career page job link and current date to Supabase.
    """
    try:
        # Default to current server date in DD-MM-YY format if not provided
        save_date = record.date.strip() if record.date and record.date.strip() else datetime.now().strftime("%d-%m-%y")
        
        # Validate format
        datetime.strptime(save_date, "%d-%m-%y")
        
        status = record.status if record.status else "Pending"

        response = supabase.table('job_url').insert({
            "url": record.url,
            "date": save_date,
            "status": status
        }).execute()

        saved_data = response.data if hasattr(response, 'data') else response
        return {
            "message": "Career page job link saved successfully",
            "saved_date": save_date,
            "data": saved_data
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Must be DD-MM-YY")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/store_record")
async def store_record(record: JobUrlRecord):
    """
    Create a new job URL record in Supabase.
    """
    try:
        data, count = supabase.table('job_url').insert({
            "url": record.url,
            "date": record.date,
            "status": record.status
        }).execute()
        
        return {"message": "Record stored successfully", "data": data[1] if len(data) > 1 else data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fetch_by_date")
async def fetch_by_date(date: str):
    """
    Fetch job URL records matching a specific date (DD-MM-YY).
    """
    try:
        datetime.strptime(date, "%d-%m-%y")
        
        response = supabase.table('job_url').select("*").eq("date", date).execute()
        records = response.data
        
        if not records:
            return {"message": "No records found for this date", "data": []}
            
        return {"message": f"Found {len(records)} records", "data": records}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Must be DD-MM-YY")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/update_record/{record_id}")
async def update_record(record_id: int, record: JobUrlUpdate):
    """
    Update an existing job URL record by ID.
    """
    update_data = {k: v for k, v in record.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields provided for update")
        
    try:
        data, count = supabase.table('job_url').update(update_data).eq("id", record_id).execute()
        return {"message": "Record updated successfully", "data": data[1] if len(data) > 1 else data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/delete_record/{record_id}")
async def delete_record(record_id: int):
    """
    Delete a job URL record by ID.
    """
    try:
        data, count = supabase.table('job_url').delete().eq("id", record_id).execute()
        return {"message": "Record deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount static files (HTML, CSS, JS) from module directory so UI works on localhost:8001
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")


