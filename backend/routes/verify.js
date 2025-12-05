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

    console.log('Verification request:');
    console.log('OCR Data:', ocrJson.substring(0, 100) + '...');
    console.log('User Data:', userJson.substring(0, 100) + '...');

    const pythonProcess = spawn('python', [scriptPath, '--ocr', ocrJson, '--user', userJson]);

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
        console.log(`Verification process exit code: ${code}`);
        
        if (code !== 0) {
            console.error(`Verification Script Error: ${errorString}`);
            return res.status(500).json({ 
                error: 'Verification failed', 
                details: errorString,
                results: [],
                averageConfidence: 0
            });
        }

        try {
            console.log('Raw verification response:', dataString.substring(0, 200) + '...');
            const result = JSON.parse(dataString);

            // Check for errors in result
            if (result.error) {
                console.error('Verification error:', result.error);
                return res.status(400).json({ 
                    error: result.error,
                    results: [],
                    averageConfidence: 0
                });
            }

            // Return the verification results as is from the Python script
            res.json({
                results: result.results || [],
                averageConfidence: result.averageConfidence || 0,
                totalFields: result.totalFields || 0,
                matchedFields: result.matchedFields || 0,
                partialMatchFields: result.partialMatchFields || 0,
                mismatchFields: result.mismatchFields || 0
            });
        } catch (err) {
            console.error('JSON Parse Error:', err);
            console.error('Raw output:', dataString);
            res.status(500).json({ 
                error: 'Failed to parse verification output', 
                raw: dataString.substring(0, 500),
                results: [],
                averageConfidence: 0
            });
        }
    });

    pythonProcess.on('error', (err) => {
        console.error('Process error:', err);
        res.status(500).json({ 
            error: 'Failed to start verification process', 
            details: err.message,
            results: [],
            averageConfidence: 0
        });
    });
});

module.exports = router;
