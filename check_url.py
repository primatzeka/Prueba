import requests
import re
import os
from urllib3.exceptions import InsecureRequestWarning
import yaml
from git import Repo

# SSL uyarılarını devre dışı bırak
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def load_config():
    with open('config.yaml', 'r') as file:
        return yaml.safe_load(file)

def get_url_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        url_match = re.search(r'mainUrl\s*=\s*"(https?://[^"]+)"', content)
        return url_match.group(1) if url_match else None

def update_file_content(file_path, old_url, new_url):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    updated_content = content.replace(old_url, new_url)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)

def update_version(gradle_path):
    with open(gradle_path, 'r', encoding='utf-8') as file:
        content = file.read()
        
    version_match = re.search(r'version\s*=\s*(\d+)', content)
    if version_match:
        current_version = int(version_match.group(1))
        new_version = current_version + 1
        updated_content = re.sub(
            r'version\s*=\s*\d+',
            f'version = {new_version}',
            content
        )
        
        with open(gradle_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)

def check_url(url, headers):
    try:
        # Yönlendirmeleri takip etme
        response = requests.get(
            url,
            headers=headers,
            allow_redirects=False,
            verify=False,
            timeout=10
        )
        
        # Direkt erişilebilir durumda
        if response.status_code == 200:
            return True, None
        
        # Yönlendirme varsa
        if response.status_code in [301, 302, 307, 308]:
            return False, response.headers.get('Location')
            
        return False, None
    
    except requests.exceptions.RequestException:
        return False, None

def increment_url(url):
    pattern = r'(\d+)'
    match = re.search(pattern, url)
    if match:
        current_number = int(match.group(1))
        new_number = current_number + 1
        return re.sub(pattern, str(new_number), url, 1)
    return None

def main():
    config = load_config()
    repo_path = config['repo_path']
    dizipal_path = os.path.join(repo_path, config['dizipal_path'])
    gradle_path = os.path.join(repo_path, config['gradle_path'])
    
    headers = {
        'User-Agent': config['user_agent'],
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

    current_url = get_url_from_file(dizipal_path)
    if not current_url:
        print("URL bulunamadı!")
        return

    url_updated = False
    test_url = current_url
    
    while True:
        is_accessible, redirect_url = check_url(test_url, headers)
        
        if is_accessible and not redirect_url:
            if test_url != current_url:
                update_file_content(dizipal_path, current_url, test_url)
                url_updated = True
            break
            
        test_url = increment_url(test_url)
        if not test_url:
            print("URL artırılamıyor!")
            break

    if url_updated:
        update_version(gradle_path)
        
        # Git işlemleri
        repo = Repo(repo_path)
        repo.index.add([dizipal_path, gradle_path])
        repo.index.commit("URL ve versiyon güncellendi")
        origin = repo.remote('origin')
        origin.push()

if __name__ == "__main__":
    main()