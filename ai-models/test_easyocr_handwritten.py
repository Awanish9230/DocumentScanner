"""
Test EasyOCR on the handwritten form image
"""
import easyocr
import json

# Initialize reader
print("Initializing EasyOCR...")
reader = easyocr.Reader(['en'], gpu=False, verbose=False)

# Test on the uploaded image
image_path = r"C:\Users\Awanish\.gemini\antigravity\brain\49ce85f2-189c-4a8d-a3f8-a20966383072\uploaded_image_1764701409635.png"

print(f"\nExtracting text from: {image_path}")
results = reader.readtext(image_path)

print("\n=== EXTRACTED TEXT ===")
for (bbox, text, conf) in results:
    print(f"{text} (confidence: {conf*100:.1f}%)")

# Combine all text
raw_text = '\n'.join([text for (bbox, text, conf) in results])
print("\n=== COMBINED TEXT ===")
print(raw_text)
