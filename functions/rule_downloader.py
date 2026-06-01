import re
import urllib.request
from pathlib import Path

def download_rules():
    target_folder = "documents"
    if not Path(target_folder).exists():
        Path(target_folder).mkdir(exist_ok=True)

    print("Downloading Magic: The Gathering Comprehensive Rules...")

    # Download the rules page
    html = urllib.request.urlopen("https://magic.wizards.com/en/rules").read().decode("utf-8")
    
    # Find the link to the TXT file
    url = re.search(r'https://media\.wizards\.com/\d+/downloads/MagicCompRules[\w% ]+\.txt', html).group(0)
    url = url.replace(" ", "%20")

    print(f"URL found: {url}")

    # Download the file
    filename = url.split("/")[-1].replace("%20", "_")
    file_path = f"{target_folder}/{filename}"
    urllib.request.urlretrieve(url, file_path)
    
    print(f"Downloaded: {filename}")
    return file_path
