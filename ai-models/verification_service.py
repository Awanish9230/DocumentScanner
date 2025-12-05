"""
Verification service - compares OCR extracted data with user-edited data.
Calculates similarity scores using Levenshtein distance.
"""
import json
import sys
import argparse
from typing import Dict, Any, List, Tuple
from difflib import SequenceMatcher

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def calculate_similarity(ocr_value: str, user_value: str) -> float:
    """
    Calculate similarity percentage between OCR and user values.
    Uses Levenshtein distance.
    """
    if not ocr_value and not user_value:
        return 100.0
    
    if not ocr_value or not user_value:
        return 0.0
    
    # Normalize values
    ocr_norm = str(ocr_value).lower().strip()
    user_norm = str(user_value).lower().strip()
    
    if ocr_norm == user_norm:
        return 100.0
    
    # Calculate using SequenceMatcher (more efficient)
    matcher = SequenceMatcher(None, ocr_norm, user_norm)
    ratio = matcher.ratio() * 100
    
    return round(ratio, 2)

def get_match_status(similarity: float) -> str:
    """Determine match status based on similarity score."""
    if similarity >= 95:
        return 'Match'
    elif similarity >= 75:
        return 'Partial Match'
    else:
        return 'Mismatch'

def verify_documents(ocr_data: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare OCR extracted data with user-edited data.
    
    Args:
        ocr_data: Dictionary with extracted OCR values. Can be:
                  - Full OCR response: {text, fields, fields_meta, confidence}
                  - Just fields dictionary: {field1, field2, ...}
        user_data: Dictionary with user-edited values {field1, field2, ...}
    
    Returns:
        Dictionary with verification results
    """
    results = []
    total_confidence = 0
    field_count = 0
    
    # Metadata keys to ignore when comparing
    metadata_keys = {'text', 'fields', 'fields_meta', 'confidence', 'raw_lines', 'error'}
    
    # Extract actual form fields from OCR data
    # If ocr_data contains a 'fields' key, use that; otherwise filter out metadata
    if isinstance(ocr_data, dict) and 'fields' in ocr_data:
        # Full OCR response object
        ocr_fields_dict = ocr_data.get('fields', {})
        if isinstance(ocr_fields_dict, dict):
            ocr_compare = ocr_fields_dict
        else:
            ocr_compare = {}
    else:
        # Already just fields, or direct comparison
        ocr_compare = {k: v for k, v in ocr_data.items() if k not in metadata_keys and not isinstance(v, (dict, list))}
    
    # Get all unique field names from actual fields only
    all_fields = set(ocr_compare.keys()) | set(user_data.keys())
    
    for field in sorted(all_fields):
        ocr_value = ocr_compare.get(field, '')
        user_value = user_data.get(field, '')
        
        # Skip empty fields
        if not ocr_value and not user_value:
            continue
        
        # Calculate similarity
        similarity = calculate_similarity(ocr_value, user_value)
        
        # Get match status
        status = get_match_status(similarity)
        
        # Use OCR extraction confidence (default 80%)
        ocr_confidence = 80.0
        
        # Combined score: average of similarity and OCR confidence
        combined_score = (similarity + ocr_confidence) / 2
        
        results.append({
            'field': field,
            'ocrValue': str(ocr_value),
            'userValue': str(user_value),
            'similarity': similarity,
            'ocr_confidence': ocr_confidence,
            'combinedScore': combined_score,
            'status': status,
            'notes': ''
        })
        
        total_confidence += combined_score
        field_count += 1
    
    # Calculate average confidence
    average_confidence = (total_confidence / field_count) if field_count > 0 else 0
    average_confidence = round(average_confidence, 2)
    
    return {
        'results': results,
        'averageConfidence': average_confidence,
        'totalFields': field_count,
        'matchedFields': len([r for r in results if r['status'] == 'Match']),
        'partialMatchFields': len([r for r in results if r['status'] == 'Partial Match']),
        'mismatchFields': len([r for r in results if r['status'] == 'Mismatch'])
    }

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify OCR data against user data')
    parser.add_argument('--ocr', type=str, required=True, help='OCR data as JSON string')
    parser.add_argument('--user', type=str, required=True, help='User data as JSON string')
    
    args = parser.parse_args()
    
    try:
        ocr_data = json.loads(args.ocr)
        user_data = json.loads(args.user)
        
        # Ensure they're dictionaries
        if not isinstance(ocr_data, dict):
            ocr_data = {'value': ocr_data}
        if not isinstance(user_data, dict):
            user_data = {'value': user_data}
        
        result = verify_documents(ocr_data, user_data)
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        error_response = {
            'error': str(e),
            'results': [],
            'averageConfidence': 0
        }
        print(json.dumps(error_response))
        sys.exit(1)
