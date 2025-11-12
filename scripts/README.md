# 🌍 HubSpot Content Translation Automation

This project automates the process of translating **HubSpot page content** from one language to another using the **Gemini API**.  
It extracts text from a HubSpot page, translates it intelligently (with skip conditions for non-relevant content), and updates the translated version back into HubSpot.

You can use these scripts to translate **any language pair** — for example:

- English → Thai
- English → French
- Spanish → English
- Japanese → German
- And many more

---

## 📂 Project Overview

The project includes **three main scripts**, forming a complete translation pipeline:

| Script              | Purpose                                                                                                                              | Output                               |
| :------------------ | :----------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------- |
| `get-content.py`    | Extracts all text-based content (titles, labels, rich text, etc.) from a HubSpot page and saves it as a JSON file.                   | `hubspot_translatable_content.json`  |
| `translate.py`      | Reads the extracted JSON, sends each text field to Gemini for translation, and generates a translated version (any target language). | `hubspot_translated_<language>.json` |
| `update_content.py` | Updates your HubSpot page by replacing English (or source language) text with the translated content.                                | Updated HubSpot page                 |

---

## ⚙️ Prerequisites

Before running the scripts, make sure you have:

1. **Python 3.10+** installed
2. Required packages:
   ```
   pip install requests google-generativeai python-dotenv
   ```
3. A `.env` file with your API keys and page id.
   ```
   HUBSPOT_API_KEY="your_hubspot_private_app_token"
   GEMINI_API_KEY="your_gemini_api_key"
   ```

## 🚀 Step-by-Step Usage Guide

### Step 1: Extract Page Content from HubSpot

**Script:** `get-content.py`

This script connects to the HubSpot CMS via API and extracts **all readable text** from a specific page, such as headings, paragraphs, and CTAs.

#### How to Run

1. Open the script and replace your HubSpot **PAGE_ID**.
2. Run the command:

   ```
    python your_file_path\get-content.py
   ```

3. Wait for the extraction to finish.
4. Output: A JSON file will be created in the same folder: `hubspot_translatable_content.json`
   Example:
   ```
    {
        "root.htmlTitle": "Welcome to our HR platform",
        "root.metaDescription": "We simplify HR workflows for businesses.",
        "root.layoutSections.dnd_area.rows[0].0.params.cta_group.button_text": "Learn More"
    }
   ```

## Step 2: Translate Extracted Content

**Script:** `translate.py`

This script reads the extracted JSON and translates each English text block into the target language using Gemini.

### How to Configure

1. Open the script and set your language preferences:

   ```
   SOURCE_LANG = "English"
   TARGET_LANG = "Japanese"
   ```

2. Run the translation:
   ```
   python translate.py
   ```

**What the Script Does**

- Translates text one field at a time (avoiding large context loss)
- Skips:
  - Placeholder text (e.g. “Lorem ipsum…”)
  - Dynamic keys such as `.rows[10].0.rows[0].0.label`
- Saves progress automatically after each translation
- Produces a new file containing **only translated text**

**Output**: `hubspot_translated_japanese.json`

## 🔁 Step 3: Update HubSpot Page with Translated Content

**Script:** `update-content.py`

This script takes the translated JSON and attempts to apply those translations back into the HubSpot page JSON via the HubSpot CMS API.

### How it works (high level)

- The script reads a JSON file in this folder (by default `hubspot_translatable_content.json`), filters for keys that end with the target language suffix (by default `_th`), strips that suffix and locates the corresponding field inside the fetched HubSpot page JSON.
- It uses dot-path traversal (supports array indices in the form `rows[0]`) to find and replace values in the page JSON.
- After applying replacements in memory, it removes read-only/system-managed fields and issues a `PATCH` to the HubSpot page endpoint (`/cms/v3/pages/site-pages/{PAGE_ID}`).

### Before you run

1. Make a manual backup of the current page JSON using `get-content.py` (recommended). Example:

```cmd
python get-content.py
```

This produces `hubspot_translatable_content.json` (or your extracted file) which you should keep as the source-of-truth backup.

2. Confirm your translated JSON file exists in the scripts folder and uses the expected key suffix (e.g. `_th` for Thai). The script currently looks for keys that end with `_th` and will strip that suffix when mapping back into the page JSON.

Example translation key:

```
root.layoutSections.dnd_area.rows[0].0.params.cta_group.button_text_th
```

When applied, the script removes `_th` and updates the `root.layoutSections.dnd_area.rows[0].0.params.cta_group.button_text` field inside the fetched HubSpot page JSON.

### How to run

Windows (cmd.exe):

```
python update-content.py
```

macOS / Linux:

```
python3 update-content.py
```

What the script prints:

- Number of translations found (keys ending with `{language}`).
- For each key it attempts to locate and update the field inside the page JSON. It prints `✅ Updated: <path>` for successes and `⚠️ Could not locate: <path>` for misses.
- A final summary with the total fields updated.

### Troubleshooting

- If the script fails to fetch the page, check `PAGE_ID` and `HUBSPOT_API_KEY` and ensure the token has CMS read/write scopes.
- If PATCH requests fail, inspect the HTTP response printed by the script — common causes are invalid payload structure or missing permissions.
- If many fields are reported as "Could not locate", the dot-path mapping may not match the live page structure; run `get-content.py` again to inspect the current page JSON structure and adjust keys if necessary.

---
