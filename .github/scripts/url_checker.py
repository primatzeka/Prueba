import os
import re
import requests
import subprocess
from pathlib import Path
import random
import time
from cloudscraper import CloudScraper

oturum = CloudScraper()

# Yaygın kullanılan tarayıcı User-Agent örnekleri
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

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

def check_url_accessibility(url, max_retries=3):
    """URL'nin erişilebilir olup olmadığını kontrol eder, bot korumasını atlatmaya çalışır."""
    print(f"URL kontrol ediliyor: {url}")
    
    for attempt in range(max_retries):
        try:
            # Rastgele User-Agent seç
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "tr,en-US;q=0.7,en;q=0.3",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Cache-Control": "max-age=0"
            }
            
            # İsteği gönderirken yönlendirmeleri takip etme ve gerçek bir tarayıcı gibi görün
            response = requests.get(
                url, 
                timeout=15, 
                allow_redirects=False, 
                headers=headers
            )
            
            # 200-299 arası kodlar başarılı kabul edilir
            status = 200 <= response.status_code < 300
            
            # Yönlendirme kontrolü
            if 300 <= response.status_code < 400:
                print(f"Dikkat: URL ({response.status_code}) yönlendirme yapıyor! Bu URL doğrudan erişilebilir değil.")
                return False
                
            print(f"URL durumu: {'Erişilebilir' if status else 'Erişilemez'} ({response.status_code})")
            return status
            
        except requests.RequestException as e:
            print(f"URL erişim hatası (Deneme {attempt+1}/{max_retries}): {e}")
            # Son deneme değilse biraz bekle ve tekrar dene
            if attempt < max_retries - 1:
                sleep_time = random.uniform(2, 5)  # 2-5 saniye arası rastgele bekle
                print(f"{sleep_time:.1f} saniye bekleniyor...")
                time.sleep(sleep_time)
    
    print(f"URL erişilemez: Maksimum deneme sayısına ulaşıldı ({max_retries})")
    return False

def check_url_with_selenium(url):
    """Selenium kullanarak URL'nin erişilebilir olup olmadığını kontrol eder.
    Not: Bu fonksiyon kullanılmak istenirse, selenium kütüphanesi ve ilgili webdriver yüklenmelidir."""
    print(f"Selenium ile URL kontrol ediliyor: {url}")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        # Selenium ayarları
        options = Options()
        options.add_argument("--headless")  # Görünmez modda çalıştır
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        
        # ChromeDriver'ı başlat
        driver = webdriver.Chrome(options=options)
        
        # Sayfayı yükle
        driver.get(url)
        
        # Sayfa yüklendikten sonra URL kontrolü yap
        current_url = driver.current_url
        
        # Yönlendirme kontrolü
        redirected = current_url != url
        if redirected:
            print(f"Dikkat: URL yönlendirme yapıyor! {url} -> {current_url}")
            driver.quit()
            return False
            
        # Temel HTML içeriğine bakarak sayfanın doğru yüklenip yüklenmediğini kontrol et
        page_source = driver.page_source
        loaded_successfully = len(page_source) > 500 and "404" not in driver.title.lower()
        
        driver.quit()
        
        print(f"URL durumu: {'Erişilebilir' if loaded_successfully else 'Erişilemez'}")
        return loaded_successfully
        
    except Exception as e:
        print(f"Selenium ile URL kontrol hatası: {e}")
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
    # İlk önce standart yöntemle dene
    is_accessible = check_url_accessibility(current_url)
    
    # Eğer normal yöntem çalışmazsa ve selenium yüklenmiş ise onunla da deneyebiliriz
    # try:
    #    if not is_accessible:
    #        print("Standart yöntem başarısız, Selenium ile deneniyor...")
    #        is_accessible = check_url_with_selenium(current_url)
    # except ImportError:
    #    print("Selenium yüklü değil, standart yöntemle devam ediliyor.")
    
    if is_accessible:
        print(f"Mevcut URL ({current_url}) erişilebilir. Değişiklik yapmaya gerek yok.")
        return 0
    
    # Erişilebilir bir URL bulana kadar denemeye devam et
    working_url = current_url
    for _ in range(20):  # Maksimum 20 deneme
        working_url = increment_url_number(working_url)
        print(f"Yeni URL deneniyor: {working_url}")
        
        # Önce standart yöntemle dene
        is_accessible = check_url_accessibility(working_url)
        
        # Eğer normal yöntem çalışmazsa ve selenium yüklenmiş ise onunla da deneyebiliriz
        # try:
        #    if not is_accessible:
        #        print("Standart yöntem başarısız, Selenium ile deneniyor...")
        #        is_accessible = check_url_with_selenium(working_url)
        # except ImportError:
        #    pass
        
        if is_accessible:
            print(f"Çalışan URL bulundu: {working_url}")
            break
        
        # Denemeler arasında rastgele bir süre bekle (rate limiting'i önlemek için)
        sleep_time = random.uniform(1, 3)
        print(f"{sleep_time:.1f} saniye bekleniyor...")
        time.sleep(sleep_time)
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

