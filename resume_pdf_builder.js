const fs = require("fs");
const PDFDocument = require("pdfkit");

const PAGE_WIDTH = 612;
const PAGE_HEIGHT = 792;
const MARGIN = 34;
const CONTENT_WIDTH = PAGE_WIDTH - (MARGIN * 2);

function compactText(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

function groupedBullets(items) {
  const groups = {};
  for (const item of items || []) {
    const key = item.chunk_id.split("_").slice(0, 2).join("_");
    (groups[key] = groups[key] || []).push(item.text);
  }
  return Object.values(groups);
}

function drawHeader(doc, profile, fontSize) {
  doc.font("Times-Bold").fontSize(fontSize + 5).text(compactText(profile.name), { align: "center" });
  doc.font("Times-Roman").fontSize(fontSize - 1).text(
    `${compactText(profile.location)} | ${compactText(profile.phone)} | ${compactText(profile.email)}`,
    { align: "center" },
  );

  const links = `${compactText(profile.linkedin)} | ${compactText(profile.github)}`;
  doc.fillColor("#1f4e79").text(links, { align: "center", underline: true });
  doc.fillColor("#111111");
  doc.moveDown(0.25);
  doc.moveTo(MARGIN, doc.y).lineTo(PAGE_WIDTH - MARGIN, doc.y).strokeColor("#777777").stroke();
  doc.strokeColor("#000000").moveDown(0.35);
}

function drawSection(doc, title, fontSize) {
  doc.font("Times-Bold").fontSize(fontSize + 1).text(title.toUpperCase(), { characterSpacing: 0.2 });
  doc.moveTo(MARGIN, doc.y - 1).lineTo(PAGE_WIDTH - MARGIN, doc.y - 1).strokeColor("#777777").stroke();
  doc.strokeColor("#000000").moveDown(0.18);
}

function drawBullets(doc, items, fontSize) {
  for (const item of items) {
    doc.font("Times-Roman").fontSize(fontSize).text(`• ${compactText(item)}`, {
      width: CONTENT_WIDTH - 8,
      indent: 8,
      paragraphGap: 1,
    });
  }
}

function renderResume(data, fontSize, outputPath) {
  const doc = new PDFDocument({ size: "LETTER", margins: { top: MARGIN, bottom: MARGIN, left: MARGIN, right: MARGIN }, autoFirstPage: true });
  const stream = fs.createWriteStream(outputPath);
  doc.pipe(stream);
  drawHeader(doc, data.profile, fontSize);

  drawSection(doc, "Professional Summary", fontSize);
  doc.font("Times-Roman").fontSize(fontSize).text(compactText(data.summary), { width: CONTENT_WIDTH, paragraphGap: 1 });
  doc.moveDown(0.3);

  drawSection(doc, "Technical Skills", fontSize);
  for (const [category, items] of Object.entries(data.skills_full || {})) {
    doc.font("Times-Bold").fontSize(fontSize).text(`${category}: `, { continued: true });
    doc.font("Times-Roman").text(items.join(", "), { width: CONTENT_WIDTH, paragraphGap: 1 });
  }
  doc.moveDown(0.25);

  drawSection(doc, "Professional Experience", fontSize);
  for (const bullets of groupedBullets(data.experience_bullets)) {
    const header = compactText(bullets[0]).split(":")[0];
    doc.font("Times-Bold").fontSize(fontSize).text(header, { paragraphGap: 1 });
    drawBullets(doc, [compactText(bullets[0]).replace(`${header}:`, ""), ...bullets.slice(1)], fontSize);
  }

  drawSection(doc, "Projects", fontSize);
  for (const bullets of groupedBullets(data.project_bullets)) {
    const header = compactText(bullets[0]).split(":")[0];
    doc.font("Times-Bold").fontSize(fontSize).text(header, { paragraphGap: 1 });
    drawBullets(doc, [compactText(bullets[0]).replace(`${header}:`, ""), ...bullets.slice(1)], fontSize);
  }

  drawSection(doc, "Education", fontSize);
  for (const education of data.education || []) {
    doc.font("Times-Roman").fontSize(fontSize).text(`${education.degree} | ${education.institution} | ${education.dates}`, { paragraphGap: 1 });
  }

  drawSection(doc, "Certifications", fontSize);
  drawBullets(doc, data.certifications || [], fontSize);

  drawSection(doc, "Key Traits", fontSize);
  doc.font("Times-Roman").fontSize(fontSize).text((data.key_traits || []).join(", "), { width: CONTENT_WIDTH });
  doc.end();
}

function main() {
  const [, , inputPath, outputPath] = process.argv;
  if (!inputPath || !outputPath) {
    console.error("Usage: node resume_pdf_builder.js resume_data.json output.pdf");
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(inputPath, "utf8"));
  renderResume(data, 7.4, outputPath);
}

main();