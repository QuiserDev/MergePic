import mimetypes
import os
import uuid
from typing import List

from fastapi import FastAPI, File, UploadFile
from fastapi.requests import Request
from fastapi.templating import Jinja2Templates

app = FastAPI()

templates = Jinja2Templates(directory="template")


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)):
    saved = {}
    for file in files:
        content = await file.read()

        if file.filename:
            safe_name = os.path.basename(file.filename)
        else:
            ext = mimetypes.guess_extension(file.content_type or "") or ""
            safe_name = f"unnamed{ext}"
        path = f"{uuid.uuid4().hex[:12]}-{safe_name}"

        with open(path, "wb") as f:
            f.write(content)

        await file.close()

        resp = {
            "content_type": file.content_type,
            "size": len(content),
        }
        saved[file.filename or safe_name] = resp
    return saved
