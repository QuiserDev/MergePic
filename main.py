import mimetypes
import os
import uuid
from typing import List

from fastapi import FastAPI, File, UploadFile
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="template")

IMAGES_DIR = "images"
os.makedirs(IMAGES_DIR, exist_ok=True)


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    subfolder_id = uuid.uuid4().hex[:12]
    subfolder_path = os.path.join(IMAGES_DIR, subfolder_id)
    os.makedirs(subfolder_path, exist_ok=True)

    uploaded = []
    for idx, file in enumerate(files, start=1):
        content = await file.read()

        if file.filename:
            safe_name = os.path.basename(file.filename)
        else:
            ext = mimetypes.guess_extension(file.content_type or "") or ""
            safe_name = f"unnamed{ext}"

        save_name = f"{idx:02d}-{safe_name}"
        path = os.path.join(subfolder_path, save_name)

        with open(path, "wb") as f:
            f.write(content)

        await file.close()

        uploaded.append({
            "filename": file.filename or safe_name,
            "content_type": file.content_type,
            "size": len(content),
        })

    return {
        "subfolder": subfolder_id,
        "files": uploaded,
    }
