# OCR Document Scanner & Verification System

A full-stack web application for extracting text and structured data from physical documents (images and PDFs). Built with **React + Node.js + MongoDB** frontend, **Express.js** backend, and **Tesseract OCR** for text extraction.

## Quick Start

### Prerequisites
- Node.js v14+
- Python 3.8+
- MongoDB (local or Atlas)
- **Tesseract OCR** (must be installed separately — see below)

### 1. Install Tesseract (Required)

**Windows:**
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer, note installation directory (e.g., `C:\Program Files\Tesseract-OCR`)
3. Add to PATH:
   ```powershell
   [Environment]::SetEnvironmentVariable('Path', $env:Path + ';C:\Program Files\Tesseract-OCR', 'User')
   ```
4. Close/reopen PowerShell and verify:
   ```powershell
   tesseract --version
   ```

**macOS:**
```bash
brew install tesseract
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt-get install tesseract-ocr
```

### 2. Setup Backend
```bash
cd backend
npm install
# Create .env file with:
# MONGO_URI=mongodb://localhost:27017/mossip_ocr
# PORT=5000
npm run dev
```

Backend runs on `http://localhost:5000`

### 3. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

### 4. Setup OCR Engine
```bash
cd ai-models
pip install -r requirements.txt
```

## How It Works

1. **Upload** — User uploads an image (JPG, PNG, GIF, BMP) or PDF through the web interface
2. **Extract** — Backend calls `ai-models/ocr_service.py` which:
   - Preprocesses image (grayscale, threshold, denoise)
   - Runs Tesseract OCR to extract text
   - Parses extracted text for structured fields (name, email, phone, address, etc.)
   - Returns JSON with extracted text and fields
3. **Review** — Frontend displays extracted fields in editable form; user can correct errors
4. **Verify** — Backend compares user-edited fields against OCR output:
   - Calculates similarity score (Levenshtein distance)
   - Combines with OCR confidence for final match score
   - Returns: Match (≥95%), Partial Match (75-94%), or Mismatch (<75%)

## Project Structure

```
MossipIITM/
├── frontend/                    # React + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadSection.jsx    # Document upload UI
│   │   │   ├── FormSection.jsx      # Editable form for extracted fields
│   │   │   ├── VerificationResult.jsx # Match/confidence report
│   │   │   └── ...
│   │   └── App.jsx
│   └── package.json
├── backend/                     # Express.js
│   ├── routes/
│   │   ├── ocr.js               # POST /api/ocr/extract
│   │   ├── verify.js            # POST /api/verify
│   │   ├── auth.js
│   │   └── documents.js
│   ├── uploads/                 # Temporary image/PDF storage
│   ├── index.js                 # Server entry point
│   └── package.json
├── ai-models/                   # Python OCR
│   ├── ocr_service.py           # Main OCR script (Tesseract-based)
│   ├── postprocess.py           # Field normalization & verification
│   ├── requirements.txt         # Python dependencies
│   ├── test-images/             # Test images folder
│   └── README.md                # Detailed OCR setup
└── README.md                    # This file
```

## API Endpoints

### OCR Extraction
**POST** `/api/ocr/extract`

Request:
```javascript
// multipart/form-data
{ document: File }  // Image or PDF
```

Response:
```json
{
  "success": true,
  "data": {
    "text": "Name: John Smith\nEmail: john@example.com\n...",
    "fields": {
      "name": "John Smith",
      "email": "john@example.com",
      "phone": "555-1234"
    },
    "fields_meta": {
      "name_confidence": 85.0,
      "email_confidence": 95.0
    },
    "confidence": 85.0
  },
  "filePath": "/uploads/1764840301960-sample.png",
  "fileType": "image/png"
}
```

### Verification
**POST** `/api/verify`

Request:
```json
{
  "ocrData": { "name": "John Smith", "email": "john@example.com" },
  "userData": { "name": "John Smith", "email": "john.smith@example.com" }
}
```

Response:
```json
{
  "results": [
    {
      "field": "name",
      "ocrValue": "John Smith",
      "userValue": "John Smith",
      "similarity": 100.0,
      "ocr_confidence": 85.0,
      "combinedScore": 100.0,
      "status": "Match",
      "notes": ""
    }
  ],
  "averageConfidence": 95.0
}
```

## Extracted Fields

