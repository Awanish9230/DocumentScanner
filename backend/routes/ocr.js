const express = require('express');
const router = express.Router();
const multer = require('multer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Multer setup
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/');
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});

const upload = multer({ storage });

router.post('/extract', upload.single('document'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }

    const filePath = path.resolve(req.file.path);
    const scriptPath = path.resolve(__dirname, '../../ai-models/ocr_service.py');

    console.log(`Processing file: ${filePath}`);
    console.log(`Using script: ${scriptPath}`);

    // Call Python script
    const pythonProcess = spawn('python', [scriptPath, filePath]);

    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorString += data.toString();
    });

    pythonProcess.on('close', (code) => {
        console.log(`Child process exited with code ${code}`);
        if (code !== 0) {
            console.error(`OCR Error: ${errorString}`);
            return res.status(500).json({ error: 'OCR processing failed', details: errorString });
        }

        try {
            // Find the JSON part in the output (in case there are warnings)
            // We assume the script prints JSON as the last line or we try to parse the whole thing.
            // A safer way is to parse the last valid JSON line.
            const lines = dataString.trim().split('\n');
            let jsonResult = null;

            // Try to parse from the end
            for (let i = lines.length - 1; i >= 0; i--) {
                try {
                    jsonResult = JSON.parse(lines[i]);
                    break;
                } catch (e) {
                    continue;
                }
            }

            if (!jsonResult) {
                throw new Error('No valid JSON output from OCR script');
            }

            res.json({ success: true, data: jsonResult, imagePath: `/uploads/${req.file.filename}` });
        } catch (err) {
            console.error('JSON Parse Error:', err);
            res.status(500).json({ error: 'Failed to parse OCR output', raw: dataString });
        }
    });
});

module.exports = router;
