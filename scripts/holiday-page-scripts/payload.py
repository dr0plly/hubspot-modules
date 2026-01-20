import json
import os
import sys

filename = "west-bengal.json"
# Fix encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

def load_json(file_path):
    """Load JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(file_path, data):
    """Save JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def generate_holiday_table_html(holidays):
    """Generate HTML table rows from holidays data"""
    rows = ""
    # Skip first row (header row)
    for holiday in holidays[1:]:
        rows += f"""<tr>
<td>{holiday['date']}</td>
<td>{holiday['day']}</td>
<td>{holiday['name']}</td>
<td>{holiday['type']}</td>
</tr>
"""
    return rows

def generate_types_list_html(types_data):
    """Generate HTML list items from types data"""
    items = ""
    for item in types_data:
        items += f"<li><strong>{item['li'].split(' - ')[0]} -</strong> {item['li'].split(' - ', 1)[1]}</li>\n"
    return items

def map_state_to_page_content(state_data, page_content_data):
    """
    Map data from filename to page_content.json
    Finds the 'Rich Text' widget and updates its HTML content
    """
    
    # Navigate to the layoutSections to find the Rich Text widget
    layout_sections = page_content_data.get('layoutSections', {})
    dnd_area = layout_sections.get('dnd_area', {})
    rows = dnd_area.get('rows', [])
    
    # Find the Rich Text widget (first row, first cell)
    if rows and isinstance(rows[0], dict):
        first_row = rows[0]
        cell = first_row.get('0', {})
        cell_rows = cell.get('rows', [])
        
        if cell_rows and isinstance(cell_rows[0], dict):
            widget = cell_rows[0].get('0', {})
            
            # Check if this is the Rich Text widget
            if widget.get('label') == 'Rich Text':
                params = widget.get('params', {})
                
                # Build new HTML content
                holiday_rows = generate_holiday_table_html(state_data['holidays'])
                types_items = generate_types_list_html(state_data['types']['ol'])
                
                new_html = f"""<section class="page-heading">
<div class="content-wrapper">
<h1 class="main-heading">{state_data['h1']}</h1>
</div>
</section>
<!-- Hero Sec -->
<section class="hero-banner">
<div class="content-wrapper">
<p class="hero-para">{state_data['para']}</p>
</div>
</section>
<!-- Table Sec -->
<section class="holiday-sec">
<div class="content-wrapper">
<table id="holiday-table">
<thead>
<tr>
<th>Date</th>
<th>Day</th>
<th>Holiday</th>
<th>Holiday Type</th>
</tr>
</thead>
<tbody>
{holiday_rows}</tbody>
</table>
</div>
</section>
<!-- Impact Sec -->
<section class="impact-sec">
<div class="content-wrapper">
<h2>{state_data['h2']}</h2>
<p>{state_data['para2']}</p>
<p>{state_data['para3']}</p>
</div>
</section>
<!-- CTA Sec -->"""
                
                # Update the HTML in params
                params['html'] = new_html
                widget['params'] = params
                
                print("✅ Successfully mapped filename data to Rich Text widget HTML")
                return page_content_data
    
    print("❌ Could not find Rich Text widget in page_content.json")
    return page_content_data

def update_faq_widget(state_data, page_content_data):
    """
    Update the FAQ widget with data from filename
    """
    
    layout_sections = page_content_data.get('layoutSections', {})
    dnd_area = layout_sections.get('dnd_area', {})
    rows = dnd_area.get('rows', [])
    
    # Find the FAQ widget (second row, first cell)
    if len(rows) > 1 and isinstance(rows[1], dict):
        second_row = rows[1]
        cell = second_row.get('0', {})
        cell_rows = cell.get('rows', [])
        
        if cell_rows and isinstance(cell_rows[0], dict):
            faq_widget = cell_rows[0].get('0', {})
            
            # Check if this is the FAQ widget
            if 'FAQ' in faq_widget.get('label', ''):
                params = faq_widget.get('params', {})
                content_group = params.get('content_group', {})
                
                # Update FAQ data
                faq_list = [{
                    "question": state_data['faq']['question'],
                    "answer": f"<p>{state_data['faq']['answer']}</p>"
                }]
                
                content_group['faq_list'] = faq_list
                params['content_group'] = content_group
                faq_widget['params'] = params
                
                print("✅ Successfully updated FAQ widget with filename data")
                return page_content_data
    
    print("⚠️  Could not find FAQ widget in page_content.json")
    return page_content_data

def main():
    """Main function to execute the payload mapping"""
    
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    state_path = os.path.join(script_dir, 'data', filename)
    page_content_path = os.path.join(script_dir, 'page_content.json')
    
    print("📂 Loading JSON files...")
    
    # Load JSON files
    state_data = load_json(state_path)
    page_content_data = load_json(page_content_path)
    
    print(f"✓ Loaded filename")
    print(f"✓ Loaded page_content.json")
    
    # Map Rich Text widget
    page_content_data = map_state_to_page_content(state_data, page_content_data)
    
    # Update FAQ widget
    page_content_data = update_faq_widget(state_data, page_content_data)
    
    # Create new filename with state name
    state_name = state_data.get('state', 'state').lower()
    updated_filename = f"updated_{state_name}_page_content.json"
    updated_path = os.path.join(script_dir, updated_filename)
    
    # Save updated page content with new filename
    print(f"\n💾 Saving updated page content as {updated_filename}...")
    save_json(updated_path, page_content_data)
    
    print(f"✅ Successfully saved to {updated_path}")
    print("\n📊 Payload mapping complete!")
    print(f"   • Mapped title, description, and holiday list to Rich Text widget")
    print(f"   • Updated FAQ widget with FAQ data")

if __name__ == "__main__":
    main()
