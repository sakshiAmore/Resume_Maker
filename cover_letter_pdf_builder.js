const fs = require("fs");
const PDFDocument = require("pdfkit");

function main() {
  const [, , inputPath, outputPath] = process.argv;
  if (!inputPath || !outputPath) {
    console.error("Usage: node cover_letter_pdf_builder.js letter.txt output.pdf");
    process.exit(1);
  }
  const text = fs.readFileSync(inputPath, "utf8").trim();
  const doc = new PDFDocument({ size: "A4", margins: { top: 54, bottom: 54, left: 60, right: 60 }, autoFirstPage: true });
  doc.pipe(fs.createWriteStream(outputPath));
  doc.font("Times-Roman").fontSize(10.8).text(text, { width: 475, lineGap: 1.8, paragraphGap: 8 });
  doc.end();
}

main();