import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self, model_name="gemini-2.5-flash", tools=None):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("Warning: GOOGLE_API_KEY not found in environment variables.")
            self.client = None
        else:
            self.client = genai.Client(api_key=api_key)
        
        self.model_name = model_name
        self.tools = tools

    def generate(self, prompt, use_tools=False):
        if not self.client:
             return {
                "content": "Error: API Key is missing or invalid.",
                "usage": {"total_tokens": 0}
            }

        import time
        import sys
        max_retries = 3
        base_delay = 15  # Increased to 15 seconds for rate limit handling

        for attempt in range(max_retries):
            try:
                config = types.GenerateContentConfig(
                    tools=self.tools if use_tools else None
                )
                
                print(f"  Making API call (attempt {attempt + 1}/{max_retries})...")
                
                # Use streaming to prevent timeout on large responses
                response_stream = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                
                # Collect streamed content
                text_content = ""
                usage = {
                    "prompt_tokens": 0,
                    "candidates_tokens": 0,
                    "total_tokens": 0
                }
                grounding_used = False
                chunk_count = 0
                
                print("  Receiving response", end="")
                sys.stdout.flush()
                
                for chunk in response_stream:
                    chunk_count += 1
                    # Show progress every 10 chunks
                    if chunk_count % 10 == 0:
                        print(".", end="")
                        sys.stdout.flush()
                    
                    # Collect text from each chunk
                    if chunk.text:
                        text_content += chunk.text
                    
                    # Get usage from the final chunk (it accumulates)
                    if chunk.usage_metadata:
                        usage["prompt_tokens"] = chunk.usage_metadata.prompt_token_count or 0
                        usage["candidates_tokens"] = chunk.usage_metadata.candidates_token_count or 0
                        usage["total_tokens"] = chunk.usage_metadata.total_token_count or 0
                    
                    # Check for grounding metadata
                    if hasattr(chunk, 'candidates') and chunk.candidates:
                        candidate = chunk.candidates[0]
                        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                            grounding_used = True
                
                print(f" Done! ({chunk_count} chunks received)")
                
                # Log grounding info after streaming completes
                if grounding_used:
                    print(f"  Grounding was used in this response")
                
                if use_tools and not grounding_used:
                    print("  Warning: Grounding was requested but no grounding metadata returned.")
                
                return {
                    "content": text_content if text_content else "Error: No text content generated.",
                    "usage": usage,
                    "grounded": grounding_used
                }

            except Exception as e:
                print("")  # New line after progress dots
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    if attempt < max_retries - 1:
                        sleep_time = base_delay * (2 ** attempt)
                        print(f"Rate limit hit. Retrying in {sleep_time} seconds...")
                        time.sleep(sleep_time)
                        continue
                
                print(f"Error in Agent generation: {e}")
                return {
                    "content": f"<p class='error'>Error generating content: {str(e)}</p>",
                    "usage": {"total_tokens": 0}
                }
        return {
            "content": "<p class='error'>Error: max retries exceeded.</p>",
            "usage": {"total_tokens": 0}
        }

class StudyPlanAgent(Agent):
    def __init__(self):
        # Enable Google Search tool using the new SDK types
        tools = [types.Tool(google_search=types.GoogleSearch())]
        super().__init__(tools=tools)

    def create_plan(self, topic):
        print(f"Generating study plan for: {topic} using Deep Research...")
        prompt = f"""
Act as a senior curriculum developer and researcher.
Use Google Search to perform deep research on the topic: '{topic}' to identify the latest trends, core concepts, and best learning paths.

Create a detailed study plan with CLEARLY NUMBERED TOPICS that can be expanded into full lessons.

## Required Structure:

### Prerequisites (What to know first)
1. [Topic 1]: Brief description (1-2 sentences)
2. [Topic 2]: Brief description (1-2 sentences)

### Core Concepts (Week 1-2)
3. [Topic 3]: Brief description
4. [Topic 4]: Brief description
... (continue numbering)

### Intermediate Skills (Week 3-4)
5. [Topic 5]: Brief description
...

### Advanced Topics (Week 5-6)
6. [Topic 6]: Brief description
...

## Requirements:
- Number EVERY topic sequentially (1, 2, 3...)
- Each topic should be a SINGLE, focused concept
- Keep descriptions to 1-2 sentences
- Include 15-25 total topics for comprehensive coverage
- Order from simplest to most complex

Provide the output in Markdown format.
"""
        return self.generate(prompt, use_tools=True)

