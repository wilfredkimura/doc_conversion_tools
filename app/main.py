import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from converters import (
    PptxToMarkdownConverter,
    PdfToMarkdownConverter,
    PdfToPptxConverter,
    PptxToPdfConverter
)

app = FastAPI(title="Multi-Format Converter API")

# Configuration
BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "app" / "static"

UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Converters instances
converters = {
    "pptx-to-md": PptxToMarkdownConverter(),
    "pdf-to-md": PdfToMarkdownConverter(),
    "pdf-to-pptx": PdfToPptxConverter(),
    "pptx-to-pdf": PptxToPdfConverter()
}

class SaveRequest(BaseModel):
    file_id: str
    target_path: str
    original_name: str

@app.get("/")
async def read_index():
    return FileResponse(STATIC_DIR / "index.html")

@app.post("/convert")
async def convert_file(
    file: UploadFile = File(...),
    format: str = Form(...)
):
    if format not in converters:
        raise HTTPException(status_code=400, detail="Invalid format selected.")

    # Save uploaded file temporarily
    file_id = str(uuid.uuid4())
    temp_dir = UPLOAD_DIR / file_id
    temp_dir.mkdir()
    
    input_path = temp_dir / file.filename
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        converter = converters[format]
        output_path = converter.convert(input_path, temp_dir)
        
        # Check if it's a markdown file for preview
        preview_content = None
        if output_path.suffix == ".md":
            with open(output_path, "r", encoding="utf-8") as f:
                preview_content = f.read()

        return {
            "file_id": file_id,
            "filename": output_path.name,
            "preview": preview_content,
            "success": True
        }
    except Exception as e:
        shutil.rmtree(temp_dir)
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.get("/download/{file_id}/{filename}")
async def download_file(file_id: str, filename: str):
    file_path = UPLOAD_DIR / file_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, filename=filename)

@app.post("/save-local")
async def save_local(request: SaveRequest):
    source_dir = UPLOAD_DIR / request.file_id
    if not source_dir.exists():
        raise HTTPException(status_code=404, detail="Converted file session not found.")
    
    # Find the converted file in the source dir (ignoring the original upload)
    # Usually it has a different extension or name
    # For now, we'll assume the converted file is the one that's NOT the input
    files = list(source_dir.glob("*"))
    # We'll just look for the one that was returned in the convert response
    # But for simplicity, let's just use the filename from the request if provided
    
    target_dir = Path(request.target_path)
    if not target_dir.exists():
        try:
            target_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid target path: {str(e)}")

    try:
        # Move all files (including images if any) to the target path
        # But specifically the main file should keep its original name or similar
        # If it's a directory (images), we move that too
        for item in source_dir.iterdir():
            dest = target_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        
        return {"success": True, "message": f"Files saved to {request.target_path}"}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
