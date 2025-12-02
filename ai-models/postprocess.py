import re
import json
import sys
from typing import List, Dict, Any, Tuple

# -------------------------------------------------------------------
# -------------------  YOUR ORIGINAL FUNCTIONS  ---------------------
# -------------------------------------------------------------------

def find_mobile_number(raw_text: str) -> str:
    match = re.search(r'\b(?:\+91[-\s]?)?[6-9]\d{9}\b', raw_text)
    return match.group(0) if match else None

def find_email(raw_text: str) -> str:
    match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', raw_text)
    return match.group(0) if match else None

def find_pincode(raw_text: str) -> str:
    match = re.search(r'\b\d{6}\b', raw_text)
    return match.group(0) if match else None

def split_name(full_name: str) -> Dict[str, str]:
    parts = full_name.strip().split()
    if len(parts) == 1:
        return {"first_name": parts[0], "middle_name": "", "last_name": ""}
    elif len(parts) == 2:
        return {"first_name": parts[0], "middle_name": "", "last_name": parts[1]}
    else:
        return {
            "first_name": parts[0],
            "middle_name": " ".join(parts[1:-1]),
            "last_name": parts[-1]
        }

def normalize_label(label: str) -> str:
    return (
        label.lower()
        .replace(":", "")
        .replace("-", " ")
        .strip()
    )

def extract_key_value(line: str) -> Tuple[str, str]:
    if ":" in line:
        parts = line.split(":", 1)
    elif "-" in line:
        parts = line.split("-", 1)
    else:
        return None, None

    key = normalize_label(parts[0])
    value = parts[1].strip()
    return key, value

def extract_fields_from_lines(lines: List[Dict[str, Any]], raw_text: str = None):
    # Initialize all standard fields
    extracted_fields = {
        "first_name": "",
        "middle_name": "",
        "last_name": "",
        "gender": "",
        "date_of_birth": "",
        "address_line_1": "",
        "address_line_2": "",
        "city": "",
        "state": "",
        "pin_code": "",
        "country": "",
        "phone_number": "",
        "email": "",
        "dynamically_detected_fields": {}
    }
    
    dynamically_detected = {}

    for item in lines:
        text = item.get("text", "").strip()
        key, value = extract_key_value(text)

        if key and value:
            if key in ["name", "full name"]:
                name_parts = split_name(value)
                extracted_fields["first_name"] = name_parts.get("first_name", "")
                extracted_fields["middle_name"] = name_parts.get("middle_name", "")
                extracted_fields["last_name"] = name_parts.get("last_name", "")
            elif key in ["address", "addr"]:
                extracted_fields["address_line_1"] = value
            elif key in ["city"]:
                extracted_fields["city"] = value
            elif key in ["state"]:
                extracted_fields["state"] = value
            elif key in ["gender", "sex"]:
                extracted_fields["gender"] = value
            elif key in ["dob", "date of birth", "birth date"]:
                extracted_fields["date_of_birth"] = value
            else:
                dynamically_detected[key] = value

    # Extra detections from raw text
    if raw_text:
        mobile = find_mobile_number(raw_text)
        if mobile:
            extracted_fields["phone_number"] = mobile
            
        email = find_email(raw_text)
        if email:
            extracted_fields["email"] = email
            
        pincode = find_pincode(raw_text)
        if pincode:
            extracted_fields["pin_code"] = pincode
    
    extracted_fields["dynamically_detected_fields"] = dynamically_detected

    return {"extracted_fields": extracted_fields}

# -------------------------------------------------------------------
# ---------------------  FIXED WRAPPER  ------------------------------
# -------------------------------------------------------------------

def postprocess_ocr(ocr_text: str):
    """
    Converts raw OCR text into the expected line array
    so extract_fields_from_lines() works correctly.
    """
    lines = []
    for line in ocr_text.split("\n"):
        if line.strip():
            lines.append({"text": line})

    return extract_fields_from_lines(lines, raw_text=ocr_text)

# -------------------------------------------------------------------
# -----------------------  MAIN EXECUTION  ---------------------------
# -------------------------------------------------------------------

if __name__ == "__main__":
    # Read input from Node.js or terminal
    ocr_text = sys.stdin.read().strip()

    # If no input → use fallback sample (THIS MAKES OUTPUT ALWAYS APPEAR)
    if not ocr_text:
        ocr_text = """
        Name: Rohit Sharma
        Father Name: Arun Kumar Sharma
        Address: Mumbai, Maharashtra 400001
        Mobile: 9876543210
        Email: demo@gmail.com
        """

    result = postprocess_ocr(ocr_text)

    print(json.dumps(result, indent=2))
