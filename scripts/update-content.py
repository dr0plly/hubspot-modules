import os
import json
import requests
from dotenv import load_dotenv
load_dotenv()

# Configuration
language = "th"
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY") or os.getenv("HUBSPOT_PRIVATE_APP_TOKEN")
PAGE_ID = os.getenv("PAGE_ID")

TARGET_SUFFIX = os.getenv("TARGET_LANG_SUFFIX", f"{language}").strip()

# Path to your translated JSON file
script_dir = os.path.dirname(os.path.abspath(__file__))
translated_env = os.getenv("TRANSLATED_JSON")
default_translated = os.path.join(script_dir, f"hubspot_translated_{TARGET_SUFFIX}.json")
fallback = os.path.join(script_dir, "hubspot_translatable_content.json")
json_path = translated_env or (default_translated if os.path.exists(default_translated) else fallback)


# Load JSON

if not os.path.exists(json_path):
    print(f"❌ Translation JSON not found at: {json_path}")
    exit(1)

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Collect translations based on the configured suffix
suffix = f"_{TARGET_SUFFIX}"
suffix_len = len(suffix)
translations = {k[:-suffix_len]: v for k, v in data.items() if k.endswith(suffix)}
print(f"✅ Using translation file: {json_path}")
print(f"✅ Found {len(translations)} translations (suffix='{suffix}').\n")


# Get existing HubSpot page

page_url = f"https://api.hubapi.com/cms/v3/pages/site-pages/{PAGE_ID}"
# page_url = f"https://api.hubapi.com/cms/v3/blogs/posts/{PAGE_ID}"
headers = {"Authorization": f"Bearer {HUBSPOT_API_KEY}", "Content-Type": "application/json"}

response = requests.get(page_url, headers=headers)
if response.status_code != 200:
    print(f"❌ Failed to fetch HubSpot page: {response.status_code}\n{response.text}")
    exit()

page_data = response.json()
print(f"✅ Page fetched successfully (ID: {page_data.get('id')})")


# Helper: update nested key

def update_nested_field(data_obj, key_path, new_value):
    """Walk through nested dict using dot notation path and update the value."""
    parts = key_path.split(".")
    ref = data_obj
    try:
        for p in parts[:-1]:
            # Handle list indices like [0]
            if "[" in p and "]" in p:
                field = p.split("[")[0]
                idx = int(p[p.find("[") + 1 : p.find("]")])
                ref = ref[field][idx]
            else:
                ref = ref[p]
        last_key = parts[-1]
        if "[" in last_key and "]" in last_key:
            field = last_key.split("[")[0]
            idx = int(last_key[last_key.find("[") + 1 : last_key.find("]")])
            ref[field][idx] = new_value
        else:
            ref[last_key] = new_value
        return True
    except (KeyError, IndexError, TypeError):
        return False


# Apply translations

updated = 0
not_found = []
for key, translated_text in translations.items():
    # Expect keys to start with 'root.'; remove it if present
    clean_path = key[5:] if key.startswith("root.") else key

    success = update_nested_field(page_data, clean_path, translated_text)
    if success:
        updated += 1
        print(f"✅ Updated: {clean_path}")
    else:
        not_found.append(clean_path)
        print(f"⚠️ Could not locate: {clean_path}")

print(f"\n🧾 Total fields updated: {updated}")
if not_found:
    print(f"⚠️ Fields not found: {len(not_found)} (examples: {not_found[:5]})")


def clean_hubspot_payload(data):
    """
    Removes read-only or system-managed fields from the HubSpot page JSON
    before sending an update request.
    """
    readonly_fields = [
        "id", "createdAt", "updatedAt", "archived", "archivedAt",
        "authorName", "categoryId", "contentTypeCategory", "domain",
        "state", "currentState", "slug", "createdById", "updatedById"
    ]
    for field in readonly_fields:
        if field in data:
            del data[field]
    return data


# Backup original page JSON before patching

from datetime import datetime

backup_dir = os.path.join(script_dir, "backups")
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir, exist_ok=True)

timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"hubspot_page_backup_{PAGE_ID}_{timestamp}.json")
with open(backup_path, "w", encoding="utf-8") as bf:
    json.dump(page_data, bf, ensure_ascii=False, indent=2)

print(f"Backup of current page saved to: {backup_path}")

# Clean the payload before sending
page_data_cleaned = clean_hubspot_payload(json.loads(json.dumps(page_data)))

# Send patch request
print("🚀 Sending update request to HubSpot...")
update_response = requests.patch(page_url, headers=headers, json=page_data_cleaned)


if update_response.status_code in (200, 204):
    print("🎉 HubSpot page updated successfully with translated content!")
    
    # Delete translation files after successful update
    files_to_delete = [
        os.path.join(script_dir, "hubspot_translatable_content.json"),
        os.path.join(script_dir, f"hubspot_translated_{TARGET_SUFFIX}.json")
    ]
    
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                print(f"✅ Deleted: {os.path.basename(file_path)}")
            except Exception as e:
                print(f"⚠️ Failed to delete {os.path.basename(file_path)}: {e}")
        else:
            print(f"ℹ️ File not found: {os.path.basename(file_path)}")
else:
    print(f"❌ Update failed ({update_response.status_code}):\n{update_response.text}")
    print(f"\n📋 Debug - Payload sent:\n{json.dumps(page_data_cleaned, indent=2, ensure_ascii=False)}")
