import os
import re
import requests
import subprocess
from pathlib import Path
import argparse
import logging

# Logging ayarları
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def check_url(url):
    """URL'nin erişilebilir olup olmadığını kontrol eder."""
    try:
        response = requests.head(url, timeout=10)
        if response.status_code < 400:
            logger.info(f"URL erişilebilir: {url} - Durum Kodu: {response.status_code}")
            return True
        else:
            logger.warning(f"URL erişilebilir değil: {url} - Durum Kodu: {response.status_code}")
            return False
    except requests.RequestException as e:
        logger.warning(f"URL kontrolü başarısız: {url} - Hata: {e}")
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

def git_commit_push(file_path, new_url):
    """Değişiklikleri commit'ler ve push'lar."""
    try:
        # Dosyayı git'e ekle
        subprocess.run(["git", "add", file_path], check=True)
        
        # Commit oluştur
        commit_message = f"URL güncellendi: {new_url}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push yap
        subprocess.run(["git", "push"], check=True)
        
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
    
    args = parser.parse_args()
    
    # Dosyayı bul
    file_path = find_file_in_directory(args.dir, args.file)
    if not file_path:
        return
    
    # Mevcut URL'yi çıkar
    current_url = extract_url(file_path)
    if not current_url:
        return
    
    # URL'yi kontrol et
    if check_url(current_url):
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
        
        if check_url(next_url):
            working_url = next_url
            logger.info(f"Çalışan URL bulundu: {working_url}")
            break
    
    if not working_url:
        logger.error(f"{args.max_attempts} deneme sonrasında çalışan URL bulunamadı!")
        return
    
    # Dosyayı güncelle
    if update_file_url(file_path, current_url, working_url):
        # Git işlemlerini yap
        git_commit_push(file_path, working_url)

if __name__ == "__main__":
    main()

