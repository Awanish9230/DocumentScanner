"""
Post-processing utilities for OCR output.

This module provides:
- normalization helpers
- key:value detection from OCR lines
- structure extraction into canonical fields
- dynamic field discovery
"""
import re
from typing import List, Dict, Any, Tuple

# ----------------------------------------------------------------------
# 1. Normalization & Cleaning
# ----------------------------------------------------------------------

def normalize_label(lbl: str) -> str:
    """Convert a label text to snake_case."""
    if not lbl:
        return ''
    s = lbl.strip().lower()
    # Remove possessives
    s = re.sub(r"\'s\b", '', s)
    # Replace non-alphanumeric with underscore
    s = re.sub(r"[^a-z0-9]+", '_', s)
    # Collapse underscores
    s = re.sub(r'_+', '_', s)
    return s.strip('_')

def clean_value(val: str) -> str:
    """Remove OCR noise and fix common issues."""
    if not val:
        return None
    
    s = val.strip()
    
    # Fix common email OCR errors (e.g. "Abigail@" -> "Abigail@gmail.com" is hard to guess, 
    # but we can fix "Abigail@ gmail . com")
    # Here we just clean up spacing around special chars
    s = re.sub(r'\s*@\s*', '@', s)
    s = re.sub(r'\s*\.\s*', '.', s)
    
    # Remove leading/trailing special chars that are likely noise
    s = s.strip(" :;,-_=|/\\")
    
    # Collapse spaces
    s = re.sub(r'\s+', ' ', s)
    
    return s if s else None

def normalize_email(s: str) -> str:
    if not s: return ''
    s = s.strip().lower()
    s = re.sub(r'\s+', '', s)
    # Fix common OCR typos for emails
    s = s.replace('..', '.')
    return s

def normalize_phone(s: str) -> str:
    if not s: return ''
    # Keep only digits and plus sign
    digits = re.sub(r'[^0-9+]', '', s)
    return digits

def normalize_date(s: str) -> str:
    if not s: return ''
    return s.strip()

# ----------------------------------------------------------------------
# 2. Field Detection Logic
# ----------------------------------------------------------------------

def split_full_name(full_name: str) -> Dict[str, str]:
    """Split a full name into first, middle, last."""
    if not full_name:
        return {"first_name": "", "middle_name": "", "last_name": ""}
    
    parts = full_name.split()
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

def detect_kv_from_line(line: str) -> Tuple[str, str]:
    """Try to detect key:value patterns in a single OCR line."""
    if not line or not line.strip():
        return (None, None)

    # Common separators: ':', '-', or just space if it looks like a form label
    # We prioritize ':' and '-'
    for sep in [':', ' - ', ' -', '- ']:
        if sep in line:
            parts = line.split(sep, 1)
            if len(parts) == 2:
                k = parts[0].strip()
                v = parts[1].strip()
                # Heuristic: Label shouldn't be too long (e.g. > 40 chars)
                if k and len(k) < 40:
                    return (k, v)
    
    return (None, None)

# ----------------------------------------------------------------------
# 3. Main Extraction
# ----------------------------------------------------------------------

def extract_fields_from_lines(lines: List[Dict[str, Any]], raw_text: str = None) -> Dict[str, Any]:
    """
    Main entry point.
    Returns the structure:
    {
      "extracted_fields": {
          "first_name": "", ...
          "dynamically_detected_fields": { ... }
      }
    }
    """
    
    # Pre-defined known fields we want to capture specifically
    known_fields_map = {
        'name': 'full_name',
        'full_name': 'full_name',
        'first_name': 'first_name',
        'middle_name': 'middle_name',
        'last_name': 'last_name',
        'gender': 'gender',
        'sex': 'gender',
        'date_of_birth': 'date_of_birth',
        'dob': 'date_of_birth',
        'birth_date': 'date_of_birth',
        'age': 'age',
        'address': 'address_line_1', # fallback
        'address_line_1': 'address_line_1',
        'address_line_2': 'address_line_2',
        'city': 'city',
        'state': 'state',
        'country': 'country',
        'pin': 'pin_code',
        'pincode': 'pin_code',
        'postal_code': 'pin_code',
        'zip': 'pin_code',
        'phone': 'phone_number',
        'mobile': 'phone_number',
        'contact': 'phone_number',
        'email': 'email',
        'e-mail': 'email',
        'document_number': 'document_number',
        'id_number': 'document_number',
        'issue_date': 'issue_date',
        'expiry_date': 'expiry_date',
        'signature': 'signature'
    }

    # Initialize output structure
    extracted = {
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
    
    # Temporary storage for found values to avoid overwriting with worse ones
    # We can use a simple dict: key -> value
    found_values = {}

    # Helper to set value if not empty
    def set_field(key, val, is_dynamic=False):
        val = clean_value(val)
        if not val:
            return
        
        if is_dynamic:
            extracted["dynamically_detected_fields"][key] = val
        else:
            # If it's a name field, we might need to split it later if we only got full_name
            found_values[key] = val
            if key in extracted:
                extracted[key] = val

    # 1. Iterate over lines to find Key-Value pairs
    for line_obj in lines:
        text = line_obj.get('text', '')
        if not text:
            continue
            
        k, v = detect_kv_from_line(text)
        if k and v:
            norm_k = normalize_label(k)
            
            # Check if it maps to a known field
            if norm_k in known_fields_map:
                canonical_key = known_fields_map[norm_k]
                set_field(canonical_key, v)
            else:
                # Dynamic field
                # Heuristic: ignore very short keys or keys that look like garbage
                if len(norm_k) > 2:
                    set_field(norm_k, v, is_dynamic=True)

    # 2. Regex / Pattern Fallbacks for missing mandatory fields
    # We search in raw_text if available, or join lines
    full_text = raw_text if raw_text else "\n".join([l.get('text', '') for l in lines])
    
    if 'email' not in found_values:
        email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', full_text)
        if email_match:
            set_field('email', normalize_email(email_match.group(1)))
            
    if 'phone_number' not in found_values:
        # Look for pattern like +91... or 10 digits
        phone_match = re.search(r'(?:\+?\d{1,3}[\s-]?)?(?:\d{10,})', full_text)
        if phone_match:
            set_field('phone_number', normalize_phone(phone_match.group(0)))
            
    if 'pin_code' not in found_values:
        pin_match = re.search(r'\b\d{6}\b', full_text)
        if pin_match:
            set_field('pin_code', pin_match.group(0))

    # 3. Handle Name Splitting
    # If we found 'full_name' but not specific parts, split it
    if 'full_name' in found_values:
        # Only overwrite if specific parts are missing
        parts = split_full_name(found_values['full_name'])
        if not extracted['first_name']: extracted['first_name'] = parts['first_name']
        if not extracted['middle_name']: extracted['middle_name'] = parts['middle_name']
        if not extracted['last_name']: extracted['last_name'] = parts['last_name']
        
    # If we have first/last but no full name, that's fine, the output format requires first/mid/last.
    
    # 4. Final Cleanup
    # Ensure all values in extracted are strings (not None)
    for k in extracted:
        if k == "dynamically_detected_fields":
            continue
        if extracted[k] is None:
            extracted[k] = ""
            
    return {"extracted_fields": extracted}
