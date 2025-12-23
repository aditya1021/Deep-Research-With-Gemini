import os
import sys
import time

# Ensure src is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from src.agents import StudyPlanAgent, StudyMaterialAgent, InterviewPrepAgent
from src.utils import generate_html_report

def main():
    print("Welcome to the Multi-Agent Study System!")
    topic = input("Enter the topic you want to master: ").strip()
    
    if not topic:
        print("Topic cannot be empty.")
        return

    try:
        # Initialize Agents
        print("\nInitializing Agents...")
        plan_agent = StudyPlanAgent()
        material_agent = StudyMaterialAgent()
        interview_agent = InterviewPrepAgent()
        
        total_tokens = {
            "prompt_tokens": 0,
            "candidates_tokens": 0,
            "total_tokens": 0
        }
        
        # Gemini 2.5 Flash pricing (per 1M tokens)
        # Input: $0.15 per 1M tokens (under 200k context)
        # Output: $0.60 per 1M tokens (under 200k context)
        COST_PER_INPUT_TOKEN = 0.15 / 1_000_000
        COST_PER_OUTPUT_TOKEN = 0.60 / 1_000_000
        
        def update_tokens(usage):
            if usage:
                total_tokens["prompt_tokens"] += usage.get("prompt_tokens", 0)
                total_tokens["candidates_tokens"] += usage.get("candidates_tokens", 0)
                total_tokens["total_tokens"] += usage.get("total_tokens", 0)

        # Step 1: Research & Plan
        print("\n--- Phase 1: Deep Research & Planning ---", flush=True)
        study_plan_data = plan_agent.create_plan(topic)
        update_tokens(study_plan_data.get("usage"))
        
        # Step 2: Content Generation
        print("\n--- Phase 2: Generating Comprehensive Study Material ---", flush=True)
        study_material_data = material_agent.create_material(topic, study_plan_data)
        update_tokens(study_material_data.get("usage"))
        
        # Small delay to avoid rate limits
        time.sleep(5)
        
        # Step 3: Interview Prep
        print("\n--- Phase 3: Preparing Interview Questions ---", flush=True)
        interview_qa_data = interview_agent.create_qa(topic, study_plan_data)
        update_tokens(interview_qa_data.get("usage"))

        # Calculate cost
        input_cost = total_tokens["prompt_tokens"] * COST_PER_INPUT_TOKEN
        output_cost = total_tokens["candidates_tokens"] * COST_PER_OUTPUT_TOKEN
        total_cost = input_cost + output_cost
        
        # Add cost info to tokens dict for template
        total_tokens["input_cost"] = input_cost
        total_tokens["output_cost"] = output_cost
        total_tokens["total_cost"] = total_cost

        # Step 4: Final Report
        print("\n--- Phase 4: Compiling Final Report ---", flush=True)
        output_path = generate_html_report(topic, study_plan_data, study_material_data, interview_qa_data, total_tokens)
        
        print(f"\nSuccess! Your study guide is ready at: {output_path}")
        print(f"Absolute path: {os.path.abspath(output_path)}")
        print(f"\n--- Token Usage Summary ---")
        print(f"  Input Tokens:  {total_tokens['prompt_tokens']:,}")
        print(f"  Output Tokens: {total_tokens['candidates_tokens']:,}")
        print(f"  Total Tokens:  {total_tokens['total_tokens']:,}")
        print(f"\n--- Cost Estimate (Gemini 2.5 Flash) ---")
        print(f"  Input Cost:  ${input_cost:.6f}")
        print(f"  Output Cost: ${output_cost:.6f}")
        print(f"  Total Cost:  ${total_cost:.6f}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
