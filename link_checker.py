import os
import re
import requests
from urllib3.exceptions import InsecureRequestWarning
import urllib3
urllib3.disable_warnings(InsecureRequestWarning)

def check_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        print(f"\nTesting URL: {url}")
        response = requests.get(
            url, 
            headers=headers, 
            timeout=10,
            verify=False,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            print(f"URL {url} is working (Status: 200)")
            return True
        else:
            print(f"URL {url} returned status code: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error checking {url}: {str(e)}")
        return False

def update_file(file_path, old_url, new_url):
    try:
        print(f"\nAttempting to update file: {file_path}")
        print(f"Replacing: {old_url}")
        print(f"With: {new_url}")
        
        # Dosyayı oku
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # İçerikte URL'nin varlığını kontrol et
        if old_url not in content:
            print("Warning: Old URL not found in file content!")
            return False
        
        # URL'yi değiştir
        new_content = content.replace(old_url, new_url)
        
        # Değişiklikleri kaydet
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        # Doğrulama
        with open(file_path, 'r', encoding='utf-8') as f:
            verify_content = f.read()
            if new_url in verify_content:
                print("File updated and verified successfully!")
                return True
            else:
                print("Update verification failed!")
                return False
                
    except Exception as e:
        print(f"Error updating file: {str(e)}")
        return False

def find_kt_file(base_folder):
    folder_name = os.path.basename(base_folder)
    kt_file = f"{folder_name}.kt"
    print(f"\nLooking for {kt_file}")
    
    for root, dirs, files in os.walk(base_folder):
        if kt_file in files:
            file_path = os.path.join(root, kt_file)
            print(f"Found file: {file_path}")
            return file_path
    return None

def main():
    base_folder = 'DizipalV2'
    
    if not os.path.exists(base_folder):
        print(f"Error: {base_folder} folder not found!")
        return
    
    kt_file_path = find_kt_file(base_folder)
    if not kt_file_path:
        print(f"Error: {base_folder}.kt file not found!")
        return
    
    try:
        # Dosyayı oku
        with open(kt_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # URL'yi bul
        url_pattern = r'override\s+var\s+mainUrl\s*=\s*"(https://dizipal\d+\.com)"'
        match = re.search(url_pattern, content)
        
        if not match:
            print("No URL pattern found in file!")
            return
        
        current_url = match.group(1)
        current_number = int(re.search(r'dizipal(\d+)', current_url).group(1))
        print(f"\nCurrent URL: {current_url}")
        print(f"Current number: {current_number}")
        
        # Mevcut URL'yi kontrol et
        if not check_url(current_url):
            print("\nCurrent URL is not working, trying next numbers...")
            
            # Sonraki URL'leri dene
            for i in range(current_number + 1, current_number + 11):
                test_url = f"https://dizipal{i}.com"
                print(f"\nTrying URL: {test_url}")
                
                if check_url(test_url):
                    print(f"\nFound working URL: {test_url}")
                    
                    # Dosyayı güncelle
                    if update_file(kt_file_path, current_url, test_url):
                        print(f"\nSuccessfully updated URL from {current_url} to {test_url}")
                        return
                    else:
                        print("Failed to update file!")
                        return
        else:
            print("\nCurrent URL is working fine, no update needed")
            
    except Exception as e:
        print(f"Error in main process: {str(e)}")

if __name__ == "__main__":
    main()