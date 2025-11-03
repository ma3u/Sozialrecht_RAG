#!/bin/bash
# Setup Azure OpenAI Environment Variables
# This script securely sets the Azure OpenAI API key without exposing it

echo "Setting up Azure OpenAI configuration..."

# Set the API key as environment variable (replace {{azure_openai_api_key}} with your actual key)
export AZURE_OPENAI_API_KEY="{{azure_openai_api_key}}"

# Set additional Azure OpenAI variables from .env
export AZURE_OPENAI_ENDPOINT="https://mabu-ai-foundary.openai.azure.com/"
export AZURE_OPENAI_DEPLOYMENT_NAME="mistral-document-ai-2505"
export AZURE_OPENAI_API_VERSION="2024-08-01-preview"

# Set Azure OpenAI Embedding variables (text-embedding-3-large for best quality)
export AZURE_OPENAI_EMBEDDING_DEPLOYMENT="text-embedding-3-large"
export AZURE_OPENAI_EMBEDDING_DIMENSIONS="3072"
export AZURE_OPENAI_EMBEDDING_MODEL="text-embedding-3-large"

# Note: Local embeddings (paraphrase-multilingual-mpnet-base-v2) are DEFAULT
# They are faster (97/sec vs 40/sec) and FREE

echo "✓ Azure OpenAI environment variables configured"
echo "✓ Endpoint: $AZURE_OPENAI_ENDPOINT"
echo "✓ LLM Deployment: $AZURE_OPENAI_DEPLOYMENT_NAME"
echo "✓ Embedding Deployment: $AZURE_OPENAI_EMBEDDING_DEPLOYMENT"
echo "✓ API Version: $AZURE_OPENAI_API_VERSION"
echo ""
echo "To use these settings, run: source setup_azure_openai.sh"
