const fs = require("fs");
const PDFDocument = require("pdfkit");

function main() {
  const [, , inputPath, outputPath] = process.argv;
  if (!inputPath || !outputPath) {
    console.error("Usage: node cover_letter_pdf_builder.js letter.txt output.pdf");
    process.exit(1);
  }
  const text = fs.readFileSync(inputPath, "utf8").trim();
  const doc = new PDFDocument({ size: "LETTER", margins: { top: 54, bottom: 54, left: 62, right: 62 }, autoFirstPage: true });
  doc.pipe(fs.createWriteStream(outputPath));
  doc.font("Times-Roman").fontSize(11).text(text, { width: 488, lineGap: 2, paragraphGap: 10 });
  doc.end();
}

main();