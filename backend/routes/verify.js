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

            // Transform the verification_result structure to match frontend expectations
            const verificationResult = result.verification_result || {};
            const results = [];

            // Process standard fields
            for (const [field, data] of Object.entries(verificationResult)) {
                if (field === 'dynamic_field_results' || field === 'overall_accuracy' ||
                    field.startsWith('fields_')) {
                    continue; // Skip metadata fields
                }

                results.push({
                    field: field,
                    status: data.match_status === 'match' ? 'Match' :
                        data.match_status === 'partial_match' ? 'Partial Match' : 'Mismatch',
                    similarity: data.confidence_score || 0,
                    ocrValue: data.ocr_value || '',
                    userValue: data.user_value || '',
                    ocr_confidence: 85, // Default OCR confidence from EasyOCR
                    combinedScore: data.confidence_score || 0
                });
            }

            // Process dynamic fields
            if (verificationResult.dynamic_field_results) {
                for (const [field, data] of Object.entries(verificationResult.dynamic_field_results)) {
                    results.push({
                        field: field,
                        status: data.match_status === 'match' ? 'Match' :
                            data.match_status === 'partial_match' ? 'Partial Match' : 'Mismatch',
                        similarity: data.confidence_score || 0,
                        ocrValue: data.ocr_value || '',
                        userValue: data.user_value || '',
                        ocr_confidence: 85,
                        combinedScore: data.confidence_score || 0
                    });
                }
            }

            res.json({
                results: results,
                averageConfidence: verificationResult.overall_accuracy || 0
            });
        } catch (err) {
            console.error('JSON Parse Error:', err);
            res.status(500).json({ error: 'Failed to parse verification output', raw: dataString });
        }
    });
});

module.exports = router;
