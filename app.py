from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import pdfplumber
import pandas as pd
import os
import uuid

# ---------------- APP SETUP ----------------
app = Flask(__name__)
CORS(app)

BASE_DIR = "files"
MAX_FILE_SIZE_MB = 5

os.makedirs(BASE_DIR, exist_ok=True)

# ---------------- HOME ----------------
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "PDF Bank Statement Converter API running",
        "endpoints": {
            "bank_statement": "/bank-statement (POST)"
        }
    })

# ---------------- VALIDATION ----------------
def validate_pdf(file):
    if not file.filename.lower().endswith(".pdf"):
        return "Only PDF files are allowed"

    file.seek(0, os.SEEK_END)
    size_mb = file.tell() / (1024 * 1024)
    file.seek(0)

    if size_mb > MAX_FILE_SIZE_MB:
        return f"File size exceeds {MAX_FILE_SIZE_MB}MB limit"

    return None

# ---------------- BANK STATEMENT EXTRACT ----------------
@app.route("/bank-statement", methods=["POST"])
def bank_statement():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    error = validate_pdf(file)
    if error:
        return jsonify({"error": error}), 400

    pdf_name = f"{uuid.uuid4()}.pdf"
    pdf_path = os.path.join(BASE_DIR, pdf_name)
    excel_path = pdf_path.replace(".pdf", ".xlsx")

    file.save(pdf_path)

    extracted_rows = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if not table or len(table) < 2:
                    continue

                headers = table[0]

                for row in table[1:]:
                    if len(row) < 5:
                        continue

                    extracted_rows.append({
                        "Date": row[0],
                        "Description": row[1],
                        "Debit": row[2],
                        "Credit": row[3],
                        "Balance": row[4]
                    })

        if not extracted_rows:
            return jsonify({"error": "No bank statement data detected"}), 400

        df = pd.DataFrame(extracted_rows)
        df.to_excel(excel_path, index=False)

        return send_file(
            excel_path,
            as_attachment=True,
            download_name="bank_statement.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    finally:
        # optional cleanup (keep files if debugging)
        pass

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
