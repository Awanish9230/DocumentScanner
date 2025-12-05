"""
Simple, direct OCR service for document scanning.

Uses Tesseract OCR via subprocess (cross-platform).
Handles both images (.jpg, .png) and PDFs.

Usage:
  python ocr_service.py /path/to/document.jpg
  python ocr_service.py /path/to/document.pdf

Output: JSON with extracted text and fields
"""
import sys
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, List

from PIL import Image
import cv2
import numpy as np

# Find Tesseract executable
TESSERACT_CMD = None
if sys.platform == 'win32':
    # Windows paths
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    for path in possible_paths:
        if os.path.exists(path):
            TESSERACT_CMD = path
            break
else:
    # Unix-like systems
    try:
        result = subprocess.run(['which', 'tesseract'], capture_output=True, text=True)
        if result.returncode == 0:
            TESSERACT_CMD = result.stdout.strip()
    except Exception:
        pass
    
    # Fallback to common paths
    if not TESSERACT_CMD:
        for path in ['/usr/bin/tesseract', '/usr/local/bin/tesseract', '/opt/homebrew/bin/tesseract']:
            if os.path.exists(path):
                TESSERACT_CMD = path
                break

# Try to import pdf2image for PDF support
try:
    from pdf2image import convert_from_path
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


def preprocess_image(image_path: str) -> Image.Image:
    """Load image and apply smart preprocessing for both printed and handwritten text."""
    # Read with OpenCV
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Resize if too small (improves OCR accuracy)
    h, w = gray.shape
    if max(h, w) < 800:
        scale = max(2, int(1200 / max(h, w)))
        gray = cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)
    
    # Method 1: Try Otsu's thresholding (good for high contrast)
    _, result_otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Method 2: Try adaptive thresholding (good for varying lighting)
    result_adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                            cv2.THRESH_BINARY, 13, 2)
    
    # Method 3: Simple thresholding at median
    median_val = np.median(gray)
    _, result_simple = cv2.threshold(gray, int(median_val), 255, cv2.THRESH_BINARY)
    
    # Decide which method worked best by checking text-to-background ratio
    # Count black pixels (text)
    black_otsu = np.sum(result_otsu < 50)
    black_adaptive = np.sum(result_adaptive < 50)
    black_simple = np.sum(result_simple < 50)
    
    total_pixels = gray.shape[0] * gray.shape[1]
    
    # Choose the method where text is 5-40% of image (most likely to be correct)
    def score_image(black_count):
        ratio = black_count / total_pixels
        # Penalize if too much or too little black
        if 0.05 < ratio < 0.40:
            return 100  # Perfect range
        elif 0.02 < ratio < 0.50:
            return 75
        elif 0.01 < ratio < 0.60:
            return 50
        else:
            return 0
    
    scores = {
        'otsu': score_image(black_otsu),
        'adaptive': score_image(black_adaptive),
        'simple': score_image(black_simple)
    }
    
    best_method = max(scores, key=scores.get)
    
    if best_method == 'otsu':
        final = result_otsu
    elif best_method == 'adaptive':
        final = result_adaptive
    else:
        final = result_simple
    
    # Light morphological cleanup
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    final = cv2.morphologyEx(final, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    # Convert to PIL Image
    pil_image = Image.fromarray(final)
    return pil_image


def extract_text_from_image(image_path: str) -> Dict[str, Any]:
    """Extract text from a single image using Tesseract with improved settings for both printed and handwritten."""
    if not TESSERACT_CMD:
        return {
            'text': '',
            'raw_lines': [],
            'error': 'Tesseract OCR engine not found. Install Tesseract and add to PATH. See README for instructions.',
            'confidence': 0.0,
            'fields': {},
            'fields_meta': {}
        }
    
    try:
        pil_image = preprocess_image(image_path)
    except Exception as e:
        return {'text': '', 'raw_lines': [], 'error': str(e), 'confidence': 0.0, 'fields': {}, 'fields_meta': {}}
    
    try:
        # Save preprocessed image to temp file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_image_path = tmp.name
        pil_image.save(temp_image_path)
        
        # Run tesseract with multiple strategies to find best results
        configs = [
            ['--psm', '6', '--oem', '3'],  # Single text block + both engines
            ['--psm', '3', '--oem', '3'],  # Fully automatic page segmentation
            ['--psm', '6', '--oem', '1'],  # Single block + legacy engine
            ['--psm', '3'],                 # Automatic + default
        ]
        
        full_text = ""
        for config in configs:
            try:
                cmd = [TESSERACT_CMD, temp_image_path, 'stdout'] + config
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=30,
                    encoding='utf-8',
                    errors='ignore'
                )
                
                extracted = result.stdout.strip() if result.stdout else ""
                # Use the first config that returns meaningful text
                if extracted and len(extracted) > 20:
                    full_text = extracted
                    break
            except Exception:
                continue
        
        # If preprocessed image didn't work well, try original image directly
        if not full_text or len(full_text) < 20:
            try:
                result = subprocess.run(
                    [TESSERACT_CMD, image_path, 'stdout', '--psm', '3'],
                    capture_output=True,
                    timeout=30,
                    encoding='utf-8',
                    errors='ignore'
                )
                extracted = result.stdout.strip() if result.stdout else ""
                if extracted and len(extracted) > 20:
                    full_text = extracted
            except Exception:
                pass
        
        # Final fallback: try original with best settings
        if not full_text or len(full_text) < 20:
            try:
                result = subprocess.run(
                    [TESSERACT_CMD, image_path, 'stdout'],
                    capture_output=True,
                    timeout=30,
                    encoding='utf-8',
                    errors='ignore'
                )
                full_text = result.stdout.strip() if result.stdout else ""
            except Exception:
                pass
        
        # Split into lines for parsing
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        # If text extraction worked, calculate a confidence score based on text length and validity
        confidence = min(100, 50 + (len(full_text.split()) * 5)) if full_text else 0
        
        result_data = {
            'text': full_text,
            'raw_lines': lines,
            'confidence': confidence,
            'fields': {},
            'fields_meta': {}
        }
        
        # Clean up temp file
        try:
            os.remove(temp_image_path)
        except Exception:
            pass
        
        return result_data
    except Exception as e:
        error_msg = str(e)
        # Try to clean up temp file
        try:
            os.remove(temp_image_path)
        except Exception:
            pass
        return {
            'text': '',
            'raw_lines': [],
            'error': error_msg,
            'confidence': 0.0,
            'fields': {},
            'fields_meta': {}
        }


