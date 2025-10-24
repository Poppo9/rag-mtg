# rag-mtg
AI chatbot that knows the rules of Magic the Gathering. 

# starting documents
MTG full rulebook
Full db of mtg cards from scryfall

# learning topics
AWS
RAG w/ Langchain
Lambda AWS
Pinecone

# main architecture idea
1. Account Setup and Credentials
- Create an AWS account (requires a credit card)
- Create a Pinecone account (email, free tier)
- Store all API keys securely

2. Local Development Environment Setup
- Install AWS CLI and configure credentials
- Install AWS SAM CLI (to test Lambda locally)
- Set up a Python virtual environment

3. Data Preparation
- Download the Magic: The Gathering rules manual (PDF or text)
- Create an S3 bucket on AWS -> not necessary
- Upload the manual to S3 -> not necessary

4. Indexing Pipeline (local script)
- Python script downloads the manual from S3 -> not necessary
- Splits text into chunks
- Calls Azure OpenAI for embeddings
- Uploads vectors to Pinecone

5. Lambda RAG Engine Development
- Create a Lambda function (Python)
- Logic: receive query → search Pinecone → generate answer with GPT
- Test locally using SAM

6. Lambda Deployment and API Gateway
- Deploy Lambda to AWS
- Create a REST API via API Gateway
- Connect the endpoint to the Lambda function
- Test using Postman or curl

7. Streamlit Integration
- Activate Streamlit Community
- Create a Lambda webhook handler
- Configure webhook URL
- Test conversation


# Project setup
This project uses poetry to handle dependencies

run:

pip install poetry
poetry install