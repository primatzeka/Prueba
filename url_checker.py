import os
import re
import requests
import subprocess
import time
import random
from pathlib import Path
import argparse
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Farklı user agent'lar listesi
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1'
]

def find_file_in_directory(start_dir, target_file):
    """Belirtilen dizin içinde hedef dosyayı bulur."""
    logger.info(f"'{target_file}' dosyası '{start_dir}' içinde aranıyor...")
    
    for root, dirs, files in os.walk(start_dir):
        if target_file in files:
            file_path = os.path.join(root, target_file)
            logger.info(f"Dosya bulundu: {file_path}")
            return file_path
    
    logger.error(f"'{target_file}' dosyası bulunamadı!")
    return None

def extract_url(file_path):
    """Dosyadan URL'yi çıkarır."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        url_pattern = r'mainUrl\s*=\s*"(https?://dizipal\d+\.com)"'
        match = re.search(url_pattern, content)
        
        if match:
            current_url = match.group(1)
            logger.info(f"Mevcut URL: {current_url}")
            return current_url
        else:
            logger.error("URL deseni bulunamadı!")
            return None
    except Exception as e:
        logger.error(f"Dosya okuma hatası: {e}")
        return None

def check_url_with_redirects(url, max_retries=3, retry_delay=2):
    """URL'nin erişilebilir olup olmadığını kontrol eder ve yönlendirmeleri takip eder."""
    for retry in range(max_retries):
        try:
            # Rastgele bir user agent seç
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
            }
            
            # Yönlendirmeleri takip et ama final URL'yi kaydet
            response = requests.get(
                url, 
                timeout=15, 
                allow_redirects=True,
                headers=headers
            )
            
            final_url = response.url
            
            # Başarılı durum kodları veya yaygın yönlendirme/erişim kodları
            # 403 veya 503 bile olsa, site muhtemelen mevcuttur ama bizi engelliyor
            if response.status_code < 500 or response.status_code in [503]:
                # Eğer yönlendirme varsa
                if final_url != url:
                    logger.info(f"URL yönlendirme tespit edildi: {url} -> {final_url}")
                    return True, final_url
                else:
                    logger.info(f"URL erişilebilir (yönlendirme yok): {url} - Durum Kodu: {response.status_code}")
                    # 403 veya başka bir erişim engelleme kodu alırsak bile, site var kabul ediyoruz
                    if response.status_code in [403, 429, 503]:
                        logger.warning(f"URL erişim engellendi ama site mevcut: {url} - Durum Kodu: {response.status_code}")
                    return True, url
            else:
                logger.warning(f"URL erişilebilir değil: {url} - Durum Kodu: {response.status_code}")
        except requests.RequestException as e:
            # Hata durumunda tekrar dene
            logger.warning(f"URL kontrolü başarısız ({retry+1}/{max_retries}): {url} - Hata: {e}")
            # Son deneme değilse bekle
            if retry < max_retries - 1:
                sleep_time = retry_delay + random.uniform(0, 2)
                logger.info(f"{sleep_time:.2f} saniye bekleniyor...")
                time.sleep(sleep_time)
    
    # Eğer check_domain başarılı olursa, URL'yi çalışır kabul et
    if check_domain(url):
        logger.info(f"Alan adı mevcut olduğu için URL çalışır kabul ediliyor: {url}")
        return True, url
    
    return False, None

def check_domain(url):
    """Domain adının var olup olmadığını kontrol eder. 
    URL'ye erişim engellenmiş olsa bile domain var mı diye bakar."""
    try:
        import socket
        from urllib.parse import urlparse
        
        # URL'den domain adını çıkar
        domain = urlparse(url).netloc
        
        # Alan adı çözümlenebiliyor mu kontrol et
        socket.gethostbyname(domain)
        logger.info(f"Alan adı DNS çözümlemesi başarılı: {domain}")
        return True
    except Exception as e:
        logger.warning(f"Alan adı DNS çözümlemesi başarısız: {e}")
        return False

def increment_url_number(url):
    """URL'deki sayıyı artırır."""
    pattern = r'(https?://dizipal)(\d+)(\.com)'
    match = re.match(pattern, url)
    
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        
        new_number = number + 1
        new_url = f"{prefix}{new_number}{suffix}"
        logger.info(f"Yeni URL oluşturuldu: {new_url}")
        return new_url
    else:
        logger.error(f"URL formatı beklendiği gibi değil: {url}")
        return None

