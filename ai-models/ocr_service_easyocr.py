"""
OCR service using EasyOCR - Python-only, no Tesseract installation required
"""
import sys
import json
import os

# Set UTF-8 encoding for output to avoid charmap errors
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Suppress EasyOCR progress bars that cause encoding issues
os.environ['EASYOCR_VERBOSE'] = '0'

def process_image_easyocr(image_path):
    """Extract text using EasyOCR"""
    try:
        import easyocr
        
        # Initialize reader (downloads models on first run)
        # verbose=False suppresses progress bars that cause encoding issues
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        
        # Read text from image
        results = reader.readtext(image_path)
        
        # Combine all text
        raw_text = '\n'.join([text for (bbox, text, conf) in results])
        
        # Import postprocess
        from postprocess import extract_fields_from_lines
        
        # Convert to lines format
        lines = []
        for (bbox, text, conf) in results:
            lines.append({'text': text.strip(), 'confidence': conf * 100})
        
        result = extract_fields_from_lines(lines, raw_text=raw_text)
        return result
        
    except ImportError:
        return {
            "error": "EasyOCR not installed. Run: pip install easyocr",
            "extracted_fields": {
                "first_name": "", "middle_name": "", "last_name": "", "gender": "", "date_of_birth": "",
                "address_line_1": "", "address_line_2": "", "city": "", "state": "", "pin_code": "",
                "country": "", "phone_number": "", "email": "",
                "dynamically_detected_fields": {}
            }
        }
    except Exception as e:
        print(f"EasyOCR error: {e}", file=sys.stderr)
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
    result = process_image_easyocr(image_path)
    
    print(json.dumps(result, ensure_ascii=False))
