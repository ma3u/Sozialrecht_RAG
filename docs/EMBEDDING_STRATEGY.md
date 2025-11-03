# Embedding Strategy Summary

## Current Configuration ⭐

**Primary (Active)**: Local Embeddings
- **Model**: paraphrase-multilingual-mpnet-base-v2
- **Dimensions**: 768
- **Speed**: 97 embeddings/second
- **Cost**: FREE
- **Quality**: Excellent for German legal text

## Rationale

### Why Local Embeddings are Default

1. **Speed**: 2-16x faster than Azure OpenAI
   - Local: 97 embeddings/sec
   - Azure (batch): ~40 embeddings/sec
   - Azure (single): ~6 embeddings/sec

2. **Cost**: Zero vs ~$0.63-$0.82 per full re-embedding
   - 41,781 chunks = FREE locally
   - Same task = $0.63-$0.82 on Azure

3. **Quality**: Optimized for multilingual text including German
   - Legal terminology support
   - No quality degradation vs Azure for German content

4. **Processing Time** (41,781 chunks):
   - Local: ~7 minutes
   - Azure: 17-116 minutes

5. **Privacy**: All data stays local, no cloud transmission

## Azure OpenAI Options (Available)

### Deployed Models

| Model | Dimensions | Cost per 1M tokens | Use Case |
|-------|------------|-------------------|----------|
| text-embedding-ada-002 | 1536 | $0.10 | Standard quality |
| text-embedding-3-large | 3072 | $0.13 | Best quality |

### When to Use Azure

- Production deployment requiring Azure ecosystem integration
- Need for higher dimensional vectors (1536 or 3072 vs 768)
- Enterprise SLA and support requirements
- Consistency with other OpenAI-based services
- Cross-language consistency beyond German

## Usage

### Default (Local Embeddings)
```bash
# Already configured in .env
USE_LOCAL_EMBEDDINGS=true

# Use existing scripts
python scripts/generate_embeddings.py --execute
```

### Azure OpenAI (Optional)
```bash
# Set credentials
source setup_azure_openai.sh

# Use Azure script with batch mode for best performance
python scripts/generate_embeddings_azure.py --execute --batch

# Or specific SGB
python scripts/generate_embeddings_azure.py --execute --batch --sgb II
```

## Performance Comparison

### For 41,781 Chunks

| Metric | Local | Azure (batch) | Azure (single) |
|--------|-------|---------------|----------------|
| Time | 7 min | 17 min | 116 min |
| Cost | $0 | $0.82 | $0.82 |
| Speed | 97/sec | 40/sec | 6/sec |
| Dimensions | 768 | 3072 | 3072 |
| Quality | Excellent | Best | Best |

## Configuration Files

- `.env` - Environment variables (local is default)
- `setup_azure_openai.sh` - Azure credentials setup
- `scripts/generate_embeddings.py` - Local embedding generation
- `scripts/generate_embeddings_azure.py` - Azure embedding generation

## Recommendation

✅ **Keep using local embeddings** for:
- Development and testing
- Fast iteration cycles
- Cost-sensitive operations
- German legal text processing

💡 **Consider Azure** only if:
- Building production system on Azure
- Need maximum embedding dimensions (3072)
- Require enterprise SLA
- Cross-platform consistency is critical

## Azure Deployments

Current Azure OpenAI deployments:
```
Name                      Model                     Status
------------------------  ------------------------  ---------
mistral-document-ai-2505  mistral-document-ai-2505  Succeeded
Mistral-Nemo              Mistral-Nemo              Succeeded
text-embedding-ada-002    text-embedding-ada-002    Succeeded
text-embedding-3-large    text-embedding-3-large    Succeeded
```

All models are deployed and ready but **not used by default**.