class StudyMaterialAgent(Agent):
    def create_material(self, topic, plan_data):
        print(f"Generating comprehensive study material for: {topic}...")
        plan_content = plan_data['content']
        prompt = f"""
You are writing the definitive study guide on '{topic}' for someone who needs to:
1. DEEPLY understand and REMEMBER this for years (not just pass an exam)
2. Be able to EXPLAIN any concept clearly if someone asks them in an interview or discussion

Study Plan to Cover:
{plan_content}

---
FOR EVERY CONCEPT IN THE PLAN, USE THIS EXACT STRUCTURE:
---

## [Concept Name]

### The One-Liner (Memorize This)
- A single, memorable sentence that captures the essence
- This is what you'd say if someone wakes you at 3 AM and asks "What is X?"

### Mental Model (How to Think About It)
- A vivid analogy or metaphor connecting to everyday life
- Example: "Think of [X] as a [familiar thing] because..."
- This creates a 'hook' in your brain for long-term memory

### Visual Memory Aid
Create a simple Mermaid diagram. CRITICAL MERMAID SYNTAX RULES - FOLLOW EXACTLY:

**ALLOWED:**
- Simple alphanumeric text: A, B, C, Data, Process, Output
- Underscores: User_Input, Final_Result
- Simple arrows: -->, ---, -.->, -.->

**FORBIDDEN (will break the diagram):**
- NO parentheses: (example) ❌
- NO square brackets inside labels: [step 1] ❌
- NO curly braces: {{data}} ❌
- NO quotes: "text" or 'text' ❌
- NO colons: key: value ❌
- NO semicolons: A; B ❌
- NO pipes: A | B ❌
- NO ampersands: A & B ❌
- NO percentages: 50% ❌
- NO special chars: @, #, $, *, etc. ❌

**KEEP IT SIMPLE:**
- Maximum 4-5 nodes
- Use single words or underscored_words only
- Use flowchart LR or TD only

CORRECT EXAMPLE:
```mermaid
flowchart LR
    A[Input] --> B[Process]
    B --> C[Output]
```

WRONG EXAMPLE (DO NOT DO THIS):
```mermaid
flowchart LR
    A[User Input (raw)] --> B[Process: Step 1]
```


### Full Explanation (For Deep Understanding)
- Start from ZERO - assume no prior knowledge
- Explain the "WHY" before the "HOW" - why was this created? What problem does it solve?
- Break down the mechanism step-by-step (First... Then... Finally...)
- Use simple language, then introduce technical terms
- Include real-world examples (e.g., "Netflix uses this for...", "This is how Google handles...")

### Code Example with Narration (if technical)
- Show working code with extensive comments
- After the code, explain it in plain English like you're teaching someone
- Show: Input -> What Happens -> Output

### Interview Q&A Practice
Prepare answers for these common questions:

**Q1: "What is [concept] in simple terms?"**
[Provide a 2-3 sentence answer a non-technical person would understand]

**Q2: "How does it actually work under the hood?"**
[Provide a technical but clear explanation]

**Q3: "When should I use this vs [alternative]?"**
[Provide comparison and decision criteria]

**Q4: "What is a common mistake people make with this?"**
[Provide 1-2 gotchas with explanations]

### Common Misconceptions
- "Many people think X, but actually Y because..."
- "Do not confuse this with Z - the key difference is..."
- Things that SOUND right but are WRONG

### Memory Anchors (Lock It In)
- **Acronym/Mnemonic** (if applicable): Create a memorable phrase
- **Key Formula/Pattern**: The core structure to remember
- **Visual**: Describe a simple diagram you could draw from memory
- **Connection**: "This relates to [other concept] because..."

### Self-Test Checklist (With Answers)
Before moving on, verify you can do each of these. Sample answers provided:

- [x] **Explain to a 10-year-old (30 sec)**: 
  [Provide a simple 2-3 sentence explanation using everyday analogies, no jargon]

- [x] **Explain to a senior engineer (2 min)**: 
  [Provide a technical explanation covering: how it works internally, time/space complexity, trade-offs, when to use vs alternatives]

- [x] **Draw the key diagram from memory**: 
  [Describe exactly what to draw - the nodes, arrows, and labels. Reference the Mermaid diagram above]

- [x] **Write a basic code example without looking**: 
  [Provide a minimal, memorable code snippet (5-10 lines) that demonstrates the core concept]

- [x] **List 2 real-world use cases**: 
  [Name 2 specific companies/products and how they use this concept]

---
CRITICAL REQUIREMENTS:
---

1. COVER EVERY SINGLE TOPIC from the study plan above. Do not skip ANY topic.
2. TEACHING TONE: Write as if explaining to a friend who is smart but new to this.
3. EVERY MAJOR CONCEPT MUST HAVE A MERMAID DIAGRAM - keep diagrams simple (max 6-8 nodes).
4. PROGRESSIVE COMPLEXITY: Start simple, go deep.
5. NO HAND-WAVING: Never say "it is complicated" or "refer to docs". Explain everything fully.
6. REAL-WORLD GROUNDING: For every concept, mention where it is used in industry.

Provide the output in Markdown format.
"""
        return self.generate(prompt)

class InterviewPrepAgent(Agent):
    def create_qa(self, topic, plan_data):
        print(f"Generating interview Q&A for: {topic}...")
        plan_content = plan_data['content']
        prompt = f"""
        Act as a senior technical interviewer.
        Based on the topic '{topic}' and the following study plan, create a list of 20 challenging and important interview questions and answers.
        
        Study Plan Context:
        {plan_content}
        
        Include:
        1. Concept-based questions relevant to the plan.
        2. Scenario/Problem-solving questions.
        3. "Gotcha" questions or common pitfalls.
        
        Provide the output in Markdown format.
        """
        return self.generate(prompt)
