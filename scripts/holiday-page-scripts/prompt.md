# Automating State-Wise Holiday Pages in HubSpot Using JSON & Python

## Objective

Design and implement a fully automated system to create **state-wise holiday pages for India** in **HubSpot CMS**, using **Python + HubSpot API**, where:

- Each Indian state has **one holiday page**
- All pages share a **fixed HTML layout**
- Holiday tables are **generated dynamically via HTML**
- An **existing FAQ module** is reused (no new modules created)
- All content is sourced from **JSON files only**
- No SQL, No HubDB, No Excel

---

## Canonical Page Structure

Each state page must strictly follow this structure:

1. **Main Heading (H1)**
2. **Introductory Paragraph**
3. **Holiday Table (HTML)**
4. **FAQ Section (existing HubSpot module)**

---

## Key Constraints & Design Rules

| Rule             | Implementation                        |
| ---------------- | ------------------------------------- |
| No new modules   | Direct HTML injection                 |
| Dynamic holidays | `<tr>` elements generated in Python   |
| FAQ handling     | Populate existing FAQ module repeater |
| Data source      | JSON only                             |
| Page creation    | HubSpot CMS Pages API                 |

---

## Step-by-Step Process

---

## STEP 1: Prepare the HubSpot Page Template

### Template Type

- **Website Page Template**

### Template HTML Skeleton

```html
<section class="state-holiday-page">
  <h1>{{ page_heading }}</h1>

  <p class="intro-text">{{ intro_text }}</p>

  <table class="holiday-table">
    <thead>
      <tr>
        <th>Date</th>
        <th>Day</th>
        <th>Holiday</th>
        <th>Type</th>
      </tr>
    </thead>

    <tbody>
      {{ holiday_table_rows }}
    </tbody>
  </table>

  {% module "faq_module" path="../modules/faq", label="FAQs" %}
</section>
```

### Notes

- `{{ holiday_table_rows }}` is a **raw HTML placeholder**
- The Python script controls creation/removal of table rows
- FAQ module already exists and supports dynamic entries

---

## STEP 2: Define the JSON Data Structure

Each state must have **one JSON object**:

```json
{
  "state": "Tamil Nadu",
  "slug": "tamil-nadu-holidays-2026",
  "meta": {
    "title": "Tamil Nadu Holidays 2026",
    "description": "Complete list of public holidays in Tamil Nadu for 2026"
  },
  "heading": "Tamil Nadu Public Holidays 2026",
  "intro": "Below is the official list of government and public holidays in Tamil Nadu for 2026.",
  "holidays": [
    {
      "date": "26 January 2026",
      "day": "Monday",
      "name": "Republic Day",
      "type": "National Holiday"
    },
    {
      "date": "14 April 2026",
      "day": "Tuesday",
      "name": "Tamil New Year",
      "type": "State Holiday"
    }
  ],
  "faqs": [
    {
      "question": "How many public holidays are there in Tamil Nadu?",
      "answer": "Tamil Nadu observes national, state, and regional holidays every year."
    }
  ]
}
```

---

## STEP 3: Generate Holiday Table HTML in Python

### Target HTML Output

```html
<tr>
  <td>26 January 2026</td>
  <td>Monday</td>
  <td>Republic Day</td>
  <td>National Holiday</td>
</tr>
```

### Python Logic (Conceptual)

```python
table_rows = ""

for holiday in data["holidays"]:
    table_rows += f"""
    <tr>
      <td>{holiday['date']}</td>
      <td>{holiday['day']}</td>
      <td>{holiday['name']}</td>
      <td>{holiday['type']}</td>
    </tr>
    """
```

✔ Adding or removing holidays updates the table automatically
✔ No module dependency
✔ Full markup control

---

## STEP 4: Data → Template Mapping

| JSON Key           | Template Field             |
| ------------------ | -------------------------- |
| `heading`          | `{{ page_heading }}`       |
| `intro`            | `{{ intro_text }}`         |
| `holidays[]`       | `{{ holiday_table_rows }}` |
| `faqs[]`           | Existing FAQ module        |
| `meta.title`       | Page meta title            |
| `meta.description` | Page meta description      |
| `slug`             | Page URL                   |

---

## STEP 5: Populate Existing FAQ Module

The script must map FAQs directly into the **existing FAQ module’s repeater fields**:

```json
"faq_module": {
  "faqs": [
    {
      "question": "How many public holidays are there in Tamil Nadu?",
      "answer": "Tamil Nadu observes national, state, and regional holidays every year."
    }
  ]
}
```

- No structural changes to the module
- Supports dynamic add/remove
- Reusable across all pages

---

## STEP 6: HubSpot Page Creation Payload (Conceptual)

```json
{
  "name": "Tamil Nadu Holidays 2026",
  "slug": "tamil-nadu-holidays-2026",
  "templatePath": "custom/state-holiday-template.html",
  "state": "PUBLISHED",
  "meta": {
    "title": "Tamil Nadu Holidays 2026",
    "description": "Public holiday list for Tamil Nadu"
  },
  "content": {
    "page_heading": "Tamil Nadu Public Holidays 2026",
    "intro_text": "Below is the official list...",
    "holiday_table_rows": "<tr>...</tr>",
    "faq_module": {
      "faqs": [...]
    }
  }
}
```

---

## STEP 7: Python Automation Structure

```
/automation
 ├── data/
 │   └── states.json
 ├── html_table_builder.py
 ├── hubspot_client.py
 ├── page_creator.py
 └── logs/
```

---

## STEP 8: Execution Workflow

1. Load JSON data
2. Validate required fields
3. Generate HTML table rows
4. Inject HTML into template placeholders
5. Populate FAQ module
6. Create page via HubSpot API
7. Publish or save as draft

---

## STEP 9: Error Handling & Safety

- Slug uniqueness check
- Empty holidays fallback message
- HTML sanitization
- API retry logic
- Draft mode for QA

---
