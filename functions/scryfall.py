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
    

def get_complete_card_info(card_name: str) -> str:
    """
    Retrieves complete card information including distilled card data and rulings.
    
    Args:
        card_name: The name of the card to search for
        
    Returns:
        A formatted string containing card info and rulings, or error message
    """
    # Find the exact card name
    exact_name = find_exact_name(card_name)
    if not exact_name:
        return f"No card found matching '{card_name}'"
    
    # Get full card data
    card_data = get_card_info(exact_name)
    if not card_data:
        return f"Error retrieving card data for '{exact_name}'"
    
    # Distill card info
    distilled_info = distill_card_info(card_data)
    
    # Get rulings
    rulings_uri = distilled_info.get("rulings_uri")
    rulings_response = get_rulings(rulings_uri) if rulings_uri else None
    
    # Format output string
    output = []
    output.append(f"=== {distilled_info['name']} ===\n")
    output.append(f"Mana Cost: {distilled_info.get('mana_cost', 'N/A')}")
    output.append(f"Type: {distilled_info.get('type_line', 'N/A')}")
    output.append(f"Colors: {', '.join(distilled_info.get('colors', [])) or 'Colorless'}")
    output.append(f"Color Identity: {', '.join(distilled_info.get('color_identity', [])) or 'Colorless'}")
    output.append(f"Rarity: {distilled_info.get('rarity', 'N/A').capitalize()}")
    output.append(f"\nOracle Text:\n{distilled_info.get('oracle_text', 'N/A')}")
    
    # Add rulings if available
    output.append("\n--- RULINGS ---")
    if rulings_response and rulings_response.get("data"):
        for i, ruling in enumerate(rulings_response["data"], 1):
            output.append(f"\n{i}. [{ruling.get('published_at', 'N/A')}]")
            output.append(f"   {ruling.get('comment', 'No comment')}")
    else:
        output.append("No rulings available for this card.")
    
    return "\n".join(output)

