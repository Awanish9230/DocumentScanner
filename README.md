# OCR Document Processor & Verification System

## Overview
This project is a comprehensive solution for automating data entry from physical documents. It utilizes a **MERN stack** (MongoDB, Express, React, Node.js) for the web application and a **Python-based OCR engine** powered by **Microsoft's TrOCR** (Transformer-based Optical Character Recognition) for high-accuracy text extraction.

The system allows users to:
1.  **Upload** scanned documents (ID cards, certificates, forms).
2.  **Extract** text automatically using deep learning models.
3.  **Review & Edit** the extracted data in a user-friendly form.
4.  **Verify** the final data against the original OCR output with confidence scoring and fuzzy matching.

## Features
-   **Automated OCR**: Extracts text from images using TrOCR.
-   **Data Verification**: Compares user inputs with OCR results to detect discrepancies.
-   **Confidence Scoring**: Provides field-level and overall confidence scores.
-   **Modern UI**: Built with React and TailwindCSS for a responsive and clean interface.
-   **Offline Capability**: The OCR engine runs locally without relying on external cloud APIs.

## Tech Stack
-   **Frontend**: React, Vite, TailwindCSS
-   **Backend**: Node.js, Express.js, MongoDB
-   **OCR Engine**: Python, PyTorch, HuggingFace Transformers, OpenCV, Pillow

## Prerequisites
Before running the project, ensure you have the following installed:
-   **Node.js** (v14 or higher)
-   **Python** (v3.8 or higher)
-   **MongoDB** (Local instance or Atlas URI)

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd MossipIITM
```

### 2. Backend Setup
Navigate to the backend directory and install dependencies:
```bash
cd backend
npm install
```
*Optional*: Create a `.env` file in the `backend` directory to specify your MongoDB URI:
```env
MONGO_URI=mongodb://localhost:27017/mossip_ocr
PORT=5000
```

### 3. Frontend Setup
Navigate to the frontend directory and install dependencies:
```bash
cd ../frontend
npm install
```

### 4. OCR Engine Setup
Navigate to the AI Models directory and install Python requirements:
```bash
cd ../ai-models
pip install -r requirements.txt
```
*Note: The first time you run the OCR, it will download the TrOCR model (~1.5GB).*

## Running the Application

### Start the Backend
```bash
cd backend
npm run dev
```
The server will start on `http://localhost:5000`.

### Start the Frontend
Open a new terminal:
```bash
cd frontend
npm run dev
```
The application will be available at `http://localhost:5173`.

## Project Structure
```
MossipIITM/
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/     # UI Components (Upload, Form, Verification)
│   │   ├── App.jsx         # Main Application Component
│   │   └── ...
├── backend/                # Express Backend
│   ├── routes/             # API Routes (OCR, Verify)
│   ├── uploads/            # Temp storage for uploaded images
│   ├── index.js            # Server Entry Point
│   └── ...
├── ai-models/              # Python OCR Service
│   ├── ocr_service.py      # Main OCR Script
│   └── requirements.txt    # Python Dependencies
└── README.md               # Project Documentation
```

## Usage Guide
1.  **Upload**: Go to the home page and upload an image file.
2.  **Extract**: Click "Extract Text" to process the document.
3.  **Edit**: Review the extracted fields. If the OCR missed something or made a mistake, correct it in the input fields.
4.  **Verify**: Click "Verify Data" to see a comparison report.
5.  **Analyze**: Check the confidence scores and match status (Match, Partial Match, Mismatch).

