import os
import json
import time
import re
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

#  Language Settings

SOURCE_LANG = "English"
TARGET_LANG = "Thai"

# Gemini Configuration

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")


# File Paths

script_dir = os.path.dirname(os.path.abspath(__file__))
base_content_path = os.path.join(script_dir, "hubspot_translatable_content.json")
translated_path = os.path.join(script_dir, f"hubspot_translated_{TARGET_LANG.lower()}.json")


# Helpers

def is_exact_dynamic_row_pattern(key: str) -> bool:
    """Return True for keys ending exactly like ...rows[<num>].0.rows[0].0.label"""
    return bool(re.search(r"\.rows\[\d+\]\.0\.rows\[0\]\.0\.label$", key))

def is_placeholder_text(value: str) -> bool:
    """Skip Lorem ipsum placeholder content (case-insensitive)"""
    return isinstance(value, str) and value.strip().lower().startswith("lorem ipsum")

def is_content_type_key(key: str) -> bool:
    """Return True for keys that end with '.content_type' — these should not be translated
    but should be copied into the translated JSON so mapping is preserved."""
    return isinstance(key, str) and key.endswith(".content_type")

def backup_file(path: str) -> str:
    """Create a timestamped backup copy and return its path"""
    base, ext = os.path.splitext(path)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = f"{base}_backup_{timestamp}{ext}"
    with open(path, "r", encoding="utf-8") as fr, open(backup_path, "w", encoding="utf-8") as fw:
        fw.write(fr.read())
    return backup_path

def clean_gemini_output(text: str) -> str:
    """Remove code block wrappers like ```html from Gemini output."""
    if not text:
        return text
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", text.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())
    return cleaned.strip()


# Load main English content

if not os.path.exists(base_content_path):
    print(f"❌ hubspot_translated_{TARGET_LANG.lower()}.json not found in script folder.")
    exit(1)

with open(base_content_path, "r", encoding="utf-8") as f:
    try:
        base_content = json.load(f)
    except Exception as e:
        print(f"❌ Failed to parse hubspot_translated_{TARGET_LANG.lower()}.json:", e)
        exit(1)

print(f"✅ Loaded {len(base_content)} entries from hubspot_translated_{TARGET_LANG.lower()}.json")


# Check existing translation file

if os.path.exists(translated_path):
    with open(translated_path, "r", encoding="utf-8") as f:
        try:
            translated_content = json.load(f)
        except:
            translated_content = {}
    print(f"📂 Found existing translation file with {len(translated_content)} entries.")
else:
    translated_content = {}
    print("🆕 No existing translation file found. Starting fresh...")


# Compare progress

base_keys = list(base_content.keys())
translated_keys = list(translated_content.keys())

if translated_keys and base_keys[-1] in translated_keys:
    print("✅ All text is already translated.")
    exit()

# Create a backup of the existing translation file (if any)
if os.path.exists(translated_path):
    try:
        backup_path = backup_file(translated_path)
        print(f"💾 Backup created: {backup_path}")
    except Exception as e:
        print(f"⚠️ Could not create backup: {e}")


# Resume or start translation

start_index = 0
if translated_keys:
    # Continue from where translation left off
    last_translated_key = translated_keys[-1]
    if last_translated_key in base_keys:
        start_index = base_keys.index(last_translated_key) + 1
        print(f"🔄 Resuming translation from key #{start_index + 1}/{len(base_keys)} ({last_translated_key})")

translated_count = 0

for i, (key, value) in enumerate(list(base_content.items())[start_index:], start=start_index):
    # Skip already translated
    if key in translated_content:
        continue

    # Skip dynamic row pattern
    if is_exact_dynamic_row_pattern(key):
        print(f"🚫 Skipping {key} (matches exact dynamic-row pattern)")
        continue

    # Skip placeholder text
    if is_placeholder_text(value):
        print(f"🚫 Skipping {key} (placeholder 'Lorem ipsum')")
        continue

    # Copy content_type keys without translating (preserve in translated JSON)
    if is_content_type_key(key):
        print(f"ℹ️ Copying {key} (content_type key) into translated file without translating")
        translated_content[key] = value
        with open(translated_path, "w", encoding="utf-8") as f:
            json.dump(translated_content, f, ensure_ascii=False, indent=2)
        continue

    # Build prompt
    prompt = (
        f"You are a professional website translator. "
        f"Translate the following text from {SOURCE_LANG} to {TARGET_LANG}. "
        "Preserve HTML tags, formatting, and tone. "
        "Use natural, concise language suitable for a business website.\n\n"
        f"TEXT:\n{value}"
    )

    try:
        print(f"🌐 Translating ({i+1}/{len(base_content)}): {key}")

        # Gemini request
        response = model.generate_content(prompt)

        translated_text = ""
        if response and getattr(response, "text", None):
            translated_text = clean_gemini_output(response.text.strip())

        if not translated_text:
            print(f"⚠️ Empty response for {key}, skipping.")
            continue

        # Save translation
        translated_content[key] = translated_text
        translated_count += 1

        # Persist progress
        with open(translated_path, "w", encoding="utf-8") as f:
            json.dump(translated_content, f, ensure_ascii=False, indent=2)

        print(f"✅ Added translation for {key}")
        time.sleep(2)

    except Exception as e:
        print(f"⚠️ Error translating {key}: {e}")
        time.sleep(5)

print(f"\n🎉 Translation complete! {translated_count} new entries added.")
print(f"📁 Updated file: {translated_path}")
