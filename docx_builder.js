/**
 * docx_builder.js — builds an ATS-safe resume .docx from tailored resume JSON.
 *
 * Usage: node docx_builder.js resume_data.json output.docx
 *
 * ATS rules enforced (see PRD section 9):
 *  - Times New Roman throughout
 *  - Single column, no tables/text boxes/images
 *  - Contact info in body (not header/footer)
 *  - Standard section names in the same order as the reference resume
 */
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  AlignmentType, BorderStyle,
} = require("docx");

const FONT = "Times New Roman";

function nameHeader(profile) {
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: profile.name, bold: true, size: 32, font: FONT })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({
        text: `${profile.location} | ${profile.phone} | ${profile.email}`,
        size: 20, font: FONT,
      })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: `${profile.linkedin} | ${profile.github}`, size: 20, font: FONT })],
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, space: 4 } },
    }),
  ];
}

function sectionHeading(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 24, font: FONT, allCaps: true })],
  });
}

function bodyPara(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 60 },
    children: [new TextRun({ text, size: 21, font: FONT, ...opts })],
  });
}

function bulletPara(text) {
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { after: 40 },
    children: [new TextRun({ text, size: 21, font: FONT })],
  });
}

function buildResumeDoc(data) {
  const children = [];
  children.push(...nameHeader(data.profile));

  children.push(sectionHeading("Professional Summary"));
  children.push(bodyPara(data.summary));

  children.push(sectionHeading("Technical Skills"));
  for (const [category, items] of Object.entries(data.skills_full)) {
    children.push(bodyPara(`${category}: ${items.join(", ")}`));
  }

  children.push(sectionHeading("Professional Experience"));
  const expByCompany = {};
  for (const b of data.experience_bullets) {
    // chunk_id like exp_idbi_1 -> group by prefix (exp_idbi)
    const key = b.chunk_id.split("_").slice(0, 2).join("_");
    (expByCompany[key] = expByCompany[key] || []).push(b.text);
  }
  for (const bullets of Object.values(expByCompany)) {
    // first bullet text includes "Role at Company: ..." — split header out
    const firstMatch = bullets[0].match(/^(.*?):\s*(.*)$/);
    if (firstMatch) {
      children.push(bodyPara(firstMatch[1], { bold: true }));
      children.push(bulletPara(firstMatch[2]));
      for (const rest of bullets.slice(1)) {
        const m = rest.match(/^(.*?):\s*(.*)$/);
        children.push(bulletPara(m ? m[2] : rest));
      }
    }
  }

  children.push(sectionHeading("Projects"));
  const projByName = {};
  for (const b of data.project_bullets) {
    const key = b.chunk_id.split("_").slice(0, 2).join("_");
    (projByName[key] = projByName[key] || []).push(b.text);
  }
  for (const bullets of Object.values(projByName)) {
    const firstMatch = bullets[0].match(/^(.*?):\s*(.*)$/);
    if (firstMatch) {
      children.push(bodyPara(firstMatch[1], { bold: true }));
      children.push(bulletPara(firstMatch[2]));
      for (const rest of bullets.slice(1)) {
        const m = rest.match(/^(.*?):\s*(.*)$/);
        children.push(bulletPara(m ? m[2] : rest));
      }
    }
  }

  children.push(sectionHeading("Education"));
  for (const e of data.education) {
    children.push(bodyPara(`${e.degree} | ${e.institution} | ${e.dates}`));
  }

  children.push(sectionHeading("Certifications"));
  for (const c of data.certifications) {
    children.push(bulletPara(c));
  }

  children.push(sectionHeading("Key Traits"));
  children.push(bodyPara(data.key_traits.join(", ")));

  return new Document({
    sections: [{
      properties: {
        page: {
          size: { width: 12240, height: 15840 }, // US Letter
          margin: { top: 720, bottom: 720, left: 900, right: 900 },
        },
      },
      children,
    }],
  });
}

async function main() {
  const [, , inputPath, outputPath] = process.argv;
  if (!inputPath || !outputPath) {
    console.error("Usage: node docx_builder.js resume_data.json output.docx");
    process.exit(1);
  }
  const data = JSON.parse(fs.readFileSync(inputPath, "utf-8"));
  const doc = buildResumeDoc(data);
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`Written: ${outputPath}`);
}

main();
