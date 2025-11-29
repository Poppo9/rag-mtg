import requests
from difflib import get_close_matches

def find_exact_name(input_name: str) -> str:
    url = "https://api.scryfall.com/catalog/card-names"
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f"Error in API call: {response.status_code}")

    # Get the list of card names
    card_names = response.json().get("data", [])

    # Find the closest name using difflib
    match = get_close_matches(input_name, card_names, n=1, cutoff=0.6)

    if match:
        print(match)
        return match[0]  # Standardized name (Oracle)
    else:
        print("no match")
        return None  # No match found
    

def get_card_info(card_name: str) -> dict:
    """
    Retrieves card information from Scryfall using its name.
    Returns the full JSON response.
    """
    base_url = "https://api.scryfall.com/cards/named"
    params = {"exact": card_name}  

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error in API call: {e}")
        return None

def distill_card_info(card_data):
    """
    Reduce the size of the dictionary. 
    """
    return {
        "name": card_data.get("name"),
        "mana_cost": card_data.get("mana_cost"),
        "type_line": card_data.get("type_line"),
        "oracle_text": card_data.get("oracle_text"),
        "colors": card_data.get("colors"),
        "color_identity": card_data.get("color_identity"),
        #"legalities": card_data.get("legalities"),
        "rarity": card_data.get("rarity"),
        "rulings_uri": card_data.get("rulings_uri")
    }

def get_rulings (rulings_uri: str) -> dict:
    """
    Retrieves card information from Scryfall using its name.
    Returns the full JSON response.
    """
    try:
        response = requests.get(rulings_uri, timeout=10)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error in API call: {e}")
        return None