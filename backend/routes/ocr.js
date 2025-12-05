const express = require('express');
const router = express.Router();
const multer = require('multer');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Multer setup: allow both images and PDFs
const storage = multer.diskStorage({
    destination: (req, file, cb) => {
        cb(null, 'uploads/');
    },
    filename: (req, file, cb) => {
        cb(null, Date.now() + '-' + file.originalname);
    }
});

const upload = multer({
    storage,
    fileFilter: (req, file, cb) => {
        // Check file extension instead of MIME type (more reliable)
        const allowedExt = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.pdf'];
        const ext = path.extname(file.originalname).toLowerCase();
        const allowedMimeTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'application/pdf'];
        
        // Accept if extension is allowed, OR if MIME type is in the allowed list
        if (allowedExt.includes(ext) || allowedMimeTypes.includes(file.mimetype)) {
            cb(null, true);
        } else {
            cb(new Error(`File type not allowed: ${file.mimetype}. Supported: ${allowedExt.join(', ')}`));
        }
    }
});

router.post('/extract', upload.single('document'), (req, res) => {
    if (!req.file) {
        return res.status(400).json({ error: 'No file uploaded' });
    }

    const filePath = path.resolve(req.file.path);
    const scriptPath = path.resolve(__dirname, '../../ai-models/ocr_service.py');

    console.log(`Processing file: ${filePath} (${req.file.mimetype})`);
    console.log(`Using script: ${scriptPath}`);

    // Call Python script with timeout
    const pythonProcess = spawn('python', [scriptPath, filePath], {
        timeout: 60000  // 60 second timeout
    });

    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorString += data.toString();
        console.error('Python stderr:', data.toString());
    });

    pythonProcess.on('close', (code) => {
        console.log(`Child process exited with code ${code}`);
        
        if (code !== 0) {
            console.error(`OCR Error: ${errorString}`);
            return res.status(500).json({ 
                error: 'OCR processing failed', 
                details: errorString || 'Unknown error' 
            });
        }

        try {
            console.log('Raw data length:', dataString.length);
            console.log('Raw data (first 200 chars):', dataString.substring(0, 200));
            
            // Try to parse the entire output as JSON
            let jsonResult = null;
            
            // First try: parse the entire string as JSON
            try {
                jsonResult = JSON.parse(dataString);
                console.log('Successfully parsed as single JSON object');
            } catch (e) {
                console.log('Failed to parse as single JSON, trying line-by-line');
                // Fallback: try line by line
                const lines = dataString.trim().split('\n');
                for (let i = lines.length - 1; i >= 0; i--) {
                    try {
                        jsonResult = JSON.parse(lines[i]);
                        console.log('Parsed from line', i);
                        break;
                    } catch (e2) {
                        continue;
                    }
                }
            }

            if (!jsonResult) {
                throw new Error(`No valid JSON output from OCR script. Got: ${dataString.substring(0, 300)}`);
            }

            console.log('Parsed JSON result:', JSON.stringify(jsonResult, null, 2).substring(0, 300));

            // Handle errors from the Python script
            if (jsonResult.error) {
                console.error('OCR extraction error:', jsonResult.error);
                return res.status(500).json({ 
                    error: jsonResult.error,
                    details: jsonResult
                });
            }

            // Return result with image/PDF path for display
            res.json({ 
                success: true, 
                data: jsonResult, 
                filePath: `/uploads/${req.file.filename}`,
                fileType: req.file.mimetype
            });
        } catch (err) {
            console.error('JSON Parse Error:', err);
            res.status(500).json({ 
                error: 'Failed to parse OCR output', 
                raw: dataString.substring(0, 500) 
            });
        }
    });

    pythonProcess.on('error', (err) => {
        console.error('Process error:', err);
        res.status(500).json({ error: 'Failed to start OCR process', details: err.message });
    });
});

module.exports = router;
