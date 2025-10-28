# Podcast Content Management Agent

An AI-powered agentic system for automated podcast content processing, designed for ad agencies to reduce manual content creation from 3-5 hours to under 5 minutes.

## Features

- **Automated Summarization**: Generates 200-300 word summaries covering all episode sections
- **Key Takeaways Extraction**: Identifies top 5 actionable insights from each episode
- **Quote Mining**: Extracts 3-10 notable, shareable quotes with timestamps
- **Topic Tagging**: Auto-generates 5-10 SEO-optimized topic tags
- **Multi-Source Fact-Checking**: Verifies claims using Perplexity, Tavily, Google Fact Check, and SerpAPI with cross-source reconciliation
- **Transparent Reasoning**: Detailed logs showing agent decision-making process
- **Multiple Output Formats**: JSON and Markdown reports
- **Model-Agnostic**: Uses OpenRouter for access to Claude, GPT-4, Gemini, and more

## Architecture

The system uses a multi-agent architecture coordinated by an orchestrator:

```
PodcastOrchestrator
├── TranscriptParser (validate and parse JSON transcripts)
├── SummarizationEngine (LLM-powered summarization)
├── ExtractionEngine (quotes, takeaways, topics)
├── FactCheckEngine (claim identification + verification)
└── ReasoningLogger (transparent decision logging)
```

## Requirements

- Python 3.12+
- **OpenRouter API key** (required for LLM access)
- **Fact-Checking API keys** (at least one required):
  - Perplexity API (recommended)
  - Tavily API (recommended)
  - Google Fact Check API
  - SerpAPI (optional)

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd seekr-2
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```
# Required
OPENROUTER_API_KEY=your_openrouter_key_here

# Fact-Checking APIs (at least one required)
PERPLEXITY_API_KEY=your_perplexity_key_here
TAVILY_API_KEY=your_tavily_key_here
GOOGLE_FACT_CHECK_API_KEY=your_google_key_here
SERPAPI_KEY=your_serpapi_key_here  # Optional
```

