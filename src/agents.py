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
        max_retries = 3
        base_delay = 15  # Increased to 15 seconds for rate limit handling

        for attempt in range(max_retries):
            try:
                config = types.GenerateContentConfig(
                    tools=self.tools if use_tools else None
                )
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config
                )
                
                # Extract content
                text_content = ""
                if response.text:
                    text_content = response.text
                
                # Extract usage metadata
                usage = {
                    "prompt_tokens": 0,
                    "candidates_tokens": 0,
                    "total_tokens": 0
                }
                if response.usage_metadata:
                    usage["prompt_tokens"] = response.usage_metadata.prompt_token_count
                    usage["candidates_tokens"] = response.usage_metadata.candidates_token_count
                    usage["total_tokens"] = response.usage_metadata.total_token_count
                
                # Check for grounding metadata (indicates search was used)
                grounding_used = False
                if hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                        grounding_used = True
                        gm = candidate.grounding_metadata
                        print(f"  ✓ Grounding detected!")
                        if hasattr(gm, 'search_entry_point') and gm.search_entry_point:
                            print(f"    Search Entry Point: {gm.search_entry_point.rendered_content[:100] if gm.search_entry_point.rendered_content else 'N/A'}...")
                        if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                            print(f"    Grounding Chunks: {len(gm.grounding_chunks)} sources found")
                            for i, chunk in enumerate(gm.grounding_chunks[:3]):  # Show first 3
                                if hasattr(chunk, 'web') and chunk.web:
                                    print(f"      [{i+1}] {chunk.web.title}: {chunk.web.uri}")
                
                if use_tools and not grounding_used:
                    print("  ⚠ Warning: Grounding was requested but no grounding metadata returned.")
                
                return {
                    "content": text_content if text_content else "Error: No text content generated.",
                    "usage": usage,
                    "grounded": grounding_used
                }

            except Exception as e:
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
            "content": "<p class='error'>Error: specific max retries exceeded.</p>",
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
        Create a detailed, step-by-step study plan for mastering this topic.
        
        The plan should:
        1. Be structured logically (e.g., Week 1, Week 2, or Module 1, Module 2).
        2. Cover prerequisites, core concepts, and advanced topics.
        3. Include specific sub-topics to focus on.
        4. Be practical and action-oriented.
        
        Provide the output in Markdown format.
        """
        return self.generate(prompt, use_tools=True)

class StudyMaterialAgent(Agent):
    def create_material(self, topic, plan_data):
        print(f"Generating comprehensive study material for: {topic}...")
        plan_content = plan_data['content']
        prompt = f"""
        You are writing a complete, professional textbook chapter on '{topic}'.
        
        Your task is to create an **exhaustive, A-to-Z study guide** that covers EVERY topic mentioned in the study plan below. This must be a ONE-STOP resource - the reader should NOT need any other material to fully understand and master this topic.
        
        Study Plan to Cover:
        {plan_content}
        
        CRITICAL REQUIREMENTS:
        
        1. **COVER EVERY SINGLE TOPIC** from the study plan above. Do not skip ANY topic or sub-topic. Each module, week, and sub-topic must have its own detailed section.
        
        2. **DEPTH OVER BREVITY**: For EACH concept:
           - Define it clearly (what it is)
           - Explain WHY it matters
           - Explain HOW it works (with step-by-step breakdowns)
           - Provide 2-3 practical examples
           - Include code snippets with line-by-line explanations (if technical)
           - List common mistakes/pitfalls
           - Provide practice exercises or thought experiments
        
        3. **BEGINNER TO ADVANCED**: Start each topic from first principles. Assume the reader knows nothing. Build up to advanced concepts progressively.
        
        4. **REAL-WORLD EXAMPLES**: Include industry use cases, practical applications, and scenarios for every major concept.
        
        5. **CODE EXAMPLES** (if technical): Provide complete, runnable code snippets. Add comments explaining each line. Show input/output examples.
        
        6. **NO SHORTCUTS**: Do NOT say "refer to documentation" or "as discussed earlier". Explain everything fully each time.
        
        7. **STRUCTURED FORMAT**: Use clear headings (H2 for modules, H3 for topics, H4 for sub-topics). Use bullet points, numbered lists, and tables where appropriate.
        
        This should be 10,000+ words minimum. Quality and completeness are paramount.
        
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
