import os
import re
import requests
import time

def check_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        print(f"Checking URL: {url}")
        response = requests.get(url, headers=headers, timeout=5)
        success = response.status_code == 200
        print(f"URL {url} is {'working' if success else 'not working'}")
        return success
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return False

def update_file(file_path, old_url, new_url):
    try:
        print(f"\nUpdating file: {file_path}")
        print(f"Old URL: {old_url}")
        print(f"New URL: {new_url}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if old_url not in content:
            print(f"Warning: Old URL not found in file!")
            return False
            
        new_content = content.replace(old_url, new_url)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print("File updated successfully")
        return True
    except Exception as e:
        print(f"Error updating file: {e}")
        return False

def find_kt_file(base_folder):
    """Base folder isminden .kt dosyasını bulur"""
    folder_name = os.path.basename(base_folder)  # Klasör ismini al
    kt_file = f"{folder_name}.kt"  # Klasör ismi + .kt
    
    for root, dirs, files in os.walk(base_folder):
        if kt_file in files:  # Dosyayı bul
            return os.path.join(root, kt_file)
    return None

def main():
    base_folder = 'DizipalV2'  # Ana klasör
    print(f"\nStarting URL checker")
    print(f"Looking for {base_folder}.kt in {base_folder} directory")
    
    if not os.path.exists(base_folder):
        print(f"Error: {base_folder} not found!")
        return
    
    # Klasör isminden .kt dosyasını bul
    kt_file_path = find_kt_file(base_folder)
    
    if not kt_file_path:
        print(f"Error: {base_folder}.kt file not found!")
        return
    
    print(f"\nFound .kt file: {kt_file_path}")
    
    try:
        with open(kt_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"File content length: {len(content)}")
            
        # URL'yi bul
        url_pattern = r'override\s+var\s+mainUrl\s*=\s*"(https://dizipal\d+\.com)"'
        match = re.search(url_pattern, content)
        
        if not match:
            print("No URL pattern found in file")
            return
            
        current_url = match.group(1)
        current_number = int(re.search(r'dizipal(\d+)', current_url).group(1))
        print(f"Found URL: {current_url} (number: {current_number})")
        
        if not check_url(current_url):
            print("\nTrying higher numbers...")
            for i in range(current_number + 1, current_number + 11):
                test_url = f"https://dizipal{i}.com"
                if check_url(test_url):
                    print(f"\nFound working URL: {test_url}")
                    if update_file(kt_file_path, current_url, test_url):
                        print("Update successful!")
                        return
                    break
        else:
            print("Current URL is working fine")
                    
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    main()