from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import json
import glob
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Drafts UI Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Parent directory containing the json files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@app.get("/api/drafts")
def get_drafts():
    """Reads all DDMMYY-COMPANY.json files in the parent directory and returns them."""
    drafts_data = []
    
    # Find all json files matching the pattern. 
    # To be safe, we'll just read all JSON files that look like they have a hyphen and don't match known static files
    json_files = glob.glob(os.path.join(BASE_DIR, "*.json"))
    
    for file_path in json_files:
        filename = os.path.basename(file_path)
        # Skip state.json or other non-draft files
        if filename in ["drafted_messages.json"] or "-" not in filename:
            continue
            
        try:
            # Parse DDMMYY-COMPANY.json
            parts = filename.replace(".json", "").split("-", 1)
            if len(parts) == 2:
                file_date = parts[0]
                company_name = parts[1]
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    if isinstance(content, list):
                        for item in content:
                            item['source_file'] = filename
                            item['parsed_company'] = company_name
                            item['parsed_date'] = file_date
                            drafts_data.append(item)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    return JSONResponse(content={"status": "success", "data": drafts_data})

# Serve static files from the current directory (ui/)
app.mount("/", StaticFiles(directory=os.path.dirname(os.path.abspath(__file__)), html=True), name="static")

if __name__ == "__main__":
    print("Starting Drafts UI server on http://localhost:8002")
    uvicorn.run(app, host="0.0.0.0", port=8002)
