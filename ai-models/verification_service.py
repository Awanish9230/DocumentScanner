import sys
import json
import difflib

def normalize_string(s):
    if s is None:
        return ""
    return str(s).strip().lower()

def calculate_confidence(ocr_val, user_val):
    """
    Calculate match status and confidence score.
    Returns: (match_status, confidence_score)
    """
    o = normalize_string(ocr_val)
    u = normalize_string(user_val)

    if not o and not u:
        return "not_found", 0
    
    if u and not o:
        return "not_found", 0 # User added, OCR missed
    
    if o and not u:
        # OCR found something, user didn't input. 
        # Technically a mismatch or just 'ocr_only'. 
        # Requirement says: "If OCR contains fields not in user input: Still include them with user_value: null."
        # We treat this as mismatch or low confidence match? 
        # Let's say mismatch for now as they don't match.
        return "mismatch", 0

    # Both present, calculate similarity
    matcher = difflib.SequenceMatcher(None, o, u)
    ratio = matcher.ratio() # 0 to 1
    score = round(ratio * 100, 2)

    if score >= 90:
        status = "match"
    elif score >= 50:
        status = "partial_match"
    else:
        status = "mismatch"
        
    return status, score

def verify(ocr_data, user_data):
    """
    Compare OCR extracted fields with User filled fields.
    """
    
    # Flatten OCR data for easier comparison
    # Structure is { "extracted_fields": { ..., "dynamically_detected_fields": {...} } }
    ocr_flat = {}
    if "extracted_fields" in ocr_data:
        base = ocr_data["extracted_fields"]
        for k, v in base.items():
            if k == "dynamically_detected_fields":
                for dk, dv in v.items():
                    ocr_flat[dk] = dv
            else:
                ocr_flat[k] = v
    else:
        # Fallback if structure is different
        ocr_flat = ocr_data

    # User data is likely flat
    user_flat = user_data

    # Collect all unique keys
    all_keys = set(ocr_flat.keys()) | set(user_flat.keys())
    
    verification_result = {}
    dynamic_field_results = {}
    
    match_count = 0
    mismatch_count = 0
    partial_count = 0
    not_found_count = 0
    total_fields = 0

    # Pre-defined standard fields to keep in the main block
    standard_fields = {
        "first_name", "middle_name", "last_name", "gender", "date_of_birth",
        "address_line_1", "address_line_2", "city", "state", "pin_code",
        "country", "phone_number", "email"
    }

    for key in all_keys:
        ocr_val = ocr_flat.get(key, None)
        user_val = user_flat.get(key, None)
        
        status, score = calculate_confidence(ocr_val, user_val)
        
        result_obj = {
            "ocr_value": ocr_val,
            "user_value": user_val,
            "match_status": status,
            "confidence_score": score
        }
        
        # Stats
        if status == "match": match_count += 1
        elif status == "mismatch": mismatch_count += 1
        elif status == "partial_match": partial_count += 1
        elif status == "not_found": not_found_count += 1
        total_fields += 1

        if key in standard_fields:
            verification_result[key] = result_obj
        else:
            dynamic_field_results[key] = result_obj

    # Calculate overall accuracy
    # We can define accuracy as (matches + partials*0.5) / total
    if total_fields > 0:
        accuracy = ((match_count * 100) + (partial_count * 50)) / total_fields
    else:
        accuracy = 0

    final_output = {
        "verification_result": {
            **verification_result,
            "dynamic_field_results": dynamic_field_results,
            "overall_accuracy": round(accuracy, 2),
            "fields_matched": match_count,
            "fields_mismatched": mismatch_count,
            "fields_partial": partial_count,
            "fields_not_found": not_found_count
        }
    }
    
    return final_output

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--ocr', type=str, required=True, help='OCR JSON string')
    parser.add_argument('--user', type=str, required=True, help='User JSON string')
    args = parser.parse_args()
    
    try:
        ocr_json = json.loads(args.ocr)
        user_json = json.loads(args.user)
        
        result = verify(ocr_json, user_json)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
