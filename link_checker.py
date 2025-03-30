import os
import re
import requests

def check_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124'
        }
        response = requests.get(url, headers=headers, timeout=5)
        print(f"Checking {url} - Status: {response.status_code}")
        return response.status_code == 200
    except:
        print(f"Failed to connect to {url}")
        return False

def main():
    # Sabit dosya yolu - değiştirin
    file_path = "DizipalV2/src/main/kotlin/com/Prueba/DizipalV2.kt"
    
    print("Starting URL check process...")
    
    try:
        # Dosyayı oku
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("File read successfully")
        
        # Mevcut URL'yi bul
        match = re.search(r'mainUrl\s*=\s*"(https://dizipal\d+\.com)"', content)
        if not match:
            print("URL pattern not found in file")
            return
        
        current_url = match.group(1)
        current_number = int(re.search(r'dizipal(\d+)', current_url).group(1))
        print(f"Current URL: {current_url}")
        
        # URL çalışıyor mu kontrol et
        if not check_url(current_url):
            print("Current URL is not working")
            
            # Yeni URL'yi bul
            for i in range(current_number + 1, current_number + 11):
                new_url = f"https://dizipal{i}.com"
                print(f"Trying {new_url}")
                
                if check_url(new_url):
                    print(f"Found working URL: {new_url}")
                    
                    # Dosyayı güncelle
                    new_content = content.replace(current_url, new_url)
                    
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print("File updated successfully")
                        
                        # Doğrulama
                        with open(file_path, 'r', encoding='utf-8') as f:
                            check_content = f.read()
                            if new_url in check_content:
                                print("Update verified successfully")
                            else:
                                print("Update verification failed")
                    except Exception as e:
                        print(f"Error updating file: {e}")
                    
                    break
        else:
            print("Current URL is working fine")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()