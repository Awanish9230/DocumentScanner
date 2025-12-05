import re

# Sample extracted text (what we see in the screenshot)
text = """Name: John Smith
Email: john.smith@example.com
Phone: +91-9876543210
Address: 123 Sample Lane, SomeCity
City: Bangalore
State: Karnataka
Country: India
Pin Code: 560001
Gender: Male
Date of Birth: 15/05/1990"""

lines = text.split('\n')
full_text = text + '\n' + '\n'.join(lines)

# Test individual patterns
patterns = {
    'name': r'(?:name|full name|applicant name)[\s:]*([^\n]+?)(?:\n|$)',
    'email': r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    'phone': r'(?:phone|mobile|contact|phone number|phone no|phone-no|phone number)[\s:]*\(?([+\d\-\s()\.]{8,}?)(?:\n|$)',
    'address': r'(?:address|location|addr|address line|address line 1|address.?line.?1)[\s:]*([^\n]+?)(?:\n|$)',
    'city': r'(?:city|town|city/town)[\s:]*([^\n]+?)(?:\n|$)',
    'state': r'(?:state|state/province)[\s:]*([^\n]+?)(?:\n|$)',
    'country': r'(?:country|nation|country/nation)[\s:]*([^\n]+?)(?:\n|$)',
    'pin_code': r'(?:pin|zip|postal code|pin code|pincode|pin.?code|zip code)[\s:]*(\d{4,10})',
}

print("Testing patterns on extracted text:")
for field_name, pattern in patterns.items():
    match = re.search(pattern, full_text, re.IGNORECASE | re.MULTILINE)
    if match:
        value = match.group(1).strip()
        print(f"✓ {field_name}: '{value}'")
    else:
        print(f"✗ {field_name}: No match")
