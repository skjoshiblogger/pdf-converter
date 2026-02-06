from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
import pdfplumber
import pandas as pd
import uuid
import os
import shutil
import re

app = FastAPI(title="Bank Statement PDF to Excel")

BASE_DIR = "files"
os.makedirs(BASE_DIR, exist_ok=True)

@app.get("/")
def home():
    return {
        "status": "running",
        "service": "Bank Statement PDF to Excel",
        "endpoint": "/bank-statement-to-excel"
    }

def parse_amount(val):
    if not val:
        return ""
    val = val.replace(",", "").strip()
    return val if re.match(r"^-?\d+(\.\d+)?$", val) else ""

@app.post("/bank-statement-to-excel")
async def bank_statement_to_excel(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files allowed")

    uid = str(uuid.uuid4())
    pdf_path = f"{BASE_DIR}/{uid}.pdf"
    excel_path = f"{BASE_DIR}/{uid}.xlsx"

    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")

            for line in lines:
                # Common Indian bank format
                # DATE | DESCRIPTION | DEBIT | CREDIT | BALANCE
                match = re.match(
                    r"(\d{2}[-/]\d{2}[-/]\d{4})\s+(.*)\s+([\d,]*\.\d{2})?\s*([\d,]*\.\d{2})?\s+([\d,]*\.\d{2})",
                    line
                )

                if match:
                    date = match.group(1)
                    desc = match.group(2)
                    debit = parse_amount(match.group(3))
                    credit = parse_amount(match.group(4))
                    balance = parse_amount(match.group(5))

                    rows.append({
                        "Date": date,
                        "Description": desc,
                        "Debit": debit,
                        "Credit": credit,
                        "Balance": balance
                    })

    if not rows:
        raise HTTPException(
            status_code=422,
            detail="No transactions detected. Scanned PDFs need OCR (paid add-on)."
        )

    df = pd.DataFrame(rows)

    # Clean columns
    df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce")
    df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce")
    df["Balance"] = pd.to_numeric(df["Balance"], errors="coerce")

    df.to_excel(excel_path, index=False)

    return FileResponse(
        excel_path,
        filename="bank_statement.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