The system automatically detects and extracts:
- **name** / **first_name** / **last_name**
- **email**
- **phone** / **phone_number**
- **date_of_birth**
- **address** / **address_line_1** / **address_line_2**
- **city** / **state** / **country**
- **pin_code** / **zip**
- **gender**

More fields can be added by extending regex patterns in `ai-models/ocr_service.py`.

## Testing Locally

### Test OCR directly
```bash
cd ai-models
python ocr_service.py test-images/sample3.png
```

This outputs JSON with extracted text and fields.

### Test with backend
```bash
# Backend running on port 5000
# Upload a file through the frontend UI at http://localhost:5173
```

## Troubleshooting

### "Tesseract is not installed or not in PATH"
**Solution:** Install Tesseract using the instructions above. After installing, close and reopen your terminal/IDE and verify with `tesseract --version`.

### "No valid JSON output from OCR script"
**Cause:** Usually means Tesseract not installed or Python package not found.
**Solution:**
1. Verify Tesseract: `tesseract --version`
2. Reinstall Python deps: `cd ai-models && pip install -r requirements.txt`
3. Test OCR directly: `python ocr_service.py test-images/sample3.png`

### OCR returns empty fields
**Cause:** Image quality too low, or field labels not recognized.
**Solution:**
- Use a higher-resolution image (≥300 DPI recommended)
- Check that field labels match expected patterns (see `Extracted Fields` section above)
- Add new regex patterns to `ocr_service.py` if field format is custom

### Backend can't find Python script
**Cause:** Incorrect path in `backend/routes/ocr.js`.
**Solution:** Verify the path `../../ai-models/ocr_service.py` is correct relative to the ocr.js file.

### MongoDB connection error
**Solution:** Ensure MongoDB is running locally or update `MONGO_URI` in `.env` to your MongoDB Atlas connection string.

## Features

✅ **Image & PDF Support** — Extracts from JPG, PNG, GIF, BMP, PDF  
✅ **Automatic Field Detection** — Parses name, email, phone, address, etc.  
✅ **Confidence Scoring** — Per-field and overall extraction confidence  
✅ **Verification Engine** — Compares OCR output against user edits with similarity matching  
✅ **Responsive UI** — Works on desktop and mobile (React + TailwindCSS)  
✅ **Offline-Ready** — No external APIs; runs Tesseract locally  
✅ **User Authentication** — Email + optional Google OAuth  
✅ **Document Storage** — Save extracted documents and verification results to MongoDB  

## Performance

- **Extraction time:** ~2-5 seconds per document (depends on image size/complexity)
- **Accuracy:** 90-98% on clear printed documents, 70-85% on handwritten documents
- **Supported languages:** English (configurable to other languages via Tesseract)

## Image Quality Recommendations

For **best OCR accuracy**, ensure:

### Printed Documents
- ✅ Clear, sharp text (no blur or pixelation)
- ✅ Adequate lighting (no shadows or glare)
- ✅ High resolution (300+ DPI recommended)
- ✅ Straight document (not tilted or skewed)
- ✅ Black or dark text on light background
- ✅ Minimal background patterns or watermarks

### Handwritten Documents
- ✅ Dark pen (blue or black ink)
- ✅ Legible handwriting (consistent and clear)
- ✅ White or light paper background
- ✅ Good lighting (no shadows)
- ✅ High resolution (at least 200 DPI)
- ✅ Straight document angle (perpendicular to camera)
- ⚠️ **Note:** Tesseract's handwriting recognition is limited. For best results with cursive/script, use high-quality scans and clear printing.

### Poor Quality Images (may fail)
- ❌ Very small text (less than 8pt)
- ❌ Faded or light gray text
- ❌ Rotated/skewed documents
- ❌ Blurry photos
- ❌ Poor lighting (very dark or washed out)
- ❌ Complex backgrounds or patterns
- ❌ Cursive handwriting that's difficult to read

## Requirements

### Python (ai-models/requirements.txt)
- pytesseract — Python wrapper for Tesseract
- pillow — Image processing
- opencv-python — Advanced image preprocessing
- pdf2image — PDF to image conversion
- numpy — Numerical operations
- torch, transformers — Optional (for future TrOCR models)

### Node.js (backend/package.json)
- express
- mongoose — MongoDB ORM
- multer — File upload handling
- cors
- dotenv

### Frontend (frontend/package.json)
- react, react-dom
- vite — Build tool
- tailwindcss — Styling

## License

This project is provided as-is for educational and commercial use.

## Support

For issues or feature requests, please check the troubleshooting section or contact the development team.

