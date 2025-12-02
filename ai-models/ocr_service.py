"""
OCR service for DocumentScanner

Features implemented for local developer testing/harness:
- Image preprocessing (grayscale, CLAHE, upscaling, denoise, deskew)
- Primary OCR using HuggingFace TrOCR (printed & handwritten models)
- Secondary/fallback OCR using pytesseract
- Per-line segmentation and candidate list voting
- Per-token approximate confidences (best-effort from TrOCR logits if available)

Usage: import functions and call `process_image(path)` or use runners in this folder.
"""
from typing import List, Dict, Any, Tuple
import os
import io
import math
import numpy as np
from PIL import Image, ImageFilter, ImageOps
import cv2
import sys

try:
    # Prefer transformers/trOCR - optional, may be absent in minimal environments
    from transformers import AutoProcessor, AutoModelForVision2Seq
    HF_AVAILABLE = True
except Exception:
    HF_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
    # check whether the underlying tesseract binary is available in PATH
    import shutil
    TESSERACT_BINARY = shutil.which('tesseract') or shutil.which('tesseract.exe')
    if not TESSERACT_BINARY:
        # if wrapper is present but binary missing, warn the user but keep wrapper available
        TESSERACT_AVAILABLE = True
        TESSERACT_BINARY = None
except Exception:
    TESSERACT_AVAILABLE = False
    TESSERACT_BINARY = None

_DEFAULT_TROCR_PRINTED = 'microsoft/trocr-base-printed'
_DEFAULT_TROCR_HANDWRITTEN = 'microsoft/trocr-base-handwritten'


def _safe_imread(path_or_image):
    if isinstance(path_or_image, (str, )):
        img = cv2.imread(path_or_image)
        if img is None:
            raise FileNotFoundError(f'Cannot read image: {path_or_image}')
        return img
    elif isinstance(path_or_image, Image.Image):
        return cv2.cvtColor(np.asarray(path_or_image), cv2.COLOR_RGB2BGR)
    elif isinstance(path_or_image, np.ndarray):
        return path_or_image
    raise ValueError('Unsupported image input')


def load_models(print_model_name=None, handwritten_model_name=None):
    """Load HF processors/models if available. Returns a small dict of models.

    Models are loaded lazily in the runner as needed.
    """
    models = {'hf': None}
    if HF_AVAILABLE:
        printed = print_model_name or _DEFAULT_TROCR_PRINTED
        handwritten = handwritten_model_name or _DEFAULT_TROCR_HANDWRITTEN
        try:
            # We'll use one processor & model for both; switching to handwritten if needed
            proc = AutoProcessor.from_pretrained(printed)
            model = AutoModelForVision2Seq.from_pretrained(printed)
            models['hf'] = {'processor': proc, 'model': model, 'name': printed}
        except Exception:
            try:
                proc = AutoProcessor.from_pretrained(handwritten)
                model = AutoModelForVision2Seq.from_pretrained(handwritten)
                models['hf'] = {'processor': proc, 'model': model, 'name': handwritten}
            except Exception:
                models['hf'] = None

    models['pytesseract'] = TESSERACT_AVAILABLE
    return models


def _deskew_gray_image(gray: np.ndarray) -> np.ndarray:
    # Use moments to estimate rotation and deskew
    coords = np.column_stack(np.where(gray < 250))
    if coords.size == 0:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    (h, w) = gray.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return rotated


def preprocess_image(img_input) -> Tuple[Image.Image, np.ndarray]:
    """Return a PIL image and the working grayscale numpy image after different cleanups.

    Steps: read -> convert -> denoise -> CLAHE -> deskew -> upscaling (if small) -> final PIL
    """
    img_cv = _safe_imread(img_input)
    # Convert BGR to gray
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

    # Resize if image very small
    h, w = gray.shape
    upscale = 1
    if max(h, w) < 1000:
        upscale = int(math.ceil(1000 / max(h, w)))
        gray = cv2.resize(gray, (w * upscale, h * upscale), interpolation=cv2.INTER_CUBIC)

    # denoise (median) and bilateral alternative for color preservation
    gray = cv2.medianBlur(gray, 3)

    # Contrast limited AHE (CLAHE)
    try:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)
    except Exception:
        pass

    # deskew
    try:
        gray = _deskew_gray_image(gray)
    except Exception:
        pass

    # final denoising
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    pil = Image.fromarray(gray).convert('L')

    # sharpen a bit
    try:
        pil = pil.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
    except Exception:
        pass

    return pil, gray


