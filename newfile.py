import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin, urlparse
from zipfile import ZipFile
import warnings
import chardet
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# تجاهل تحذيرات التحقق من الشهادات
warnings.simplefilter('ignore', InsecureRequestWarning)

def fetch_files(url, base_url, session, visited):
    try:
        response = session.get(url, verify=False)  # تجاوز التحقق من الشهادة
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching the page {url}: {e}")
        return []

    # اكتشاف الترميز واستخدامه لقراءة النصوص
    encoding = chardet.detect(response.content)['encoding']
    response_text = response.content.decode(encoding)

    soup = BeautifulSoup(response_text, 'html.parser')
    files = []

    if url not in visited:
        files.append({'url': url, 'filename': 'index.html', 'content': response_text})
        visited.add(url)

    tags = {
        'a': 'href',
        'link': 'href',
        'script': 'src',
        'img': 'src',
    }

    for tag, attr in tags.items():
        for element in soup.find_all(tag):
            href = element.get(attr)
            if href:
                full_url = urljoin(base_url, href)
                parsed_url = urlparse(full_url)
                file_name = os.path.basename(parsed_url.path)
                if not file_name or parsed_url.scheme not in ('http', 'https') or full_url in visited:
                    continue

                try:
                    file_response = session.get(full_url, verify=False)  # تجاوز التحقق من الشهادة
                    file_response.raise_for_status()
                    visited.add(full_url)
                    content_type = file_response.headers.get('Content-Type')
                    if content_type and 'text' in content_type:
                        encoding = chardet.detect(file_response.content)['encoding']
                        file_content = file_response.content.decode(encoding)
                        files.append({'url': full_url, 'filename': file_name, 'content': file_content})
                    else:
                        files.append({'url': full_url, 'filename': file_name, 'content': file_response.content})
                except requests.RequestException as e:
                    print(f"Failed to download {full_url}: {e}")

    return files

def save_files_to_zip(files, zip_filename):
    with ZipFile(zip_filename, 'w') as zipf:
        for file in files:
            if isinstance(file['content'], str):
                zipf.writestr(file['filename'], file['content'])
            else:
                zipf.writestr(file['filename'], file['content'])
    print(f"All files have been saved to {zip_filename}")

if __name__ == "__main__":
    url = input("Enter the website URL: ")
    base_url = url if url.endswith('/') else url + '/'
    session = requests.Session()
    session.verify = False  # تجاوز التحقق من الشهادة
    visited = set()
    files = fetch_files(url, base_url, session, visited)
    zip_filename = 'website_files.zip'
    save_files_to_zip(files, zip_filename)