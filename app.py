from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import pdfplumber, pandas as pd
from docx import Document
import uuid, os

app = FastAPI()

BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)

@app.post("/pdf-to-excel")
async def pdf_to_excel(file: UploadFile = File(...)):
    pdf_path = f"{BASE_DIR}/{uuid.uuid4()}.pdf"
    excel_path = pdf_path.replace(".pdf", ".xlsx")

    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    tables = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                tables.extend(table)

    df = pd.DataFrame(tables)
    df.to_excel(excel_path, index=False)

    return FileResponse(excel_path, filename="output.xlsx")

@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    pdf_path = f"{BASE_DIR}/{uuid.uuid4()}.pdf"
    docx_path = pdf_path.replace(".pdf", ".docx")

    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    doc = Document()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            doc.add_paragraph(page.extract_text() or "")

    doc.save(docx_path)
    return FileResponse(docx_path, filename="output.docx")