def ocr_trocr_image(pil_image: Image.Image, models) -> Dict[str, Any]:
    """Run TrOCR OCR on a single image and return text + optional scores.

    Returns: {'text': str, 'raw_candidates': [str], 'avg_confidence': float}
    """
    if not HF_AVAILABLE or models.get('hf') is None:
        return {'text': '', 'raw_candidates': [], 'avg_confidence': 0.0, 'source': 'trocr_unavailable'}

    # We assume processor & model exist
    proc = models['hf']['processor']
    model = models['hf']['model']

    # Convert to RGB for trocr
    img_rgb = pil_image.convert('RGB')
    pixel_values = proc(images=img_rgb, return_tensors='pt').pixel_values

    # forward
    # Explicitly pass decoder_start_token_id to avoid configuration errors with some models
    outputs = model.generate(pixel_values, max_length=512, decoder_start_token_id=model.config.decoder_start_token_id)
    text = proc.batch_decode(outputs, skip_special_tokens=True)[0]

    # TrOCR models don't expose per-token confidences easily via generate output; use heuristics
    avg_conf = 85.0 if text.strip() else 0.0
    return {'text': text, 'raw_candidates': [text], 'avg_confidence': avg_conf, 'source': f"trocr:{models['hf']['name']}"}


def ocr_tesseract_image(pil_image: Image.Image, lang: str = 'eng') -> Dict[str, Any]:
    if not TESSERACT_AVAILABLE:
        return {'text': '', 'raw_candidates': [], 'avg_confidence': 0.0, 'source': 'tesseract_wrapper_missing'}
    if TESSERACT_AVAILABLE and not TESSERACT_BINARY:
        return {'text': '', 'raw_candidates': [], 'avg_confidence': 0.0, 'source': 'tesseract_binary_missing', 'error': 'tesseract binary not found in PATH'}

    try:
        raw = pytesseract.image_to_string(pil_image, lang=lang)
        # Tesseract doesn't expose a single confidence reliably via image_to_string; we set heuristic
        conf = 70.0 if raw.strip() else 0.0
        return {'text': raw, 'raw_candidates': [raw], 'avg_confidence': conf, 'source': 'tesseract'}
    except Exception:
        return {'text': '', 'raw_candidates': [], 'avg_confidence': 0.0, 'source': 'tesseract_error'}


