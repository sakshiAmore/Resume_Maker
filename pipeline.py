"""
pipeline.py — orchestrates the full JD -> resume + cover letter + cold email flow.

Usage:
    python3 pipeline.py --jd path/to/jd.txt --company "Acme Corp" --role "GenAI Engineer" --outdir outputs/Acme_GenAI

Set GROQ_API_KEY in your environment, or add it to groq_api_key.txt, for real LLM-generated output.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agents.jd_analyzer import analyze
from agents.resume_tailor import tailor_resume
from agents.cover_letter_agent import generate_cover_letter
from agents.cold_email_agent import generate_cold_email
from application_tracker import append_application
from resume_text_export import export_resume_text

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def slugify(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_") or "Untitled"


def run(jd_text: str, company: str, role: str, outdir: str, resume_text: str = ""):
    os.makedirs(outdir, exist_ok=True)

    print("Analyzing job description...")
    jd_analysis = analyze(jd_text)
    company = company or jd_analysis.get("company", "")
    role = role or jd_analysis.get("role_title", "")
    with open(os.path.join(outdir, "jd_analysis.json"), "w") as f:
        json.dump(jd_analysis, f, indent=2)

    print("Retrieving relevant experience + tailoring resume...")
    tailored = tailor_resume(jd_text, resume_text=resume_text)
    resume_json_path = os.path.join(outdir, "resume_data.json")
    with open(resume_json_path, "w") as f:
        json.dump(tailored, f, indent=2)

    print("Building one-page resume PDF...")
    resume_pdf_path = os.path.join(outdir, f"Resume_{slugify(company)}_{slugify(role)}.pdf")
    subprocess.run(
        ["node", os.path.join(PROJECT_DIR, "resume_pdf_builder.js"), resume_json_path, resume_pdf_path],
        check=True,
    )
    resume_txt_path = os.path.join(outdir, f"Resume_{slugify(company)}_{slugify(role)}.txt")
    export_resume_text(tailored, resume_txt_path)

    print("Generating cover letter...")
    letter = generate_cover_letter(jd_text, tailored, company=company, role_title=role)
    letter_txt_path = os.path.join(outdir, "cover_letter.txt")
    with open(letter_txt_path, "w") as f:
        f.write(letter)
    letter_pdf_path = os.path.join(outdir, f"CoverLetter_{slugify(company)}_{slugify(role)}.pdf")
    subprocess.run(
        ["node", os.path.join(PROJECT_DIR, "cover_letter_pdf_builder.js"), letter_txt_path, letter_pdf_path],
        check=True,
    )

    print("Generating cold email...")
    email = generate_cold_email(jd_text, tailored, company=company, role_title=role)
    email_path = os.path.join(outdir, f"ColdEmail_{slugify(company)}_{slugify(role)}.txt")
    with open(email_path, "w") as f:
        f.write(email)

    print(f"\nDone. Mode: {tailored.get('_mode', 'unknown')} "
          f"({'set GROQ_API_KEY or add groq_api_key.txt for LLM-generated content' if tailored.get('_mode') == 'template' else 'LLM-generated'})")
    print(f"Output folder: {outdir}")

    tracker_path = append_application(PROJECT_DIR, {
        "company": company or "Unknown company",
        "role": role or "Unknown role",
        "outdir": outdir,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "mode": tailored.get("_mode", "unknown"),
        "resume_pdf": os.path.relpath(resume_pdf_path, PROJECT_DIR),
        "cover_letter_pdf": os.path.relpath(letter_pdf_path, PROJECT_DIR),
        "cold_email_txt": os.path.relpath(email_path, PROJECT_DIR),
    })
    print(f"Application tracker: {tracker_path}")
    return {
        "mode": tailored.get("_mode", "unknown"),
        "resume_pdf": resume_pdf_path,
        "cover_letter_pdf": letter_pdf_path,
        "cold_email_txt": email_path,
        "jd_analysis": jd_analysis,
        "ats": tailored.get("ats", {}),
        "tracker_file": tracker_path,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jd", required=True, help="Path to a text file containing the job description")
    parser.add_argument("--company", default="")
    parser.add_argument("--role", default="")
    parser.add_argument("--outdir", default="outputs/latest")
    args = parser.parse_args()

    with open(args.jd) as f:
        jd_text = f.read()

    run(jd_text, args.company, args.role, args.outdir)
