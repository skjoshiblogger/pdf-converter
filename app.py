from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import pdfplumber
import pandas as pd
import re
import uuid
import os

app = FastAPI(title="Bank Statement to Excel Converter")

UPLOAD_DIR = "/tmp"

DATE_REGEX = re.compile(r"\d{2}[-/]\d{2}[-/]\d{4}")
AMOUNT_REGEX = re.compile(r"\d{1,3}(?:,\d{3})*(?:\.\d{2})?")

@app.post("/bank-statement-to-excel")
async def bank_statement_to_excel(file: UploadFile = File(...)):

    # ---------- Validation ----------
    if not file.filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content={"error": "Only PDF files are allowed"}
        )

    pdf_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.pdf")
    excel_path = pdf_path.replace(".pdf", ".xlsx")

    # ---------- Save PDF ----------
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    transactions = []

    # ---------- PDF Parsing ----------
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                lines = text.split("\n")

                for line in lines:
                    date_match = DATE_REGEX.search(line)
                    if not date_match:
                        continue

                    date = date_match.group()
                    amounts = AMOUNT_REGEX.findall(line)

                    debit = ""
                    credit = ""
                    balance = ""

                    if len(amounts) >= 2:
                        balance = amounts[-1]
                        txn_amount = amounts[-2]

                        upper_line = line.upper()

                        if "CR" in upper_line or "CREDIT" in upper_line:
                            credit = txn_amount
                        elif "DR" in upper_line or "DEBIT" in upper_line:
                            debit = txn_amount
                        else:
                            # Default assumption (most Indian banks)
                            debit = txn_amount

                    # ---------- Clean Description ----------
                    description = line
                    description = description.replace(date, "")

                    for amt in amounts:
                        description = description.replace(amt, "")

                    description = (
                        description
                        .replace("DR", "")
                        .replace("CR", "")
                        .replace("Debit", "")
                        .replace("Credit", "")
                        .strip()
                    )

                    transactions.append([
                        date,
                        description,
                        debit,
                        credit,
                        balance
                    ])

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"PDF processing failed: {str(e)}"}
        )

    if not transactions:
        return JSONResponse(
            status_code=400,
            content={"error": "No transactions detected in PDF"}
        )

    # ---------- Create Excel ----------
    df = pd.DataFrame(
        transactions,
        columns=["Date", "Description", "Debit", "Credit", "Balance"]
    )

    df.to_excel(excel_path, index=False)

    # ---------- Return File ----------
    return FileResponse(
        excel_path,
        filename="bank_statement.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
