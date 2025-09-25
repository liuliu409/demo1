from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
import os
import uuid

from schema import ExportRequest
from services.export_service import process_export

# Load env
load_dotenv(override=True)
DATA_DIR = os.getenv("DATA_DIR", "data")
TEMP_DIR = os.getenv("TEMP_DIR", "temp_exports")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

app = FastAPI()

@app.post("/api/export/excel")
async def export_excel(request: ExportRequest):
    try:
        file_id = process_export(request, DATA_DIR, TEMP_DIR)
        return {
            "status": "success",
            "message": "Excel file created successfully.",
            "file_id": file_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")

@app.get("/api/downloads/{file_id}")
async def download_file(file_id: str):
    file_path = os.path.join(TEMP_DIR, f"export_{file_id}.xlsx")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found.")
    
    return FileResponse(
        file_path,
        filename=f"report_{uuid.uuid4()}.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
