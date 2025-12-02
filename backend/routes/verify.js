const express = require('express');
const router = express.Router();
const { spawn } = require('child_process');
const path = require('path');

router.post('/', (req, res) => {
    const { ocrData, userData } = req.body;

    if (!ocrData || !userData) {
        return res.status(400).json({ error: 'Missing data for verification' });
    }

    const scriptPath = path.resolve(__dirname, '../../ai-models/verification_service.py');

    // Prepare arguments as JSON strings
    const ocrJson = JSON.stringify(ocrData);
    const userJson = JSON.stringify(userData);

    const pythonProcess = spawn('python', [scriptPath, '--ocr', ocrJson, '--user', userJson]);

    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
        dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        errorString += data.toString();
    });

    pythonProcess.on('close', (code) => {
        if (code !== 0) {
            console.error(`Verification Script Error: ${errorString}`);
            return res.status(500).json({ error: 'Verification failed', details: errorString });
        }

        try {
            const result = JSON.parse(dataString);
            res.json(result);
        } catch (err) {
            console.error('JSON Parse Error:', err);
            res.status(500).json({ error: 'Failed to parse verification output', raw: dataString });
        }
    });
});

module.exports = router;
