# Design Specification: Podcast Content Management MVP (Local)

---

## 1. Core System Architecture

### 1.1 Application Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Input Layer                              │
│  ┌──────────────┐                    ┌──────────────┐      │
│  │     CLI      │                    │   REST API   │      │
│  │   (Click)    │                    │  (FastAPI)   │      │
│  └──────────────┘                    └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 Agent Orchestrator                          │
│  ┌────────────┬─────────────┬──────────────────────┐      │
│  │   Planner  │  Executor   │    State Manager     │      │
│  └────────────┴─────────────┴──────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Processing Engines                         │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐ │
│  │Transcript│ Summary  │ Extract  │Fact Check│  Social  │ │
│  │   Parser │  Engine  │  Engine  │  Engine  │Generator │ │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   External APIs                             │
│  ┌──────────────┬──────────────┬────────────────────────┐  │
│  │  OpenRouter  │  Perplexity  │   Google Fact Check    │  │
│  │     API      │     API      │        (optional)      │  │
│  └──────────────┴──────────────┴────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Component Design

| Component | Responsibility | Design Pattern |
|-----------|---------------|----------------|
| **CLI Interface** | Command-line interaction, progress display | Command pattern with Click framework |
| **REST API** | HTTP endpoint for programmatic access | FastAPI with async handlers |
| **Agent Orchestrator** | Multi-step task planning and execution | State machine with DAG execution |
| **Task Planner** | Dependency resolution and optimization | Topological sort for task ordering |
| **State Manager** | Tracks processing state and progress | In-memory state with persistence option |
| **Processing Engines** | Specialized task execution | Strategy pattern for different processors |
| **LLM Gateway** | Unified interface to multiple LLMs | Adapter pattern for model abstraction |

---

## 2. Agent Orchestration Design

### 2.1 Agent Architecture

```
                    ┌─────────────┐
                    │   Request   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Planning   │
                    │    Phase     │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌──────▼──────┐    ┌─────▼─────┐
   │ Analyze │      │  Generate   │    │  Extract  │
   │Transcript│     │  Execution  │    │   Tasks   │
   └─────────┘      │    Plan     │    └───────────┘
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  Execution  │
                    │    Phase    │
                    └──────┬──────┘
                           │
     ┌─────────┬───────────┼───────────┬─────────┐
     │         │           │           │         │
┌────▼───┐ ┌──▼──┐ ┌──────▼─────┐ ┌──▼──┐ ┌────▼────┐
│Summary │ │Quote│ │Fact Check  │ │Tags │ │Social   │
│Engine  │ │Ext. │ │   Engine   │ │Gen. │ │Generator│
└────────┘ └─────┘ └────────────┘ └─────┘ └─────────┘
```

### 2.2 Planning Strategy

**Task Dependency Graph**:

```python
Task Dependencies:
- preprocess: []                    # No dependencies
- summarize: [preprocess]           # Depends on preprocessing
- extract_quotes: [preprocess]      # Can run parallel with summary
- extract_takeaways: [preprocess]   # Can run parallel
- identify_claims: [preprocess]     # Can run parallel
- verify_claims: [identify_claims]  # Sequential after identification
- generate_social: [extract_quotes] # Needs quotes first
- generate_tags: [summarize]        # Better with summary context
```

**Optimization Rules**:
1. Maximum parallel execution where dependencies allow
2. Group similar LLM calls for batch processing
3. Prioritize fast operations to show early progress
4. Cache intermediate results for retry resilience

### 2.3 State Management

**Processing States**:
```
PENDING → PLANNING → EXECUTING → AGGREGATING → COMPLETED
                         ↓
                    FAILED (with retry)
```

**State Tracking Structure**:
- Job ID and metadata
- Current phase and progress percentage
- Completed tasks list
- Pending tasks queue
- Error log and retry count
- Reasoning decision log

---

## 3. Data Flow Design

### 3.1 Input Processing Pipeline

```
Raw JSON → Validation → Parsing → Normalization → Chunking
             ↓            ↓          ↓              ↓
         Schema Check  Extract    Clean Text   Context Windows
                      Speakers    Remove Filler  (for LLMs)
```

### 3.2 Information Extraction Flow

**Hierarchical Processing**:

1. **Document Level**: Full transcript analysis
   - Overall themes and narrative arc
   - Speaker dynamics and perspectives
   
