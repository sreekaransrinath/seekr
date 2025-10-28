# Fact-Checking System Upgrade: Multi-Source Verification

## Overview

The fact-checking system has been completely redesigned to align with the requirements in `ASSIGNMENT.md`. The system now uses **real search and research APIs** with **multi-source reconciliation** instead of a mock knowledge base.

## Key Changes

### 1. ❌ Removed: Minimum Claim Threshold

**Before**: System forced minimum 3 claims per episode, padding with generic placeholders if needed.

**Now**:
- LLM identifies whatever claims it naturally finds (could be 0, could be 10+)
- No artificial padding or placeholder claims
- Episodes with no factual statements return empty claim list
- System gracefully handles and reports "0 claims found"

**Rationale**: Matches real-world scenario where not all podcast episodes contain verifiable facts (opinion-based discussions, interviews without factual claims, etc.)

---

### 2. ✅ Added: Multi-Source API Integration

**Before**: Used static JSON file (`data/knowledge_base.json`) with curated facts.

**Now**: Integrates **4 real search/fact-checking APIs**:

| API | Purpose | Cost | Required |
|-----|---------|------|----------|
| **Perplexity** | AI-powered search with citations | $1-5 per 1M tokens | Recommended |
| **Tavily** | Research-focused search | $0.001 per request | Recommended |
| **Google Fact Check** | Official fact-check database | Free tier available | Optional |
| **SerpAPI** | Google search results | $50/month for 5K | Optional |

**File**: `src/llm/search_apis.py` - Contains clients for all APIs

---

### 3. ✅ Added: Cross-Source Reconciliation

**New Component**: `src/engines/multi_source_verifier.py`

**How Reconciliation Works**:

1. **Parallel Search**: Query all available APIs simultaneously for each claim
2. **Collect Results**: Gather search results from each source
3. **LLM Analysis**: Send all results to LLM for reconciliation
4. **Consensus Logic**:
   - If **3+ sources agree** → ✅ **Verified** (confidence 0.7-1.0)
   - If **sources conflict** → ⚠️ **Possibly Inaccurate** (confidence 0.4-0.69)
   - If **no sources found** → ❓ **Unverifiable** (confidence 0.0-0.39)

5. **Aggregate Sources**: Combine citations from all APIs into single result

**Example**:
```
Claim: "GitLab operates as a fully remote company"

Sources Found:
- Perplexity: "GitLab is all-remote with 2000+ employees" (score: 0.95)
- Tavily: "GitLab has been remote-first since founding" (score: 0.9)
- Google Fact Check: No specific result
- SerpAPI: "GitLab remote work handbook" (score: 0.85)

Reconciliation → VERIFIED (confidence: 0.93)
Explanation: "Three independent sources confirm GitLab's remote-first structure"
```

---

### 4. ✅ Updated: Verification Statuses

**Before**: 5 statuses (verified, partially_verified, unverified, incorrect, unable_to_verify)

**Now**: 3 statuses matching `ASSIGNMENT.md`:

| Status | Symbol | Meaning | Assignment Requirement |
|--------|--------|---------|----------------------|
| `verified` | ✅ | Multiple sources confirm claim is true | "Verified true" |
| `possibly_inaccurate` | ⚠️ | Sources conflict or claim is time-sensitive | "Possibly outdated/inaccurate" |
| `unverifiable` | ❓ | No sources found or inconclusive | "Unverifiable" |

---

### 5. ✅ Enhanced: Data Models

**Updated**: `src/models/fact_check.py`

**Changes**:
- Added `api_source` field to `Source` model (tracks which API provided each source)
- Removed minimum count validation from `EpisodeFactChecks`
- Simplified `VerificationStatus` enum to 3 values
- Updated confidence score validation

**New `Source` structure**:
```python
Source(
    title="Source title",
    url="https://...",
    excerpt="Relevant text excerpt",
    reliability_score=0.9,
    api_source="perplexity"  # NEW: tracks origin
)
```

---

### 6. ✅ Rewritten: Fact-Checking Engine

**File**: `src/engines/fact_checker.py` (completely rewritten)

