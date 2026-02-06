from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import uuid, os, shutil

app = FastAPI(title="PDF Converter API")

BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "PDF Converter API is live",
        "endpoints": [
            "/pdf-to-excel",
            "/pdf-to-word",
            "/docs"
        ]
    }

@app.post("/pdf-to-excel")
async def pdf_to_excel(file: UploadFile = File(...)):
    uid = str(uuid.uuid4())
    pdf_path = f"{BASE_DIR}/{uid}.pdf"
    xlsx_path = f"{BASE_DIR}/{uid}.xlsx"

    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # dummy excel (for now)
    with open(xlsx_path, "w") as f:
        f.write("Excel created")

    return FileResponse(
        xlsx_path,
        filename="converted.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    uid = str(uuid.uuid4())
    pdf_path = f"{BASE_DIR}/{uid}.pdf"
    docx_path = f"{BASE_DIR}/{uid}.docx"

    with open(pdf_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with open(docx_path, "w") as f:
        f.write("Word created")

    return FileResponse(
        docx_path,
        filename="converted.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
