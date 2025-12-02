"""
Run OCR on an image (using ocr_service.extract_text) and verify it against a provided JSON file
containing expected userData fields (so you can reproduce the backend verify behavior locally).

Usage:
  python run_verify_sample.py /path/to/image.jpg /path/to/userdata.json

The script prints verification results (similarity, ocr_confidence, combinedScore, status).
"""
import sys
import json
import re
from ocr_service import extract_text


def levenshtein(a, b):
    if len(a) == 0:
        return len(b)
    if len(b) == 0:
        return len(a)

    matrix = [[0] * (len(a) + 1) for _ in range(len(b) + 1)]
    for i in range(len(b) + 1):
        matrix[i][0] = i
    for j in range(len(a) + 1):
        matrix[0][j] = j

    for i in range(1, len(b) + 1):
        for j in range(1, len(a) + 1):
            if b[i - 1] == a[j - 1]:
                matrix[i][j] = matrix[i - 1][j - 1]
            else:
                matrix[i][j] = min(matrix[i - 1][j - 1] + 1,
                                   matrix[i][j - 1] + 1,
                                   matrix[i - 1][j] + 1)
    return matrix[len(b)][len(a)]


def similarity_score(a, b):
    a = a.lower()
    b = b.lower()
    dist = levenshtein(a, b)
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 100.0
    return ((max_len - dist) / max_len) * 100


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_verify_sample.py /path/to/image.jpg /path/to/userdata.json")
        sys.exit(1)

    image_path = sys.argv[1]
    user_json = sys.argv[2]

    try:
        user_data = json.load(open(user_json))
    except Exception as e:
        print("Failed to read userData JSON:", e)
        sys.exit(1)

    print("Running OCR on:", image_path)
    try:
        ocr_out = extract_text(image_path)
    except FileNotFoundError as fe:
        print(json.dumps({"error": str(fe)}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": "OCR processing failed", "details": str(e)}))
        sys.exit(1)
    print('\nOCR fields detected:')
    print(json.dumps(ocr_out.get('fields', {}), indent=2))

    print('\nVerifying against provided userData:')
    results = []
    total = 0
    count = 0
    for k, user_val in user_data.items():
        if isinstance(user_val, (int, float)):
            user_val = str(user_val)
        user_val = (user_val or '').strip()
        ocr_val = ''
        if k in ocr_out:
            ocr_val = str(ocr_out[k])
        elif 'fields' in ocr_out and k in ocr_out['fields']:
            ocr_val = str(ocr_out['fields'][k])

        # Trim and normalize
        uTrim = (user_val or '').strip()
        oTrim = (ocr_val or '').strip()

        # If both empty
        if not uTrim and not oTrim:
            print(f"- {k}: user='(empty)' | ocr='(empty)' -> Not Provided | combined=0.00")
            total += 0
            count += 1
            continue

        if uTrim and not oTrim:
            print(f"- {k}: user='{uTrim}' | ocr='(empty)' -> User Added | combined=0.00")
            total += 0
            count += 1
            continue

        if oTrim and not uTrim:
            print(f"- {k}: user='(empty)' | ocr='{oTrim}' -> OCR Present | combined=0.00")
            total += 0
            count += 1
            continue

        sim = similarity_score(uTrim, oTrim)
        ocr_conf = 0
        if f"{k}_confidence" in ocr_out:
            try:
                ocr_conf = float(ocr_out[f"{k}_confidence"]) or 0
            except Exception:
                ocr_conf = 0
        combined = (0.55 * sim + 0.45 * ocr_conf) if ocr_conf > 0 else sim

        status = 'Mismatch'
        if combined >= 95:
            status = 'Match'
        elif combined >= 75:
            status = 'Partial Match'

        print(f"- {k}: user='{user_val}' | ocr='{ocr_val}' | sim={sim:.2f} | ocr_conf={ocr_conf} | combined={combined:.2f} -> {status}")
        total += combined
        count += 1

    avg = (total / count) if count > 0 else 0
    print(f"\nAverage combined verification score: {avg:.2f}%")


if __name__ == '__main__':
    main()