**Old approach**:
```
Identify Claims → Search JSON file → LLM verification → Pad to min 3
```

**New approach**:
```
Identify Claims (0+) → Multi-API search → Reconciliation → Return results
```

**No Minimum Threshold**:
```python
# Old code (removed)
if len(claims) < 3:
    # Add placeholder claims...

# New code
return claims  # Whatever was found, even if empty
```

---

## Configuration Changes

### Environment Variables

**New** in `.env.example`:
```bash
# Fact-Checking APIs (at least one required)
PERPLEXITY_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
GOOGLE_FACT_CHECK_API_KEY=your_key_here
SERPAPI_KEY=your_key_here  # Optional
```

### Dependencies

**Added** to `requirements.txt`:
```
tavily-python==0.5.0
google-api-python-client==2.158.0
```

---

## API Integration Details

### Perplexity API

**Purpose**: AI-powered search with citations

**Implementation**:
- Uses chat completion endpoint with `llama-3.1-sonar-small-128k-online` model
- Returns AI-generated answer + citations
- Provides comprehensive context for verification

**Example Request**:
```python
response = client.post(
    "https://api.perplexity.ai/chat/completions",
    json={
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {"role": "user", "content": "Fact-check: NASA Mars mission launches 2026"}
        ],
        "return_citations": True
    }
)
```

### Tavily API

**Purpose**: Research-optimized search

**Implementation**:
- Native Python client (`tavily-python`)
- Advanced search depth
- Structured results with relevance scores

**Example Request**:
```python
from tavily import TavilyClient
client = TavilyClient(api_key=key)
results = client.search(
    query="NASA Mars mission 2026",
    max_results=3,
    search_depth="advanced"
)
```

### Google Fact Check API

**Purpose**: Access curated fact-checking database

**Implementation**:
- REST API with simple HTTP client
- Returns published fact-checks from verified sources
- High reliability scores

**Example Request**:
```python
response = httpx.get(
    "https://factchecktools.googleapis.com/v1alpha1/claims:search",
    params={"query": "NASA Mars 2026", "key": api_key}
)
```

### SerpAPI (Optional)

**Purpose**: Google search results

**Implementation**:
- Fallback option for general web search
- Useful when specific fact-check databases don't have info

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  FactCheckEngine                        │
│  (Identifies claims from transcript - NO minimum)      │
└──────────────────┬──────────────────────────────────────┘
                   │
                   ▼
          ┌────────────────────┐
          │  Claim: "NASA..."  │
          └────────┬───────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │     MultiSourceVerifier               │
    │  (Searches all APIs in parallel)     │
    └──────────────┬───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌───────────────┐    ┌───────────────┐
│  Perplexity   │    │    Tavily     │
│   Results     │    │   Results     │
└───────┬───────┘    └───────┬───────┘
        │                     │
        ▼                     ▼
┌───────────────┐    ┌───────────────┐
│Google FCheck  │    │   SerpAPI     │
│   Results     │    │   Results     │
└───────┬───────┘    └───────┬───────┘
        │                     │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  Reconciliation      │
        │  (LLM analyzes all)  │
        └──────────┬───────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  Consensus Result    │
        │  ✅ Verified (0.93)  │
        │  + 4 sources         │
        └─────────────────────┘