def extract_text_from_pdf(pdf_path: str) -> Dict[str, Any]:
    """Extract text from PDF by converting to images first."""
    if not PDF_SUPPORT:
        return {
            'text': '',
            'raw_lines': [],
            'error': 'PDF support not available. Install: pip install pdf2image',
            'confidence': 0.0,
            'fields': {},
            'fields_meta': {}
        }
    
    try:
        # Convert PDF to images
        images = convert_from_path(pdf_path, first_page=1, last_page=1)  # First page only
        if not images:
            return {'text': '', 'raw_lines': [], 'error': 'No pages in PDF', 'confidence': 0.0, 'fields': {}, 'fields_meta': {}}
        
        # Save first page as temporary image
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_image_path = tmp.name
        
        images[0].save(temp_image_path)
        
        # Extract text from the image
        result = extract_text_from_image(temp_image_path)
        
        # Clean up
        try:
            os.remove(temp_image_path)
        except Exception:
            pass
        
        return result
    except Exception as e:
        return {'text': '', 'raw_lines': [], 'error': str(e), 'confidence': 0.0, 'fields': {}, 'fields_meta': {}}


def parse_fields_from_text(text: str, lines: List[str]) -> Dict[str, str]:
    """Parse structured fields from extracted text using flexible heuristics for both printed and handwritten."""
    fields = {}
    
    if not text:
        return fields
    
    # Join text and lines for pattern matching
    full_text = text + '\n' + '\n'.join(lines)
    
    # More flexible field patterns to handle handwriting variations
    patterns = {
        'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Direct email
        'phone': r'(?:phone|mobile|contact|phone number|phone no|phone-no|phone number)[\s:]*\(?([+\d\-\s()\.]{8,}?)(?:\n|$)',
        'first_name': r'(?:first name|fname|first.?name)[\s:]*([^\n]+?)(?:\n|$)',
        'middle_name': r'(?:middle name|mname|middle.?name)[\s:]*([^\n]+?)(?:\n|$)',
        'last_name': r'(?:last name|lname|surname|last.?name)[\s:]*([^\n]+?)(?:\n|$)',
        'name': r'(?:name|full name|applicant name)[\s:]*([^\n]+?)(?:\n|$)',
        'date_of_birth': r'(?:date of birth|dob|birth date|date of birth|d\.o\.b|d/o/b)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        'address': r'(?:address|location|addr|address line|address line 1|address.?line.?1)[\s:]*([^\n]+?)(?:\n|$)',
        'address_line_2': r'(?:address.?line.?2|address line 2|apt|suite|po box)[\s:]*([^\n]+?)(?:\n|$)',
        'city': r'(?:city|town|city/town)[\s:]*([^\n]+?)(?:\n|$)',
        'state': r'(?:state|state/province)[\s:]*([^\n]+?)(?:\n|$)',
        'country': r'(?:country|nation|country/nation)[\s:]*([^\n]+?)(?:\n|$)',
        'pin_code': r'(?:pin|zip|postal code|pin code|pincode|pin.?code|zip code)[\s:]*(\d{4,10})',
        'gender': r'(?:gender|sex|gender/sex)[\s:]*([MmFf]|Male|Female|M|F)',
        'age': r'(?:age)[\s:]*(\d{1,3})',
    }
    
    for field_name, pattern in patterns.items():
        match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            
            # Remove common label prefixes that got captured
            value = re.sub(r'^(name|email|phone|date|address|city|state|country|gender|pin|age)[\s:]*', '', value, flags=re.IGNORECASE)
            # Clean up special chars but keep some (like - for phone)
            value = re.sub(r'[|\/\[\]()]+', '', value)
            value = re.sub(r'\s+', ' ', value)  # Normalize spaces
            value = value.strip()
            
            # Avoid capturing duplicate/conflicting field names
            if field_name == 'name' and any(k in fields for k in ['first_name', 'last_name']):
                continue
            
            if value and len(value) > 1 and value.lower() not in ['n/a', 'none', 'na', 'unknown', '---', '—']:
                fields[field_name] = value
    
    return fields


def process_document(file_path: str) -> Dict[str, Any]:
    """Main entry point: process image or PDF and return extracted data."""
    file_path = str(file_path)
    
    if not os.path.exists(file_path):
        return {'error': f'File not found: {file_path}'}
    
    file_ext = Path(file_path).suffix.lower()
    
    # Process based on file type
    if file_ext in ['.pdf']:
        result = extract_text_from_pdf(file_path)
    elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
        result = extract_text_from_image(file_path)
    else:
        return {'error': f'Unsupported file type: {file_ext}'}
    
    # If extraction succeeded, parse fields
    if result.get('text'):
        fields = parse_fields_from_text(result['text'], result.get('raw_lines', []))
        result['fields'] = fields
        result['fields_meta'] = {
            f'{k}_confidence': 80.0 for k in fields.keys()
        }
    else:
        result['fields'] = {}
        result['fields_meta'] = {}
    
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python ocr_service.py <image_or_pdf_path>')
        sys.exit(1)
    
    file_path = sys.argv[1]
    result = process_document(file_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))
