# Repo rag-mtg
AI chatbot that knows the rules of Magic the Gathering. 

# Starting Documents
MTG full rulebook.
https://media.wizards.com/images/magic/tcg/resources/rules/MagicCompRules_21031101.pdf
Full db of mtg cards from scryfall called via API.
https://scryfall.com/docs/api

# Learning Topics
- RAG logics implementation without using already developed libraries.
- NVIDIA free api testing
- CHROMADB vector db + Llamaindex.
- Easy streamlit frontend

# Main Architecture Idea & Guidelines
1. Account Setup and Credentials
- [X] Create an NVIDIA account and deploy a model to get API key.
- [X] Store all API keys securely

2. Data Preparation
- Download the Magic: The Gathering rules manual (PDF or text)
- Test scryfall API

3. Indexing Pipeline (local ipynb script)
- Splits text into chunks
- Call NVIDIA for embeddings (same model used for retrieval)
- Uploads vectors to a chroma DB

4. Local Development Environment Setup
- Set up a Python virtual environment (here with UV to test it)

5. Setup a way to chat with it 
- Discord bot is feasable with a cloud VM (Oracle Cloud offers low tier free VMs)
- Quick and easy streamlit FE to run locally

# Project Setup
This project uses UV to handle dependencies
https://docs.astral.sh/uv/getting-started/

# Notes
At first, I considered indexing the entire card database, but that would require a recurring script to keep the index updated. I’ll still need to do something similar for the rules manual, though rule changes occur far less frequently than new card releases.

# TODO
- [X] Switch OpenaAI to NVIDIA models in /functions/agents.py
- [X] Switch OpenaAI to NVIDIA models in /functions/chroma.py
- [X] Switch OpenaAI to NVIDIA models in chroma-setup.ipynb
- [X] Switch OpenaAI to NVIDIA models in chroma-test.ipynb
- [X] Switch OpenaAI to NVIDIA models in demo.ipynb
- [X] Add endpoint in the chatbot to index the knowledgebase from discord
- [X] System prompt optimization and edge case handling
