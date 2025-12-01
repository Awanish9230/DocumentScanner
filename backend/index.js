const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const path = require('path');
const fs = require('fs');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 5000;

// Middleware
app.use(cors());
app.use(express.json());
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Ensure uploads directory exists
const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) {
    fs.mkdirSync(uploadDir);
}

// Ensure uploads/pdfs exists for generated PDFs
const pdfDir = path.join(__dirname, 'uploads', 'pdfs');
if (!fs.existsSync(pdfDir)) {
    fs.mkdirSync(pdfDir, { recursive: true });
}

// Routes
const ocrRoutes = require('./routes/ocr');
const verifyRoutes = require('./routes/verify');
const authRoutes = require('./routes/auth');
const documentRoutes = require('./routes/documents');

app.use('/api/ocr', ocrRoutes);
app.use('/api/verify', verifyRoutes);
app.use('/api/auth', authRoutes);
app.use('/api/documents', documentRoutes);

// Database Connection
// For demo purposes, if no MONGO_URI is provided, we'll skip DB connection or use a local one.
const MONGO_URI = process.env.MONGO_URI || 'mongodb://localhost:27017/mossip_ocr';

mongoose.connect(MONGO_URI)
    .then(() => console.log('MongoDB connected'))
    .catch(err => console.error('MongoDB connection error:', err));

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
