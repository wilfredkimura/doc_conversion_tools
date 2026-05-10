import os
import shutil
import uuid
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.requests import Request

from .converters import (
    PptxToMarkdownConverter,
    PdfToMarkdownConverter,
    PdfToPptxConverter,
    PdfToPptxConverter,
    DocxToMarkdownConverter,
    MarkdownToDocxConverter
)

app = FastAPI(title="Multi-Format Converter API")

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Cloud Detection
IS_CLOUD = os.getenv("SPACE_ID") is not None or os.getenv("RENDER") is not None

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
    "docx-to-md": DocxToMarkdownConverter(),
    "md-to-docx": MarkdownToDocxConverter()
}

class SaveRequest(BaseModel):
    file_id: str
    target_path: str
    original_name: str

@app.get("/")
async def read_index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/config")
async def get_config():
    return {
        "is_cloud": IS_CLOUD,
        "max_batch_size": 10,
        "allowed_formats": list(converters.keys())
    }

@app.post("/convert")
@limiter.limit("10/minute")
async def convert_files(
    request: Request,
    files: list[UploadFile] = File(...),
    format: str = Form(...)
):
    if format not in converters:
        raise HTTPException(status_code=400, detail="Invalid format selected.")

    results = []
    
    for file in files:
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

            results.append({
                "file_id": file_id,
                "filename": output_path.name,
                "preview": preview_content,
                "success": True
            })
        except Exception as e:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            results.append({
                "filename": file.filename,
                "success": False,
                "detail": str(e)
            })
            
    return {"results": results}

@app.get("/download/{file_id}/{filename}")
async def download_file(file_id: str, filename: str):
    file_path = UPLOAD_DIR / file_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, filename=filename)

@app.post("/save-local")
async def save_local(request: SaveRequest):
    if IS_CLOUD:
        raise HTTPException(status_code=501, detail="Local save is not available in cloud mode.")
    
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
        for item in source_dir.iterdir():
            dest = target_dir / item.name
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        
        return {"success": True, "message": f"Files saved to {request.target_path}", "path": request.target_path}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

@app.post("/open-folder")
async def open_folder(request: dict):
    if IS_CLOUD:
        raise HTTPException(status_code=501, detail="Folder access is not available in cloud mode.")
    
    path = request.get("path")
    if not path:
        raise HTTPException(status_code=400, detail="Path is required")
    
    path_obj = Path(path)
    if not path_obj.exists():
        raise HTTPException(status_code=404, detail="Path does not exist")
    
    try:
        import subprocess
        import platform

        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path])
        else:  # Linux and others
            subprocess.run(["xdg-open", path])
            
        return {"success": True}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "detail": str(e)}
        )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
