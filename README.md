# Repo rag-mtg
AI chatbot that knows the rules of Magic the Gathering. 

# Starting Documents
MTG full rulebook.
https://media.wizards.com/images/magic/tcg/resources/rules/MagicCompRules_21031101.pdf
Full db of mtg cards from scryfall called via API.
https://scryfall.com/docs/api

# Learning Topics
- RAG logics implementation without using already developed libraries.
- Lambda AWS. https://docs.aws.amazon.com/lambda/
- Pinecone vector db + Llamaindex. https://developers.llamaindex.ai/python/framework-api-reference/storage/vector_store/pinecone/

# Main Architecture Idea & Guidelines
1. Account Setup and Credentials
- [ ] Create an AWS account (requires a credit card)
- [X] Create a Pinecone account (email, free tier)
- [X] Create an OpenAI account and deploy a model to get API key.
- [X] Store all API keys securely

2. Data Preparation
- Download the Magic: The Gathering rules manual (PDF or text)
- Test scryfall API

3. Indexing Pipeline (local ipynb script)
- Splits text into chunks
- Call OpenAI for embeddings
- Uploads vectors to Pinecone

4. Local Development Environment Setup
- Install AWS CLI and configure credentials
- Install AWS SAM CLI (to test Lambda locally)
- Set up a Python virtual environment

5. Lambda RAG Engine Development
- Create a Lambda function (Python)
- Logic: receive query → generate API query → call scryfall → search Pinecone → generate answer with GPT
- Test locally using SAM

6. Lambda Deployment and API Gateway
- Deploy Lambda to AWS
- Create a REST API via API Gateway
- Connect the endpoint to the Lambda function
- Test using Postman or curl

7. Streamlit Integration
- Create a basic frontend in Streamlit
- Activate Streamlit Community
- Create a Lambda webhook handler
- Configure webhook URL
- Test conversation


# Project Setup
This project uses poetry to handle dependencies

run:

pip install poetry
poetry install


# Notes
At first, I considered indexing the entire card database, but that would require a recurring script to keep the index updated. I’ll still need to do something similar for the rules manual, though rule changes occur far less frequently than new card releases.