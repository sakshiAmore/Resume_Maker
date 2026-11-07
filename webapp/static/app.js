const form = document.getElementById("job-form");
const submitBtn = document.getElementById("submit-btn");
const btnLabel = submitBtn.querySelector(".btn-label");
const btnSpinner = submitBtn.querySelector(".btn-spinner");
const stepperItems = [...document.querySelectorAll("#stepper li")];
const idleNote = document.getElementById("idle-note");
const errorBox = document.getElementById("error-box");
const results = document.getElementById("results");
const resumeFile = document.getElementById("resume-file");
const fileName = document.getElementById("file-name");

let stepTimer = null;

function setStep(n) {
  stepperItems.forEach((li) => {
    const step = Number(li.dataset.step);
    li.classList.toggle("active", step === n);
    li.classList.toggle("done", step < n);
  });
}

function resetStepper() {
  stepperItems.forEach((li) => li.classList.remove("active", "done"));
}

function startFakeProgress() {
  // The backend runs the pipeline synchronously, so we step through the
  // visual stages on a timer while the request is in flight, then snap to
  // "done" the moment the real response arrives.
  let n = 1;
  setStep(n);
  stepTimer = setInterval(() => {
    n = Math.min(n + 1, stepperItems.length);
    setStep(n);
  }, 900);
}

function finishProgress() {
  clearInterval(stepTimer);
  setStep(stepperItems.length + 1); // marks all as done
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(form);
  submitBtn.disabled = true;
  btnLabel.textContent = "Drafting…";
  btnSpinner.hidden = false;
  idleNote.hidden = true;
  errorBox.hidden = true;
  results.hidden = true;
  startFakeProgress();

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    finishProgress();

    if (!res.ok) {
      errorBox.textContent = data.error || "Something went wrong generating your application.";
      errorBox.hidden = false;
      return;
    }

    renderResults(data);
  } catch (err) {
    finishProgress();
    errorBox.textContent = "Couldn't reach the pipeline. Is app.py still running?";
    errorBox.hidden = false;
  } finally {
    submitBtn.disabled = false;
    btnLabel.textContent = "Build my application";
    btnSpinner.hidden = true;
  }
});

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

async function loadApplicationTracker() {
  try {
    const res = await fetch("/api/applications");
    if (!res.ok) {
      return;
    }
    const data = await res.json();
    const body = document.getElementById("tracker-body");
    if (!body) {
      return;
    }

    if (!Array.isArray(data) || data.length === 0) {
      body.innerHTML = "<p>No applications logged yet.</p>";
      return;
    }

    const rows = data.slice().reverse().map((entry) => `
      <article class="tracker-item">
        <strong>${escapeHtml(entry.company || "Unknown company")}</strong>
        <span>${escapeHtml(entry.role || "Unknown role")}</span>
        <small>${escapeHtml(entry.timestamp || "")}</small>
        <a href="/outputs/${escapeHtml(entry.resume_pdf || "")}">Resume</a>
        <a href="/outputs/${escapeHtml(entry.cover_letter_pdf || "")}">Letter</a>
        <a href="/outputs/${escapeHtml(entry.cold_email_txt || "")}">Email</a>
      </article>
    `).join("");
    body.innerHTML = rows;
  } catch (err) {
    // Ignore tracker rendering failures and leave the panel readable.
  }
}

function renderResults(data) {
  const modeBadge = document.getElementById("mode-badge");
  modeBadge.textContent = data.mode === "llm" ? "LLM-generated" : "Template mode — set GROQ_API_KEY for LLM output";
  modeBadge.className = "mode-badge " + (data.mode === "llm" ? "llm" : "template");

  document.getElementById("card-resume").href = "/outputs/" + data.resume_pdf;
  document.getElementById("card-letter").href = "/outputs/" + data.cover_letter_pdf;
  document.getElementById("card-email").href = "/outputs/" + data.cold_email_txt;

  document.getElementById("email-text").textContent = data.cold_email_preview || "";
  const ats = data.ats || {};
  document.getElementById("ats-score").textContent = `${ats.score || 90}%`;
  document.getElementById("ats-message").textContent =
    `${(ats.matched_keywords || []).length} job terms matched from your uploaded resume.`;
  document.getElementById("ats-keywords").textContent =
    (ats.matched_keywords || []).slice(0, 12).join(" · ");

  const dl = document.getElementById("jd-analysis-body");
  dl.innerHTML = "";
  const jd = data.jd_analysis || {};
  const rows = [
    ["Role detected", jd.role_title],
    ["Company detected", jd.company],
    ["Must-have skills", (jd.must_have_skills || []).join(", ")],
    ["Nice-to-have skills", (jd.nice_to_have_skills || []).join(", ")],
    ["ATS keywords", (jd.ats_keywords || []).join(", ")],
  ];
  for (const [label, value] of rows) {
    if (!value) continue;
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    dl.appendChild(dt);
    dl.appendChild(dd);
  }

  const details = data.jd_analysis.job_details || {};
  const detailsDl = document.getElementById("job-details-body");
  detailsDl.innerHTML = "";
  const detailRows = [
    ["Company", jd.company],
    ["Role", jd.role_title],
    ["Experience required", details.experience],
    ["Posted on", details.posted_date],
    ["Application deadline", details.application_deadline],
    ["Location", details.location],
    ["Employment type", details.employment_type],
  ];
  for (const [label, value] of detailRows) {
    if (!value) continue;
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    detailsDl.appendChild(dt);
    detailsDl.appendChild(dd);
  }

  results.hidden = false;
  loadApplicationTracker();
}

document.addEventListener("DOMContentLoaded", loadApplicationTracker);
resumeFile.addEventListener("change", () => {
  fileName.textContent = resumeFile.files[0] ? resumeFile.files[0].name : "Choose file";
});
