"""
Quick test to verify the OCR pipeline works
"""
import json
from PIL import Image, ImageDraw, ImageFont

# Create a simple test image with text
img = Image.new('RGB', (400, 200), color='white')
draw = ImageDraw.Draw(img)

# Add some text
text_lines = [
    "Name: John Doe",
    "Email: john@example.com",
    "Phone: 9876543210"
]

y = 20
for line in text_lines:
    draw.text((20, y), line, fill='black')
    y += 40

# Save test image
test_path = "backend/uploads/test_ocr.png"
img.save(test_path)
print(f"Created test image: {test_path}")

# Now run OCR on it
from ocr_service import process_image, load_models

models = load_models()
result = process_image(test_path, models=models)

print("\nOCR Result:")
print(json.dumps(result, indent=2, ensure_ascii=False))