def update_file_url(file_path, old_url, new_url):
    """Dosyadaki URL'yi günceller."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        updated_content = content.replace(old_url, new_url)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        logger.info(f"Dosya güncellendi: {old_url} -> {new_url}")
        return True
    except Exception as e:
        logger.error(f"Dosya güncelleme hatası: {e}")
        return False

def update_version_in_gradle(gradle_file):
    """build.gradle.kts dosyasındaki versiyon numarasını artırır."""
    try:
        if not os.path.exists(gradle_file):
            logger.error(f"Gradle dosyası bulunamadı: {gradle_file}")
            return False

        with open(gradle_file, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Version değerini bul
        version_pattern = r'version\s*=\s*(\d+)'
        match = re.search(version_pattern, content)
        
        if match:
            current_version = int(match.group(1))
            new_version = current_version + 1
            logger.info(f"Versiyon güncelleniyor: {current_version} -> {new_version}")
            
            # Yeni versiyon ile içeriği güncelle
            updated_content = re.sub(version_pattern, f'version = {new_version}', content)
            
            with open(gradle_file, 'w', encoding='utf-8') as file:
                file.write(updated_content)
            
            logger.info(f"Gradle versiyon güncellendi: {new_version}")
            return True
        else:
            logger.error("Gradle dosyasında versiyon deseni bulunamadı!")
            return False
    except Exception as e:
        logger.error(f"Gradle dosyası güncelleme hatası: {e}")
        return False

def git_commit_push(file_paths, new_url, new_version):
    """Değişiklikleri commit'ler ve push'lar."""
    try:
        # Dosyaları git'e ekle
        for file_path in file_paths:
            subprocess.run(["git", "add", file_path], check=True)
        
        # Commit oluştur
        commit_message = f"URL güncellendi: {new_url}, versiyon: {new_version}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push yap
        subprocess.run(["git", "push", "origin", "master"], check=True)
        
        logger.info("Git işlemleri başarıyla tamamlandı")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git işlemi hatası: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='URL kontrol ve güncelleme aracı')
    parser.add_argument('--dir', type=str, help='Arama yapılacak dizin yolu', default='./DizipalV2')
    parser.add_argument('--file', type=str, help='Aranacak dosya adı', default='DizipalV2.kt')
    parser.add_argument('--max-attempts', type=int, help='Maksimum deneme sayısı', default=100)
    parser.add_argument('--gradle-file', type=str, help='Gradle dosyası yolu', default='./build.gradle.kts')
    parser.add_argument('--retry-delay', type=float, help='URL kontrol denemesi arasındaki minimum gecikme (saniye)', default=3.0)
    
    args = parser.parse_args()
    
    # Dosyayı bul
    file_path = find_file_in_directory(args.dir, args.file)
    if not file_path:
        return
    
    # Mevcut URL'yi çıkar
    current_url = extract_url(file_path)
    if not current_url:
        return
    
    # Rastgele gecikme ekle
    time.sleep(random.uniform(1, 3))
    
    # URL'yi kontrol et ve yönlendirmeler için izle
    is_accessible, redirect_url = check_url_with_redirects(current_url)
    
    # Eğer URL yönlendirme yapıyorsa, yönlendirilen URL'yi kullan
    if is_accessible and redirect_url != current_url:
        logger.info(f"URL yönlendirme tespit edildi ve kullanılacak: {redirect_url}")
        if update_file_url(file_path, current_url, redirect_url):
            # Gradle dosyasındaki versiyonu güncelle
            if update_version_in_gradle(args.gradle_file):
                # Yeni versiyon değerini al
                new_version = None
                with open(args.gradle_file, 'r', encoding='utf-8') as file:
                    content = file.read()
                    version_match = re.search(r'version\s*=\s*(\d+)', content)
                    if version_match:
                        new_version = version_match.group(1)
                
                # Git işlemlerini yap
                git_commit_push([file_path, args.gradle_file], redirect_url, new_version)
        return
    # Eğer mevcut URL çalışıyorsa ve yönlendirme yoksa
    elif is_accessible:
        logger.info(f"Mevcut URL çalışıyor, güncellemeye gerek yok: {current_url}")
        return
    
    # Çalışan URL'yi bul
    working_url = None
    next_url = current_url
    
    for attempt in range(args.max_attempts):
        next_url = increment_url_number(next_url)
        if not next_url:
            break
            
        logger.info(f"Deneme {attempt+1}/{args.max_attempts}: {next_url}")
        
        # Her deneme arasında rastgele gecikme ekle (bot tespitini zorlaştırmak için)
        delay = args.retry_delay + random.uniform(1, 5)
        logger.info(f"{delay:.2f} saniye bekleniyor...")
        time.sleep(delay)
        
        is_accessible, redirect_url = check_url_with_redirects(next_url)
        
        if is_accessible:
            # Eğer URL yönlendirme yapıyorsa, yönlendirilen URL'yi kullan
            if redirect_url != next_url:
                working_url = redirect_url
                logger.info(f"Yönlendirme ile çalışan URL bulundu: {next_url} -> {working_url}")
            else:
                working_url = next_url
                logger.info(f"Çalışan URL bulundu: {working_url}")
            break
    
    if not working_url:
        logger.error(f"{args.max_attempts} deneme sonrasında çalışan URL bulunamadı!")
        return
    
    # Dosyayı güncelle
    if update_file_url(file_path, current_url, working_url):
        # Gradle dosyasındaki versiyonu güncelle
        if update_version_in_gradle(args.gradle_file):
            # Yeni versiyon değerini al
            new_version = None
            with open(args.gradle_file, 'r', encoding='utf-8') as file:
                content = file.read()
                version_match = re.search(r'version\s*=\s*(\d+)', content)
                if version_match:
                    new_version = version_match.group(1)
            
            # Git işlemlerini yap
            git_commit_push([file_path, args.gradle_file], working_url, new_version)

if __name__ == "__main__":
    main()

