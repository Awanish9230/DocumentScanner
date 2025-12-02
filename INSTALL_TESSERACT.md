# Installing Tesseract OCR on Windows

## Quick Install

1. **Download Tesseract Installer:**
   - Go to: https://github.com/UB-Mannheim/tesseract/wiki
   - Download the latest Windows installer (e.g., `tesseract-ocr-w64-setup-5.3.3.20231005.exe`)

2. **Run the Installer:**
   - Double-click the downloaded `.exe` file
   - **IMPORTANT:** During installation, note the installation path (default: `C:\Program Files\Tesseract-OCR`)
   - Complete the installation

3. **Add Tesseract to System PATH:**
   - Open System Environment Variables:
     - Press `Win + R`, type `sysdm.cpl`, press Enter
     - Go to "Advanced" tab → Click "Environment Variables"
   - Under "System variables", find and select "Path", click "Edit"
   - Click "New" and add: `C:\Program Files\Tesseract-OCR`
   - Click OK on all dialogs

4. **Verify Installation:**
   Open a **NEW** Command Prompt or PowerShell and run:
   ```
   tesseract --version
   ```
   You should see version information.

5. **Restart Your Backend Server:**
   - Stop the backend (`Ctrl+C` in the terminal)
   - Start it again: `npm run dev`

## Alternative: Quick Test Without Installation

If you want to test without installing Tesseract, I can create a version that uses **EasyOCR** instead (Python-only, no external dependencies).

Let me know which approach you prefer!
