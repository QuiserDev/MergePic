import time
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

        with open(str(time.time()) + "-" + str(file.filename), "wb") as f:
            f.write(content)

        resp = {
            "content_type": file.content_type,
            "size": len(content),
        }
        saved[file.filename] = resp
    return saved