2. **Section Level**: Grouped by topic sections
   - Topic transitions and depth
   - Key discussion points per section
   
3. **Utterance Level**: Individual statements
   - Factual claims vs opinions
   - Quotable moments
   - Specific insights

### 3.3 Output Generation Pipeline

```
Collected Results → Validation → Formatting → Output
        ↓              ↓            ↓           ↓
   Merge Tasks    Check Quality  Apply Template  JSON/MD
```

---

## 4. LLM Integration Architecture

### 4.1 Multi-Model Strategy

| Task Type | Primary Model | Secondary Model | Reasoning |
|-----------|--------------|-----------------|-----------|
| **Summarization** | Claude-3-Opus | GPT-4-Turbo | Claude for nuance, GPT-4 for structure |
| **Claim Extraction** | GPT-4-Turbo | - | Precision and low hallucination |
| **Fact Verification** | Claude-3-Opus | GPT-4 | Reasoning capability critical |
| **Quote Extraction** | GPT-4 | Claude-3 | Balance of accuracy and creativity |
| **Social Generation** | GPT-4-Turbo | - | Engagement optimization |

### 4.2 Prompt Engineering Architecture

**Prompt Template Structure**:

```
System Context → Task Definition → Input Format → Output Schema → Examples → Data
```

**Multi-Pass Processing Design**:

```
Pass 1: Extract/Generate (Temperature: 0.7)
    ↓
Pass 2: Validate/Verify (Temperature: 0.1)
    ↓
Pass 3: Refine/Polish (Temperature: 0.3)
```

### 4.3 LLM Call Optimization

**Batching Strategy**:
- Group similar prompts together
- Combine multiple small tasks into single prompt
- Use structured output formats (JSON mode)

**Context Management**:
- Sliding window for long transcripts
- Overlap regions for continuity
- Summary propagation for context

---

## 5. Fact-Checking System Design

### 5.1 Claim Identification Pipeline

```
Transcript → Statement Extraction → Classification → Prioritization
                    ↓                     ↓              ↓
              Sentence Split      Fact vs Opinion   Importance Score
```

**Classification Categories**:
- **Factual Claims**: Verifiable statements about reality
- **Statistical Claims**: Numbers, percentages, quantities
- **Temporal Claims**: Dates, timelines, sequences
- **Entity Claims**: People, organizations, places
- **Causal Claims**: Cause-effect relationships
- **Opinions**: Subjective viewpoints (skip verification)

### 5.2 Dual Verification Architecture

**Primary Channel (Perplexity)**:
```
Claim → Query Construction → Perplexity API → Parse Results → Score
           ↓                                      ↓            ↓
    Optimize for search                    Extract sources  Confidence
```

**Secondary Channel (Reasoning)**:
```
Claim → Context Building → LLM Reasoning → Logical Check → Score
           ↓                   ↓               ↓            ↓
    Related statements    Common sense    Consistency   Confidence
```

### 5.3 Confidence Scoring System

**Score Composition**:
```
Final Score = 0.5 * Perplexity_Score + 0.3 * Reasoning_Score + 0.2 * Source_Quality
```

**Confidence Levels**:
- **HIGH (0.85-1.0)**: Multiple authoritative sources agree
- **MEDIUM (0.60-0.84)**: Single reliable source or partial agreement
- **LOW (0.40-0.59)**: Conflicting information or weak sources
- **UNVERIFIABLE (<0.40)**: No reliable information found

---

## 6. Social Media Generation Design

### 6.1 Quote Selection Pipeline

```
All Quotes → Relevance Filter → Engagement Scoring → Top Selection → Formatting
                ↓                      ↓                  ↓              ↓
          Remove mundane      Predict virality      Best 5-10     Tweet-ready
```

### 6.2 Engagement Scoring Algorithm

**Scoring Factors**:
- **Novelty** (0-1): Uniqueness of insight
- **Emotion** (0-1): Emotional resonance
- **Brevity** (0-1): Conciseness and clarity
- **Controversy** (0-1): Debate potential
- **Actionability** (0-1): Practical value

**Composite Score**:
```
Engagement = 0.3*Novelty + 0.25*Emotion + 0.2*Brevity + 0.15*Controversy + 0.1*Actionability
```

### 6.3 Platform Optimization

**Twitter/X Format**:
- Maximum 280 characters
- Strategic hashtag placement
- Thread potential identification

