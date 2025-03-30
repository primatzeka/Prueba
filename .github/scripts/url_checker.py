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

def increment_url_number(url):
    """URL'deki son sayıyı bir artırır."""
    match = re.search(r'(https://dizipal)(\d+)(\.com)', url)
    if match:
        prefix, number, suffix = match.groups()
        new_number = int(number) + 1
        new_url = f"{prefix}{new_number}{suffix}"
        print(f"URL güncellendi: {url} -> {new_url}")
        return new_url
    
    print(f"URL formatı tanınmadı, artırılamadı: {url}")
    return url

def update_file_url(file_path, old_url, new_url):
    """Dosyadaki URL'yi günceller ve başarılı olursa True döndürür."""
    print(f"'{file_path}' dosyasında URL güncelleniyor: {old_url} -> {new_url}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Dosya içeriğini kontrol etmek için bir kısmını yazdır
        print(f"Dosya içeriği (ilk 200 karakter): {content[:200]}...")
        
        # URL'nin gerçekten dosyada olup olmadığını kontrol et
        if old_url not in content:
            print(f"UYARI: '{old_url}' URL'si dosyada bulunamadı!")
            
            # Alternatif olarak, daha esnek bir URL deseni aralığı
            url_pattern = r'(https://dizipal\d+\.com)'
            url_matches = re.findall(url_pattern, content)
            if url_matches:
                print(f"Dosyada bulunan URL'ler: {url_matches}")
                
                # İlk bulunan URL'yi kullan
                first_url = url_matches[0]
                print(f"Mevcut URL ({first_url}) yeni URL ({new_url}) ile değiştiriliyor...")
                updated_content = content.replace(first_url, new_url)
            else:
                print("Dosyada hiçbir dizipal URL'si bulunamadı!")
                return False
        else:
            updated_content = content.replace(old_url, new_url)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        # Güncelleme gerçekleşti mi kontrol et
        is_updated = content != updated_content
        print(f"Dosya güncellendi mi: {'Evet' if is_updated else 'Hayır'}")
        return is_updated
        
    except Exception as e:
        print(f"Dosya güncellenirken hata oluştu: {e}")
        return False

def update_version(version_file_path):
    """build.gradle.kts dosyasındaki version değerini bir artırır."""
    print(f"Versiyon güncelleniyor: {version_file_path}")
    
    try:
        with open(version_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Dosya içeriğini kontrol etmek için bir kısmını yazdır
        print(f"Dosya içeriği (ilk 200 karakter): {content[:200]}...")
        
        # 'version = "X"' veya 'version = X' şeklindeki tüm desenleri kontrol et
        version_patterns = [
            r'version\s*=\s*"(\d+)"',
            r'version\s*=\s*(\d+)',
            r'versionCode\s*=\s*(\d+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, content)
            if match:
                current_version = int(match.group(1))
                new_version = current_version + 1
                print(f"Versiyon bulundu: {current_version} -> {new_version}")
                
                # Desene göre değiştirme şeklini belirle
                if '"' in pattern:
                    replace_pattern = re.sub(r'\(\\\d\+\)', f'"{current_version}"', pattern)
                    replacement = re.sub(r'"\d+"', f'"{new_version}"', match.group(0))
                else:
                    replace_pattern = re.sub(r'\(\\\d\+\)', f'{current_version}', pattern)
                    replacement = re.sub(r'\d+', f'{new_version}', match.group(0))
                
                updated_content = content.replace(match.group(0), replacement)
                
                with open(version_file_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)
                
                return True, new_version
        
        print("Versiyon deseni bulunamadı!")
        return False, None
        
    except Exception as e:
        print(f"Versiyon güncellenirken hata oluştu: {e}")
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
    
    # DizipalV2 klasörünü bul
    dizipal_dir = os.path.join(repo_root, 'DizipalV2')
    if not os.path.exists(dizipal_dir):
        print(f"DizipalV2 dizini bulunamadı: {dizipal_dir}")
        # Tüm klasörü listele
        print("Mevcut dizinler:")
        for item in os.listdir(repo_root):
            print(f"- {item}")
        dizipal_dir = repo_root  # Eğer DizipalV2 klasörü yoksa, kök dizinden başla
    
    # DizipalV2.kt dosyasını bul
    dizipal_file_path = find_file(dizipal_dir, 'DizipalV2.kt')
    if not dizipal_file_path:
        print("DizipalV2.kt dosyası bulunamadı! Tüm .kt dosyaları listeleniyor:")
        for root, dirs, files in os.walk(dizipal_dir):
            for file in files:
                if file.endswith('.kt'):
                    print(f"- {os.path.join(root, file)}")
        return 1
    
    # build.gradle.kts dosyasını bul
    build_gradle_path = find_file(dizipal_dir, 'build.gradle.kts')
    if not build_gradle_path:
        print("build.gradle.kts dosyası bulunamadı!")
        return 1
    
    # DizipalV2.kt dosyasındaki URL'yi bul
    try:
        with open(dizipal_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Daha geniş URL deseni kullan
        url_pattern = r'(https://dizipal\d+\.com)'
        url_match = re.search(url_pattern, content)
        
        if not url_match:
            print("Hata: URL deseni bulunamadı! Dosya içeriği kontrol ediliyor...")
            print(f"Dosya içeriği (ilk 500 karakter): {content[:500]}...")
            
            # mainUrl değişkenini ara
            main_url_pattern = r'mainUrl\s*=\s*"([^"]+)"'
            main_url_match = re.search(main_url_pattern, content)
            
            if main_url_match:
                current_url = main_url_match.group(1)
                print(f"mainUrl değişkeni bulundu: {current_url}")
                
                # Dizipal URL'si mi kontrol et
                if 'dizipal' in current_url.lower():
                    print(f"Geçerli Dizipal URL'si bulundu: {current_url}")
                else:
                    print(f"Bulunan URL Dizipal URL'si değil: {current_url}")
                    return 1
            else:
                print("mainUrl değişkeni bulunamadı!")
                return 1
        else:
            current_url = url_match.group(1)
            print(f"Mevcut URL: {current_url}")
    
    except Exception as e:
        print(f"Dosya okuma hatası: {e}")
        return 1
    
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
        
        if updated_files:
            commit_and_push(updated_files, commit_message.strip())
            print("Değişiklikler commit ve push edildi.")
    else:
        print("Herhangi bir değişiklik yapılmadı.")
    
    return 0

if __name__ == "__main__":
    exit(main())
