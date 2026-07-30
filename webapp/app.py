"""
app.py — local web frontend for the resume/cover-letter/cold-email pipeline.

Run:
    pip install flask
    python3 app.py
Then open http://127.0.0.1:5050 in your browser.
"""
import json
import os
import sys
import uuid
import traceback

from flask import Flask, request, jsonify, send_from_directory, render_template

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
from pipeline import run, slugify  # noqa: E402

OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "outputs")

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def generate():
    data = request.get_json(force=True, silent=True) or {}
    jd_text = (data.get("jd_text") or "").strip()
    company = (data.get("company") or "").strip()
    role = (data.get("role") or "").strip()

    if not jd_text:
        return jsonify({"error": "Paste a job description first."}), 400

    outdir_name = f"{slugify(company or 'Company')}_{slugify(role or 'Role')}_{uuid.uuid4().hex[:6]}"
    outdir = os.path.join(OUTPUTS_DIR, outdir_name)

    try:
        result = run(jd_text, company, role, outdir)
    except Exception as exc:
        return jsonify({"error": str(exc), "trace": traceback.format_exc()}), 500

    def rel(p):
        return os.path.relpath(p, OUTPUTS_DIR).replace(os.sep, "/")

    cold_email_text = ""
    try:
        with open(result["cold_email_txt"]) as f:
            cold_email_text = f.read()
    except OSError:
        pass

    return jsonify({
        "mode": result.get("mode", "unknown"),
        "jd_analysis": result.get("jd_analysis", {}),
        "resume_pdf": rel(result["resume_pdf"]),
        "cover_letter_pdf": rel(result["cover_letter_pdf"]),
        "cold_email_txt": rel(result["cold_email_txt"]),
        "cold_email_preview": cold_email_text,
    })


@app.route("/api/applications")
def applications():
    tracker_path = os.path.join(OUTPUTS_DIR, "applications_tracker.json")
    if not os.path.exists(tracker_path):
        return jsonify([])
    with open(tracker_path, encoding="utf-8") as handle:
        return jsonify(json.load(handle))


@app.route("/outputs/<path:filename>")
def download(filename):
    return send_from_directory(OUTPUTS_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    app.run(debug=True, port=5050, use_reloader=False)
