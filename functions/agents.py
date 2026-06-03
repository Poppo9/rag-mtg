import os
import re
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
from functions.scryfall import get_complete_card_info
from functions.chroma import query_chroma_index
import ast 

MODEL_NAME = os.environ["MODEL_NAME"]

def extract_card_names_from_query(query: str) -> list:
    print("Run function: extract_card_names_from_query")
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
        model=MODEL_NAME,
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
    print("Run function: magic_agent")
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
        "4. If you're not sure about a ruling, state it honestly. Do not hallucinate.\n"
        "5. RULES INTERACTION PARADIGM — when cards interact via continuous effects:\n"
        "   a. LAYER: identify which layer each effect applies in (rule 613.1).\n"
        "   b. TIMESTAMP: within the same layer, effects apply in timestamp order (613.7).\n"
        "   c. DEPENDENCY: before using timestamp, check rule 613.8a — if applying effect A\n"
        "      changes what effect B does or what it applies to, B depends on A and A applies\n"
        "      first, regardless of timestamp.\n"
        "   d. CDA: characteristic-defining abilities always apply before other effects in the\n"
        "      same layer (613.3).\n"
        "   e. STATE THE CONCLUSION: what are the final characteristics after all layers resolve?\n"
        "   Cite the rule number when context includes it. Flag uncertainty explicitly.\n\n"
        "LANGUAGE:\n"
        "Detect the language of the user's question and reply in the same language.\n"
        "If the question is in Italian, answer in Italian. If in English, answer in English.\n"
        "Do not mix languages within a single response.\n\n"
        "RESPONSE FORMAT:\n"
        "Structure every answer using the following sections (omit sections that don't apply):\n\n"
        "**Cards involved** — list each card with a one-line summary of its relevant effect.\n\n"
        "**Answer** — direct answer to the question, written in plain prose.\n\n"
        "**Rules explanation** — step-by-step reasoning. For interactions, apply the RULES\n"
        "INTERACTION PARADIGM (point 5 above). Cite rule numbers when available.\n\n"
        "**Verdict** — one or two sentences summarising the final outcome clearly.\n\n"
        "**Uncertainty** — if any part of the ruling is unclear or disputed, flag it here.\n"
        "Omit this section if you are fully confident in the answer.\n"
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
            print(f"Retrieved info for \"{card_name}\": {card_info.splitlines()[0]}")
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

    print("\n\n\nCalling GPT with the following prompt:\n\n\n")
    print(final_user_message)
    # 7. Call GPT
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
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
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating response: {str(e)}"