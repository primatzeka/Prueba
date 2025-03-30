import os
import re
import requests
import subprocess
from pathlib import Path

def find_file(start_dir, target_file):
    """Belirtilen klasör içinde hedef dosyayı arar."""
    for root, dirs, files in os.walk(start_dir):
        if target_file in files:
            return os.path.join(root, target_file)
    return None

def check_url_accessibility(url):
    """URL'nin erişilebilir olup olmadığını kontrol eder."""
    try:
        response = requests.head(url, timeout=10)
        return response.status_code < 400
    except requests.RequestException:
        return False

def increment_url_number(url):
    """URL'deki son sayıyı bir artırır."""
    match = re.search(r'(\D+)(\d+)(\.\w+)$', url)
    if match:
        prefix, number, suffix = match.groups()
        new_number = int(number) + 1
        return f"{prefix}{new_number}{suffix}"
    return url

def update_file_url(file_path, old_url, new_url):
    """Dosyadaki URL'yi günceller."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    updated_content = content.replace(old_url, new_url)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    return updated_content != content

def update_version(version_file_path):
    """build.gradle.kts dosyasındaki version değerini bir artırır."""
    with open(version_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 'version = X' şeklindeki değeri bul ve bir artır
    version_pattern = r'version\s*=\s*(\d+)'
    match = re.search(version_pattern, content)
    
    if match:
        current_version = int(match.group(1))
        new_version = current_version + 1
        updated_content = re.sub(version_pattern, f'version = {new_version}', content)
        
        with open(version_file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        return True, new_version
    
    return False, None

def commit_and_push(file_paths, commit_message):
    """Değişiklikleri commit ve push yapar."""
    subprocess.run(['git', 'add'] + file_paths)
    subprocess.run(['git', 'commit', '-m', commit_message])
    subprocess.run(['git', 'push'])

def main():
    repo_root = os.getenv('GITHUB_WORKSPACE', '.')
    
    # Görüntüdeki dosya yapısına göre hedef dosya yolu belirleniyor
    dizipal_file_path = os.path.join(repo_root, 'DizipalV2', 'src', 'main', 'kotlin', 'com', 'Prueba', 'DizipalV2.kt')
    
    # build.gradle.kts dosyasının tam yolu
    build_gradle_path = os.path.join(repo_root, 'DizipalV2', 'build.gradle.kts')
    
    # DizipalV2.kt dosyası doğrudan belirtilen yolda yoksa, onu arayalım
    if not os.path.exists(dizipal_file_path):
        dizipal_file_path = find_file(os.path.join(repo_root, 'DizipalV2', 'src'), 'DizipalV2.kt')
    
    if not dizipal_file_path:
        print("Hata: DizipalV2.kt dosyası bulunamadı!")
        return 1
    
    print(f"Dosya bulundu: {dizipal_file_path}")
    
    # Dosyadaki mevcut URL'yi bul
    with open(dizipal_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    url_match = re.search(r'mainUrl\s*=\s*"(https://dizipal\d+\.com)"', content)
    if not url_match:
        print("Hata: URL deseni bulunamadı!")
        return 1
    
    current_url = url_match.group(1)
    print(f"Mevcut URL: {current_url}")
    
    # URL erişilebilir mi kontrol et, erişilemiyorsa artırarak devam et
    working_url = current_url
    url_updated = False
    
    if not check_url_accessibility(working_url):
        print(f"{working_url} erişilebilir değil, alternatif aranıyor...")
        
        for _ in range(20):  # Maksimum 20 deneme
            working_url = increment_url_number(working_url)
            print(f"Deneniyor: {working_url}")
            
            if check_url_accessibility(working_url):
                print(f"Çalışan URL bulundu: {working_url}")
                url_updated = update_file_url(dizipal_file_path, current_url, working_url)
                break
        else:
            print("Erişilebilir bir URL bulunamadı!")
            return 1
    
    # Version güncellemesi
    version_updated, new_version = update_version(build_gradle_path)
    
    if url_updated or version_updated:
        updated_files = []
        commit_message = ""
        
        if url_updated:
            updated_files.append(dizipal_file_path)
            commit_message += f"URL güncellendi: {current_url} -> {working_url}. "
        
        if version_updated:
            updated_files.append(build_gradle_path)
            commit_message += f"Version güncellendi: {new_version}. "
        
        commit_and_push(updated_files, commit_message.strip())
        print("Değişiklikler commit ve push edildi.")
    else:
        print("Herhangi bir değişiklik yapılmadı.")
    
    return 0

if __name__ == "__main__":
    exit(main())
