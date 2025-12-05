#!/usr/bin/env python3
"""Test OCR field parsing with actual extracted text"""

import sys
sys.path.insert(0, 'ai-models')
from ocr_service import parse_fields_from_text

# Sample extracted text from OCR (what Tesseract would return)
sample_text = """Name: John Smith
Email: john.smith@example.com
Phone: +91-9876543210
Address: 123 Sample Lane, SomeCity
City: Bangalore
State: Karnataka
Country: India
Pin Code: 560001
Gender: Male
Date of Birth: 15/05/1990"""

sample_lines = sample_text.split('\n')

print("Testing parse_fields_from_text with sample extracted text:")
print("=" * 60)
print(sample_text)
print("=" * 60)

fields = parse_fields_from_text(sample_text, sample_lines)

print("\nExtracted Fields:")
print("-" * 60)
for field_name, value in sorted(fields.items()):
    print(f"{field_name:20} = {value}")

print(f"\nTotal fields extracted: {len(fields)}")
