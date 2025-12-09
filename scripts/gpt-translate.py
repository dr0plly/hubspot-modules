import os
import json
import time
import re
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

#  Language Settings

SOURCE_LANG = "English"
TARGET_LANG = "Thai"

# OpenAI Configuration

GPT_API_KEY = os.getenv("GPT_API_KEY")
client = OpenAI(api_key=GPT_API_KEY)


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

def is_dnd_area_label_key(key: str) -> bool:
    """Return True for keys ending with 'dnd_area.label' — these should not be translated."""
    return isinstance(key, str) and key.endswith("dnd_area.label")

def is_rows_label_key(key: str) -> bool:
    """Return True for keys ending with '0.rows[0].0.label' — these should not be translated."""
    return isinstance(key, str) and key.endswith("0.rows[0].0.label")

def backup_file(path: str) -> str:
    """Create a timestamped backup copy and return its path"""
    base, ext = os.path.splitext(path)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    backup_path = f"{base}_backup_{timestamp}{ext}"
    with open(path, "r", encoding="utf-8") as fr, open(backup_path, "w", encoding="utf-8") as fw:
        fw.write(fr.read())
    return backup_path

def clean_gpt_output(text: str) -> str:
    """Remove code block wrappers from API output only. Keep all HTML tags intact."""
    if not text:
        return text
    # Remove code block wrappers only
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

    # Skip placeholder text
    if is_placeholder_text(value):
        print(f"🚫 Skipping {key} (placeholder 'Lorem ipsum')")
        continue

    # Skip dnd_area.label keys
    if is_dnd_area_label_key(key):
        print(f"ℹ️ Copying {key} (dnd_area.label key) into translated file without translating")
        translated_content[key] = value
        with open(translated_path, "w", encoding="utf-8") as f:
            json.dump(translated_content, f, ensure_ascii=False, indent=2)
        continue

    # Skip 0.rows[0].0.label keys (check this BEFORE is_exact_dynamic_row_pattern)
    if is_rows_label_key(key):
        print(f"ℹ️ Copying {key} (0.rows[0].0.label key) into translated file without translating")
        translated_content[key] = value
        with open(translated_path, "w", encoding="utf-8") as f:
            json.dump(translated_content, f, ensure_ascii=False, indent=2)
        continue

    # Skip dynamic row pattern
    if is_exact_dynamic_row_pattern(key):
        print(f"🚫 Skipping {key} (matches exact dynamic-row pattern)")
        continue
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
        f"Translate the following English text to Thai. Requirements:\n"
        "1. Use natural, professional, and easy-to-understand tone for business audience\n"
        "2. Make it sound human and polished, aligned with HR/technology context\n"
        "3. Maintain clarity, smooth flow, and correct technical meaning\n"
        "4. Avoid robotic language\n"
        "5. Output ONLY the Thai translation, nothing else\n"
        "6. IMPORTANT: Keep all HTML tags exactly as they are in the original text\n"
        "7. Do NOT remove, add, or modify any HTML tags (<br>, <strong>, <p>, <h1>, <h2>, <h3>, <h4>, <div>, <span>, etc.)\n"
        "8. Translate only the text content inside and between the HTML tags\n"
        "9. Preserve all attributes, styles, and structure of HTML tags\n\n"
        f"{value}"
    )

    try:
        print(f"🌐 Translating ({i+1}/{len(base_content)}): {key}")

        # OpenAI ChatGPT request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a professional translator specializing in translating English content to Thai with a focus on HR technology and business contexts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        translated_text = ""
        if response and response.choices and len(response.choices) > 0:
            translated_text = clean_gpt_output(response.choices[0].message.content.strip())

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
