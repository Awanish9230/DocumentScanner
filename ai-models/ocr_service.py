import sys
import json
import cv2
import numpy as np
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch

import re

def _clean_spaces(s: str) -> str:
    return re.sub(r'\s+', ' ', s).strip()

def post_process_text(s: str) -> str:
    if not isinstance(s, str):
        return s
    s = s.strip()
    # Replace common OCR mistakes and normalize punctuation
    subs = [
        (r'\s*:\s*', ': '),
        (r'\s*-\s*', '-'),
        (r'\s*\.\s*', '. '),
        (r'[^\S\r\n]+', ' '),  # collapse spaces (but keep newlines)
    ]
    for pat, rep in subs:
        s = re.sub(pat, rep, s)

    # Fix broken ' @ ' or spaces around @ and dot in emails
    s = re.sub(r'\s*@\s*', '@', s)
    s = re.sub(r'\s*\.\s*', '.', s)

    # Trim punctuation at ends
    s = s.strip(" \t\n\r\f\v:;.,-_")

    return _clean_spaces(s)

def normalize_phone(s: str) -> str:
    if not s: return ''
    digits = re.sub(r'\D', '', s)
    # heuristics: if starts with country code or length 10/11/12
    if len(digits) >= 10:
        return digits
    return s

def normalize_pin(s: str) -> str:
    if not s: return ''
    digits = re.sub(r'\D', '', s)
    if len(digits) == 6:
        return digits
    return s

def normalize_email(s: str) -> str:
    if not s: return ''
    s = s.strip().lower()
    s = re.sub(r'\s+', '', s)
    return s

def ensemble_texts(candidates):
    # simple char-wise majority vote across candidate strings
    if not candidates:
        return ''
    # keep only non-empty trimmed candidates
    cands = [c for c in [x or '' for x in candidates] if c.strip()]
    if not cands:
        return ''
    # if only one candidate, return it cleaned
    if len(cands) == 1:
        return post_process_text(cands[0])

    max_len = max(len(c) for c in cands)
    out_chars = []
    for i in range(max_len):
        chars = [c[i] for c in cands if i < len(c)]
        # choose most common character (excluding blanks) or fallback to space
        if not chars:
            out_chars.append(' ')
            continue
        # prefer letters/digits over punctuation when tie
        from collections import Counter
        cnt = Counter(chars)
        char, _ = cnt.most_common(1)[0]
        out_chars.append(char)

    out = ''.join(out_chars)
    out = re.sub(r'\s+', ' ', out)
    return post_process_text(out)

def load_model():
    # Prefer a handwritten variant when available (handwriting documents). Fall back
    # to printed variants if not found in the environment.
    candidates = [
        'microsoft/trocr-large-handwritten',
        'microsoft/trocr-large-printed',
        'microsoft/trocr-base-printed'
    ]

    processor = None
    model = None
    for model_name in candidates:
        try:
            processor = TrOCRProcessor.from_pretrained(model_name)
            model = VisionEncoderDecoderModel.from_pretrained(model_name)
            # Stop at the first successful load
            break
        except Exception:
            continue

    if processor is None or model is None:
        # final fallback: try the base printed model explicitly (will raise if not available)
        processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
        model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.to(device)
    return processor, model, device