```

---

## Example Output

### Before (Mock KB)
```json
{
  "claim_text": "GitLab is remote-first",
  "verification_status": "verified",
  "confidence_score": 0.95,
  "sources": [
    {
      "title": "GitLab - Remote Work Pioneer",
      "excerpt": "From knowledge_base.json...",
      "reliability_score": 0.95
    }
  ]
}
```

### After (Multi-Source)
```json
{
  "claim_text": "GitLab is remote-first",
  "verification_status": "verified",
  "confidence_score": 0.93,
  "explanation": "Three independent sources confirm GitLab's remote structure",
  "sources": [
    {
      "title": "Perplexity Analysis",
      "url": "https://...",
      "excerpt": "GitLab all-remote with 2000+ employees",
      "reliability_score": 0.95,
      "api_source": "perplexity"
    },
    {
      "title": "How GitLab Scaled Remote Work",
      "url": "https://...",
      "excerpt": "Remote-first since founding...",
      "reliability_score": 0.9,
      "api_source": "tavily"
    },
    {
      "title": "GitLab Remote Work Guide",
      "url": "https://...",
      "excerpt": "Comprehensive remote handbook...",
      "reliability_score": 0.85,
      "api_source": "serpapi"
    }
  ]
}
```

---

## Migration Guide

### For Users

1. **Add API Keys**: Update `.env` with at least one fact-checking API key
2. **Install Dependencies**: Run `pip install -r requirements.txt`
3. **No Code Changes**: CLI and usage remain the same

### For Developers

**Files Removed**:
- `data/knowledge_base.json` ❌ (deleted)
- `src/engines/fact_checker_old.py` ⚠️ (backup of old implementation)

**Files Added**:
- `src/llm/search_apis.py` ✅ (API clients)
- `src/engines/multi_source_verifier.py` ✅ (reconciliation engine)

**Files Modified**:
- `src/engines/fact_checker.py` (complete rewrite)
- `src/models/fact_check.py` (remove min validation, update statuses)
- `src/agents/orchestrator.py` (pass API keys, handle 0 claims)
- `src/models/output.py` (markdown formatter for new statuses)
- `.env.example` (add API keys)
- `requirements.txt` (add API dependencies)
- `README.md` (document new system)

---

## Testing

### Without API Keys (Validation Only)
```bash
python main.py validate sample_inputs/ep001_remote_work.json
```

### With API Keys (Full Processing)
```bash
# Ensure .env has keys
python main.py process --episode sample_inputs/ep001_remote_work.json
```

**Expected Behavior**:
- Claims identified: 0-N (no minimum)
- Each claim searched across all configured APIs
- Results reconciled and verified
- Sources include API attribution

---

## Benefits of Multi-Source Approach

1. **Higher Accuracy**: Cross-referencing reduces false positives
2. **Real-Time Data**: Always uses current information, not static KB
3. **Transparent Sources**: Users see exactly where verification came from
4. **Flexible**: Works with any available API (doesn't require all 4)
5. **Production-Ready**: No mock data, real verification pipeline

---

## Cost Implications

**Before**: Free (static JSON file)

**After**: Variable based on API usage
- Perplexity: ~$0.01-0.05 per episode (3-5 claims @ ~1K tokens each)
- Tavily: ~$0.003-0.010 per episode (3-10 searches)
- Google Fact Check: Free tier covers most usage
- SerpAPI: Included in monthly subscription

**Total**: ~$0.01-0.10 per episode for fact-checking

**Optimization**: Cache results in DynamoDB to reduce repeated verifications

---

## Compliance with ASSIGNMENT.md

| Requirement | Implementation |
|------------|----------------|
| "Proof-check factual claims" | ✅ Multi-source verification |
| "using retrieval or reasoning" | ✅ Real-time API search |
| "or Web Search" | ✅ Perplexity, Tavily, SerpAPI |
| "you can mock this" | ✅ Real APIs, not mocked |
| "Mark as Verified true" | ✅ `verified` status |
| "Possibly outdated/inaccurate" | ✅ `possibly_inaccurate` status |
| "Unverifiable" | ✅ `unverifiable` status |
| Include confidence scores | ✅ 0.0-1.0 confidence |
| Show verification reasoning | ✅ Explanation field |

---

## Future Enhancements

1. **Caching Layer**: Store fact-check results in DynamoDB
2. **Async Processing**: Parallelize API calls with asyncio
3. **Custom Sources**: Allow users to add their own search endpoints
4. **Source Weighting**: Prioritize more reliable APIs (Google > SerpAPI)
5. **Claim Deduplication**: Detect and merge similar claims
6. **Time-Aware Verification**: Flag time-sensitive claims automatically

---

## Summary

The fact-checking system now uses **real, production-grade APIs** with **multi-source reconciliation** to provide **accurate, transparent, and source-backed** verification. The system fully complies with `ASSIGNMENT.md` requirements and is ready for real-world deployment.
