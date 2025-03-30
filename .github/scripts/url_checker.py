import os
import re
import requests
import subprocess
from pathlib import Path

def find_file(start_dir, target_file):
    """Belirtilen klasör içinde hedef dosyayı arar ve tam yolunu döndürür."""
    print(f"'{start_dir}' içinde '{target_file}' dosyası aranıyor...")
    
    for root, dirs, files in os.walk(start_dir):
        if target_file in files:
            full_path = os.path.join(root, target_file)
            print(f"Dosya bulundu: {full_path}")
            return full_path
    
    print(f"'{target_file}' dosyası bulunamadı!")
    return None

def check_url_accessibility(url):
    """URL'nin erişilebilir olup olmadığını kontrol eder."""
    print(f"URL kontrol ediliyor: {url}")
    try:
        response = requests.head(url, timeout=10)
        status = response.status_code < 400
        print(f"URL durumu: {'Erişilebilir' if status else 'Erişilemez'} ({response.status_code})")
        return status
    except requests.RequestException as e:
        print(f"URL erişim hatası: {e}")
        return False

def extract_dizipal_number(url):
    """URL'deki Dizipal sayısını çıkarır."""
    match = re.search(r'https://dizipal(\d+)\.com', url)
    if match:
        return int(match.group(1))
    return None

def increment_url_number(url):
    """URL'deki son sayıyı bir artırır."""
    num = extract_dizipal_number(url)
    if num is not None:
        new_url = f"https://dizipal{num+1}.com"
        print(f"URL güncellendi: {url} -> {new_url}")
        return new_url
    
    print(f"URL formatı tanınmadı, artırılamadı: {url}")
    return url

def extract_main_url_from_file(file_path):
    """DizipalV2.kt dosyasından mainUrl değişkenini çıkarır."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # override var mainUrl = "https://dizipal910.com" şeklindeki deseni ara
        pattern = r'override\s+var\s+mainUrl\s*=\s*"(https://dizipal\d+\.com)"'
        match = re.search(pattern, content)
        
        if match:
            url = match.group(1)
            print(f"Dosyadan çıkarılan mainUrl: {url}")
            return url, content
        
        print("mainUrl değişkeni bulunamadı!")
        return None, content
    except Exception as e:
        print(f"Dosya okuma hatası: {e}")
        return None, ""

def update_main_url_in_file(file_path, old_url, new_url, content=None):
    """DizipalV2.kt dosyasındaki mainUrl değişkenini günceller."""
    print(f"mainUrl güncelleniyor: {old_url} -> {new_url}")
    
    try:
        if content is None:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
        
        # Tam olarak mainUrl tanımını güncelle
        pattern = f'(override\\s+var\\s+mainUrl\\s*=\\s*")({old_url})(")'
        updated_content = re.sub(pattern, f'\\1{new_url}\\3', content)
        
        # Değişiklik olup olmadığını kontrol et
        if updated_content == content:
            print("Dosyada herhangi bir değişiklik yapılmadı, eski ve yeni URL aynı olabilir.")
            return False
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        print("mainUrl başarıyla güncellendi.")
        return True
        
    except Exception as e:
        print(f"Dosya güncelleme hatası: {e}")
        return False

def update_version(file_path):
    """build.gradle.kts dosyasındaki versionCode değerini bir artırır."""
    print(f"Versiyon güncelleniyor: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # versionCode alanını bul ve güncelle
        version_pattern = r'(versionCode\s*=\s*)(\d+)'
        match = re.search(version_pattern, content)
        
        if match:
            current_version = int(match.group(2))
            new_version = current_version + 1
            print(f"Mevcut versiyon: {current_version}, Yeni versiyon: {new_version}")
            
            updated_content = re.sub(version_pattern, f'\\1{new_version}', content)
            
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
            
            print("Versiyon başarıyla güncellendi.")
            return True, new_version
        
        print("versionCode alanı bulunamadı!")
        return False, None
        
    except Exception as e:
        print(f"Versiyon güncelleme hatası: {e}")
        return False, None

def commit_and_push(file_paths, commit_message):
    """Değişiklikleri commit ve push yapar."""
    print(f"Git işlemleri başlatılıyor:")
    print(f"Dosyalar: {file_paths}")
    print(f"Commit mesajı: {commit_message}")
    
    try:
        subprocess.run(['git', 'add'] + file_paths, check=True)
        print("Git add başarılı")
        
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        print("Git commit başarılı")
        
        subprocess.run(['git', 'push'], check=True)
        print("Git push başarılı")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Git işlemi sırasında hata oluştu: {e}")
        return False

def main():
    print("==== DizipalV2 URL ve Versiyon Güncelleyici ====")
    repo_root = os.getenv('GITHUB_WORKSPACE', '.')
    print(f"Repo kök dizini: {repo_root}")
    
    # DizipalV2.kt ve build.gradle.kts dosyalarını bul
    dizipal_file_path = find_file(repo_root, 'DizipalV2.kt')
    if not dizipal_file_path:
        print("DizipalV2.kt dosyası bulunamadı!")
        return 1
    
    build_gradle_path = find_file(repo_root, 'build.gradle.kts')
    if not build_gradle_path:
        print("build.gradle.kts dosyası bulunamadı!")
        return 1
    
    # DizipalV2.kt dosyasından mevcut URL'yi çıkar
    current_url, file_content = extract_main_url_from_file(dizipal_file_path)
    if not current_url:
        print("mainUrl değişkeni bulunamadı!")
        return 1
    
    # URL'nin erişilebilirliğini kontrol et
    if check_url_accessibility(current_url):
        print(f"Mevcut URL ({current_url}) erişilebilir. Değişiklik yapmaya gerek yok.")
        return 0
    
    # Erişilebilir bir URL bulana kadar denemeye devam et
    working_url = current_url
    for _ in range(20):  # Maksimum 20 deneme
        working_url = increment_url_number(working_url)
        print(f"Yeni URL deneniyor: {working_url}")
        
        if check_url_accessibility(working_url):
            print(f"Çalışan URL bulundu: {working_url}")
            break
    else:
        print("Erişilebilir bir URL bulunamadı!")
        return 1
    
    # DizipalV2.kt dosyasını güncelle
    url_updated = update_main_url_in_file(dizipal_file_path, current_url, working_url, file_content)
    
    # Eğer URL güncellemesi yapıldıysa, versiyonu da güncelle
    version_updated = False
    new_version = None
    
    if url_updated:
        version_updated, new_version = update_version(build_gradle_path)
    else:
        print("URL değişmedi, versiyon güncellenmeyecek.")
    
    # Değişiklikleri commit ve push yap
    if url_updated or version_updated:
        updated_files = []
        commit_message_parts = []
        
        if url_updated:
            updated_files.append(dizipal_file_path)
            commit_message_parts.append(f"URL güncellendi: {current_url} -> {working_url}")
        
        if version_updated:
            updated_files.append(build_gradle_path)
            commit_message_parts.append(f"Version güncellendi: {new_version}")
        
        commit_message = ". ".join(commit_message_parts)
        
        if updated_files:
            if commit_and_push(updated_files, commit_message):
                print("Değişiklikler commit ve push edildi.")
            else:
                print("Git işlemi başarısız!")
    else:
        print("Herhangi bir değişiklik yapılmadı.")
    
    return 0

if __name__ == "__main__":
    exit(main())
