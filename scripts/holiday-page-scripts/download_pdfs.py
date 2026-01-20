import json
import os
import requests
from pathlib import Path

# Define paths
data_folder = Path(__file__).parent / "data"
pdf_folder = Path(__file__).parent / "pdf"

# Create pdf folder if it doesn't exist
pdf_folder.mkdir(exist_ok=True)

def download_pdf(url, filename):
    """Download PDF from URL and save to pdf folder."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        filepath = pdf_folder / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✓ Downloaded: {filename}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed to download {filename}: {e}")
        return False

def process_json_files():
    """Process all JSON files in data folder."""
    if not data_folder.exists():
        print(f"Error: Data folder not found at {data_folder}")
        return
    
    json_files = list(data_folder.glob("*.json"))
    
    if not json_files:
        print("No JSON files found in data folder.")
        return
    
    print(f"Found {len(json_files)} JSON files. Starting download...\n")
    
    successful = 0
    failed = 0
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if pdf field exists
            if 'pdf' in data and data['pdf']:
                pdf_url = data['pdf']
                # Use state name or filename for pdf name
                state_name = data.get('state', json_file.stem)
                pdf_filename = f"{state_name.lower().replace(' ', '-')}.pdf"
                
                if download_pdf(pdf_url, pdf_filename):
                    successful += 1
                else:
                    failed += 1
            else:
                print(f"⊘ No PDF URL found in {json_file.name}")
        
        except json.JSONDecodeError:
            print(f"✗ Invalid JSON: {json_file.name}")
            failed += 1
        except Exception as e:
            print(f"✗ Error processing {json_file.name}: {e}")
            failed += 1
    
    print(f"\n{'='*50}")
    print(f"Download Summary: {successful} successful, {failed} failed")
    print(f"PDFs saved to: {pdf_folder}")

if __name__ == "__main__":
    process_json_files()