**LinkedIn Format**:
- Professional tone adjustment
- Longer form (1300 chars)
- Business insight focus

---

## 7. API and CLI Design

### 7.1 REST API Specification

**Core Endpoints**:

```
POST /process
  Body: {
    transcript: {...},
    options: {
      summarization: true,
      fact_checking: true,
      social_media: true,
      parallel_execution: true
    }
  }
  Response: {
    job_id: "uuid",
    status: "pending",
    estimated_time: 180
  }

GET /status/{job_id}
  Response: {
    status: "executing",
    progress: 45,
    current_task: "fact_checking",
    completed_tasks: ["summarization", "quote_extraction"]
  }

GET /result/{job_id}
  Response: {
    summary: {...},
    takeaways: [...],
    quotes: [...],
    fact_checks: [...],
    social_media: {...},
    processing_time: 142.3,
    reasoning_log: [...]
  }
```

### 7.2 CLI Interface Design

**Command Structure**:

```bash
# Basic processing
podcast-ai process episode.json

# With options
podcast-ai process episode.json --parallel --verbose --output-format=markdown

# Batch processing
podcast-ai batch ./transcripts/ --pattern="*.json"

# Real-time monitoring
podcast-ai process episode.json --watch
```

**Progress Display**:
```
Processing Episode: "The Future of Remote Work"
[===========-------] 55% | Fact Checking (12/22 claims verified) | ETA: 1m 23s
├─ ✓ Summarization (32s)
├─ ✓ Quote Extraction (28s)
├─ ⟳ Fact Checking
└─ ⋯ Social Generation
```

---

## 8. Quality Assurance Strategy

### 8.1 Multi-Pass Validation

**Summary Quality Check**:
```
Generate → Self-Critique → Refine → Final Validation
    ↓           ↓           ↓            ↓
  Draft    Check accuracy  Improve   Verify coverage
```

**Fact-Check Validation**:
```
Identify → Verify → Cross-Reference → Confidence Score
    ↓         ↓           ↓                ↓
  Claims   Sources    Reasoning      Final assessment
```

### 8.2 Error Detection Patterns

**Hallucination Detection**:
- Cross-reference with source transcript
- Consistency checking across outputs
- Confidence threshold enforcement

**Quality Metrics**:
- Summary completeness score
- Fact-check coverage rate
- Quote relevance score
- Output coherence measure

---

## 9. Local Development Setup

### 9.1 Directory Structure

```
podcast-ai/
├── src/
│   ├── agents/
│   │   ├── orchestrator.py
│   │   ├── planner.py
│   │   └── executor.py
│   ├── engines/
│   │   ├── summarization.py
│   │   ├── extraction.py
│   │   ├── fact_checking.py
│   │   └── social_media.py
│   ├── llm/
│   │   ├── gateway.py
│   │   ├── prompts.py
│   │   └── models.py
│   ├── api/
│   │   └── server.py
│   └── cli/
│       └── commands.py
├── config/
│   └── settings.yaml
├── tests/
├── outputs/
└── requirements.txt
```

### 9.2 Configuration Management

**Settings Structure** (`config/settings.yaml`):

```yaml
llm:
  openrouter:
    api_key: ${OPENROUTER_API_KEY}
    models:
      summary: claude-3-opus-20240229
      extraction: gpt-4-turbo-preview
  perplexity:
    api_key: ${PERPLEXITY_API_KEY}
    
processing:
  max_parallel_tasks: 5
  chunk_size: 2000
  overlap: 200
  
quality:
  min_confidence_score: 0.6
  max_retries: 3
  validation_passes: 2
```

---

## 10. Agent Reasoning and Logging

### 10.1 Decision Logging Structure

```json
{
  "timestamp": "2025-10-27T10:30:45Z",
  "phase": "planning",
  "decision": "parallel_execution",
  "reasoning": "No dependencies between summarization and extraction tasks",
  "confidence": 0.95,
  "alternatives_considered": ["sequential", "batch"],
  "selected_plan": {
    "tasks": ["summarize", "extract_quotes", "identify_claims"],
    "parallel": true,
    "estimated_time": 45
  }
}
```

### 10.2 Reasoning Transparency

**Logged Decision Points**:
1. Task planning and dependency resolution
2. Model selection for each task
3. Retry decisions on failures
4. Fact-check source selection
5. Confidence score calculations
6. Quality validation outcomes

---