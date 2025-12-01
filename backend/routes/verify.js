const express = require('express');
const router = express.Router();

// Levenshtein distance for fuzzy matching
const levenshtein = (a, b) => {
    if (a.length === 0) return b.length;
    if (b.length === 0) return a.length;

    const matrix = [];

    for (let i = 0; i <= b.length; i++) {
        matrix[i] = [i];
    }

    for (let j = 0; j <= a.length; j++) {
        matrix[0][j] = j;
    }

    for (let i = 1; i <= b.length; i++) {
        for (let j = 1; j <= a.length; j++) {
            if (b.charAt(i - 1) === a.charAt(j - 1)) {
                matrix[i][j] = matrix[i - 1][j - 1];
            } else {
                matrix[i][j] = Math.min(
                    matrix[i - 1][j - 1] + 1,
                    Math.min(matrix[i][j - 1] + 1, matrix[i - 1][j] + 1)
                );
            }
        }
    }

    return matrix[b.length][a.length];
};

router.post('/', (req, res) => {
    const { ocrData, userData } = req.body;

    if (!ocrData || !userData) {
        return res.status(400).json({ error: 'Missing data for verification' });
    }

    const results = [];
    let totalScore = 0;
    let fieldCount = 0;

    for (const key in userData) {
        if (userData.hasOwnProperty(key)) {
            const userValue = userData[key] || '';
            const ocrValue = ocrData[key] || '';

            const dist = levenshtein(userValue.toLowerCase(), ocrValue.toLowerCase());
            const maxLength = Math.max(userValue.length, ocrValue.length);
            const similarity = maxLength === 0 ? 100 : ((maxLength - dist) / maxLength) * 100;

            const isMatch = similarity === 100;
            const status = isMatch ? 'Match' : (similarity > 80 ? 'Partial Match' : 'Mismatch');

            results.push({
                field: key,
                ocrValue,
                userValue,
                similarity: similarity.toFixed(2),
                status
            });

            totalScore += similarity;
            fieldCount++;
        }
    }

    const averageConfidence = fieldCount === 0 ? 0 : (totalScore / fieldCount).toFixed(2);

    res.json({
        results,
        averageConfidence
    });
});

module.exports = router;
