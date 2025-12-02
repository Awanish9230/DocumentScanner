"""
Simplified OCR service using Tesseract for better full-document text extraction
"""
import sys
import json
import cv2
import numpy as np
from PIL import Image

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except:
    TESSERACT_AVAILABLE = False

def preprocess_image(image_path):
    """Simple preprocessing for better OCR"""
    # Read image
    img = cv2.imread(image_path)
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply thresholding to get black text on white background
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Denoise
    denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
    
    return Image.fromarray(denoised)

def extract_text_tesseract(image_path):
    """Extract text using Tesseract OCR"""
    if not TESSERACT_AVAILABLE:
        return ""
    
    try:
        # Preprocess image
        img = preprocess_image(image_path)
        
        # Extract text
        text = pytesseract.image_to_string(img, config='--psm 6')
        
        return text.strip()
    except Exception as e:
        print(f"Tesseract error: {e}", file=sys.stderr)
        return ""

def process_image_simple(image_path):
    """Simple OCR extraction"""
    raw_text = extract_text_tesseract(image_path)
    
    # Import postprocess
    try:
        from postprocess import extract_fields_from_lines
        
        # Convert raw text to lines format
        lines = []
        for line in raw_text.split('\n'):
            if line.strip():
                lines.append({'text': line.strip()})
        
        result = extract_fields_from_lines(lines, raw_text=raw_text)
        return result
    except Exception as e:
        print(f"Postprocess error: {e}", file=sys.stderr)
        # Return empty structure
        return {
            "extracted_fields": {
                "first_name": "", "middle_name": "", "last_name": "", "gender": "", "date_of_birth": "",
                "address_line_1": "", "address_line_2": "", "city": "", "state": "", "pin_code": "",
                "country": "", "phone_number": "", "email": "",
                "dynamically_detected_fields": {}
            }
        }

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No image path provided"}))
        sys.exit(1)
    
    image_path = sys.argv[1]
    result = process_image_simple(image_path)
    
    print(json.dumps(result, ensure_ascii=False))
