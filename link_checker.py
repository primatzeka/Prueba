import os
import re
import requests
from git import Repo
import time

def check_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
        }
        print(f"Checking URL: {url}")
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        print(f"Response status code: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error checking URL {url}: {str(e)}")
        return False

def update_files_and_commit(file_path, old_url, new_url):
    try:
        # Dosyayı oku
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"Current content contains old URL: {'mainUrl = "' + old_url + '"' in content}")

        # Değişiklikleri yap
        new_content = content.replace(f'mainUrl = "{old_url}"', f'mainUrl = "{new_url}"')
        if content == new_content:
            print("No changes needed in content")
            return False

        # Dosyayı güncelle
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"File updated: {file_path}")

        # Git işlemleri
        repo = Repo('.')
        repo.index.add([file_path])
        commit_message = f"Update mainUrl from {old_url} to {new_url}"
        repo.index.commit(commit_message)
        origin = repo.remote('origin')
        origin.push()
        print("Changes committed and pushed to GitHub")
        return True

    except Exception as e:
        print(f"Error in update_files_and_commit: {str(e)}")
        return False

def main():
    dizipal_folder = 'DizipalV2'
    print(f"Starting script, checking folder: {dizipal_folder}")
    
    if not os.path.exists(dizipal_folder):
        print(f"Error: {dizipal_folder} folder not found")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Directory contents: {os.listdir('.')}")
        return

    for root, dirs, files in os.walk(dizipal_folder):
        print(f"Checking directory: {root}")
        print(f"Found files: {files}")
        
        for file in files:
            if file.endswith('.kt'):
                file_path = os.path.join(root, file)
                print(f"\nProcessing file: {file_path}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        url_match = re.search(r'override\s+var\s+mainUrl\s*=\s*"(https://dizipal\d+\.com)"', content)
                        
                        if url_match:
                            current_url = url_match.group(1)
                            print(f"Found URL in file: {current_url}")
                            
                            # Mevcut numara
                            current_number = int(re.search(r'dizipal(\d+)', current_url).group(1))
                            print(f"Current number: {current_number}")
                            
                            if not check_url(current_url):
                                print("Current URL is not working, trying next numbers...")
                                
                                # Sonraki 10 sayıyı dene
                                for i in range(current_number + 1, current_number + 11):
                                    test_url = f"https://dizipal{i}.com"
                                    print(f"\nTesting URL: {test_url}")
                                    
                                    if check_url(test_url):
                                        print(f"Found working URL: {test_url}")
                                        if update_files_and_commit(file_path, current_url, test_url):
                                            print("File updated and changes pushed successfully")
                                            return  # İşlem başarılı, scripti sonlandır
                                        break
                            else:
                                print("Current URL is working fine, no changes needed")
                        else:
                            print("No matching URL pattern found in file")
                
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")

if __name__ == "__main__":
    main()