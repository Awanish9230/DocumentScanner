const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const Document = require('../models/Document');
const PDFDocument = require('pdfkit');
const fs = require('fs');
const path = require('path');

// Save OCR results for user and generate PDF
router.post('/save', auth, async (req, res) => {
  try {
    const { title, ocrData, imagePath } = req.body;
    // ensure uploads/pdfs exists
    const pdfDir = path.join(__dirname, '..', 'uploads', 'pdfs');
    if (!fs.existsSync(pdfDir)) fs.mkdirSync(pdfDir, { recursive: true });

    // create a PDF file using pdfkit
    const filename = `doc_${Date.now()}.pdf`;
    const filePath = path.join(pdfDir, filename);
    const doc = new PDFDocument();
    const writeStream = fs.createWriteStream(filePath);
    doc.pipe(writeStream);

    doc.fontSize(18).text(title || 'Extracted Document', { underline: true });
    doc.moveDown();

    // write OCR data
    if (typeof ocrData === 'string') {
      doc.fontSize(12).text(ocrData);
    } else if (Array.isArray(ocrData)) {
      ocrData.forEach((page, idx) => {
        doc.fontSize(12).text(`Page ${idx + 1}`);
        doc.fontSize(10).text(page || '');
        doc.addPage();
      });
    } else if (ocrData && typeof ocrData === 'object') {
      doc.fontSize(12).text(JSON.stringify(ocrData, null, 2));
    }

    doc.end();

    writeStream.on('finish', async () => {
      const newDoc = new Document({
        user: req.user.id,
        title: title || 'Untitled',
        ocrText: typeof ocrData === 'string' ? ocrData : JSON.stringify(ocrData),
        pdfPath: `/uploads/pdfs/${filename}`,
        imagePath
      });
      await newDoc.save();
      res.json({ success: true, doc: newDoc });
    });

    writeStream.on('error', (err) => {
      console.error('PDF write error', err);
      res.status(500).json({ message: 'Failed to create pdf' });
    });

  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Server error' });
  }
});

// List user's documents
router.get('/', auth, async (req, res) => {
  try {
    const docs = await Document.find({ user: req.user.id }).sort({ createdAt: -1 });
    res.json({ docs });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Server error' });
  }
});

// Delete document
router.delete('/:id', auth, async (req, res) => {
  try {
    const doc = await Document.findById(req.params.id);
    if (!doc) return res.status(404).json({ message: 'Not found' });
    if (doc.user.toString() !== req.user.id) return res.status(403).json({ message: 'Forbidden' });

    // remove PDF from disk if it exists
    if (doc.pdfPath) {
      const fullPath = path.join(__dirname, '..', doc.pdfPath.replace('/uploads/', 'uploads/'));
      if (fs.existsSync(fullPath)) fs.unlinkSync(fullPath);
    }

    await doc.deleteOne();
    res.json({ success: true });
  } catch (err) {
    console.error(err);
    res.status(500).json({ message: 'Server error' });
  }
});

module.exports = router;
