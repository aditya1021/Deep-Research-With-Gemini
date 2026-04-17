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

### Core Concepts (Week 1-2)
1. [Topic 1]: Brief description
2. [Topic 2]: Brief description
... (continue numbering)

### Intermediate Skills (Week 3-4)
3. [Topic 3]: Brief description
...

### Advanced Topics (Week 5-6)
4. [Topic 4]: Brief description
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
        
        # 1. Parse the plan to extract topics
        import re
        # Find all lines starting with a number, a dot, and a space (e.g., "1. ")
        # We capture the full line as the topic description
        topics = []
        for line in plan_content.split('\n'):
            line = line.strip()
            if re.match(r'^\d+\.', line):
                topics.append(line)
        
        print(f"  Found {len(topics)} topics in the plan.")
        
        full_study_material = ""
        total_usage = {
            "prompt_tokens": 0,
            "candidates_tokens": 0,
            "total_tokens": 0
        }
        
        # 2. Generate material for EACH topic individually
        for i, topic_line in enumerate(topics):
            sub_topic = topic_line.split(':', 1)[0] # Just the "1. [Topic Name]" part for logging
            print(f"  Processing topic {i+1}/{len(topics)}: {sub_topic}...")
            
            prompt = f"""
You are writing a section of a definitive study guide on '{topic}'.

Context (The full plan):
{plan_content}

Current Focus:
Write the study material ONLY for this specific topic from the plan:
"{topic_line}"

---
USE THIS STRUCTURE FOR THIS TOPIC, ADOPTING A "SMART BREVITY" STYLE (punchy, scannable, bolding key terms, no fluff, direct):
---

## {topic_line}

### The Big Picture (Explain Like I'm 5)
- **What it is:** A single, punchy sentence explaining the core concept in plain English.
- **Why it matters:** Why was this invented? What exact problem does it solve in the real world?

### Think of it like...
- **The Analogy:** A vivid, highly relatable everyday metaphor. (e.g., "Think of [X] as a [familiar thing] because...")

### The Visual
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

### How it Works (Deep Dive, Step-by-Step)
Explain the mechanism from ZERO. Assume the reader is a complete beginner. **Use bullet points and bold text for scannability, but DO NOT skip the technical depth.** Teach it thoroughly.
1. **The Setup (Input):** Define what comes in and any prerequisites.
2. **The Execution (Process):** Explain exactly what happens under the hood. Define any new terms immediately.
3. **The Result (Output):** Explain what comes out and why.
*Example: [Name a real company, e.g., Netflix] uses this to [Action].*

### Show Me The Code / Example (if technical)
- **The Code:** Provide a clean, minimal snippet (5-15 lines).
- **Line-by-Line Breakdown:**
  - `Line X`: Does [Action] so that [Reason].
  - `Line Y`: Does [Action] so that [Reason].
*(If not a technical coding concept, provide a concrete real-world scenario/workflow instead)*

### Catch & Correct
- **The Myth:** What beginners usually get wrong or confuse this with.
- **The Reality:** The actual truth.

### The Bottom Line
- **Rule of thumb:** The absolute core takeaway or formula to remember.

### Quick Check
Verify you can do each of these (Provide brief sample answers):
- [x] **Explain broadly (30s):** [Simple explanation, no jargon]
- [x] **Explain deeply (2m):** [Detailed technical explanation]
- [x] **Code it:** [Describe the exact minimal snippet needed]
- [x] **Apply it:** [List 2 strict, real-world use cases]

---
CRITICAL REQUIREMENTS:
1. ONLY write about "{topic_line}"
2. INSTRUCTIONAL DEPTH: Explain from ZERO. Assume no prior knowledge. TEACH, don't just summarize. 
3. TONE: Smart Brevity format. Punchy, scannable, confident. Use bolding for key terms. Avoid massive walls of text, but keep the educational depth high.
4. INCLUDE MERMAID DIAGRAM.
5. Provide output in Markdown.
"""
            result = self.generate(prompt)
            full_study_material += result['content'] + "\n\n---\n\n"
            
            # Aggregate usage
            if result.get('usage'):
                total_usage['prompt_tokens'] += result['usage'].get('prompt_tokens', 0)
                total_usage['candidates_tokens'] += result['usage'].get('candidates_tokens', 0)
                total_usage['total_tokens'] += result['usage'].get('total_tokens', 0)
                
            # Small delay to keep within rate limits
            import time
            time.sleep(2)

        return {
            "content": full_study_material,
            "usage": total_usage
        }

class InterviewPrepAgent(Agent):
    def create_qa(self, topic, plan_data):
        print(f"Skipping interview Q&A for: {topic} as requested...")
        return {
            "content": "",
            "usage": {
                "prompt_tokens": 0,
                "candidates_tokens": 0,
                "total_tokens": 0
            }
        }
