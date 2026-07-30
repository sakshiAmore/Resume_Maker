# AI Resume / Cover Letter / Cold Email Pipeline (Phase 1-2)

This is a working RAG pipeline: paste a job description in, get a JD-tailored,
ATS-safe one-page resume (PDF, Times New Roman) + a one-page cover letter (PDF) + a cold email out.
Everything is grounded in `knowledge_base.json` — the pipeline never invents
experience you don't have.

## What's here

```
knowledge_base.json      Your real experience/projects/skills, chunked for retrieval
retriever.py             RAG retrieval (TF-IDF now; swap-in point for real embeddings documented inside)
llm_client.py            Groq API wrapper — works with a key, falls back to template mode without one
agents/
  jd_analyzer.py         Extracts role/company/keywords from a JD
  resume_tailor.py       Retrieves relevant chunks, tailors resume content to the JD
  cover_letter_agent.py  Generates the cover letter
  cold_email_agent.py    Generates the cold outreach email
resume_pdf_builder.js    Builds the ATS-safe one-page resume PDF
cover_letter_pdf_builder.js  Builds the one-page cover letter PDF
pipeline.py              Orchestrates the whole flow end-to-end
samples/sample_jd_genai.txt   A test JD to try it on
outputs/                 Generated output from the test run
```

## Running it

```bash
pip install -r requirements.txt
npm install             # installs DOCX/PDF generation dependencies

# Without an API key — runs in template mode (still fully functional, just not LLM-rewritten)
python3 pipeline.py --jd samples/sample_jd_genai.txt --company "Acme Corp" --role "GenAI Engineer" --outdir outputs/Acme

# With real Groq LLM generation (PowerShell)
$env:GROQ_API_KEY = "gsk_..."
python3 pipeline.py --jd path/to/real_jd.txt --company "Acme Corp" --role "GenAI Engineer" --outdir outputs/Acme
```

Output: `Resume_<Company>_<Role>.pdf`, `CoverLetter_<Company>_<Role>.pdf`,
`ColdEmail_<Company>_<Role>.txt`, plus `resume_data.json` and `jd_analysis.json`
for debugging/auditing what was retrieved and generated.

## What "template mode" vs "LLM mode" means

Without `ANTHROPIC_API_KEY` set, every agent falls back to assembling output
directly from the retrieved knowledge-base chunks (no rewriting) — so you can
run and inspect the entire pipeline right now, for free, with zero setup.
With a key set, the same agents call Groq to intelligently rewrite/select
bullets to mirror the JD's language, while still only using retrieved
(real) facts as source material.

## Known gaps / next steps (not built yet, see the PRD for the full roadmap)

- **Google Drive integration** — not wired up yet. Add a `drive_uploader.py`
  using the Google Drive API (OAuth2) to push the `outputs/<folder>/` contents
  into your `/JobApplicationAI/Applications/...` structure automatically.
- **Real embeddings** — `retriever.py` uses TF-IDF right now because this dev
  sandbox can't reach huggingface.co to download embedding models. Swap in
  `sentence-transformers` + FAISS on your own machine (code stub is in
  `retriever.py`) for meaningfully better retrieval quality.
- **Auto-apply agent** — not built. This needs Playwright running against
  live LinkedIn/job-site sessions with a human-confirm-before-submit gate
  (see PRD §12). Best built and tested on your own machine, not in a shared
  dev sandbox, since it needs your real logged-in session.
- **ATS scoring engine** (rule-based checklist from PRD §8/9) — not built in
  this pass; you picked Phase 1-2 (RAG + generators). Say the word and I'll
  build that next — it's a self-contained module that doesn't depend on
  anything else here.

## Extending the knowledge base

`knowledge_base.json` is hand-populated from your resume right now. To make
this generalize to future updates without manual JSON editing, add an
ingestion script that parses a resume file (docx/pdf) into this same chunk
schema — happy to build that next too.
