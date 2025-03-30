import os
import re
import requests
from git import Repo

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

def commit_and_push_changes(file_path, old_url, new_url):
    try:
        print("\nCommitting and pushing changes...")
        # Git repo objesi oluştur
        repo = Repo('.')
        
        # Değişiklikleri staging'e ekle
        repo.index.add([file_path])
        
        # Commit oluştur
        commit_message = f"Update mainUrl from {old_url} to {new_url}"
        repo.index.commit(commit_message)
        
        # Push yap
        origin = repo.remote('origin')
        origin.push()
        
        print("Changes committed and pushed successfully")
        return True
    except Exception as e:
        print(f"Error in Git operations: {e}")
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
                        
                        # Git işlemleri
                        if commit_and_push_changes(file_path, current_url, new_url):
                            print("All operations completed successfully")
                        else:
                            print("Failed to commit and push changes")
                            
                    except Exception as e:
                        print(f"Error updating file: {e}")
                    
                    break
        else:
            print("Current URL is working fine")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()