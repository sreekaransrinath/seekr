# Testing Guide

## Running Tests

The project includes a comprehensive test suite to validate functionality.

### Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Test File

```bash
pytest tests/test_parser.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=html
```

## Validation Without API Key

You can validate episode files without an OpenRouter API key:

```bash
python main.py validate sample_inputs/ep001_remote_work.json
```

This will parse and validate the JSON structure, showing:
- Episode metadata (ID, title, host, guests)
- Transcript statistics (segments, word count, sections, speakers)
- Duration estimate

## Manual Testing

### 1. Validate All Sample Episodes

```bash
for file in sample_inputs/*.json; do
    echo "Validating $file"
    python main.py validate "$file"
    echo ""
done
```

Expected output: All 3 episodes should validate successfully.

### 2. Test CLI Help System

```bash
python main.py --help
python main.py process --help
python main.py info
```

Expected output: Formatted help text and system information.

### 3. Test with Real API Key (Optional)

If you have an OpenRouter API key:

```bash
# Set API key
export OPENROUTER_API_KEY=your_key_here

# Process single episode
python main.py process --episode sample_inputs/ep001_remote_work.json

# Process all episodes
python main.py process --all
```

Expected outputs in `outputs/`:
- `ep001_report.json` and `ep001_report.md`
- `ep002_report.json` and `ep002_report.md`
- `ep003_report.json` and `ep003_report.md`
- `aggregate_report.json` and `aggregate_report.md`
- `agent_reasoning_<timestamp>.log`
- `agent_reasoning_<timestamp>.json`

## Test Coverage

Current test coverage:

- ✅ Transcript parsing and validation
- ✅ Episode data model validation
- ✅ Error handling (missing files, invalid JSON)
- ✅ Episode helper methods (sections, speakers, text extraction)
- ✅ Multi-episode processing

## Continuous Integration

For CI/CD pipelines:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --cov=src
```

## Performance Benchmarks

Expected performance (with LLM API calls):

- Single episode: 30-60 seconds
- All 3 sample episodes: ~2 minutes
- Validation only: <1 second per episode

## Known Issues

1. **Pydantic Validation**: Very strict validation may reject some edge cases. Adjust validators in `src/models/` if needed.

2. **LLM Response Parsing**: If LLM returns non-JSON despite prompts, the system will retry or return default values.

3. **Rate Limiting**: Heavy usage may hit OpenRouter rate limits. System includes retry logic with exponential backoff.

## Troubleshooting Tests

### Import Errors

```bash
# Ensure you're in project root
cd /path/to/seekr-2

# Reinstall dependencies
pip install -r requirements.txt
```

### File Not Found Errors

```bash
# Tests expect to be run from project root
pytest tests/
```

### Environment Issues

```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
find . -type f -name "*.pyc" -delete
```
