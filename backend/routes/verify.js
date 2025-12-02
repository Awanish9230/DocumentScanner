const express = require('express');
const router = express.Router();

/* -------------------------------
   Levenshtein Distance (Fixed)
--------------------------------*/
const levenshtein = (a, b) => {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;

    const matrix = [];

    // Initialize matrix
    for (let i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }
    for (let j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }

    // Compute distance
    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1,
                    matrix[i][j - 1] + 1,
                    matrix[i - 1][j] + 1
                );
            }
        }
    }

    return matrix[b.length][a.length];
};


/* -------------------------------
   Verification Route
--------------------------------*/
router.post('/', (req, res) => {
    const { ocrData, userData } = req.body;

    if (!ocrData || !userData) {
        return res.status(400).json({ error: 'Missing data for verification' });
    }

    const results = [];
    let totalScore = 0;
    let fieldCount = 0;

    // Build dynamic keys list
    const keysSet = new Set();

    Object.keys(userData || {}).forEach(k => keysSet.add(k));

    if (ocrData && typeof ocrData === 'object') {
        if (ocrData.fields && typeof ocrData.fields === 'object') {
            Object.keys(ocrData.fields).forEach(k => keysSet.add(k));
        } else {
            Object.keys(ocrData).forEach(k => keysSet.add(k));
        }
    }

    for (const key of keysSet) {
        // Skip unnecessary meta keys
        if (!userData.hasOwnProperty(key) && (key === 'lines' || key === 'raw_text' || key === 'average_confidence')) continue;
        if (key.endsWith('_confidence')) continue;

        const userValue = (userData[key] || '').toString();

        // Get OCR field value
        let ocrValue = '';
        if (ocrData && typeof ocrData === 'object') {
            if (ocrData[key]) ocrValue = ocrData[key];
            else if (ocrData.fields && ocrData.fields[key]) ocrValue = ocrData.fields[key];
        }
        ocrValue = (ocrValue || '').toString();

        // OCR confidence detection
        let ocrConf = 0;
        if (ocrData && typeof ocrData === 'object') {
            if (ocrData[`${key}_confidence`] !== undefined) {
                ocrConf = Number(ocrData[`${key}_confidence`]) || 0;
            } else if (ocrData.fields && ocrData.fields[`${key}_confidence`] !== undefined) {
                ocrConf = Number(ocrData.fields[`${key}_confidence`]) || 0;
            }
        }

        const uTrim = userValue.trim();
        const oTrim = ocrValue.trim();

        // Case 1: Both empty
        if (!uTrim && !oTrim) {
            results.push({
                field: key,
                ocrValue: '',
                userValue: '',
                similarity: '0.00',
                ocr_confidence: ocrConf,
                combinedScore: '0.00',
                status: 'Not Provided',
                notes: 'No value provided by either OCR or user'
            });
            fieldCount++;
            continue;
        }

        // Case 2: User added field manually
        if (uTrim && !oTrim) {
            results.push({
                field: key,
                ocrValue: '',
                userValue: uTrim,
                similarity: '0.00',
                ocr_confidence: ocrConf,
                combinedScore: '0.00',
                status: 'User Added',
                notes: 'Value provided by user but not detected by OCR'
            });
            fieldCount++;
            continue;
        }

        // Case 3: OCR has value but user left empty
        if (oTrim && !uTrim) {
            results.push({
                field: key,
                ocrValue: oTrim,
                userValue: '',
                similarity: '0.00',
                ocr_confidence: ocrConf,
                combinedScore: '0.00',
                status: 'OCR Present',
                notes: 'OCR found a value but user left the field empty'
            });
            fieldCount++;
            continue;
        }

        // Case 4: Both have values → calculate similarity
        const dist = levenshtein(uTrim.toLowerCase(), oTrim.toLowerCase());
        const maxLength = Math.max(uTrim.length, oTrim.length);
        const similarity = maxLength === 0 ? 0 : ((maxLength - dist) / maxLength) * 100;

        // Combine similarity and confidence
        const combinedScore = ocrConf > 0
            ? (0.55 * similarity + 0.45 * ocrConf)
            : similarity;

        const status =
            combinedScore >= 95 ? 'Match'
                : combinedScore >= 75 ? 'Partial Match'
                    : 'Mismatch';

        let notes = '';
        if (status === 'Mismatch') {
            notes = 'Values differ significantly; please verify the correct value';
        }

        results.push({
            field: key,
            ocrValue: oTrim,
            userValue: uTrim,
            similarity: similarity.toFixed(2),
            ocr_confidence: ocrConf,
            combinedScore: combinedScore.toFixed(2),
            status,
            notes
        });

        totalScore += combinedScore;
        fieldCount++;
    }

    const averageConfidence = fieldCount === 0 ? 0 : (totalScore / fieldCount).toFixed(2);

    res.json({
        results,
        averageConfidence
    });
});

module.exports = router;
