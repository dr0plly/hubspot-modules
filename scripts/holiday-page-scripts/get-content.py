import requests
import json
import os
import sys
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

#  Keys
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
PAGE_ID = os.getenv("PAGE_ID")


# HubSpot API Setup
page_url = f"https://api.hubapi.com/cms/v3/pages/site-pages/{PAGE_ID}"
# page_url = f"https://api.hubapi.com/cms/v3/blogs/posts/{PAGE_ID}"
headers = {"Authorization": f"Bearer {HUBSPOT_API_KEY}"}

# Fetch the page
response = requests.get(page_url, headers=headers)

# Check if request was successful
if response.status_code != 200:
    print(f"❌ Error: {response.status_code} - {response.text}")
    exit(1)

page_data = response.json()

# Saving the File
print("\nPage Content JSON:")

# Get the folder where the script itself is located
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "page_content.json")

# Save JSON file
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(page_data, f, indent=2, ensure_ascii=False)

print(f"\nSaved to {output_path}")
print(f"Successfully fetched and saved page content!")
