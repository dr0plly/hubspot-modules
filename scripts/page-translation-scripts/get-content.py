import requests
import json
import os
from dotenv import load_dotenv
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
print(f"Debug - URL: {page_url}")
print(f"Debug - Status Code: {response.status_code}")
print(f"Debug - Full Response: {response.text}")
if response.status_code != 200:
    print(f"❌ Failed to fetch page: {response.status_code}\n{response.text}")
    exit()

page_data = response.json()
print("✅ Page fetched successfully!")

# Recursive function to collect all text-like fields
def extract_text_fields(obj, path="root", result=None):
    if result is None:
        result = {}

    # If it's a dictionary, go deeper
    if isinstance(obj, dict):
        for key, value in obj.items():
            # Dive deeper into nested structures
            if isinstance(value, (dict, list)):
                extract_text_fields(value, f"{path}.{key}", result)
            else:
                # Identify text-based keys
                if isinstance(value, str) and (
                    any(
                        kw in key.lower()
                        for kw in [
                            "text",
                            "heading",
                            "title",
                            "label",
                            "content",
                            "value",
                            "placeholder",
                            "caption",
                            "alt",
                            "description",
                        ]
                    )
                ):
                    # Exclude code, style, or script data
                    if not any(
                        bad in key.lower() for bad in ["script", "style", "css", "path"]
                    ):
                        if value.strip():
                            result[f"{path}.{key}"] = value

    # If it's a list, loop through its items
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            extract_text_fields(item, f"{path}[{i}]", result)

    return result


# Extract all text content
translatable_fields = extract_text_fields(page_data)

# Save as JSON
print("\n🧾 Translatable Text JSON:")
print(json.dumps(translatable_fields, indent=2, ensure_ascii=False))

# Get the folder where the script itself is located
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, "hubspot_translatable_content.json")

# Save JSON file
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(translatable_fields, f, ensure_ascii=False, indent=2)

print(f"\n💾 Saved to {output_path}")

