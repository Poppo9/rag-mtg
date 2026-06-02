import os
import re
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from functions.scryfall import get_complete_card_info
from functions.chroma import query_chroma_index
import ast 

def extract_card_names_from_query(query: str) -> list:
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.environ["NVIDIA_API_KEY"])
    
    system_prompt = (
        "You are an expert in Magic: The Gathering. Your single task is to identify and extract card names from the user query.\n"
        "RULES:\n"
        "1. Return strictly a valid Python list of strings, containing only the extracted card names.\n"
        "2. Do NOT include any introductory or concluding text. No explanations.\n"
        "3. If no cards are mentioned, return an empty list: []\n"
        "4. If too many cards are mentioned, extract ONLY the most relevant ones (MAXIMUM 5 cards).\n"
        "5. Even if you suspect a word might be a card name but are not 100% sure, include it."
    )
    
    response = client.chat.completions.create(
        model="meta/llama-3.1-8b-instruct",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0.0 # Low temperature for deterministic output, since we want a strict list of card names
    )
    
    content = response.choices[0].message.content.strip()
    
    # Use regex to extract the list from the response
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        list_str = match.group(0)
        try:
            card_names = ast.literal_eval(list_str)
            if isinstance(card_names, list):
                return card_names[:5] # Extract only the first 5 cards if there are more
        except Exception:
            pass
    
    return []


def magic_agent(user_query: str, verbose = False) -> str:
    if verbose:
        print("\n\n=== STEP 1: Initializing NVIDIA client ===")
        print(f"Asking question: {user_query}")
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.environ["NVIDIA_API_KEY"])

    # 1. System Prompt 
    system_prompt = (
        "You are an expert Magic: The Gathering assistant. You help players understand cards, strategies, rules, and game mechanics.\n\n"
        "CRITICAL RULE - OFF-TOPIC FILTER:\n"
        "If the user's question is completely unrelated to Magic: The Gathering (e.g., general knowledge, cooking, other games, coding, life advice), "
        "you MUST refuse to answer. Respond in a brief, annoyed, sarcastic, or grumpy tone, stating clearly that the question has nothing to do with MTG, "
        "and tell them to go bother another AI (like ChatGPT or Claude) for that kind of stuff. Do not be helpful for off-topic questions.\n\n"
        "RULES FOR MTG QUESTIONS:\n"
        "1. Use the provided card details and context to give accurate answers.\n"
        "2. If multiple cards are provided, compare them or analyze their interaction as requested.\n"
        "3. If the context states that a card was not found, inform the user about it.\n"
        "4. If you're not sure about a ruling, state it honestly. Do not hallucinate."
    )
    
    # 2. Extract card names
    card_names = extract_card_names_from_query(user_query)
    if verbose:
        print(f"Extracted card names: {card_names}")

    # 3. Retrieve card info
    card_info_strings = []
    missing_cards = []
    
    for card_name in card_names:
        try:
            card_info = get_complete_card_info(card_name)
            if card_info and not card_info.startswith("No card found") and not card_info.startswith("Error"):
                card_info_strings.append(card_info)
            else:
                missing_cards.append(card_name)
        except Exception as e:
            missing_cards.append(card_name)
            if verbose:
                print(f"✗ Error retrieving info on {card_name}: {e}")

    # 4. Query ChromaDB
    chroma_results = query_chroma_index(user_query)
    
    # 5. Build context
    context_parts = []
    
    if card_info_strings:
        context_parts.append("=== CARD DETAILS WITH RULINGS ===\n")
        context_parts.extend(card_info_strings)
    
    # Signal the LLM if Scryfall didn't find some cards requested by the user
    if missing_cards:
        context_parts.append(f"=== MISSING CARDS ===\nNote: The following cards requested by the user could not be found in the database: {', '.join(missing_cards)}")
        
    if chroma_results:
        context_parts.append("=== ADDITIONAL CONTEXT ===\n" + chroma_results)
    
    context = "\n".join(context_parts)

    # 6. Build final prompt
    # If the context is empty (e.g., a generic question), pass only the question.
    if context:
        final_user_message = f"{context}\n\n=== USER QUESTION ===\n{user_query}"
    else:
        final_user_message = f"=== USER QUESTION ===\n{user_query}"

    # 7. Call GPT
    try:
        response = client.chat.completions.create(
            model="meta/llama-3.1-8b-instruct",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_user_message}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
        
    except Exception as e:
        return f"Error generating response: {str(e)}"


def non_rag_magic_agent(user_query: str, verbose = False) -> str:
    client = OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=os.environ["NVIDIA_API_KEY"])
    
    system_prompt = (
        "You are an expert Magic: The Gathering assistant. You help players understand cards, strategies, and game mechanics.\n\n"
        "CRITICAL RULE - OFF-TOPIC FILTER:\n"
        "If the user's question is completely unrelated to Magic: The Gathering, you MUST refuse to answer. "
        "Respond in a brief, annoyed, sarcastic, or grumpy tone, stating clearly that the question has nothing to do with MTG, "
        "and tell them to go ask another AI for that stuff. Do not help them with non-MTG topics."
    )
    
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
        return f"Error generating response: {str(e)}"