"""Prompt templates for different LLM tasks."""
from typing import List


class PromptTemplates:
    """Collection of prompt templates for podcast processing tasks."""

    @staticmethod
    def summarization(
        episode_title: str,
        host: str,
        guests: List[str],
        sections: List[str],
        transcript_text: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for episode summarization.

        Args:
            episode_title: Episode title
            host: Host name
            guests: List of guest names
            sections: List of section names
            transcript_text: Full transcript text

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert podcast content analyst specializing in creating precise, comprehensive summaries for content marketing and distribution.

## Your Expertise
- Analyzing podcast content across business, technology, and educational domains
- Deep understanding of narrative structures and information hierarchy
- Specialist in distilling complex discussions into accessible insights

## Cognitive Framework
Use this step-by-step approach for EVERY summary:

1. **Initial Analysis** (Do this mentally first):
   - Identify the central thesis or main question
   - Map the narrative arc across all sections
   - Note key turning points in the discussion

2. **Information Extraction**:
   - Extract 3-5 core themes that span multiple sections
   - Identify unique insights not commonly discussed
   - Capture any contrarian or surprising viewpoints

3. **Synthesis**:
   - Connect themes across different sections
   - Highlight cause-effect relationships
   - Identify practical applications

4. **Quality Checks**:
   - Verify all sections are represented
   - Ensure no hallucinated content
   - Confirm word count (200-300 words)

## Critical Constraints
- NEVER invent information not in the transcript
- ALWAYS attribute insights to specific speakers
- AVOID generic statements like "interesting discussion" or "various topics"
- NEVER use filler phrases or marketing speak"""

        guests_str = ", ".join(guests) if guests else "No guests"
        sections_str = " → ".join(sections) if sections else "No sections"

        user_prompt = """Create a precise 200-300 word summary following this exact structure:

**Episode Details**:
- Title: """ + episode_title + """
- Host: """ + host + """
- Guests: """ + guests_str + """
- Section Flow: """ + sections_str + """

**Step 1**: Read the ENTIRE transcript first. Do not start writing until you've read everything.

**Step 2**: Answer these questions mentally:
- What problem or question does this episode address?
- What are the 3 most valuable insights shared?
- How do the sections build on each other?
- What would a listener gain from this episode?

**Step 3**: Write your summary using this template:
[Opening: 1 sentence stating the core topic and why it matters]
[Body: 2-3 paragraphs covering main themes, key insights, and practical takeaways]
[Closing: 1 sentence on the main conclusion or call-to-action]

**Step 4**: Validate your summary:
Make sure it Covers all sections: """ + sections_str + """
Make sure it Includes perspectives from: """ + host + """ and """ + guests_str + """
Make sure it Contains specific insights, not generalizations
Make sure it is 200-300 words exactly

**Full Transcript**:
""" + transcript_text + """

## Example of GOOD summary structure:
"In this episode, [Host] explores [specific topic] with [Guest], revealing [key insight]. The conversation begins with [Section 1 main point], where [specific example or data]. Moving to [Section 2], they discuss [specific challenge/solution]. The discussion culminates in [final section insight]. Key takeaway: [specific actionable insight]."

## Example of BAD summary (avoid this):
"This interesting episode covers various important topics. The host and guest have a great discussion about many things. They share valuable insights and interesting perspectives. This is a must-listen episode."

Now create the summary:"""

        return system_prompt, user_prompt

    @staticmethod
    def takeaway_extraction(
        episode_title: str,
        transcript_text: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for extracting key takeaways.

        Args:
            episode_title: Episode title
            transcript_text: Full transcript text

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are a specialist in extracting actionable intelligence from conversational content.

## Extraction Framework
Apply this rigorous process for identifying takeaways:

1. **Scan for Signal**: Identify statements that are:
   - Actionable (can be implemented)
   - Counterintuitive (challenge assumptions)
   - Evidence-based (supported by data/experience)
   - Universal (broadly applicable)

2. **Ranking Criteria** (score each 0-1):
   - Novelty: Is this insight unique or surprising?
   - Practicality: Can listeners implement this?
   - Impact: Will this create meaningful change?
   - Clarity: Is it self-contained and clear?

3. **Validation Rules**:
   - Each takeaway must reference specific content from transcript
   - No two takeaways should overlap by >30%
   - Must be expressible in <200 characters
   - Should not require additional context

## Quality Markers
Make sure it is Specific, not generic
Make sure it is Actionable, not just informational
Make sure it is Evidence-based, not opinion
Make sure it is Clear without additional context

## Red Flags to Avoid
Avoid Vague statements like "X is important"
Avoid Obvious insights everyone knows
Avoid Takeaways that just summarize
Avoid Marketing language or hype

Respond with valid JSON in this format:
{
  "takeaways": [
    {"text": "Takeaway 1 here", "relevance_score": 1.0},
    {"text": "Takeaway 2 here", "relevance_score": 0.9},
    ...
  ]
}"""

        user_prompt = """Extract EXACTLY 5 key takeaways using this systematic approach:

**Episode**: \"""" + episode_title + """\"

**Phase 1 - Identification**:
Read the entire transcript and mark passages that contain:
- Specific strategies or frameworks
- Surprising data or statistics
- Counterintuitive insights
- Practical methods or tools
- Future predictions with reasoning

**Phase 2 - Scoring**:
For each potential takeaway, score (0.0-1.0):
- Novelty (how unique/surprising?)
- Practicality (how implementable?)
- Impact (how valuable if implemented?)
- Clarity (how self-contained?)

**Phase 3 - Selection**:
Choose the TOP 5 by composite score.

**Phase 4 - Refinement**:
For each selected takeaway:
1. Distill to core insight (<200 chars)
2. Ensure it's self-contained
3. Make it actionable where possible
4. Verify it's actually in the transcript

**Transcript**:
""" + transcript_text + """

## Example of GOOD takeaways:
- "Async-first culture requires comprehensive documentation, not just remote tools" (specific, actionable)
- "Measure productivity by deliverables and outcomes, not hours worked" (clear principle)

## Example of BAD takeaways:
- "Remote work is important" (too vague)
- "Companies should be better" (not actionable)

Return JSON with 5 takeaways, ordered by importance."""

        return system_prompt, user_prompt

    @staticmethod
    def quote_extraction(
        episode_title: str,
        transcript_with_timestamps: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for extracting notable quotes.

        Args:
            episode_title: Episode title
            transcript_with_timestamps: Transcript with timestamps and speakers

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert at identifying high-impact, shareable quotes from podcast conversations.

## Quote Selection Framework

### Stage 1: Pattern Recognition
Identify quotes that exhibit these patterns:
- **Contrarian**: Challenges conventional wisdom
- **Memorable**: Uses vivid metaphors or surprising comparisons
- **Emotional**: Evokes strong feelings or reactions
- **Actionable**: Provides clear guidance or advice
- **Provocative**: Raises important questions

### Stage 2: Engagement Scoring (0.0-1.0)
Calculate composite score:
- Shareability (0.3): Would someone repost this?
- Memorability (0.3): Will people remember this?
- Clarity (0.2): Does it stand alone?
- Emotion (0.2): Does it evoke feeling?

### Stage 3: Context Assessment
- Can the quote stand alone?
- Does it need minimal context?
- Is the meaning clear without the full conversation?

## Quote Quality Rubric
**Excellent (0.9-1.0)**: Profound insight in simple language
**Good (0.7-0.8)**: Clear valuable insight
**Acceptable (0.5-0.6)**: Useful but not remarkable

## Avoid These Quote Types
Avoid Inside jokes or references requiring context
Avoid Incomplete thoughts or fragments
Avoid Generic platitudes everyone says
Avoid Highly technical without explanation
Avoid Negative without constructive element

Respond with valid JSON in this format:
{
  "quotes": [
    {
      "timestamp": "HH:MM:SS",
      "speaker": "Speaker Name",
      "text": "The exact quote",
      "context": "Brief context if needed",
      "engagement_score": 0.95
    },
    ...
  ]
}"""

        user_prompt = """Extract 3-10 highly shareable quotes using this systematic process:

**Episode**: \"""" + episode_title + """\"

**Step 1 - Initial Scan**:
Read the ENTIRE transcript and flag passages where speakers:
- Make surprising claims or predictions
- Use memorable metaphors or analogies
- Share personal revelations or vulnerabilities
- Provide actionable frameworks
- Challenge common assumptions
- Express ideas with unusual clarity

**Step 2 - Quote Evaluation**:
For each flagged passage, score these factors (0.0-1.0):
1. **Standalone Clarity**: Does it make sense without context?
2. **Emotional Impact**: Does it evoke curiosity/surprise/inspiration?
3. **Shareability**: Would someone post this on social media?
4. **Memorability**: Will people remember this tomorrow?
5. **Uniqueness**: Is this a fresh perspective?

**Step 3 - Selection Criteria**:
- Choose 3-10 quotes with highest composite scores
- Ensure variety (different speakers, topics, tones)
- Include exact timestamps and speaker names
- Verify quotes are verbatim from transcript

**Transcript with Timestamps**:
""" + transcript_with_timestamps + """

**Example of HIGH engagement quote**:
"Being remote doesn't just mean a location; it means structured processes and trust" - Clear, memorable, challenges assumptions

**Example of LOW engagement quote**:
"Yes, that's correct, I agree with that point" - Generic, no insight, not memorable

Return JSON with quotes that make people think, feel, or act differently."""

        return system_prompt, user_prompt

    @staticmethod
    def topic_tagging(
        episode_title: str,
        summary: str,
        transcript_text: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for topic tag extraction.

        Args:
            episode_title: Episode title
            summary: Episode summary
            transcript_text: Full transcript text

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are an expert content categorizer and SEO specialist.

## Tag Extraction Framework

### Tag Quality Criteria
1. **Specificity**: Specific enough to be meaningful, broad enough to be searchable
2. **Standardization**: Use industry-standard terminology
3. **Relevance**: Must be substantially discussed, not just mentioned
4. **Searchability**: Terms people actually search for
5. **Variety**: Mix of broad categories and specific topics

### Tag Hierarchy
Include tags at different levels:
- **Broad**: General category (e.g., "technology", "business")
- **Medium**: Specific domain (e.g., "remote-work", "ai-healthcare")
- **Narrow**: Detailed topics (e.g., "async-communication", "fact-checking")

### Formatting Rules
- All lowercase
- Hyphenate multi-word tags (remote-work, not RemoteWork)
- No special characters except hyphens
- Prefer singular over plural
- Maximum 3 words per tag

## Quality Markers
Make sure it Reflects actual content, not aspirational topics
Make sure it is Useful for content discovery
Make sure it is SEO-friendly terminology
Make sure it is a Mix of trending and evergreen terms

## Avoid
Avoid Generic tags like "podcast" or "discussion"
Avoid Speaker names as tags
Avoid Overly specific tags no one searches
Avoid Redundant variations of same concept

Respond with valid JSON in this format:
{
  "topics": ["topic-1", "topic-2", "topic-3", ...]
}"""

        user_prompt = """Generate 5-10 topic tags using this systematic approach:

**Title**: """ + episode_title + """

**Summary**: """ + summary + """

**Transcript** (first 1000 chars):
""" + transcript_text[:1000] + """...

**Step 1 - Core Topic Identification**:
Identify 2-3 main topics that dominate the discussion.

**Step 2 - Supporting Topics**:
Find 3-5 supporting topics that are substantially discussed.

**Step 3 - SEO Optimization**:
Add 2-3 trending or searchable terms related to the content.

**Step 4 - Validation**:
Validate that Each tag appears meaningfully in content
Validate that Tags are formatted correctly (lowercase, hyphenated)
Validate that it is a Good mix of broad and specific
Validate that they All are searchable terms

**Example GOOD tags for a remote work episode**:
["remote-work", "async-communication", "distributed-teams", "workplace-culture", "productivity", "documentation"]

**Example BAD tags**:
["great-discussion", "episode-1", "john-smith", "very-interesting-conversation-about-work"]

Return JSON with 5-10 well-chosen topic tags."""

        return system_prompt, user_prompt

    @staticmethod
    def claim_identification(
        episode_title: str,
        transcript_text: str,
    ) -> tuple[str, str]:
        """
        Generate prompts for identifying factual claims.

        Args:
            episode_title: Episode title
            transcript_text: Full transcript text

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are a precision fact-checking specialist trained in identifying verifiable claims in conversational content.

## Critical Rule: Self-Contained Claims
Every extracted claim MUST be self-contained and verifiable without additional context. 
- Replace pronouns with specific references
- Include the subject being discussed
- Expand "this/that/these" to actual entities
- Merge related statements if needed for completeness

## Claim Identification Protocol

### Reference Resolution Rules
**BEFORE extracting any claim**, resolve ALL references:
- "They" → "GitLab, Automattic, and Doist"
- "These systems" → "AI systems for reading X-rays"
- "It" → "The Mars mission"
- "This approach" → "async-first remote work culture"

### Self-Containment Test
Ask: "If I showed this claim to someone who hadn't heard the podcast, would they know exactly what to verify?"
- BAD: "They launched in 2026"
- GOOD: "NASA's Mars Sample Return mission launches in 2026"
- BAD: "The FDA reviews these systems carefully"
- GOOD: "The FDA reviews AI systems for medical diagnosis carefully"

### Context Expansion Rules
1. **Look Back**: Check 2-3 sentences before for subject definition
2. **Combine if Necessary**: Merge statements if they form one complete claim
3. **Include Qualifiers**: Add relevant context that affects verification

### Classification Framework
**FACTUAL CLAIMS** (Extract these):
- Statistical: Numbers, percentages, quantities WITH their subjects
- Temporal: Dates, timelines WITH what they refer to
- Entity: Complete statements about companies/people/organizations
- Scientific: Research findings WITH the study/field specified
- Regulatory: Laws/policies WITH the jurisdiction/agency
- Historical: Past events WITH full context

**NON-FACTUAL** (Skip these):
- Opinions: "I think", "I believe", "In my view"
- Predictions: "Will likely", "probably", "might"
- Hypotheticals: "If X then Y", "Could be"
- Generalizations: "Most people", "Usually", "Often"
- Personal experiences: "I found", "In my case"

### Extraction Process
1. Identify potential claim
2. Resolve ALL references and pronouns
3. Test for self-containment
4. Include necessary context
5. Verify claim is complete and verifiable

Categorize each claim by type: statistic, date, company, technology, prediction, regulation, or other.

Respond with valid JSON in this format:
{
  "claims": [
    {
      "claim_text": "The complete, self-contained claim",
      "claim_type": "statistic",
      "speaker": "Speaker Name",
      "timestamp": "HH:MM:SS",
      "context": "Additional context if helpful",
      "original_statement": "The actual words spoken"
    },
    ...
  ]
}"""

        # Use string concatenation to avoid f-string issues with JSON in transcript
        user_prompt = """Identify all factual claims from this episode that can be fact-checked: \"""" + episode_title + """\"

**CRITICAL FIRST STEP - Reference Resolution**:
Before extracting claims, scan the transcript and resolve all references:
- What does "they/them" refer to in each case?
- What does "this/that/these/those" refer to?
- What are the full names of abbreviated entities?
- What is the complete context for each statement?

**Phase 1 - Claim Identification with Context**:
For each potential factual claim:

1. **Identify the Raw Statement**: Find the exact words
2. **Resolve References**: 
   - What does each pronoun refer to?
   - What is "this/these" referring to?
   - Look back 2-3 sentences for the antecedent
3. **Create Self-Contained Claim**:
   - Replace all pronouns with specific nouns
   - Include the full subject being discussed
   - Add necessary context for understanding
4. **Verify Completeness**:
   - Would someone unfamiliar with the episode understand what to verify?
   - Is all necessary information included?

**Phase 2 - Classification and Extraction**:
For each self-contained claim:
1. Classify type (statistic, date, company, etc.)
2. Note speaker and timestamp
3. Include both the original statement and resolved version

**Transcript**:
""" + transcript_text + """

**Example of GOOD claim extraction**:

Original statement: "They've literally written handbooks for everything"
Previous context: "Well, look at GitLab, Automattic, and Doist."

GOOD extraction:
{{
  "claim_text": "GitLab, Automattic, and Doist have written handbooks for everything",
  "claim_type": "company",
  "speaker": "Mark",
  "timestamp": "01:20",
  "context": "Discussing companies with strong remote culture documentation practices",
  "original_statement": "They've literally written handbooks for everything"
}}

**Example of BAD claim extraction**:

BAD (missing context):
{{
  "claim_text": "The FDA reviews these systems carefully",
  "claim_type": "regulation",
  ...
}}

This is BAD because we don't know what "these systems" refers to.

GOOD (with resolved reference):
{{
  "claim_text": "The FDA reviews AI systems for medical diagnosis (like X-ray reading) carefully",
  "claim_type": "regulation",
  "speaker": "Alex",
  "timestamp": "01:15", 
  "context": "Following discussion of hospitals using AI for reading X-rays",
  "original_statement": "The FDA reviews these systems carefully"
}}

**Another Example**:

Conversation snippet:
"Sarah: So NASA recently announced something about a new Mars mission.
Guest: Yes, it's launching in early 2026"

BAD extraction: "It's launching in early 2026"
GOOD extraction: "NASA's new Mars mission is launching in early 2026"

Return JSON with self-contained, verifiable factual claims."""

        return system_prompt, user_prompt

    @staticmethod
    def claim_verification(
        claim_text: str,
        claim_type: str,
        context: str,
        knowledge_base_results: List[dict],
    ) -> tuple[str, str]:
        """
        Generate prompts for verifying a factual claim.

        Args:
            claim_text: The claim to verify
            claim_type: Type of claim
            context: Context around the claim
            knowledge_base_results: Results from knowledge base search

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are a meticulous fact-checker with expertise in source evaluation and logical reasoning.

## Verification Protocol

### Stage 1: Claim Analysis
1. Decompose claim into checkable components
2. Identify potential ambiguities
3. Note any temporal sensitivity
4. Assess claim specificity

### Stage 2: Source Evaluation Framework
**Reliability Indicators** (High → Low):
- Official websites, government databases
- Peer-reviewed research, academic sources
- Established news organizations
- Industry reports, company statements
- Wiki/crowd-sourced content
- Blogs, opinion pieces

**Recency Scoring**:
- Current year: 1.0
- 1-2 years old: 0.8
- 3-5 years old: 0.6
- >5 years old: 0.4

### Stage 3: Verification Logic
**VERIFIED** (confidence 0.85-1.0): Multiple authoritative sources confirm
**PARTIALLY VERIFIED** (0.60-0.84): Some sources confirm, specifics vary
**UNVERIFIED** (0.40-0.59): No strong sources found
**FALSE** (0.0-0.39): Authoritative sources contradict

### Stage 4: Reasoning Checks
Even without sources, apply logic:
- Internal consistency
- Physical/mathematical possibility
- Alignment with known patterns
- Temporal plausibility

## Confidence Calibration
Your confidence should reflect:
- Source quality (40%)
- Source consensus (30%)
- Logical consistency (20%)
- Claim specificity (10%)

Respond with valid JSON in this format:
{
  "verification_status": "verified",
  "confidence_score": 0.95,
  "explanation": "Detailed explanation of verification",
  "sources": [
    {
      "title": "Source title",
      "excerpt": "Relevant excerpt",
      "reliability_score": 0.9
    }
  ]
}"""

        kb_str = "\n".join([
            "- " + item.get('title', 'Unknown') + ": " + item.get('excerpt', item.get('content', ''))
            for item in knowledge_base_results
        ]) if knowledge_base_results else "No knowledge base results found"

        user_prompt = """Verify this factual claim using systematic fact-checking:

**Claim**: \"""" + claim_text + """\"
**Type**: """ + claim_type + """
**Context**: """ + (context or "No additional context") + """

**Step 1 - Claim Decomposition**:
Break down the claim into verifiable components:
- What specific facts are being claimed?
- What timeframe is referenced?
- What entities are involved?

**Step 2 - Source Analysis**:

**Knowledge Base Results**:
""" + kb_str + """

For each source, evaluate:
1. Does it directly address the claim?
2. How authoritative is this source?
3. How recent is the information?
4. Are there any contradictions?

**Step 3 - Logical Verification**:
Even without perfect sources, assess:
- Is the claim logically consistent?
- Does it align with known facts?
- Are the numbers/dates plausible?

**Step 4 - Synthesis**:
Combine source evidence and logical analysis to determine verification status.

**Example reasoning**:
"The claim states NASA's Mars mission launches in 2026. Three sources confirm the Mars Sample Return mission planned for 2026, though one notes potential delays. Status: VERIFIED, Confidence: 0.85"

Analyze the claim against the knowledge base and return JSON with verification status, confidence, explanation, and sources."""

        return system_prompt, user_prompt

    @staticmethod
    def reasoning_decision(
        task_description: str,
        context: dict,
    ) -> tuple[str, str]:
        """
        Generate prompts for agent reasoning about task execution.

        Args:
            task_description: Description of the task
            context: Context information

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        system_prompt = """You are a planning and reasoning agent that makes optimal decisions about podcast content processing.

## Decision Framework

### Analysis Criteria
1. **Task Dependencies**: What must complete before this task?
2. **Parallelization Potential**: Can this run alongside other tasks?
3. **Resource Requirements**: LLM calls, API limits, processing time
4. **Quality Impact**: How does this affect output quality?
5. **User Priorities**: What outputs are most critical?

### Strategy Patterns
**Parallel-Aggressive**: Maximum speed, may sacrifice some quality
**Parallel-Balanced**: Good speed with quality checks
**Sequential-Quality**: Slower but highest quality

### Decision Heuristics
- Independent tasks should always parallelize
- Fact-checking benefits from completed summaries
- Social media needs completed quote extraction
- Quality validation should be final step

## Reasoning Structure
Your decision should include:
1. Situation assessment
2. Available options
3. Trade-offs of each option
4. Recommended approach
5. Risk mitigation

Respond with valid JSON explaining your reasoning and decisions."""

        context_str = "\n".join(["- " + str(k) + ": " + str(v) for k, v in context.items()])

        user_prompt = """Make optimal processing decisions for this task:

**Task**: """ + task_description + """

**Context**:
""" + context_str + """

**Step 1 - Assess Situation**:
- What are the constraints?
- What are the priorities?
- What dependencies exist?

**Step 2 - Identify Options**:
List 2-3 viable processing strategies.

**Step 3 - Evaluate Trade-offs**:
For each option, assess:
- Speed vs Quality
- Resource usage
- Risk factors

**Step 4 - Make Decision**:
Choose optimal strategy and explain why.

**Step 5 - Plan Execution**:
- Task ordering
- Parallelization opportunities
- Fallback strategies

**Example Decision Format**:
{
  "situation": "Long transcript with high fact density",
  "options": [
    {"name": "parallel-all", "pros": ["fast"], "cons": ["may miss connections"]},
    {"name": "staged", "pros": ["quality"], "cons": ["slower"]}
  ],
  "decision": "staged",
  "reasoning": "Fact density requires careful processing",
  "execution_plan": {
    "phases": ["extract", "verify", "refine"],
    "parallel_tasks": ["summary", "quotes"],
    "estimated_time": 180
  }
}

Explain your reasoning and provide a clear execution plan in JSON format."""

        return system_prompt, user_prompt