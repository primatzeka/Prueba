import os
import re
import requests
import time
import random
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_session():
    """Create a requests session with headers that mimic a real browser"""
    session = requests.Session()
    
    # Configure retries with backoff
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Randomize user agent to avoid detection
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0',
        'TE': 'Trailers',
    }
    
    session.headers.update(headers)
    return session

def check_url(url, session):
    """Check if URL is accessible"""
    try:
        # Add a random delay to appear more human-like
        time.sleep(random.uniform(1, 3))
        
        response = session.get(url, timeout=10)
        
        # Handle Cloudflare challenges
        if response.status_code == 403 and "cloudflare" in response.text.lower():
            print(f"Cloudflare detected for {url}, cannot proceed automatically")
            return False
            
        # Check for common indicators of a working page
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Check if content exists (not just an error page)
            if soup.title and not any(err in soup.title.text.lower() for err in ['404', 'error', 'not found']):
                return True
                
        return False
        
    except Exception as e:
        print(f"Error checking {url}: {str(e)}")
        return False

def extract_current_url(kt_file_path):
    """Extract the current mainUrl from DizipalV2.kt"""
    with open(kt_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        
    match = re.search(r'override\s+var\s+mainUrl\s*=\s*"(https://dizipal\d+\.com)"', content)
    if match:
        return match.group(1)
    return None

def increment_url(url):
    """Increment the numeric part of the Dizipal URL"""
    match = re.search(r'(https://dizipal)(\d+)(\.com)', url)
    if match:
        prefix = match.group(1)
        number = int(match.group(2))
        suffix = match.group(3)
        return f"{prefix}{number+1}{suffix}"
    return url

def update_kt_file(kt_file_path, new_url):
    """Update the mainUrl in DizipalV2.kt file"""
    with open(kt_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    updated_content = re.sub(
        r'(override\s+var\s+mainUrl\s*=\s*")https://dizipal\d+\.com(")', 
        r'\1' + new_url + r'\2', 
        content
    )
    
    with open(kt_file_path, 'w', encoding='utf-8') as file:
        file.write(updated_content)
    
    return True

def update_gradle_version(gradle_file_path):
    """Increment the version in build.gradle.kts file"""
    with open(gradle_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    match = re.search(r'version\s*=\s*(\d+)', content)
    if match:
        current_version = int(match.group(1))
        new_version = current_version + 1
        
        updated_content = re.sub(
            r'(version\s*=\s*)(\d+)', 
            r'\1' + str(new_version), 
            content
        )
        
        with open(gradle_file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
            
        return True
    
    return False

def main():
    # File paths
    kt_file_path = 'src/main/kotlin/com/Prueba/DizipalV2.kt'
    gradle_file_path = 'build.gradle.kts'
    
    # Create session with anti-bot measures
    session = create_session()
    
    # Get current URL
    current_url = extract_current_url(kt_file_path)
    if not current_url:
        print("Could not find mainUrl in DizipalV2.kt")
        return
    
    print(f"Current URL: {current_url}")
    
    # Check if current URL works
    if check_url(current_url, session):
        print(f"Current URL {current_url} is accessible, no changes needed")
        return
    
    # Find a working URL
    new_url = current_url
    max_attempts = 10
    for _ in range(max_attempts):
        new_url = increment_url(new_url)
        print(f"Trying URL: {new_url}")
        
        if check_url(new_url, session):
            print(f"Found working URL: {new_url}")
            
            # Update DizipalV2.kt
            kt_updated = update_kt_file(kt_file_path, new_url)
            
            # Update build.gradle.kts
            gradle_updated = update_gradle_version(gradle_file_path)
            
            if kt_updated and gradle_updated:
                print("Files updated successfully")
                # Set GitHub output for the action
                if 'GITHUB_OUTPUT' in os.environ:
                    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                        f.write(f"url_updated=true\n")
                        f.write(f"new_url={new_url}\n")
            return
    
    print(f"Could not find a working URL after {max_attempts} attempts")

if __name__ == "__main__":
    main()
