import requests
import re
import os
from urllib.parse import urlparse
import time
import random

def get_cloudflare_session():
    session = requests.Session()
    session.headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    return session

def check_url(url):
    session = get_cloudflare_session()
    try:
        time.sleep(random.uniform(2, 5))  # Random delay
        response = session.get(url, timeout=15)
        return response.status_code == 200
    except:
        return False

def increment_url(url):
    parsed = urlparse(url)
    base = parsed.netloc.rstrip('0123456789')
    current_number = int(re.search(r'\d+', parsed.netloc).group())
    new_number = current_number + 1
    new_url = f"https://{base}{new_number}.com"
    return new_url

def update_files(kt_file_path, gradle_file_path):
    # Read DizipalV2.kt
    with open(kt_file_path, 'r', encoding='utf-8') as f:
        kt_content = f.read()

    # Extract current URL
    url_match = re.search(r'override var mainUrl = "(https://dizipal\d+\.com)"', kt_content)
    if not url_match:
        raise Exception("URL pattern not found in DizipalV2.kt")

    current_url = url_match.group(1)
    new_url = current_url

    # Check current URL
    while not check_url(new_url):
        new_url = increment_url(new_url)
        if int(re.search(r'\d+', urlparse(new_url).netloc).group()) - int(re.search(r'\d+', urlparse(current_url).netloc).group()) > 10:
            raise Exception("Failed to find working URL after 10 attempts")

    # Update files if URL changed
    if new_url != current_url:
        # Update DizipalV2.kt
        new_kt_content = kt_content.replace(current_url, new_url)
        with open(kt_file_path, 'w', encoding='utf-8') as f:
            f.write(new_kt_content)

        # Update build.gradle.kts
        with open(gradle_file_path, 'r', encoding='utf-8') as f:
            gradle_content = f.read()

        version_match = re.search(r'version = (\d+)', gradle_content)
        if version_match:
            current_version = int(version_match.group(1))
            new_version = current_version + 1
            new_gradle_content = gradle_content.replace(
                f'version = {current_version}',
                f'version = {new_version}'
            )
            with open(gradle_file_path, 'w', encoding='utf-8') as f:
                f.write(new_gradle_content)

        return True
    return False

if __name__ == "__main__":
    kt_path = "DizipalV2/src/main/kotlin/com/Prueba/DizipalV2.kt"
    gradle_path = "build.gradle.kts"
    
    if update_files(kt_path, gradle_path):
        print("Files updated successfully")
        # Git commands will be handled by GitHub Actions
    else:
        print("No updates needed")