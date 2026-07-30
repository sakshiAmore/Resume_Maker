/**
 * letter_docx_builder.js — builds a plain-text-style .docx (cover letter) in Times New Roman.
 * Usage: node letter_docx_builder.js letter.txt output.docx "Sender Name"
 */
const fs = require("fs");
const { Document, Packer, Paragraph, TextRun } = require("docx");

const FONT = "Times New Roman";

async function main() {
  const [, , inputPath, outputPath] = process.argv;
  const text = fs.readFileSync(inputPath, "utf-8");
  const paragraphs = text.split("\n\n").map(
    (para) => new Paragraph({
      spacing: { after: 200 },
      children: [new TextRun({ text: para.replace(/\n/g, " "), size: 22, font: FONT })],
    })
  );
  const doc = new Document({
    sections: [{
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 },
        },
      },
      children: paragraphs,
    }],
  });
  const buffer = await Packer.toBuffer(doc);
  fs.writeFileSync(outputPath, buffer);
  console.log(`Written: ${outputPath}`);
}

main();