def preprocess_image(image_path):
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found or could not be read: {image_path}")

    # defensive: ensure we have a 3-channel image
    if len(img.shape) == 2:
        # single-channel image -> convert to BGR for downstream ops
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # upscale small images to help the model see character strokes better
    h, w = gray.shape[:2]
    if max(h, w) < 1200:
        scale = 2
        gray = cv2.resize(gray, (w * scale, h * scale), interpolation=cv2.INTER_CUBIC)

    # contrast limited adaptive histogram equalization (CLAHE) can help with uneven lighting
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Unsharp mask (sharpening) to make strokes clearer for handwriting
    gaussian = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.0)
    gray = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)

    # Reduce noise (handwriting often benefits from median blur)
    denoised = cv2.medianBlur(gray, 3)

    # Adaptive threshold works better for uneven lighting and handwriting
    thresh = cv2.adaptiveThreshold(denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                   cv2.THRESH_BINARY_INV, 15, 9)

    # Try to deskew the document — compute angle from non-zero pixels and rotate
    try:
        coords = np.column_stack(np.where(thresh > 0))
        if coords.shape[0] > 50:
            rect = cv2.minAreaRect(coords)
            angle = rect[-1]
            # minAreaRect angle logic: adjust to get correct rotation direction
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            if abs(angle) > 0.5:
                # rotate original color image and thresh/denoised for more accurate layout
                (h0, w0) = img.shape[:2]
                center = (w0 // 2, h0 // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                img = cv2.warpAffine(img, M, (w0, h0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                gray = cv2.warpAffine(gray, M, (w0, h0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                denoised = cv2.warpAffine(denoised, M, (w0, h0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
                thresh = cv2.warpAffine(thresh, M, (w0, h0), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    except Exception:
        # deskew attempt may fail on tiny inputs or unusual images — ignore
        pass

    # Small closing then dilation to join broken strokes without merging lines
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (12, 3))
    dilated = cv2.dilate(closed, kernel, iterations=1)
    
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
    
    # We'll collect a token-confidence-aware transcription per line and
    # also attempt a Tesseract fallback for very low-confidence lines (handwriting)
    try:
        import pytesseract
        has_tesseract = True
    except Exception:
        has_tesseract = False

    # helper to set field values if not already set
    def maybe_assign(key, val, conf):
        if key and val:
            if key not in extracted_data or not extracted_data[key]:
                extracted_data[key] = val
                extracted_data[f"{key}_confidence"] = round(conf * 100, 2)

    # If line segmentation failed (no contours found), fall back to whole-image OCR
    if not lines:
        h, w = img.shape[:2]
        lines = [(0, 0, w, h)]

    for i, (x, y, w, h) in enumerate(lines):
        # clamp bounding box to image bounds and add small padding for context
        ih, iw = img.shape[:2]
        pad_x = max(2, int(w * 0.02))
        pad_y = max(2, int(h * 0.02))
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(iw, x + w + pad_x)
        y2 = min(ih, y + h + pad_y)
        w = x2 - x1
        h = y2 - y1
        # Skip empty or degenerate boxes
        if w <= 0 or h <= 0:
            continue
        # Crop the line
        crop = img[y1:y2, x1:x2]
        # ensure crop is non-empty before calling cvtColor
        if crop is None or crop.size == 0:
            continue
        try:
            rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        except Exception:
            # if conversion fails, skip this crop
            continue
        pil_img = Image.fromarray(rgb_crop)
        
        # OCR - generate with scores so we can compute token-level confidence
        inputs = processor(images=pil_img, return_tensors="pt").pixel_values.to(device)
        # Use beam search and a reasonable max length to improve for handwriting
        try:
            outputs = model.generate(inputs, return_dict_in_generate=True, output_scores=True, max_length=256, num_beams=3)
        except TypeError:
            # older HF models might not accept num_beams; fall back
            outputs = model.generate(inputs, return_dict_in_generate=True, output_scores=True, max_length=256)
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

        # If confidence is very low and pytesseract is available, try tesseract (handwriting fallback)
        t_text = ''
        if line_conf < 0.55 and has_tesseract:
            try:
                # psm 7 treats the image as a single text line which is good for our crops
                t_text = pytesseract.image_to_string(pil_img, config='--psm 7')
                t_text = t_text.strip()
                if t_text and len(t_text) > 2:
                    # We keep both outputs and decide via ensemble (voting+postprocessing)
                    pass
            except Exception:
                pass

        # Build candidate list and ensemble
        candidates = [text]
        if t_text:
            candidates.append(t_text)

        ensembled = ensemble_texts(candidates)

        # prefer ensembled text but preserve original model confidence
        text = ensembled or text

        full_text.append(text)
        lines_out.append({'text': text, 'confidence': round(line_conf * 100, 2), 'candidates': candidates})
        
        # Simple heuristic mapping (very basic)
        # Simple heuristic mapping into structured fields
        lower_text = text.lower()

        # split by ':' or '-' to detect label:value pairs - common in forms
        label = None
        value = None
        if ':' in text:
            parts = text.split(':', 1)
            label = parts[0].strip().lower()
            value = parts[1].strip()
        elif '-' in text and len(text.split('-')) >= 2 and len(text.split('-')[0]) < 30:
            parts = text.split('-', 1)
            label = parts[0].strip().lower()
            value = parts[1].strip()

        # (maybe_assign helper defined once outside the loop)

        # If we detected an explicit label, map it to normalized keys
        if label and value:
            if 'first' in label and 'name' in label:
                maybe_assign('first_name', post_process_text(value), line_conf)
            elif 'middle' in label and 'name' in label:
                maybe_assign('middle_name', post_process_text(value), line_conf)
            elif 'last' in label and 'name' in label:
                maybe_assign('last_name', post_process_text(value), line_conf)
            elif 'name' == label or ('name' in label and len(value.split())>1):
                # name may be 'name : Abigail Grace Summer' etc
                # split into parts if possible
                names = value.split()
                maybe_assign('name', post_process_text(value), line_conf)
                if len(names) >= 1:
                    maybe_assign('first_name', names[0], line_conf)
                if len(names) == 2:
                    maybe_assign('last_name', names[-1], line_conf)
                if len(names) >= 3:
                    # assume middle names exist
                    maybe_assign('middle_name', ' '.join(names[1:-1]), line_conf)
            elif 'gender' in label:
                    maybe_assign('gender', post_process_text(value), line_conf)
            elif 'date of birth' in label or 'dob' in label or 'birth' in label:
                    maybe_assign('date_of_birth', post_process_text(value), line_conf)
            elif 'address line 1' in label or ('address' in label and '1' in label):
                maybe_assign('address_line_1', post_process_text(value), line_conf)
            elif 'address line 2' in label or ('address' in label and '2' in label):
                maybe_assign('address_line_2', post_process_text(value), line_conf)
            elif 'address' in label:
                # if address given in single line assign to line1 if empty
                maybe_assign('address_line_1', post_process_text(value), line_conf)
            elif 'city' in label:
                maybe_assign('city', post_process_text(value), line_conf)
            elif 'state' in label:
                maybe_assign('state', post_process_text(value), line_conf)
            elif 'pin' in label or 'pincode' in label or 'postal' in label:
                maybe_assign('pin_code', normalize_pin(value), line_conf)
            elif 'phone' in label or 'mobile' in label:
                maybe_assign('phone_number', normalize_phone(value), line_conf)
            elif 'email' in label or 'e-mail' in label:
                maybe_assign('email', normalize_email(value), line_conf)
        else:
            # If no explicit label, try to detect common data by regex across the text
            # email
            import re
            email_match = re.search(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}", text)
            phone_match = re.search(r"(\+?\d[\d\-\s]{7,}\d)", text)
            pin_match = re.search(r"\b(\d{6})\b", text)
            dob_match = re.search(r"(\b\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}\b)", text)

            if email_match:
                maybe_assign('email', normalize_email(email_match.group(0)), line_conf)
            if phone_match and len(re.sub(r'\D', '', phone_match.group(0))) >= 7:
                maybe_assign('phone_number', normalize_phone(phone_match.group(0).strip()), line_conf)
            if pin_match:
                maybe_assign('pin_code', normalize_pin(pin_match.group(1)), line_conf)
            if dob_match:
                maybe_assign('date_of_birth', post_process_text(dob_match.group(1)), line_conf)

            # fallback heuristics for names and address if not yet found
            if ('name' in lower_text or ('first' in lower_text and 'name' in lower_text)) and 'first_name' not in extracted_data:
                maybe_assign('name', text.replace('Name', '').strip(), line_conf)

            
    # Fallbacks
    extracted_data['lines'] = lines_out
    extracted_data["raw_text"] = "\n".join(full_text)

    # compute overall average confidence
    confidences = [l['confidence'] for l in lines_out if isinstance(l.get('confidence'), (int, float))]
    extracted_data['average_confidence'] = round(sum(confidences) / len(confidences), 2) if confidences else 0.0

    # Provide a simpler fields object for easy form population (normalize keys)
    fields = {}
    # map a list of canonical field names into the fields output
    canonical_keys = ['first_name','middle_name','last_name','name','gender','date_of_birth','address_line_1','address_line_2','city','state','pin_code','phone_number','email']
    for k in canonical_keys:
        # Always expose canonical keys (fill with detected value or empty string)
        fields[k] = extracted_data.get(k, '')
        # also ensure a confidence key exists
        conf_key = f"{k}_confidence"
        if conf_key not in extracted_data:
            extracted_data[conf_key] = extracted_data.get(conf_key, 0.0)

    # attach the fields dict (keeps backward compatibility too)
    extracted_data['fields'] = fields

    # Also expose structured metadata per field for UI consumption
    fields_meta = {}
    for k in canonical_keys:
        fields_meta[k] = {
            'value': extracted_data.get(k, '') or '',
            'confidence': float(extracted_data.get(f"{k}_confidence", 0.0)),
            'status': 'Detected' if (extracted_data.get(k) and str(extracted_data.get(k)).strip()) else 'Not Detected'
        }

    extracted_data['fields_meta'] = fields_meta
    # If not many canonical fields detected, try a full-image Tesseract pass (best-effort)
    detected_count = sum(1 for k in canonical_keys if extracted_data.get(k) and str(extracted_data.get(k)).strip())
    threshold = max(3, int(len(canonical_keys) * 0.25))
    if detected_count < threshold and has_tesseract:
        try:
            pil_full = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            t_all = pytesseract.image_to_string(pil_full, config='--psm 3')
            for line in [l.strip() for l in t_all.splitlines() if l.strip()]:
                label = None
                value = None
                if ':' in line:
                    parts = line.split(':', 1)
                    label = parts[0].strip().lower()
                    value = parts[1].strip()
                elif '-' in line and len(line.split('-')) >= 2 and len(line.split('-')[0]) < 30:
                    parts = line.split('-', 1)
                    label = parts[0].strip().lower()
                    value = parts[1].strip()

                if label and value:
                    if 'first' in label and 'name' in label:
                        maybe_assign('first_name', value, 0.45)
                    elif 'middle' in label and 'name' in label:
                        maybe_assign('middle_name', value, 0.45)
                    elif 'last' in label and 'name' in label:
                        maybe_assign('last_name', value, 0.45)
                    elif 'name' in label:
                        maybe_assign('name', value, 0.45)
                    elif 'gender' in label:
                        maybe_assign('gender', value, 0.45)
                    elif 'dob' in label or 'date' in label or 'birth' in label:
                        maybe_assign('date_of_birth', value, 0.45)
                    elif 'address' in label:
                        if '2' in label:
                            maybe_assign('address_line_2', value, 0.45)
                        else:
                            maybe_assign('address_line_1', value, 0.45)
                    elif 'city' in label:
                        maybe_assign('city', value, 0.45)
                    elif 'state' in label:
                        maybe_assign('state', value, 0.45)
                    elif 'pin' in label or 'pincode' in label or 'postal' in label:
                        maybe_assign('pin_code', value, 0.45)
                    elif 'phone' in label or 'mobile' in label:
                        maybe_assign('phone_number', value, 0.45)
                    elif 'email' in label or 'e-mail' in label:
                        maybe_assign('email', value, 0.45)
                else:
                    import re
                    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}", line)
                    phone_match = re.search(r"(\+?\d[\d\-\s]{7,}\d)", line)
                    pin_match = re.search(r"\b(\d{6})\b", line)
                    dob_match = re.search(r"(\b\d{1,2}[\-/]\d{1,2}[\-/]\d{2,4}\b)", line)
                    if email_match:
                        maybe_assign('email', email_match.group(0), 0.45)
                    if phone_match and len(re.sub(r'\D', '', phone_match.group(0))) >= 7:
                        maybe_assign('phone_number', phone_match.group(0).strip(), 0.45)
                    if pin_match:
                        maybe_assign('pin_code', pin_match.group(1), 0.45)
                    if dob_match:
                        maybe_assign('date_of_birth', dob_match.group(1), 0.45)
        except Exception:
            # swallow errors in fallback, we don't want overall failure
            pass
    
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
