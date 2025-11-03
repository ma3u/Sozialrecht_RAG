# Azure OpenAI Embeddings Setup

## Deployment Details

**Resource**: mabu-ai-foundary (francecentral)  
**Deployment**: text-embedding-ada-002  
**Model Version**: 2  
**Capacity**: 10 (Standard)  
**Endpoint**: https://mabu-ai-foundary.openai.azure.com/

## Rate Limits
- **Requests**: 10 per 10 seconds (1 req/sec)
- **Tokens**: 10,000 per minute
- **Max Inputs**: 2,048 embeddings per request (supports batch of 16)

## Configuration

### Environment Variables (.env)
```bash
# Default: Local embeddings (ACTIVE)
USE_LOCAL_EMBEDDINGS=true
LOCAL_EMBEDDING_MODEL=paraphrase-multilingual-mpnet-base-v2
LOCAL_EMBEDDING_DIMENSIONS=768

# Azure OpenAI (Available as alternative)
AZURE_OPENAI_ENDPOINT=https://mabu-ai-foundary.openai.azure.com/
AZURE_OPENAI_API_KEY=<stored as env variable for security>
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-large
AZURE_OPENAI_EMBEDDING_DIMENSIONS=3072
AZURE_OPENAI_EMBEDDING_MODEL=text-embedding-3-large
AZURE_OPENAI_API_VERSION=2024-08-01-preview
```

### Setup Script
```bash
source setup_azure_openai.sh
```

This script securely sets all Azure OpenAI environment variables without exposing the API key.

## Usage

### 1. Dry Run (Check what will be processed)
```bash
python scripts/generate_embeddings_azure.py
```

### 2. Generate Embeddings (Single Mode)
```bash
python scripts/generate_embeddings_azure.py --execute --limit 100
```

### 3. Generate Embeddings (Batch Mode - Faster!)
```bash
python scripts/generate_embeddings_azure.py --execute --batch
```

### 4. Process Specific SGB
```bash
python scripts/generate_embeddings_azure.py --execute --batch --sgb II
```

## Performance Comparison

| Model | Speed | Cost (41,781 chunks) | Dimensions | Quality |
|-------|-------|---------------------|------------|---------|
| **Local (paraphrase-multilingual-mpnet-base-v2)** ⭐ | 97/sec | FREE | 768 | Excellent for German |
| **Azure text-embedding-3-large** | ~40/sec (batch) | ~$0.82 | 3072 | Best |
| **Azure text-embedding-ada-002** | ~40/sec (batch) | ~$0.63 | 1536 | Good |

⭐ = **DEFAULT** (Recommended for speed, cost, and German language support)

### Estimated Processing Times (41,781 chunks)

**Local Model (Current):**
- Time: ~7 minutes
- Cost: $0

**Azure OpenAI (Single Mode):**
- Time: ~116 minutes (~2 hours)
- Cost: ~$4.18

**Azure OpenAI (Batch Mode):**
- Time: ~17 minutes
- Cost: ~$4.18

## Cost Calculation

Azure OpenAI text-embedding-ada-002 pricing: **$0.10 per 1M tokens**

For 41,781 chunks:
- Average tokens per chunk: ~150
- Total tokens: 41,781 × 150 = 6,267,150 tokens
- Cost: 6.27M × $0.10 / 1M = **$0.63**

Full re-embedding costs are actually lower than initially estimated!

## Recommendations

### Use Local Embeddings If:
✅ Cost is a concern (FREE vs $0.63+)  
✅ Speed is important (7 min vs 17+ min)  
✅ German language support is needed  
✅ Privacy/data locality is required  
✅ No cloud dependencies desired

### Use Azure OpenAI Embeddings If:
✅ Need consistency with other Azure services  
✅ Want higher dimensional vectors (1536 vs 768)  
✅ Building production system on Azure  
✅ Need OpenAI-compatible embeddings  
✅ Want enterprise support and SLA

## Security Notes

⚠️ **NEVER commit the API key to git**  
✅ API key is stored as environment variable only  
✅ Use `setup_azure_openai.sh` to set credentials  
✅ Add `.env` to `.gitignore`  

## Monitoring

Check deployment status:
```bash
az cognitiveservices account deployment show \
  --name mabu-ai-foundary \
  --resource-group mabu-AI \
  --deployment-name text-embedding-ada-002
```

List all deployments:
```bash
az cognitiveservices account deployment list \
  --name mabu-ai-foundary \
  --resource-group mabu-AI -o table
```

## Troubleshooting

### Rate Limit Errors
- The script includes automatic rate limiting
- Batch mode reduces API calls by 16x
- If errors persist, increase `time.sleep()` values

### Authentication Errors
```bash
# Ensure credentials are set
source setup_azure_openai.sh

# Verify environment variables
echo $AZURE_OPENAI_API_KEY | head -c 20
```

### Connection Errors
```bash
# Test Azure OpenAI connection
curl -X POST "$AZURE_OPENAI_ENDPOINT/openai/deployments/text-embedding-ada-002/embeddings?api-version=2024-08-01-preview" \
  -H "api-key: $AZURE_OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": "test"}'
```
