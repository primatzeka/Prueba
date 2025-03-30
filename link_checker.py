import os
import re
import requests
from bs4 import BeautifulSoup
from fp.fp import FreeProxy
import json
from git import Repo
import time

def check_url(url, use_proxy=False):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        if use_proxy:
            proxy = FreeProxy(timeout=1).get()
            response = requests.get(url, proxies={"http": proxy, "https": proxy}, headers=headers, timeout=5)
        else:
            response = requests.get(url, headers=headers, timeout=5)
        return response.status_code == 200
    except:
        return False

def increment_url(url):
    match = re.search(r'(\d+)$', url)
    if match:
        num = int(match.group(1))
        new_url = url[:match.start(1)] + str(num + 1)
        return new_url
    return url + "1"

def update_version(gradle_file):
    with open(gradle_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    version_pattern = r'version\s*=\s*"([0-9]+\.[0-9]+\.[0-9]+)"'
    match = re.search(version_pattern, content)
    if match:
        current_version = match.group(1)
        version_parts = current_version.split('.')
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        new_version = '.'.join(version_parts)
        new_content = re.sub(version_pattern, f'version = "{new_version}"', content)
        
        with open(gradle_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def update_kt_file(file_path, old_url, new_url):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    updated_content = content.replace(f'mainUrl = "{old_url}"', f'mainUrl = "{new_url}"')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

def commit_and_push(repo_path, files_changed):
    try:
        repo = Repo(repo_path)
        repo.index.add(files_changed)
        repo.index.commit(f"Update mainUrl and version - {time.strftime('%Y-%m-%d %H:%M:%S')}")
        origin = repo.remote('origin')
        origin.push()
        print(f"Changes pushed successfully: {files_changed}")
    except Exception as e:
        print(f"Error during git operations: {str(e)}")

def main():
    # DizipalV2 klasörü
    dizipal_folder = 'DizipalV2'
    
    if not os.path.exists(dizipal_folder):
        print(f"Error: {dizipal_folder} folder not found")
        return
    
    modified_files = []
    
    # .kt dosyalarını recursive olarak arama
    for root, dirs, files in os.walk(dizipal_folder):
        for file in files:
            if file.endswith('.kt'):
                file_path = os.path.join(root, file)
                print(f"Checking file: {file_path}")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        url_match = re.search(r'override\s+var\s+mainUrl\s*=\s*"([^"]+)"', content)
                        
                        if url_match:
                            current_url = url_match.group(1)
                            print(f"Found URL: {current_url}")
                            working_url = None
                            
                            # Normal kontrol
                            if not check_url(current_url):
                                print("URL not working, trying with proxy...")
                                
                                # Proxy ile kontrol
                                if not check_url(current_url, use_proxy=True):
                                    print("URL not working with proxy, trying increment...")
                                    
                                    # URL'yi artırarak kontrol
                                    test_url = increment_url(current_url)
                                    if check_url(test_url):
                                        working_url = test_url
                                        print(f"Found working URL: {working_url}")
                            
                            if working_url:
                                # Kotlin dosyasını güncelle
                                update_kt_file(file_path, current_url, working_url)
                                modified_files.append(file_path)
                                
                                # build.gradle.kts dosyasını güncelle
                                gradle_file = os.path.join(dizipal_folder, 'build.gradle.kts')
                                if os.path.exists(gradle_file):
                                    if update_version(gradle_file):
                                        modified_files.append(gradle_file)
                
                except Exception as e:
                    print(f"Error processing file {file_path}: {str(e)}")
    
    # Değişiklik varsa commit ve push yap
    if modified_files:
        commit_and_push('.', modified_files)
        print("All changes committed and pushed successfully")
    else:
        print("No changes needed")

if __name__ == "__main__":
    main()