from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import pandas as pd
from docx import Document
import uuid, os

app = FastAPI()

# CORS (required for browser)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "PDF Converter API running"}

# ---------------- PDF TO EXCEL ----------------
@app.post("/pdf-to-excel")
async def pdf_to_excel(file: UploadFile = File(...)):
    try:
        pdf_path = f"{BASE_DIR}/{uuid.uuid4()}.pdf"
        excel_path = pdf_path.replace(".pdf", ".xlsx")

        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        all_rows = []

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        all_rows.append(row)

        if not all_rows:
            return JSONResponse(
                status_code=400,
                content={"error": "No tables found in PDF"}
            )

        df = pd.DataFrame(all_rows)
        df.to_excel(excel_path, index=False, header=False)

        return FileResponse(
            excel_path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="converted.xlsx"
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ---------------- PDF TO WORD ----------------
@app.post("/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    try:
        pdf_path = f"{BASE_DIR}/{uuid.uuid4()}.pdf"
        docx_path = pdf_path.replace(".pdf", ".docx")

        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        doc = Document()

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    for line in text.split("\n"):
                        doc.add_paragraph(line)

        doc.save(docx_path)

        return FileResponse(
            docx_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="converted.docx"
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