Get API keys from:
- [OpenRouter](https://openrouter.ai/) (required)
- [Perplexity](https://www.perplexity.ai/settings/api) (recommended)
- [Tavily](https://tavily.com/) (recommended)
- [Google Fact Check Tools API](https://developers.google.com/fact-check/tools/api)
- [SerpAPI](https://serpapi.com/) (optional)

## Usage

### Process All Sample Episodes

```bash
python main.py process --all
```

This will process all episodes in `sample_inputs/` directory.

### Process a Single Episode

```bash
python main.py process --episode sample_inputs/ep001_remote_work.json
```

### Use a Different Model

```bash
python main.py process --all --model openai/gpt-4o
```

Available models include:
- `anthropic/claude-3.5-sonnet` (default, recommended)
- `anthropic/claude-3-opus`
- `openai/gpt-4o`
- `openai/gpt-4-turbo`
- `google/gemini-pro-1.5`

### Custom Output Directory

```bash
python main.py process --all --output-dir my_outputs
```

### Validate Episode File

```bash
python main.py validate sample_inputs/ep001_remote_work.json
```

### Display Help

```bash
python main.py --help
python main.py process --help
```

## Output Files

After processing, the following files are generated in the `outputs/` directory:

### Per-Episode Reports

- `{episode_id}_report.json` - Complete report in JSON format
- `{episode_id}_report.md` - Formatted Markdown report

### Aggregate Reports (when processing multiple episodes)

- `aggregate_report.json` - Combined statistics across all episodes
- `aggregate_report.md` - Summary report with common themes

### Reasoning Logs

- `agent_reasoning_<timestamp>.log` - Human-readable decision log
- `agent_reasoning_<timestamp>.json` - Structured JSON decision log

## Episode Report Structure

Each episode report includes:

### 1. Metadata
- Episode ID, title, host, guests
- Duration, word count, sections

### 2. Summary
- 200-300 word episode summary
- Key themes identified

### 3. Key Takeaways
- Top 5 actionable insights
- Relevance scores

### 4. Notable Quotes
- 3-10 memorable quotes
- Speaker, timestamp, and context
- Engagement scores

### 5. Topic Tags
- 5-10 SEO-optimized tags
- Lowercase, hyphenated format

### 6. Fact Checks
- Identified factual claims
- Verification status (verified, partially_verified, unverified, incorrect)
- Confidence scores
- Source citations
- Detailed explanations

### 7. Processing Metrics
- Model used
- Processing time
- API calls made
- Tokens consumed

## Agent Reasoning Logs

The system generates transparent reasoning logs showing:

- **Planning**: What processing strategy was chosen and why
- **Decisions**: Key decisions made during processing
- **Execution**: What actions were taken
- **Validation**: How results were validated
- **Errors**: Any issues encountered and how they were handled

Example log entry:
```
[PLANNING] Episode Processing Pipeline
  → Processing episode from ep001_remote_work.json. Will execute: Parse →
    Summarize → Extract → Fact-check → Format. Summarization and extraction
    can theoretically run in parallel after parsing, but for simplicity and
    token management, running sequentially.
```

## Sample Episodes

Three sample podcast episodes are included in `sample_inputs/`:

1. **ep001_remote_work.json** - Discussion on remote work culture
2. **ep002_ai_healthcare.json** - AI applications in healthcare
3. **ep003_bootstrapping.json** - Bootstrapping vs VC funding

## Configuration

### Environment Variables

Set in `.env` file:

```bash
OPENROUTER_API_KEY=your_api_key_here
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
MAX_PARALLEL_TASKS=5
MAX_RETRIES=3
REQUEST_TIMEOUT=60
LOG_LEVEL=INFO
```

### Settings File

Customize processing in `config/settings.yaml`:

```yaml
llm:
  default_model: "anthropic/claude-3.5-sonnet"
  max_tokens: 4096
  temperature: 0.7

quality:
  summary:
    min_words: 200
    max_words: 300
  takeaways:
    count: 5
  quotes:
    min_count: 3
    max_count: 10
  fact_checks:
    min_count: 3
    min_confidence: 0.6
```

## Multi-Source Fact-Checking

The fact-checking engine uses **multiple real-time search APIs** to verify claims:

### How It Works

1. **Claim Identification**: LLM identifies factual claims from transcript (no minimum threshold)
2. **Multi-API Search**: Each claim is verified against:
   - **Perplexity**: AI-powered search with citations
   - **Tavily**: Research-focused search API
   - **Google Fact Check**: Official fact-checking database
   - **SerpAPI**: Google search results (optional)
3. **Reconciliation**: Cross-references results from all sources
4. **Consensus Verification**: Determines status based on agreement:
   - ✅ **Verified**: 3+ sources agree
   - ⚠️ **Possibly Inaccurate**: Sources conflict or time-sensitive
   - ❓ **Unverifiable**: No sources found or inconclusive

### Important Notes
- At least one fact-checking API key is required
- System gracefully handles 0 claims (if episode has no factual statements)
- Each fact-check result includes sources from multiple APIs
- Confidence scores reflect consensus strength

## Project Structure

```
seekr-2/
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── config/
│   └── settings.yaml         # Configuration
├── data/                     # Data directory (for future use)
├── sample_inputs/            # Sample podcast transcripts
│   ├── ep001_remote_work.json
│   ├── ep002_ai_healthcare.json
│   └── ep003_bootstrapping.json
├── outputs/                  # Generated reports (created on run)
├── src/
│   ├── models/              # Pydantic data models
│   │   ├── transcript.py
│   │   ├── summary.py
│   │   ├── fact_check.py
│   │   └── output.py
│   ├── engines/             # Processing engines
│   │   ├── parser.py
│   │   ├── summarizer.py
│   │   ├── extractor.py
│   │   └── fact_checker.py
│   ├── llm/                 # LLM integration
│   │   ├── gateway.py
│   │   └── prompts.py
│   ├── agents/              # Orchestration
│   │   ├── orchestrator.py
│   │   └── reasoning.py
│   └── cli/                 # CLI interface
│       └── main.py
└── tests/                   # Unit tests (future)
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Type checking
mypy src/

# Linting
ruff check src/

# Formatting
black src/
```

## Performance

Typical processing times (using Claude 3.5 Sonnet):
- Single episode: 30-60 seconds
- All 3 sample episodes: ~2 minutes
- Tokens per episode: 5,000-10,000

## Cost Estimation

### OpenRouter (LLM)
- Claude 3.5 Sonnet: $3 per 1M tokens (input) / $15 per 1M tokens (output)
- Per episode: ~$0.05-0.15
- 100 episodes: ~$5-15

### Fact-Checking APIs (approximate)
- Perplexity: $1-5 per 1M tokens
- Tavily: $0.001 per search request
- Google Fact Check: Free tier available
- SerpAPI: $50/month for 5K searches

**Total per episode**: ~$0.10-0.25 including all APIs

## Limitations

Current limitations:
- Sequential processing (could parallelize summarization and extraction)
- No caching for fact-check results (repeated claims verified each time)
- Limited error recovery
- No social media content generation (planned feature)

## Troubleshooting

### API Key Issues

```
Error: OpenRouter API key required
```

Solution: Set `OPENROUTER_API_KEY` in `.env` file or use `--api-key` flag.

### Rate Limiting

If you hit rate limits, the system will automatically retry up to 3 times. You can adjust retry settings in `config/settings.yaml`.

### Validation Errors

```
ValidationError: Summary too short
```

This means the LLM generated a summary shorter than 150 words. Try a different model or adjust `min_words` in settings.

## Support

For issues, questions, or contributions:
1. Check existing documentation
2. Review reasoning logs for debugging
3. Open an issue with reproduction steps

## License

[Your License Here]

## Acknowledgments

- Built with OpenRouter for model-agnostic LLM access
- Uses Pydantic v2 for robust data validation
- CLI built with Click and Rich for great UX
