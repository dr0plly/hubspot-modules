import requests
import json
import os
import shutil
import subprocess
import sys
from dotenv import load_dotenv

load_dotenv()

# Keys
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")
BASE_PAGE_ID = os.getenv("PAGE_ID")

# HubSpot API URLs
CLONE_URL = "https://api.hubapi.com/cms/v3/pages/site-pages/clone"

headers = {
    "Authorization": f"Bearer {HUBSPOT_API_KEY}",
    "Content-Type": "application/json"
}

def get_state_files():
    """Get all state JSON files except delhi.json and andhra-pradesh.json"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    
    state_files = []
    for file in sorted(os.listdir(data_dir)):
        if file.endswith('.json') and file not in ['delhi.json', 'andhra-pradesh.json']:
            state_files.append(file)
    
    return state_files

def get_state_name_from_file(filename):
    """Extract state name from filename"""
    return filename.replace('.json', '')

def clone_hubspot_page(state_name, clone_name):
    """Clone the HubSpot page for the state"""
    print(f"\n🔄 Cloning HubSpot page for {state_name}...")
    print(f"🔗 URL: {CLONE_URL}")
    
    payload = {
        "id": BASE_PAGE_ID,
        "cloneName": clone_name
    }
    
    try:
        response = requests.post(CLONE_URL, json=payload, headers=headers)
        
        # Accept both 200 and 201 as success (HubSpot API may return either)
        if response.status_code in [200, 201]:
            response_data = response.json()
            new_page_id = response_data.get('id')
            print(f"✅ Page cloned successfully!")
            print(f"📝 New Page ID: {new_page_id}")
            return new_page_id
        
        elif response.status_code == 401:
            print(f"❌ Error 401: Unauthorized - Invalid API Key")
            print(f"💡 Response: {response.text}")
            return None
        
        elif response.status_code == 404:
            print(f"❌ Error 404: Page not found")
            print(f"💡 Please check your PAGE_ID: {BASE_PAGE_ID}")
            print(f"💡 Response: {response.text}")
            return None
        
        else:
            print(f"❌ Error {response.status_code}")
            print(f"💡 Response: {response.text}")
            return None
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return None

def update_env_page_id(page_id):
    """Update PAGE_ID in .env file and reload environment"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    
    # Read .env file
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add PAGE_ID
        found = False
        for i, line in enumerate(lines):
            if line.startswith('PAGE_ID='):
                lines[i] = f'PAGE_ID={page_id}\n'
                found = True
                break
        
        if not found:
            lines.append(f'PAGE_ID={page_id}\n')
        
        # Write back to .env
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        # Reload environment variables
        os.environ['PAGE_ID'] = page_id
        return True
    
    return False

def run_python_script(script_name, page_id=None):
    """Run a Python script with optional PAGE_ID override"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, script_name)
    
    print(f"\n▶️  Running {script_name}...")
    
    try:
        # Create environment with updated PAGE_ID if provided
        env = os.environ.copy()
        if page_id:
            env['PAGE_ID'] = page_id
        
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=60,
            env=env
        )
        
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"✅ {script_name} completed successfully")
            return True
        else:
            print(f"❌ {script_name} failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
    
    except subprocess.TimeoutExpired:
        print(f"❌ {script_name} timed out")
        return False
    except Exception as e:
        print(f"❌ Error running {script_name}: {str(e)}")
        return False

def move_updated_file(state_name):
    """Move updated_<state_name>_page_content.json to updated folder"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    updated_file = os.path.join(script_dir, f"updated_{state_name}_page_content.json")
    updated_folder = os.path.join(script_dir, 'updated')
    
    # Create updated folder if it doesn't exist
    if not os.path.exists(updated_folder):
        os.makedirs(updated_folder)
    
    if os.path.exists(updated_file):
        destination = os.path.join(updated_folder, f"updated_{state_name}_page_content.json")
        try:
            shutil.move(updated_file, destination)
            print(f"📁 Moved {os.path.basename(updated_file)} to updated/ folder")
            return True
        except Exception as e:
            print(f"❌ Error moving file: {str(e)}")
            return False
    else:
        print(f"⚠️  File not found: {os.path.basename(updated_file)}")
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
    
    if not BASE_PAGE_ID:
        print("❌ PAGE_ID not found in .env file")
        return False
    
    return True

def main():
    """Main automation function"""
    
    print("=" * 70)
    print("🚀 HubSpot Holiday Page Automation")
    print("=" * 70)
    
    # Validate environment
    if not validate_environment():
        print("\n💡 Make sure your .env file has:")
        print("   HUBSPOT_API_KEY=your_api_key")
        print("   PAGE_ID=your_page_id")
        return
    
    # Get state files
    state_files = get_state_files()
    
    if not state_files:
        print("❌ No state JSON files found in data/ folder")
        return
    
    print(f"\n📋 Found {len(state_files)} state(s) to process:")
    for file in state_files:
        print(f"   • {get_state_name_from_file(file)}")
    
    # Process each state - only clone pages
    successful_states = []
    failed_states = []
    
    for idx, state_file in enumerate(state_files, 1):
        state_name = get_state_name_from_file(state_file)
        
        print(f"\n" + "=" * 70)
        print(f"[{idx}/{len(state_files)}] Cloning page for: {state_name}")
        print("=" * 70)
        
        # Clone the page
        clone_name = f"[Holiday] - {state_name.replace('-', ' ').title()}"
        new_page_id = clone_hubspot_page(state_name, clone_name)
        
        if not new_page_id:
            print(f"❌ Failed to clone page for {state_name}")
            failed_states.append(state_name)
            continue
        
        successful_states.append(state_name)
        print(f"✅ Successfully cloned page for {state_name}")
    
    # Summary
    print(f"\n" + "=" * 70)
    print("📊 AUTOMATION SUMMARY")
    print("=" * 70)
    print(f"✅ Successful: {len(successful_states)}")
    for state in successful_states:
        print(f"   • {state}")
    
    if failed_states:
        print(f"\n❌ Failed: {len(failed_states)}")
        for state in failed_states:
            print(f"   • {state}")
    
    print(f"\n" + "=" * 70)
    if not failed_states:
        print("🎉 All states processed successfully!")
    else:
        print(f"⚠️  {len(failed_states)} state(s) failed. Please review the errors above.")
    print("=" * 70)

if __name__ == "__main__":
    main()
