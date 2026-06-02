import os
import re
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from functions.scryfall import get_complete_card_info
from functions.chroma import query_chroma_index

def extract_card_names_from_query(query: str) -> list:
    
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.environ["NVIDIA_API_KEY"])
    
    system_prompt = (
        "You are an expert in Magic: The Gathering cards. "
        "Given a user query, identify all the card names mentioned and return them as a Python list. "
        "Format the response strictly as a Python list of strings."
        "Even if don't know the card but you suspect that one could be a card, treat it as such."
    )
    
    response = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
    )
    
    content = response.choices[0].message.content
    
    # Use regex to extract the Python list from the response
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        list_str = match.group(0)
        try:
            card_names = eval(list_str)
            if isinstance(card_names, list):
                return card_names
        except Exception:
            pass
    
    return []


def magic_agent(user_query: str, verbose = False) -> str:
    """
    An agent that processes a user query about Magic: The Gathering cards.
    It extracts card names, retrieves their details from Scryfall,
    queries a ChromaDB collection for additional context, and then
    constructs a comprehensive response using GPT.
    """
    if verbose:
        print("\n\n=== STEP 1: Initializing NVIDIA client ===")
        print(f"Asking question: {user_query}")
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.environ["NVIDIA_API_KEY"])

    # 1. Define the system prompt
    system_prompt = (
        "You are an expert Magic: The Gathering assistant. "
        "You help players understand cards, strategies, and game mechanics. "
        "Use the provided card details and context to give accurate and helpful answers. "
        "If you're not sure about something, say so rather than making up information."
    )
    
    # 2. Extract card names from the user query
    if verbose:
        print("\n\n=== STEP 2: Extracting card names ===")
    card_names = extract_card_names_from_query(user_query)
    if verbose:
        print(f"Extracted card names: {card_names}")

    # 3. Retrieve complete card info (including rulings) for each card
    if verbose:
        print("\n\n=== STEP 3: Retrieving card info from Scryfall ===")
    card_info_strings = []
    for card_name in card_names:
        try:
            card_info = get_complete_card_info(card_name)
            if card_info and not card_info.startswith("No card found") and not card_info.startswith("Error"):
                card_info_strings.append(card_info)
                if verbose:
                    print(f"✓ Retrieved info for: {card_name}")
            else:
                if verbose:
                    print(f"✗ Could not retrieve info for: {card_name}")
        except Exception as e:
            if verbose:
                print(f"✗ Error retrieving info on {card_name}: {e}")
    if verbose:
        print(f"Total cards retrieved: {len(card_info_strings)}/{len(card_names)}")

    # 4. Query ChromaDB for additional context
    if verbose:
        print("\n\n=== STEP 4: Querying ChromaDB ===")
    chroma_results = query_chroma_index(user_query)
    if verbose:
        print("ChromaDB query completed.")
        print(f"ChromaDB results type: {type(chroma_results)}")
    
        # 5. Build the context for the final prompt
        print("\n\n=== STEP 5: Building context ===")
    context_parts = []
    
    # Add complete card details (already formatted by get_complete_card_info)
    if card_info_strings:
        context_parts.append("=== CARD DETAILS WITH RULINGS ===\n")
        context_parts.extend(card_info_strings)
        if verbose:
            print(f"Added {len(card_info_strings)} card details to context")
    
    # Add results from ChromaDB (ora è una stringa formattata)
    if chroma_results:
        context_parts.append(chroma_results)
        if verbose:
            print("Added ChromaDB results to context")
    else:
        if verbose:
            print("No ChromaDB results to add")
    
    context = "\n".join(context_parts)

    # 6. Build the final prompt with all context
    if verbose:
        print("=== STEP 6: Building final prompt ===")
    final_user_message = f"{context}\n\n=== USER QUESTION ===\n{user_query}"
    if verbose:
        print(f"Final prompt length: {len(final_user_message)} characters")
        print(f"Final prompt preview:\n--- START OF PROMPT ---\n{final_user_message}\n\n--- END OF PROMPT ---\n")

        # 7. Call GPT with all context
        print("\n=== STEP 7: Calling GPT ===")
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_user_message}
            ],
            temperature=0.7
        )
        if verbose:
            print("✓ GPT response received successfully")
            print(f"Response length: {len(response.choices[0].message.content)} characters")
        
        return response.choices[0].message.content
        
    except Exception as e:
        if verbose:
            print(f"✗ Error calling GPT: {e}")
        return f"Error generating response: {str(e)}"


def non_rag_magic_agent(user_query: str, verbose = False) -> str:
    """
    An agent that processes a user query about Magic: The Gathering cards.
    It extracts card names, retrieves their details from Scryfall,
    queries a ChromaDB collection for additional context, and then
    constructs a comprehensive response using GPT.
    """

    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.environ["NVIDIA_API_KEY"])
    
    # 1. Define the system prompt this is the same as in magic_agent
    system_prompt = (
        "You are an expert Magic: The Gathering assistant. "
        "You help players understand cards, strategies, and game mechanics. "
        "Use the provided card details and context to give accurate and helpful answers. "
        "If you're not sure about something, say so rather than making up information."
    )
    
    # 2. Build the final prompt without all context
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.7
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"✗ Error calling GPT: {e}")
        return f"Error generating response: {str(e)}"