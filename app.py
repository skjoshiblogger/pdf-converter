from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pdfplumber
import pandas as pd
import os
import uuid

app = Flask(__name__)
CORS(app)

UPLOAD_DIR = "files"
MAX_FILE_SIZE_MB = 5
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.route("/", methods=["GET"])
def home():
    return {"status": "Bank Statement API running"}

# ---------- VALIDATION ----------
def validate_pdf(file):
    if not file.filename.lower().endswith(".pdf"):
        return "Only PDF files allowed"
    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)
    if size_mb > MAX_FILE_SIZE_MB:
        return f"File too large. Max {MAX_FILE_SIZE_MB}MB allowed"
    return None

# ---------- BANK STATEMENT EXTRACT ----------
@app.route("/bank-statement", methods=["POST"])
def bank_statement():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    error = validate_pdf(file)
    if error:
        return jsonify({"error": error}), 400

    pdf_path = f"{UPLOAD_DIR}/{uuid.uuid4()}.pdf"
    xls_path = pdf_path.replace(".pdf", ".xlsx")
    file.save(pdf_path)

    rows = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if not table:
                continue

            for row in table[1:]:  # skip header
                if len(row) < 5:
                    continue
                rows.append({
                    "Date": row[0],
                    "Description": row[1],
                    "Debit": row[2],
                    "Credit": row[3],
                    "Balance": row[4]
                })

    if not rows:
        return jsonify({"error": "No bank data detected"}), 400

    df = pd.DataFrame(rows)
    df.to_excel(xls_path, index=False)

    return send_file(
        xls_path,
        as_attachment=True,
        download_name="bank_statement.xlsx"
    )

if __name__ == "__main__":
    app.run(debug=True)
