"""
Small dev harness to run the OCR service against a local image and print results.
Usage: python run_sample.py /path/to/image.jpg
"""
import sys
import json
from ocr_service import extract_text


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_sample.py /path/to/image.jpg")
        sys.exit(1)

    path = sys.argv[1]
    try:
        out = extract_text(path)
        print('\n--- OCR Output (processed JSON) ---')
        print(json.dumps(out, indent=2))

        # also print a friendly per-line debug summary if available
        if out.get('lines'):
            print('\n--- Per-line summary ---')
            for i, l in enumerate(out.get('lines', []), 1):
                print(f"{i:02d}) text: {l.get('text')}")
                print(f"    confidence: {l.get('confidence')}%")
                if l.get('candidates'):
                    print("    candidates:")
                    for c in l.get('candidates'):
                        print(f"      - {c}")
                print('')
    except FileNotFoundError as fe:
        print(json.dumps({"error": str(fe)}))
    except Exception as e:
        # Print a readable JSON error to make backend parsing robust
        print(json.dumps({"error": "OCR processing failed", "details": str(e)}))


if __name__ == '__main__':
    main()
