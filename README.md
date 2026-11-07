# AI Resume / Cover Letter / Cold Email Pipeline

This project creates ATS-friendly application assets from the resume you upload:
resume PDF, cover letter PDF, cold email text, a plain-text resume export, and an
application tracker. The web app reads PDF, DOCX, and TXT resumes directly, then matches verified resume text to the job description. The local knowledge base remains available as a terminal fallback.

## What is included

- Resume PDF and plain-text resume export
- Cover letter PDF
- Cold email draft
- JD analysis and keyword extraction
- Application tracker in JSON and CSV
- Local web app for easy use

## Run it locally

```powershell
cd F:\ai_resume_pipeline
C:/Users/Saksh/AppData/Local/Programs/Python/Python313/python.exe -m pip install -r requirements.txt
npm install
C:/Users/Saksh/AppData/Local/Programs/Python/Python313/python.exe webapp/app.py
```

Then open http://127.0.0.1:5050. Upload a PDF, DOCX, or TXT resume and paste the target job description. Company and role fields are optional.

## Run the pipeline from the terminal

```powershell
C:/Users/Saksh/AppData/Local/Programs/Python/Python313/python.exe pipeline.py --jd samples/sample_jd_genai.txt --company "Acme Corp" --role "GenAI Engineer" --outdir outputs/Acme
```

With a real Groq key:

```powershell
$env:GROQ_API_KEY = "your-key-here"
```

## Output files

Each run creates:
- Resume_*.pdf
- Resume_*.txt
- CoverLetter_*.pdf
- ColdEmail_*.txt
- resume_data.json
- jd_analysis.json
- applications_tracker.json and applications_tracker.csv

## ATS tips

For best results with ATS and OCR systems:
- keep the header simple with name, phone, email, LinkedIn, GitHub
- use standard section headings
- prefer plain text and simple bullets
- include keywords from the target job description naturally

The app reports an ATS optimization score and the matched terms used in the generated application. Scores are a transparent keyword guide, not a guarantee of any external ATS vendor's result.

## GitHub push

```powershell
cd D:\ai_resume_pipeline
git add .
git commit -m "Build direct resume upload workflow"
git remote add origin https://github.com/sakshiAmore/Resume_Maker.git
git branch -M main
git push -u origin main
```
