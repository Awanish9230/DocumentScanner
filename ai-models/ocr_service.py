import sys
import json
import cv2
import numpy as np
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch

def load_model():
    processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
    model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
    return processor, model

def preprocess_image(image_path):
    # Load image
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Thresholding to binarize
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Dilate to connect text components
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 3))
    dilated = cv2.dilate(thresh, kernel, iterations=1)
    
    # Find contours (lines)
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    lines = []
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        if w > 50 and h > 10: # Filter small noise
            lines.append((x, y, w, h))
            
    # Sort lines from top to bottom
    lines.sort(key=lambda b: b[1])
    
    return img, lines

def extract_text(image_path):
    processor, model = load_model()
    img, lines = preprocess_image(image_path)
    
    extracted_data = {}
    full_text = []
    
    for i, (x, y, w, h) in enumerate(lines):
        # Crop the line
        crop = img[y:y+h, x:x+w]
        rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_crop)
        
        # OCR
        pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values
        generated_ids = model.generate(pixel_values)
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        full_text.append(text)
        
        # Simple heuristic mapping (very basic)
        lower_text = text.lower()
        if "name" in lower_text:
            extracted_data["name"] = text.replace("Name", "").replace(":", "").strip()
        elif "dob" in lower_text or "date of birth" in lower_text:
            extracted_data["dob"] = text.replace("DOB", "").replace("Date of Birth", "").replace(":", "").strip()
        elif "id" in lower_text and "no" in lower_text:
            extracted_data["id_number"] = text.split(":")[-1].strip()
            
    # Fallback if fields not found, just put raw text in a generic field
    extracted_data["raw_text"] = "\n".join(full_text)
    
    return extracted_data

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No image path provided"}))
        sys.exit(1)
        
    image_path = sys.argv[1]
    try:
        data = extract_text(image_path)
        print(json.dumps(data))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