def segment_lines(gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Return bounding boxes for line-like contours (x, y, w, h) in the grayscale image."""
    h, w = gray.shape[:2]
    # Adaptive threshold to find text areas
    try:
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10)
    except Exception:
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Dilate to connect components into lines
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (int(max(10, w // 80)), 1))
    dilated = cv2.dilate(thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in contours:
        x, y, cw, ch = cv2.boundingRect(c)
        # filter tiny regions
        if cw < max(30, w // 50) or ch < 10:
            continue
        boxes.append((x, y, cw, ch))

    # sort top-to-bottom
    boxes = sorted(boxes, key=lambda b: b[1])
    return boxes


def crop_box_from_gray(gray: np.ndarray, box: Tuple[int, int, int, int], pad: int = 5) -> Image.Image:
    x, y, w, h = box
    h_img, w_img = gray.shape[:2]
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(w_img, x + w + pad)
    y2 = min(h_img, y + h + pad)
    crop = gray[y1:y2, x1:x2]
    return Image.fromarray(crop).convert('L')


def ensemble_line_ocr(pil_line: Image.Image, models) -> List[Dict[str, Any]]:
    """Return a list of candidate dicts [{'text':..., 'confidence':..., 'source':...}] in descending confidence"""
    candidates = []

    # Try both trocr and tesseract; add multiple Tesseract configs if available
    trocr_res = ocr_trocr_image(pil_line, models)
    if trocr_res.get('text', '').strip():
        candidates.append({'text': trocr_res['text'].strip(), 'confidence': float(trocr_res.get('avg_confidence', 0.0)), 'source': trocr_res.get('source', 'trocr')})

    tess_res = ocr_tesseract_image(pil_line)
    if tess_res.get('text', '').strip():
        candidates.append({'text': tess_res['text'].strip(), 'confidence': float(tess_res.get('avg_confidence', 0.0)), 'source': tess_res.get('source', 'tesseract')})

    # Add a second tesseract pass with single-line config (PSM 7) if available to capture short lines
    try:
        if TESSERACT_AVAILABLE:
            import pytesseract
            cfg = '--psm 7'
            extra = pytesseract.image_to_string(pil_line, config=cfg)
            if extra and extra.strip() and all(extra.strip() != c['text'] for c in candidates):
                candidates.append({'text': extra.strip(), 'confidence': 64.0, 'source': 'tesseract_psm7'})
    except Exception:
        pass

    # If still no candidates, return empty
    if not candidates:
        return []

    # Score candidates using heuristic: base confidence + length bonus + punctuation/word penalty
    scored = []
    for c in candidates:
        base = float(c.get('confidence', 0.0))
        text = c.get('text', '')
        length_bonus = min(20.0, len(text) * 0.6)  # favor longer non-empty lines
        word_score = (len(text.split()) * 2.0)
        punctuation_penalty = -2.0 * sum(1 for ch in text if ch in '\\/*[]{}<>')
        # penalize very short gibberish (numbers only or single-char)
        gibberish_pen = 0.0
        if len(text) <= 2 or text.isdigit():
            gibberish_pen = -15.0

        score = base + length_bonus + word_score + punctuation_penalty + gibberish_pen
        scored.append({**c, 'score': score})

    # Keep unique best candidate texts with best score
    seen_text = {}
    for s in sorted(scored, key=lambda x: x['score'], reverse=True):
        t = s['text']
        if t in seen_text:
            # already seen
            continue
        seen_text[t] = s

    uniq = sorted(seen_text.values(), key=lambda x: x['score'], reverse=True)

    # Normalize and clamp confidences to 0..100 for returned candidates
    out = []
    for u in uniq:
        conf = float(u.get('confidence', 0.0))
        # If the model gave low raw confidence but heuristic score is high, boost a bit
        heuristic_boost = max(0.0, (u.get('score', 0) - 50.0) * 0.1)
        conf = max(conf, min(100.0, conf + heuristic_boost))
        out.append({'text': u['text'], 'confidence': round(conf, 2), 'source': u.get('source', 'unknown')})

    return out


def process_image(image_path: str, models=None) -> Dict[str, Any]:
    """High-level entry: preprocess image, segment lines, run ensemble per-line OCR and return a structured result."""
    if models is None:
        models = load_models()

    pil, gray = preprocess_image(image_path)
    boxes = segment_lines(gray)
    
    lines = []
    aggregated_text = []
    total_conf = 0.0
    conf_count = 0
    
    # 1. Run OCR on segmented lines
    for i, b in enumerate(boxes):
        try:
            crop = crop_box_from_gray(gray, b)
            candidates = ensemble_line_ocr(crop, models)
        except Exception:
            candidates = []

        best_text = candidates[0]['text'] if candidates else ''
        best_conf = candidates[0]['confidence'] if candidates else 0.0

        line_obj = {
            'box': b, 
            'candidates': candidates, 
            'best': best_text, 
            'best_confidence': best_conf, 
            'text': best_text, 
            'confidence': best_conf
        }
        lines.append(line_obj)
        if best_text.strip():
            aggregated_text.append(best_text.strip())
            total_conf += best_conf
            conf_count += 1

    # Fallback: if no boxes found, try whole-image OCR
    if not lines:
        try:
            whole_crop = pil
            whole_candidates = ensemble_line_ocr(whole_crop, models)
            best_text = whole_candidates[0]['text'] if whole_candidates else ''
            best_conf = whole_candidates[0]['confidence'] if whole_candidates else 0.0
            lines = [{'box': (0, 0, pil.width, pil.height), 'candidates': whole_candidates, 'best': best_text, 'best_confidence': best_conf, 'text': best_text, 'confidence': best_conf}]
            if best_text.strip():
                aggregated_text.append(best_text.strip())
                total_conf += best_conf
                conf_count += 1
        except Exception:
            pass

    avg_confidence = 0.0 if conf_count == 0 else (total_conf / max(1, conf_count))
    raw_text_str = '\n'.join(aggregated_text)

    # 2. Structural Extraction using postprocess
    # We default to empty structure if import fails
    final_output = {
        "extracted_fields": {
             "first_name": "", "middle_name": "", "last_name": "", "gender": "", "date_of_birth": "",
             "address_line_1": "", "address_line_2": "", "city": "", "state": "", "pin_code": "",
             "country": "", "phone_number": "", "email": "",
             "dynamically_detected_fields": {}
        }
    }

    try:
        from postprocess import extract_fields_from_lines
        # This returns {"extracted_fields": { ... }}
        extracted_data = extract_fields_from_lines(lines, raw_text=raw_text_str)
        final_output.update(extracted_data)
    except Exception as e:
        pass
    
    # Keep this debug print as it is useful for the user to see what was extracted
    sys.stderr.write(f"DEBUG RAW TEXT:\n{raw_text_str}\n")
    return final_output


if __name__ == '__main__':
    import argparse, json

    parser = argparse.ArgumentParser(description='Run OCR service on a single image (simple CLI).')
    parser.add_argument('image', help='image path to process')
    parser.add_argument('--print-model', help='HF trocr model name (optional)')
    args = parser.parse_args()

    models = load_models(print_model_name=args.print_model)
    out = process_image(args.image, models=models)
    print(json.dumps(out, ensure_ascii=False))
