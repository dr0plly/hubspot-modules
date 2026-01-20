import requests
import json
import os
import sys
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Keys
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
PAGE_ID = os.getenv("PAGE_ID")

# HubSpot API Setup
page_url = f"https://api.hubapi.com/cms/v3/pages/site-pages/{PAGE_ID}"
headers = {
    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
    "Content-Type": "application/json"
}

def find_updated_file():
    """Find the updated_<state_name>_page_content.json file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Look for updated_*_page_content.json files
    for file in os.listdir(script_dir):
        if file.startswith("updated_") and file.endswith("_page_content.json"):
            return os.path.join(script_dir, file)
    
    return None

def load_json(file_path):
    """Load JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def prepare_update_payload(page_data):
    """
    Prepare the payload for HubSpot PATCH request
    Only include updateable fields, remove read-only fields
    """
    # Fields that can be updated via HubSpot API
    updateable_fields = {
        'layoutSections',
        'name',
        'slug',
        'pageTitle',
        'metaDescription',
        'pageExcerpt',
        'category',
        'subcategory'
    }
    
    payload = {}
    
    # Include updateable fields if they exist
    for field in updateable_fields:
        if field in page_data:
            payload[field] = page_data[field]
    
    # Always ensure layoutSections is included (the main content)
    if 'layoutSections' in page_data:
        payload['layoutSections'] = page_data['layoutSections']
    
    return payload

def update_hubspot_page(page_data):
    """
    Update the HubSpot page with the new content
    """
    print(f"\n📤 Pushing content to HubSpot...")
    print(f"🔗 URL: {page_url}")
    
    # Prepare the payload with only updateable fields
    payload = prepare_update_payload(page_data)
    
    print(f"📦 Payload fields: {list(payload.keys())}")
    
    try:
        # Make PATCH request to update the page
        response = requests.patch(page_url, headers=headers, json=payload)
        
        # Check if request was successful
        if response.status_code == 200:
            print(f"\n✅ Page updated successfully!")
            print(f"📝 Page ID: {PAGE_ID}")
            
            response_data = response.json()
            updated_at = response_data.get('updatedAt', 'Unknown')
            print(f"⏰ Updated at: {updated_at}")
            
            return True
        
        elif response.status_code == 400:
            print(f"❌ Error 400: Bad Request")
            print(f"💡 The payload structure might be invalid")
            print(f"\n📋 Response details:")
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    for error in error_data['errors']:
                        print(f"   • {error.get('message', 'Unknown error')}")
                else:
                    print(f"   {error_data}")
            except:
                print(f"   {response.text}")
            return False
        
        elif response.status_code == 401:
            print(f"❌ Error 401: Unauthorized - Invalid API Key")
            print(f"💡 Please check your HUBSPOT_API_KEY in .env file")
            return False
        
        elif response.status_code == 404:
            print(f"❌ Error 404: Page not found")
            print(f"💡 Please check your PAGE_ID in .env file")
            print(f"   Current PAGE_ID: {PAGE_ID}")
            return False
        
        elif response.status_code == 405:
            print(f"❌ Error 405: Method Not Allowed")
            print(f"💡 The API endpoint does not accept this request method")
            return False
        
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False

def move_updated_file(updated_file_path):
    """Move updated_<state_name>_page_content.json to updated folder"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    updated_folder = os.path.join(script_dir, 'updated')
    
    # Create updated folder if it doesn't exist
    if not os.path.exists(updated_folder):
        os.makedirs(updated_folder)
    
    try:
        file_name = os.path.basename(updated_file_path)
        destination = os.path.join(updated_folder, file_name)
        
        # Move the file
        import shutil
        shutil.move(updated_file_path, destination)
        print(f"📁 Moved {file_name} to updated/ folder")
        return True
    except Exception as e:
        print(f"❌ Error moving file: {str(e)}")
        return False

def cleanup_page_content():
    """Delete page_content.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    page_content_path = os.path.join(script_dir, 'page_content.json')
    
    if os.path.exists(page_content_path):
        try:
            os.remove(page_content_path)
            print(f"🗑️  Deleted page_content.json")
            return True
        except Exception as e:
            print(f"❌ Error deleting file: {str(e)}")
            return False
    
    return True

def validate_environment():
    """Validate that required environment variables are set"""
    if not HUBSPOT_API_KEY:
        print("❌ HUBSPOT_API_KEY not found in .env file")
        return False
    
    if not PAGE_ID:
        print("❌ PAGE_ID not found in .env file")
        return False
    
    return True

def main():
    """Main function to push updated content to HubSpot"""
    
    print("🚀 HubSpot Page Content Updater")
    print("=" * 50)
    
    # Validate environment variables
    if not validate_environment():
        print("\n💡 Make sure your .env file has:")
        print("   HUBSPOT_API_KEY=your_api_key")
        print("   PAGE_ID=your_page_id")
        return
    
    # Find the updated file
    print("\n🔍 Looking for updated page content file...")
    updated_file = find_updated_file()
    
    if not updated_file:
        print("❌ No updated_*_page_content.json file found!")
        print("💡 Please run payload.py first to generate the updated file")
        return
    
    file_name = os.path.basename(updated_file)
    print(f"✓ Found: {file_name}")
    
    # Load the updated page content
    print("\n📂 Loading updated page content...")
    try:
        page_data = load_json(updated_file)
        print(f"✓ Successfully loaded {file_name}")
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {str(e)}")
        return
    except FileNotFoundError as e:
        print(f"❌ File not found: {str(e)}")
        return
    
    # Update HubSpot page
    success = update_hubspot_page(page_data)
    
    if success:
        # Move updated file to updated folder
        move_updated_file(updated_file)
        
        # Cleanup page_content.json
        cleanup_page_content()
        
        print("\n" + "=" * 50)
        print("✅ Content update process completed successfully!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("⚠️  Content update failed. Please check the errors above.")
        print("=" * 50)

if __name__ == "__main__":
    main()
