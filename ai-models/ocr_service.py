import sys
import json
import cv2
import numpy as np
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch

def load_model():
    # Use a larger TrOCR variant for better accuracy when possible
    model_name = 'microsoft/trocr-large-printed'
    try:
        processor = TrOCRProcessor.from_pretrained(model_name)
        model = VisionEncoderDecoderModel.from_pretrained(model_name)
    except Exception:
        # fallback to smaller model if large not available in environment
        processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
        model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    return processor, model, device

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
    processor, model, device = load_model()
    img, lines = preprocess_image(image_path)
    
    extracted_data = {}
    full_text = []
    lines_out = []
    
    for i, (x, y, w, h) in enumerate(lines):
        # Crop the line
        crop = img[y:y+h, x:x+w]
        rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb_crop)
        
        # OCR - generate with scores so we can compute token-level confidence
        inputs = processor(images=pil_img, return_tensors="pt").pixel_values.to(device)
        outputs = model.generate(inputs, return_dict_in_generate=True, output_scores=True)
        generated_ids = outputs.sequences
        text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        # compute per-token probabilities from scores (softmax)
        token_probs = []
        if hasattr(outputs, 'scores') and outputs.scores is not None:
            # outputs.scores is a list of tensors each shape (batch, vocab)
            # generated_ids shape: (batch, seq_len)
            seq = generated_ids[0].tolist()
            # outputs.scores length = seq_len - 1 typically
            for step_idx, score in enumerate(outputs.scores):
                # score: tensor (batch, vocab)
                logits = score[0]
                probs = torch.nn.functional.softmax(logits, dim=-1)
                # predicted token at this step corresponds to seq[step_idx + 1]
                token_id = seq[step_idx + 1] if step_idx + 1 < len(seq) else None
                if token_id is not None:
                    p = probs[token_id].item()
                    token_probs.append(p)

        # average token probability as line confidence
        line_conf = float(sum(token_probs) / len(token_probs)) if token_probs else 0.0

        full_text.append(text)
        lines_out.append({'text': text, 'confidence': round(line_conf * 100, 2)})
        
        # Simple heuristic mapping (very basic)
        lower_text = text.lower()
        if "name" in lower_text:
            extracted_data["name"] = text.replace("Name", "").replace(":", "").strip()
        elif "dob" in lower_text or "date of birth" in lower_text:
            extracted_data["dob"] = text.replace("DOB", "").replace("Date of Birth", "").replace(":", "").strip()
        elif "id" in lower_text and "no" in lower_text:
            extracted_data["id_number"] = text.split(":")[-1].strip()
            
    # Fallback if fields not found, just put raw text in a generic field
    extracted_data['lines'] = lines_out
    extracted_data["raw_text"] = "\n".join(full_text)

    # compute overall average confidence
    confidences = [l['confidence'] for l in lines_out if isinstance(l.get('confidence'), (int, float))]
    extracted_data['average_confidence'] = round(sum(confidences) / len(confidences), 2) if confidences else 0.0
    
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
