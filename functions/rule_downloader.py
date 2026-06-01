import re
import urllib.request

def download_rules(target_folder="documents"):
    print("Scaricamento delle regole di Magic: The Gathering...")

    # Scarica la pagina delle regole
    html = urllib.request.urlopen("https://magic.wizards.com/en/rules").read().decode("utf-8")
    
    # Trova il link al TXT
    url = re.search(r'https://media\.wizards\.com/\d+/downloads/MagicCompRules[\w% ]+\.txt', html).group(0)
    url = url.replace(" ", "%20")

    print(f"URL trovato: {url}")

    # Scarica il file
    filename = url.split("/")[-1].replace("%20", "_")
    file_path = f"{target_folder}/{filename}"
    urllib.request.urlretrieve(url, file_path)
    
    print(f"Scaricato: {filename}")
    return file_path
