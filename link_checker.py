import os
import re
import requests
import time

def extract_number_from_url(url):
    # dizipalXXX.com formatından XXX sayısını çıkarır
    match = re.search(r'dizipal(\d+)\.com', url)
    if match:
        return int(match.group(1))
    return None

def create_new_url(base_number):
    # Yeni URL oluşturur
    return f"https://dizipal{base_number}.com"

def check_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def update_kt_file(file_path, old_url, new_url):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # mainUrl değerini güncelle
        updated_content = content.replace(f'mainUrl = "{old_url}"', f'mainUrl = "{new_url}"')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"Updated {file_path} with new URL: {new_url}")
        return True
    except Exception as e:
        print(f"Error updating file {file_path}: {str(e)}")
        return False

def main():
    dizipal_folder = 'DizipalV2'
    
    if not os.path.exists(dizipal_folder):
        print(f"Error: {dizipal_folder} folder not found")
        return
    
    # .kt dosyalarını recursive olarak ara
    for root, dirs, files in os.walk(dizipal_folder):
        for file in files:
            if file.endswith('.kt'):
                file_path = os.path.join(root, file)
                print(f"Checking file: {file_path}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        url_match = re.search(r'override\s+var\s+mainUrl\s*=\s*"(https://dizipal\d+\.com)"', content)
                        
                        if url_match:
                            current_url = url_match.group(1)
                            print(f"Found URL: {current_url}")
                            
                            # Mevcut URL'den sayıyı çıkar
                            current_number = extract_number_from_url(current_url)
                            if current_number is None:
                                continue
                            
                            # Mevcut URL çalışıyor mu kontrol et
                            if not check_url(current_url):
                                print(f"Current URL {current_url} is not working, trying next numbers...")
                                
                                # Sonraki 10 sayıyı dene
                                for i in range(current_number + 1, current_number + 11):
                                    test_url = create_new_url(i)
                                    print(f"Testing URL: {test_url}")
                                    
                                    if check_url(test_url):
                                        print(f"Found working URL: {test_url}")
                                        # Dosyayı güncelle
                                        if update_kt_file(file_path, current_url, test_url):
                                            print(f"Successfully updated {file_path}")
                                        break
                
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")

if __name__ == "__main__":
    main()