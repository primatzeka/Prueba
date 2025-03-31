import os import re import requests import time from git import Repo

def check_website(url): headers = { "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36", } try: response = requests.get(url, headers=headers, timeout=10) return response.status_code == 200 except requests.RequestException: return False

def update_dizipal_url(file_path): with open(file_path, "r", encoding="utf-8") as f: content = f.read()

match = re.search(r'override var mainUrl = "(https://dizipal\d+\.com)"', content)
if not match:
    print("mainUrl bulunamadı.")
    return None

current_url = match.group(1)
base_url = "https://dizipal"
domain_number = int(re.search(r'\d+', current_url).group())

new_url = current_url
while not check_website(new_url):
    domain_number += 1
    new_url = f"{base_url}{domain_number}.com"
    print(f"Deniyor: {new_url}")
    time.sleep(3)  # Cloudflare önlemi için bekleme süresi

if new_url == current_url:
    print("Değişiklik gerekmiyor.")
    return None

new_content = re.sub(r'override var mainUrl = ".*?"', f'override var mainUrl = "{new_url}"', content)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print(f"Güncellendi: {new_url}")
return new_url

def update_version(file_path): with open(file_path, "r", encoding="utf-8") as f: content = f.read()

match = re.search(r'version\s*=\s*(\d+)', content)
if not match:
    print("Version bilgisi bulunamadı.")
    return

new_version = int(match.group(1)) + 1
new_content = re.sub(r'version\s*=\s*\d+', f'version = {new_version}', content)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)
print(f"Version güncellendi: {new_version}")

def git_commit_and_push(repo_path, files, message): repo = Repo(repo_path) repo.index.add(files) repo.index.commit(message) origin = repo.remote(name='origin') origin.push() print("Değişiklikler GitHub'a gönderildi.")

repo_path = os.getcwd() kotlin_file = os.path.join(repo_path, "src/main/kotlin/com/Prueba/DizipalV2.kt") gradle_file = os.path.join(repo_path, "build.gradle.kts")

new_url = update_dizipal_url(kotlin_file) if new_url: update_version(gradle_file) git_commit_and_push(repo_path, [kotlin_file, gradle_file], f"URL güncellendi: {new_url}")

